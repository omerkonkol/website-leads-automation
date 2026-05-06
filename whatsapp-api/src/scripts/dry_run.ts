import * as fs from "fs";
import * as path from "path";
import { parse } from "csv-parse/sync";
import Database from "better-sqlite3";
import { buildLeadMessage, isFullyHebrewSafe, LeadForMessage } from "../utils/leads_message";

const MANIFEST_PATH = "E:\\הורדות\\manifest (2).csv";
const DB_PATH = "e:/system/leads.db";
const DEFAULT_IMAGE = "E:\\הורדות\\WhatsApp Image 2026-05-01 at 22.17.19 (2).jpeg";

type DbLead = LeadForMessage;

function loadManifest(): Map<number, string> {
  const buffer = fs.readFileSync(MANIFEST_PATH);
  const records = parse(buffer, {
    columns: true,
    skip_empty_lines: true,
    bom: true,
    trim: true,
  }) as Array<Record<string, string>>;
  const map = new Map<number, string>();
  for (const r of records) {
    const id = parseInt(r.id, 10);
    if (id && r.full_url) map.set(id, r.full_url);
  }
  return map;
}

function main() {
  console.log("🧪 DRY RUN — checking inputs\n");

  if (!fs.existsSync(MANIFEST_PATH)) {
    console.error(`❌ Manifest not found: ${MANIFEST_PATH}`);
    process.exit(1);
  }
  if (!fs.existsSync(DB_PATH)) {
    console.error(`❌ DB not found: ${DB_PATH}`);
    process.exit(1);
  }
  if (!fs.existsSync(DEFAULT_IMAGE)) {
    console.error(`❌ Image not found: ${DEFAULT_IMAGE}`);
    process.exit(1);
  }
  console.log("✅ All input files exist");
  console.log(`   Manifest: ${MANIFEST_PATH}`);
  console.log(`   DB:       ${DB_PATH}`);
  console.log(`   Image:    ${DEFAULT_IMAGE}\n`);

  const manifest = loadManifest();
  console.log(`📋 Manifest loaded: ${manifest.size} URLs`);

  const db = new Database(DB_PATH, { readonly: true });
  const candidates = db.prepare(`
    SELECT id, name, phone, category, city, owner_name
    FROM businesses
    WHERE (website IS NULL OR website = '')
      AND phone IS NOT NULL AND phone != ''
      AND (whatsapp_sent IS NULL OR whatsapp_sent = 0)
      AND (blacklisted IS NULL OR blacklisted = 0)
    ORDER BY COALESCE(lead_score, 0) DESC
  `).all() as DbLead[];

  console.log(`📊 DB candidates (no-website, not-sent): ${candidates.length}\n`);

  const matched: Array<DbLead & { url: string }> = [];
  let skippedNoUrl = 0;
  let skippedEnglishName = 0;
  for (const lead of candidates) {
    const url = manifest.get(lead.id);
    if (!url) { skippedNoUrl++; continue; }
    if (!isFullyHebrewSafe(lead)) { skippedEnglishName++; continue; }
    matched.push({ ...lead, url });
    if (matched.length >= 5) break;
  }

  console.log(`🎯 Matched (DB ∩ manifest, Hebrew-name only), showing first 5:\n`);
  for (const lead of matched) {
    console.log(`──────────────────────────────────────`);
    console.log(`ID: ${lead.id}  |  ${lead.name}`);
    console.log(`Phone: ${lead.phone}  |  Category: ${lead.category}  |  City: ${lead.city}`);
    console.log(``);
    console.log(buildLeadMessage(lead, lead.url));
    console.log(``);
    console.log(`[image: ${path.basename(DEFAULT_IMAGE)}]`);
    console.log(``);
  }

  // Stats over the whole candidate pool
  const allMatched = candidates.filter((c) => manifest.has(c.id));
  const fullyHebrew = allMatched.filter((c) => isFullyHebrewSafe(c));
  console.log(`──────────────────────────────────────`);
  console.log(`Total candidates loaded: ${candidates.length}`);
  console.log(`  ↳ with manifest URL:    ${allMatched.length}`);
  console.log(`  ↳ Hebrew-name + URL:    ${fullyHebrew.length}  (will be sent to)`);
  console.log(`  ↳ skipped (no URL):     ${skippedNoUrl}`);
  console.log(`  ↳ skipped (English):    ${skippedEnglishName}`);

  db.close();
}

main();
