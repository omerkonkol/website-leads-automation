import { Request, Response } from "express";
import { whatsappService } from "../services/whatsapp.service";
import { parseExcelBuffer, buildExcelBuffer, LeadRow } from "../utils/excel";
import { randomSleep, coffeBreakSleep } from "../utils/sleep";

// ── Anti-ban settings ─────────────────────────────────────────────
const MAX_MESSAGES_PER_BATCH = 40;    // Don't send more than this per request
const COFFEE_BREAK_EVERY = 5;          // Take a long pause every N messages

// Track daily sends across requests (resets on server restart)
let dailySentCount = 0;
let dailyResetDate = new Date().toDateString();
const MAX_MESSAGES_PER_DAY = 80;

function checkDailyLimit(): boolean {
  const today = new Date().toDateString();
  if (today !== dailyResetDate) {
    dailySentCount = 0;
    dailyResetDate = today;
  }
  return dailySentCount < MAX_MESSAGES_PER_DAY;
}

/**
 * Replace {{name}} placeholders in the message with the contact's name.
 * This makes each message unique — critical for avoiding bans.
 */
function personalizeMessage(template: string, name: string): string {
  return template.replace(/\{\{name\}\}/gi, name || "");
}

export async function sendCampaign(
  req: Request,
  res: Response
): Promise<void> {
  try {
    // ── Validate upload ───────────────────────────────────────────────
    if (!req.file) {
      res.status(400).json({ error: "No file uploaded. Send an .xlsx file." });
      return;
    }

    if (!whatsappService.getIsReady()) {
      res.status(503).json({ error: "WhatsApp client is not ready yet." });
      return;
    }

    if (!checkDailyLimit()) {
      res.status(429).json({
        error: `Daily limit reached (${MAX_MESSAGES_PER_DAY}). Try again tomorrow.`,
        dailySent: dailySentCount,
      });
      return;
    }

    // ── Parse Excel ───────────────────────────────────────────────────
    const rows: LeadRow[] = await parseExcelBuffer(req.file.buffer);
    if (rows.length === 0) {
      res.status(400).json({ error: "Excel file contains no data rows." });
      return;
    }

    console.log(`\n📋 Campaign started — ${rows.length} rows loaded.`);
    console.log(`   📊 Daily sent so far: ${dailySentCount}/${MAX_MESSAGES_PER_DAY}`);
    console.log(`   📦 Batch limit: ${MAX_MESSAGES_PER_BATCH}\n`);

    let sent = 0;
    let skipped = 0;
    let failed = 0;

    // ── Send loop ─────────────────────────────────────────────────────
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];

      // Batch limit
      if (sent >= MAX_MESSAGES_PER_BATCH) {
        console.log(`   🛑 Batch limit reached (${MAX_MESSAGES_PER_BATCH}). Stopping.`);
        break;
      }

      // Daily limit
      if (!checkDailyLimit()) {
        console.log(`   🛑 Daily limit reached (${MAX_MESSAGES_PER_DAY}). Stopping.`);
        break;
      }

      // Skip already-sent rows
      if (row.status.toLowerCase() === "sent") {
        console.log(`   ⏭  Row ${i + 2}: already sent — skipping.`);
        skipped++;
        continue;
      }

      // Skip rows with missing data
      if (!row.phone || !row.message) {
        console.log(`   ⏭  Row ${i + 2}: missing phone or message — skipping.`);
        row.status = "Skipped";
        skipped++;
        continue;
      }

      try {
        // Personalize the message so each one is unique
        const personalizedMsg = personalizeMessage(row.message, row.name);

        await whatsappService.sendMessage(row.phone, personalizedMsg);
        row.status = "Sent";
        sent++;
        dailySentCount++;
        console.log(
          `   ✅ Row ${i + 2}: sent to ${row.phone} (${row.name}) [${dailySentCount}/${MAX_MESSAGES_PER_DAY} today]`
        );
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        row.status = "Failed";
        failed++;
        console.error(
          `   ❌ Row ${i + 2}: failed for ${row.phone} — ${message}`
        );
      }

      // Delay between messages (skip after last row)
      if (i < rows.length - 1) {
        // Every N messages, take a longer "coffee break"
        if (sent > 0 && sent % COFFEE_BREAK_EVERY === 0) {
          await coffeBreakSleep();
        } else {
          await randomSleep();
        }
      }
    }

    // ── Build updated Excel and respond ───────────────────────────────
    const updatedBuffer = await buildExcelBuffer(rows);

    console.log(
      `\n📊 Campaign finished — Sent: ${sent}, Skipped: ${skipped}, Failed: ${failed}`
    );
    console.log(`   📊 Daily total: ${dailySentCount}/${MAX_MESSAGES_PER_DAY}\n`);

    res.setHeader(
      "Content-Disposition",
      'attachment; filename="campaign_result.xlsx"'
    );
    res.setHeader(
      "Content-Type",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    );
    res.send(updatedBuffer);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("💥 Campaign error:", message);
    res.status(500).json({ error: "Campaign processing failed.", details: message });
  }
}


