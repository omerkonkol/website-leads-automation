import * as XLSX from "xlsx";

export interface LeadRow {
  name: string;
  phone: string;
  message: string;
  status: string;
}

/**
 * Find a value in a row object by trying multiple possible column names (case-insensitive).
 */
function findColumn(row: Record<string, unknown>, ...keys: string[]): string {
  for (const key of Object.keys(row)) {
    const lower = key.toLowerCase().trim();
    if (keys.includes(lower)) {
      return String(row[key] ?? "").trim();
    }
  }
  return "";
}

/**
 * Parse an Excel buffer into an array of LeadRow objects.
 * Accepts columns named: name, phone/number, message, status (any casing).
 */
export function parseExcelBuffer(buffer: Buffer): LeadRow[] {
  const workbook = XLSX.read(buffer, { type: "buffer" });
  const sheetName = workbook.SheetNames[0];
  if (!sheetName) {
    throw new Error("Excel file contains no sheets.");
  }

  const sheet = workbook.Sheets[sheetName];
  const rows = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet);

  return rows.map((row, index) => {
    const name = findColumn(row, "name");
    const phone = findColumn(row, "phone", "number");
    const message = findColumn(row, "message");
    const status = findColumn(row, "status");

    if (!phone || !message) {
      console.warn(
        `⚠️  Row ${index + 2}: missing phone or message — will be skipped.`
      );
    }

    return { name, phone, message, status };
  });
}

/**
 * Convert an array of LeadRow objects back into an Excel buffer (.xlsx).
 */
export function buildExcelBuffer(rows: LeadRow[]): Buffer {
  const worksheet = XLSX.utils.json_to_sheet(rows);
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Campaign");
  return XLSX.write(workbook, { type: "buffer", bookType: "xlsx" }) as Buffer;
}
