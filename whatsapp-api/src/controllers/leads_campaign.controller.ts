import { Request, Response } from "express";
import * as fs from "fs";
import * as path from "path";
import { parse } from "csv-parse/sync";
import Database from "better-sqlite3";
import { accountPool } from "../services/whatsapp_pool";
import { dispatcher } from "../services/dispatcher";
import { randomSleep, coffeBreakSleep } from "../utils/sleep";
import { buildLeadMessage, isFullyHebrewSafe, LeadForMessage } from "../utils/leads_message";

// Use the v2-generated manifest (premium dark template, real services, hours, etc.).
// Fall back to the original Cloudflare manifest if the new one isn't there.
const MANIFEST_PATH_V2 = "e:/system/leads-landing-pages/manifest.csv";
const MANIFEST_PATH_V1 = "E:\\הורדות\\manifest (2).csv";
const MANIFEST_PATH = fs.existsSync(MANIFEST_PATH_V2) ? MANIFEST_PATH_V2 : MANIFEST_PATH_V1;
const DB_PATH = "e:/system/leads.db";
const DEFAULT_IMAGE = "E:\\הורדות\\WhatsApp Image 2026-05-01 at 22.17.19 (2).jpeg";
const COFFEE_BREAK_EVERY = 10;
const SEND_HOUR_START = 9;
const SEND_HOUR_END = 22;

let dailySentCount = 0;
let dailyResetDate = new Date().toDateString();
let stopRequested = false;

export function stopLeadsCampaign(_req: Request, res: Response): void {
  stopRequested = true;
  res.json({ stopped: true });
}

function checkDailyLimit(limit: number): boolean {
  const today = new Date().toDateString();
  if (today !== dailyResetDate) {
    dailySentCount = 0;
    dailyResetDate = today;
  }
  return dailySentCount < limit;
}

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

type DbLead = LeadForMessage;

function loadLeads(db: Database.Database, limit: number): DbLead[] {
  return db.prepare(`
    SELECT id, name, phone, category, city, owner_name, google_rating, google_reviews
    FROM businesses
    WHERE (website IS NULL OR website = '')
      AND phone IS NOT NULL AND phone != ''
      AND (whatsapp_sent IS NULL OR whatsapp_sent = 0)
      AND (blacklisted IS NULL OR blacklisted = 0)
    ORDER BY COALESCE(lead_score, 0) DESC
    LIMIT ?
  `).all(limit) as DbLead[];
}

function isWithinSendingHours(): boolean {
  const formatter = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Jerusalem",
    hour: "numeric",
    hour12: false,
  });
  const parts = formatter.formatToParts(new Date());
  const hourStr = parts.find((p) => p.type === "hour")?.value ?? "0";
  const hour = parseInt(hourStr, 10);
  return hour >= SEND_HOUR_START && hour < SEND_HOUR_END;
}

