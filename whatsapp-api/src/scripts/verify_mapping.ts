import * as fs from "fs";
import { parse } from "csv-parse/sync";
import Database from "better-sqlite3";
import { isFullyHebrewSafe, LeadForMessage } from "../utils/leads_message";

const MANIFEST_PATH = "E:\\הורדות\\manifest (2).csv";
const DB_PATH = "e:/system/leads.db";

interface ManifestRow {
  id: string;
  name: string;
  phone: string;
  category: string;
  city: string;
  url_path: string;
  full_url: string;
}

function normPhone(p: string): string {
  return (p || "").replace(/\D/g, "").replace(/^972/, "0");
}

function main() {
  const buf = fs.readFileSync(MANIFEST_PATH);
  const csvRows = parse(buf, {
    columns: true,
    skip_empty_lines: true,
    bom: true,
    trim: true,
  }) as ManifestRow[];
  const csvById = new Map<number, ManifestRow>();
  for (const r of csvRows) {
    const id = parseInt(r.id, 10);
    if (id) csvById.set(id, r);
  }

  const db = new Database(DB_PATH, { readonly: true });
  const dbLeads = db.prepare(`
    SELECT id, name, phone, category, city, owner_name
    FROM businesses
    WHERE (website IS NULL OR website = '')
      AND phone IS NOT NULL AND phone != ''
      AND (whatsapp_sent IS NULL OR whatsapp_sent = 0)
      AND (blacklisted IS NULL OR blacklisted = 0)
    ORDER BY COALESCE(lead_score, 0) DESC
  `).all() as LeadForMessage[];

  let total = 0;
  let urlMismatch = 0;
  let phoneMismatch = 0;
  let nameDiff = 0;
  let englishSkipped = 0;
  const sampleMismatches: string[] = [];

  for (const lead of dbLeads) {
    const csv = csvById.get(lead.id);
    if (!csv) continue;
    if (!isFullyHebrewSafe(lead)) {
      englishSkipped++;
      continue;
    }
    total++;

    // 1. URL must contain the lead's ID
    const urlContainsId = csv.full_url.includes(`-${lead.id}/`) || csv.full_url.includes(`/l/${lead.id}/`);
    if (!urlContainsId) {
      urlMismatch++;
      if (sampleMismatches.length < 5) {
        sampleMismatches.push(`URL missing ID ${lead.id}: ${csv.full_url}`);
      }
    }

    // 2. Phone in CSV must roughly match phone in DB
    if (normPhone(csv.phone) !== normPhone(lead.phone)) {
      phoneMismatch++;
      if (sampleMismatches.length < 10) {
        sampleMismatches.push(`Phone mismatch id=${lead.id}: DB=${lead.phone} CSV=${csv.phone}`);
      }
    }

    // 3. Name should match (informational only — names can be slightly different formatting)
    if ((csv.name || "").trim() !== (lead.name || "").trim()) {
      nameDiff++;
    }
  }

  console.log("\n📋 VERIFICATION REPORT\n");
  console.log(`DB candidates: ${dbLeads.length}`);
  console.log(`Manifest entries: ${csvById.size}`);
  console.log(`Skipped (English-only name): ${englishSkipped}`);
  console.log(`Verified pairs (will be sent): ${total}`);
  console.log(``);
  console.log(`✅ URL contains lead ID:      ${total - urlMismatch}/${total}`);
  console.log(`${urlMismatch === 0 ? '✅' : '❌'} URL ID-mismatches:        ${urlMismatch}`);
  console.log(`${phoneMismatch === 0 ? '✅' : '⚠️ '} Phone DB↔CSV mismatches:  ${phoneMismatch}`);
  console.log(`ℹ️  Name DB↔CSV differs:     ${nameDiff} (informational; we use DB name)`);

  if (sampleMismatches.length > 0) {
    console.log(`\nFirst mismatches:`);
    sampleMismatches.forEach((m) => console.log(`   - ${m}`));
  }

  console.log(``);
  if (urlMismatch === 0) {
    console.log(`✅ All ${total} leads have a URL that correctly contains their ID. Safe to send.`);
  } else {
    console.log(`❌ STOP — ${urlMismatch} URL mismatches. Do NOT send until resolved.`);
    process.exit(1);
  }

  db.close();
}

main();
