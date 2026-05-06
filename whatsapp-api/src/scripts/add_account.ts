/**
 * Add a new WhatsApp Business account to the pool.
 *
 * Usage:
 *   npm run add-account -- --phone +972XXXXXXXXX --label secondary
 *
 * Boots a whatsapp-web.js client, prints QR, waits for ready, inserts
 * a row in wa_accounts.
 */
import Database from "better-sqlite3";
import { WhatsAppAccount } from "../services/whatsapp_account";

const DB_PATH = "e:/system/leads.db";

function arg(name: string): string | undefined {
  const i = process.argv.findIndex((a) => a === `--${name}`);
  return i >= 0 ? process.argv[i + 1] : undefined;
}

async function main() {
  const phone = arg("phone");
  const label = arg("label") || "secondary";
  const dailyLimit = parseInt(arg("daily-limit") || "20", 10);

  if (!phone || !phone.startsWith("+")) {
    console.error('Usage: npm run add-account -- --phone +972XXXXXXXXX [--label secondary] [--daily-limit 20]');
    process.exit(1);
  }

  // Check not already present
  const db = new Database(DB_PATH);
  try {
    const existing = db.prepare("SELECT phone, status FROM wa_accounts WHERE phone=?").get(phone) as
      | { phone: string; status: string } | undefined;
    if (existing) {
      console.warn(`Account ${phone} already exists (status=${existing.status}). Re-using session...`);
    } else {
      db.prepare(`
        INSERT INTO wa_accounts (phone, label, status, daily_limit, branding_set)
        VALUES (?, ?, 'pending', ?, 0)
      `).run(phone, label, dailyLimit);
      console.log(`📝 Inserted ${phone} into wa_accounts (label=${label}).`);
    }
  } finally {
    db.close();
  }

  const acc = new WhatsAppAccount(phone, label);
  await acc.initialize();

  // Mark ready
  const db2 = new Database(DB_PATH);
  try {
    db2.prepare("UPDATE wa_accounts SET status='ready' WHERE phone=?").run(phone);
  } finally {
    db2.close();
  }

  console.log(`\n✅ Account ${phone} ready. Remember to set Business Name = "NovaDigital" in WhatsApp Business app, then run:`);
  console.log(`   sqlite3 ${DB_PATH} "UPDATE wa_accounts SET branding_set=1 WHERE phone='${phone}';"`);
  console.log(`\nYou can now Ctrl+C to exit. The next server start will pick up this account automatically.`);
}

main().catch((e) => {
  console.error("Fatal:", e);
  process.exit(1);
});