export async function sendLeadsCampaign(
  req: Request,
  res: Response
): Promise<void> {
  try {
    const dryRun = req.body.dryRun === true || req.body.dryRun === "true";
    const dailyLimit = parseInt(String(req.body.dailyLimit), 10) || 20;
    const imagePath: string = req.body.imagePath || DEFAULT_IMAGE;
    const testPhone: string | undefined = req.body.testPhone;
    const testLeadId: number | undefined = req.body.testLeadId
      ? parseInt(String(req.body.testLeadId), 10)
      : undefined;

    if (!fs.existsSync(imagePath)) {
      res.status(400).json({ error: `Image not found: ${imagePath}` });
      return;
    }

    if (!fs.existsSync(MANIFEST_PATH)) {
      res.status(400).json({ error: `Manifest CSV not found: ${MANIFEST_PATH}` });
      return;
    }

    if (!fs.existsSync(DB_PATH)) {
      res.status(400).json({ error: `DB not found: ${DB_PATH}` });
      return;
    }

    if (!dryRun) {
      const ready = accountPool.ready();
      if (ready.length === 0) {
        res.status(503).json({ error: "No WhatsApp accounts ready." });
        return;
      }
      // testPhone bypasses sending-hours and daily-limit checks
      if (!testPhone) {
        if (!isWithinSendingHours()) {
          res.status(429).json({
            error: `Outside sending hours (${SEND_HOUR_START}:00-${SEND_HOUR_END}:00 IST). Try again later.`,
          });
          return;
        }
        if (!checkDailyLimit(dailyLimit)) {
          res.status(429).json({
            error: `Daily limit reached (${dailyLimit}).`,
            dailySent: dailySentCount,
          });
          return;
        }
      }
    }

    // ── TEST-PHONE SHORTCUT ──────────────────────────────────────────
    // Sends ONE message to testPhone using a real lead's content (default: top-priority lead, or testLeadId).
    // Does NOT update DB. For verification only.
    if (testPhone && !dryRun) {
      const manifest = loadManifest();
      const db = new Database(DB_PATH, { readonly: true });

      let lead: (DbLead & { url: string }) | null = null;
      if (testLeadId) {
        const row = db.prepare(`
          SELECT id, name, phone, category, city, owner_name FROM businesses WHERE id = ?
        `).get(testLeadId) as DbLead | undefined;
        if (row) {
          const url = manifest.get(row.id);
          if (url) lead = { ...row, url };
        }
      } else {
        const candidates = loadLeads(db, 50);
        for (const c of candidates) {
          const url = manifest.get(c.id);
          if (url && isFullyHebrewSafe(c)) { lead = { ...c, url }; break; }
        }
      }
      db.close();

      if (!lead) {
        res.status(404).json({ error: "No lead matched for test send." });
        return;
      }

      const message = buildLeadMessage(lead, lead.url);
      try {
        const result = await dispatcher.send({ leadId: lead.id, peerPhone: testPhone }, message, imagePath);
        console.log(`   🧪 TEST sent to ${testPhone} from ${result.accountPhone} using lead ${lead.id} (${lead.name})`);
        res.json({
          test: true,
          sentTo: testPhone,
          fromAccount: result.accountPhone,
          leadUsed: { id: lead.id, name: lead.name, phone: lead.phone, url: lead.url },
          message,
          image: imagePath,
        });
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err);
        console.error(`   ❌ TEST send failed: ${errMsg}`);
        res.status(500).json({ error: "Test send failed", details: errMsg });
      }
      return;
    }

    const manifest = loadManifest();
    const db = new Database(DB_PATH, { readonly: dryRun });

    const remainingToday = dryRun ? 5 : dailyLimit - dailySentCount;
    // Pull more candidates than needed because some get filtered out
    // (no manifest URL, or business name lacks Hebrew chars)
    const candidates = loadLeads(db, Math.max(remainingToday * 5, 100));

    const leads: Array<DbLead & { url: string }> = [];
    let skippedNoUrl = 0;
    let skippedEnglishName = 0;
    for (const lead of candidates) {
      const url = manifest.get(lead.id);
      if (!url) { skippedNoUrl++; continue; }
      if (!isFullyHebrewSafe(lead)) { skippedEnglishName++; continue; }
      leads.push({ ...lead, url });
      if (leads.length >= remainingToday) break;
    }

    if (leads.length === 0) {
      db.close();
      res.json({
        message: "No matching leads (DB candidates without URL in manifest).",
        manifest_size: manifest.size,
        db_candidates: candidates.length,
      });
      return;
    }

    console.log(`\n📋 Leads campaign — ${leads.length} leads. dryRun=${dryRun}`);
    console.log(`   📊 Daily sent today: ${dailySentCount}/${dailyLimit}`);
    console.log(`   🖼  Image: ${imagePath}\n`);

    if (dryRun) {
      const preview = leads.slice(0, 5).map((lead) => ({
        id: lead.id,
        name: lead.name,
        phone: lead.phone,
        category: lead.category,
        city: lead.city,
        url: lead.url,
        message: buildLeadMessage(lead, lead.url),
      }));

      console.log("🧪 DRY RUN — first 5 messages:\n");
      for (const p of preview) {
        console.log(`─── ID ${p.id}: ${p.name} (${p.phone}) ───`);
        console.log(p.message);
        console.log(`\n[image: ${path.basename(imagePath)}]`);
        console.log("");
      }

      db.close();
      res.json({
        dryRun: true,
        manifest_size: manifest.size,
        db_candidates: candidates.length,
        matched: leads.length,
        skipped_no_url: skippedNoUrl,
        skipped_english_name: skippedEnglishName,
        image_path: imagePath,
        preview,
      });
      return;
    }

    const updateStmt = db.prepare(`
      UPDATE businesses
      SET whatsapp_sent = 1, whatsapp_sent_at = ?, pipeline_stage = 'contacted'
      WHERE id = ?
    `);
    const logStmt = db.prepare(`
      INSERT INTO outreach_log (business_id, channel, status, message, sent_at)
      VALUES (?, 'whatsapp', ?, ?, ?)
    `);

    const results: Array<{ id: number; phone: string; status: string; error?: string; account?: string }> = [];
    let sent = 0;
    let failed = 0;
    let consecutiveFails = 0;

    stopRequested = false;
    for (let i = 0; i < leads.length; i++) {
      const lead = leads[i];

      if (stopRequested) {
        console.log(`   🛑 Stop requested — halting campaign.`);
        break;
      }

      if (sent >= remainingToday) {
        console.log(`   🛑 Daily limit (${dailyLimit}) reached.`);
        break;
      }

      if (consecutiveFails >= 3) {
        console.error(`   🚨 3 consecutive failures — stopping batch to avoid ban.`);
        break;
      }

      const message = buildLeadMessage(lead, lead.url);
      const sentAt = new Date().toISOString();

      try {
        const result = await dispatcher.send({ leadId: lead.id, peerPhone: lead.phone }, message, imagePath);
        updateStmt.run(sentAt, lead.id);
        // outreach_log now also tracks which account sent
        db.prepare(`
          INSERT INTO outreach_log (business_id, channel, status, message, sent_at, account_phone)
          VALUES (?, 'whatsapp', 'sent', ?, ?, ?)
        `).run(lead.id, message, sentAt, result.accountPhone);
        sent++;
        dailySentCount++;
        consecutiveFails = 0;
        results.push({ id: lead.id, phone: lead.phone, status: "sent", account: result.accountPhone });
        console.log(`   ✅ [${result.accountPhone}] ${lead.name} (${lead.phone}) [${dailySentCount}/${dailyLimit}]`);
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err);
        const isNoLid = errMsg.includes("No LID");
        logStmt.run(lead.id, "failed", `${message}\n\nERROR: ${errMsg}`, sentAt);
        // Mark no-LID leads so they won't be retried
        if (isNoLid) {
          db.prepare(`UPDATE businesses SET whatsapp_sent=1, whatsapp_sent_at=?, notes='No WhatsApp - No LID' WHERE id=?`)
            .run(sentAt, lead.id);
        }
        failed++;
        if (!isNoLid) consecutiveFails++;
        results.push({ id: lead.id, phone: lead.phone, status: "failed", error: errMsg });
        console.error(`   ❌ ${lead.name} (${lead.phone}) — ${errMsg}`);
      }

      const isLast = i === leads.length - 1 || sent >= remainingToday;
      if (!isLast) {
        if (sent > 0 && sent % COFFEE_BREAK_EVERY === 0) {
          await coffeBreakSleep(300000, 600000);
        } else {
          await randomSleep(30000, 60000);
        }
      }
    }

    db.close();

    console.log(`\n📊 Done — Sent: ${sent}, Failed: ${failed}\n`);
    res.json({
      sent,
      failed,
      total: leads.length,
      dailySent: dailySentCount,
      stoppedEarly: consecutiveFails >= 3,
      results,
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("💥 Leads campaign error:", message);
    res.status(500).json({ error: "Campaign failed.", details: message });
  }
}
