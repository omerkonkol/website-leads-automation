import ExcelJS from "exceljs";

export interface LeadRow {
  name: string;
  phone: string;
  message: string;
  status: string;
}

/**
 * Parse an Excel buffer into an array of LeadRow objects.
 * Accepts columns named: name, phone/number, message, status (any casing).
 */
export async function parseExcelBuffer(buffer: Buffer): Promise<LeadRow[]> {
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.load(buffer as unknown as ExcelJS.Buffer);
  const sheet = workbook.worksheets[0];
  if (!sheet) {
    throw new Error("Excel file contains no sheets.");
  }

  // Read header row to map column indices
  const headerRow = sheet.getRow(1);
  const colMap: Record<string, number> = {};
  headerRow.eachCell((cell, colNumber) => {
    const key = String(cell.value ?? "").toLowerCase().trim();
    colMap[key] = colNumber;
  });

  // Find columns by possible names
  function findCol(...keys: string[]): number | undefined {
    for (const k of keys) {
      if (colMap[k] !== undefined) return colMap[k];
    }
    return undefined;
  }

  const nameCol = findCol("name");
  const phoneCol = findCol("phone", "number");
  const messageCol = findCol("message");
  const statusCol = findCol("status");

  const rows: LeadRow[] = [];
  sheet.eachRow((row, rowNumber) => {
    if (rowNumber === 1) return; // skip header

    const name = nameCol ? String(row.getCell(nameCol).value ?? "").trim() : "";
    const phone = phoneCol ? String(row.getCell(phoneCol).value ?? "").trim() : "";
    const message = messageCol ? String(row.getCell(messageCol).value ?? "").trim() : "";
    const status = statusCol ? String(row.getCell(statusCol).value ?? "").trim() : "";

    if (!phone || !message) {
      console.warn(`⚠️  Row ${rowNumber}: missing phone or message — will be skipped.`);
    }

    rows.push({ name, phone, message, status });
  });

  return rows;
}

/**
 * Convert an array of LeadRow objects back into an Excel buffer (.xlsx).
 */
export async function buildExcelBuffer(rows: LeadRow[]): Promise<Buffer> {
  const workbook = new ExcelJS.Workbook();
  const sheet = workbook.addWorksheet("Campaign");

  sheet.columns = [
    { header: "name", key: "name" },
    { header: "phone", key: "phone" },
    { header: "message", key: "message" },
    { header: "status", key: "status" },
  ];

  for (const row of rows) {
    sheet.addRow(row);
  }

  const arrayBuffer = await workbook.xlsx.writeBuffer();
  return Buffer.from(arrayBuffer);
}
