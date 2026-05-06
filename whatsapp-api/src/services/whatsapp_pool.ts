import Database from "better-sqlite3";
import { WhatsAppAccount, AccountStatus, InboundMessage } from "./whatsapp_account";

const DB_PATH = "e:/system/leads.db";

export interface AccountRow {
  phone: string;
  label: string | null;
  status: string;
  daily_limit: number;
  daily_sent: number;
  daily_reset_date: string;
  last_sent_at: string | null;
  ban_reason: string | null;
  branding_set: number;
}

class AccountPool {
  private accounts = new Map<string, WhatsAppAccount>();

  /** Load all accounts from DB and initialize whatsapp-web.js for each. */
  async initializeAll(): Promise<void> {
    const db = new Database(DB_PATH, { readonly: true });
    const rows = db
      .prepare("SELECT phone, label FROM wa_accounts WHERE status != 'banned' ORDER BY created_at")
      .all() as Array<{ phone: string; label: string | null }>;
    db.close();

    if (rows.length === 0) {
      console.warn("⚠️  No accounts in wa_accounts table. Add one with `npm run add-account`.");
      return;
    }

    console.log(`📞 Loading ${rows.length} account(s) from DB...`);
    const initPromises = rows.map(async (r) => {
      const acc = new WhatsAppAccount(r.phone, r.label || "primary");
      this.accounts.set(r.phone, acc);
      acc.onInbound(handleInbound);
      try {
        await acc.initialize();
        this.markStatus(r.phone, "ready");
      } catch (e) {
        console.error(`❌ [${r.phone}] init failed:`, e);
        this.markStatus(r.phone, "disconnected");
      }
    });
    await Promise.all(initPromises);
    const ready = Array.from(this.accounts.values()).filter((a) => a.isReady()).length;
    console.log(`\n✅ Pool initialized: ${ready}/${rows.length} accounts ready.\n`);
  }

  add(account: WhatsAppAccount): void {
    this.accounts.set(account.phone, account);
    account.onInbound(handleInbound);
  }

  get(phone: string): WhatsAppAccount | undefined {
    return this.accounts.get(phone);
  }

  /** All ready accounts. */
  ready(): WhatsAppAccount[] {
    return Array.from(this.accounts.values()).filter((a) => a.isReady());
  }

  all(): WhatsAppAccount[] {
    return Array.from(this.accounts.values());
  }

  /** Pick the ready account with the most remaining capacity today. */
  pickAvailable(): { account: WhatsAppAccount; row: AccountRow } | null {
    const db = new Database(DB_PATH, { readonly: true });
    try {
      const rows = db
        .prepare(`
          SELECT phone, label, status, daily_limit, daily_sent,
                 daily_reset_date, last_sent_at, ban_reason, branding_set
            FROM wa_accounts
           WHERE status != 'banned'
        `)
        .all() as AccountRow[];

      const today = new Date().toISOString().slice(0, 10);
      // Reset counters for any account whose reset_date is stale
      const candidates = rows
        .map((r) => {
          const dailyUsed = r.daily_reset_date === today ? r.daily_sent : 0;
          return { row: r, capacity: r.daily_limit - dailyUsed };
        })
        .filter(({ row, capacity }) => {
          const acc = this.accounts.get(row.phone);
          return acc && acc.isReady() && capacity > 0;
        })
        .sort((a, b) => b.capacity - a.capacity);

      if (candidates.length === 0) return null;
      const winner = candidates[0];
      return { account: this.accounts.get(winner.row.phone)!, row: winner.row };
    } finally {
      db.close();
    }
  }