/**
 * JSON-based campaign endpoint — accepts { leads: [{name, phone, message}] }
 * Returns JSON with per-lead results instead of an Excel file.
 */
export async function sendCampaignJson(
  req: Request,
  res: Response
): Promise<void> {
  try {
    const { leads } = req.body as {
      leads: Array<{ id?: number; name: string; phone: string; message: string }>;
    };

    if (!leads || !Array.isArray(leads) || leads.length === 0) {
      res.status(400).json({ error: "Missing or empty 'leads' array in body." });
      return;
    }

    if (!whatsappService.getIsReady()) {
      res.status(503).json({ error: "WhatsApp client is not ready yet." });
      return;
    }

    if (!checkDailyLimit()) {
      res.status(429).json({
        error: `Daily limit reached (${MAX_MESSAGES_PER_DAY}). Try again tomorrow.`,
        dailySent: dailySentCount,
      });
      return;
    }

    console.log(`\n📋 JSON Campaign started — ${leads.length} leads.`);
    console.log(`   📊 Daily sent so far: ${dailySentCount}/${MAX_MESSAGES_PER_DAY}\n`);

    const results: Array<{ id?: number; phone: string; status: string; error?: string }> = [];
    let sent = 0;
    let failed = 0;

    for (let i = 0; i < leads.length; i++) {
      const lead = leads[i];

      if (sent >= MAX_MESSAGES_PER_BATCH) {
        console.log(`   🛑 Batch limit reached (${MAX_MESSAGES_PER_BATCH}).`);
        break;
      }

      if (!checkDailyLimit()) {
        console.log(`   🛑 Daily limit reached (${MAX_MESSAGES_PER_DAY}).`);
        break;
      }

      if (!lead.phone || !lead.message) {
        results.push({ id: lead.id, phone: lead.phone || "", status: "skipped", error: "missing phone or message" });
        continue;
      }

      try {
        const personalizedMsg = personalizeMessage(lead.message, lead.name);
        await whatsappService.sendMessage(lead.phone, personalizedMsg);
        sent++;
        dailySentCount++;
        results.push({ id: lead.id, phone: lead.phone, status: "sent" });
        console.log(`   ✅ ${lead.name} (${lead.phone}) [${dailySentCount}/${MAX_MESSAGES_PER_DAY} today]`);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        failed++;
        results.push({ id: lead.id, phone: lead.phone, status: "failed", error: message });
        console.error(`   ❌ ${lead.name} (${lead.phone}) — ${message}`);
      }

      // Delay between messages
      if (i < leads.length - 1) {
        if (sent > 0 && sent % COFFEE_BREAK_EVERY === 0) {
          await coffeBreakSleep();
        } else {
          await randomSleep();
        }
      }
    }

    console.log(`\n📊 JSON Campaign done — Sent: ${sent}, Failed: ${failed}\n`);

    res.json({ sent, failed, total: leads.length, dailySent: dailySentCount, results });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("💥 JSON Campaign error:", message);
    res.status(500).json({ error: "Campaign processing failed.", details: message });
  }
}