  /** Find account that previously contacted this peer (sticky lead↔account). */
  pickSticky(peerPhone: string): { account: WhatsAppAccount; row: AccountRow } | null {
    const db = new Database(DB_PATH, { readonly: true });
    try {
      const normalized = peerPhone.replace(/\D/g, "").replace(/^972/, "0");
      const stickyPhone = db
        .prepare(`
          SELECT account_phone FROM wa_messages
           WHERE direction='out' AND (peer_phone=? OR peer_phone=?)
           ORDER BY sent_at ASC LIMIT 1
        `)
        .get(peerPhone, normalized) as { account_phone: string } | undefined;
      if (!stickyPhone) return null;
      const acc = this.accounts.get(stickyPhone.account_phone);
      if (!acc || !acc.isReady()) return null;
      const row = db
        .prepare(`
          SELECT phone, label, status, daily_limit, daily_sent,
                 daily_reset_date, last_sent_at, ban_reason, branding_set
            FROM wa_accounts WHERE phone=?
        `)
        .get(stickyPhone.account_phone) as AccountRow | undefined;
      if (!row) return null;
      return { account: acc, row };
    } finally {
      db.close();
    }
  }

  /** Increment daily_sent for an account, reset if day rolled over. */
  recordSend(phone: string): void {
    const db = new Database(DB_PATH);
    try {
      const today = new Date().toISOString().slice(0, 10);
      const nowIso = new Date().toISOString();
      db.prepare(`
        UPDATE wa_accounts
           SET daily_sent = CASE
                   WHEN daily_reset_date = ? THEN daily_sent + 1
                   ELSE 1
                END,
               daily_reset_date = ?,
               last_sent_at = ?
         WHERE phone = ?
      `).run(today, today, nowIso, phone);
    } finally {
      db.close();
    }
  }

  markStatus(phone: string, status: AccountStatus, banReason?: string): void {
    const acc = this.accounts.get(phone);
    if (acc) acc.setStatus(status);
    const db = new Database(DB_PATH);
    try {
      if (banReason) {
        db.prepare("UPDATE wa_accounts SET status=?, ban_reason=? WHERE phone=?")
          .run(status, banReason, phone);
      } else {
        db.prepare("UPDATE wa_accounts SET status=? WHERE phone=?").run(status, phone);
      }
    } finally {
      db.close();
    }
  }
}

// ── Inbox listener: write inbound message into wa_messages ────────────
function handleInbound(msg: InboundMessage): void {
  const db = new Database(DB_PATH);
  try {
    // Try to link to a lead by matching phone (only if peerPhone looks like a real phone)
    const isRealPhone = /^\d{8,15}$/.test(msg.peerPhone);
    let leadId: number | null = null;
    if (isRealPhone) {
      const normalized = msg.peerPhone.replace(/\D/g, "");
      const localStyle = normalized.startsWith("972") ? "0" + normalized.slice(3) : normalized;
      const lead = db
        .prepare(`SELECT id FROM businesses WHERE REPLACE(phone, '-', '')=? OR REPLACE(phone, '-', '')=? LIMIT 1`)
        .get(normalized, localStyle) as { id: number } | undefined;
      leadId = lead?.id ?? null;
    }

    // Display name fallback: pushname → peer phone/LID
    const displayName = msg.pushname || msg.peerPhone;

    db.prepare(`
      INSERT INTO wa_messages (account_phone, lead_id, peer_phone, peer_chat_id, direction, status, body, media_path, raw_id, sent_at)
      VALUES (?, ?, ?, ?, 'in', 'received', ?, ?, ?, ?)
    `).run(
      msg.accountPhone,
      leadId,
      msg.peerPhone,
      msg.peerChatId,
      msg.body,
      msg.mediaPath,
      msg.rawId,
      msg.receivedAt.toISOString(),
    );

    if (leadId) {
      db.prepare(`
        UPDATE businesses
           SET last_response = ?, response_date = ?, pipeline_stage = 'responded'
         WHERE id = ?
      `).run(msg.body.slice(0, 500), msg.receivedAt.toISOString(), leadId);
    }

    console.log(`📩 [${msg.accountPhone}] ← ${displayName} (${msg.peerPhone})${leadId ? ` (lead #${leadId})` : ""}: ${msg.body.slice(0, 80)}`);
  } catch (e) {
    console.error("inbox handler db error:", e);
  } finally {
    db.close();
  }
}

export const accountPool = new AccountPool();
export { handleInbound };
