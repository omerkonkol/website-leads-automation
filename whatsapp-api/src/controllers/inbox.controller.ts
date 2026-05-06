import { Request, Response } from "express";
import Database from "better-sqlite3";
import { dispatcher } from "../services/dispatcher";

const DB_PATH = "e:/system/leads.db";

interface ConversationRow {
  peer_phone: string;
  account_phone: string;
  lead_id: number | null;
  lead_name: string | null;
  lead_category: string | null;
  lead_city: string | null;
  last_body: string;
  last_at: string;
  last_direction: "in" | "out";
  unread_count: number;
  total_count: number;
}

/**
 * GET /api/inbox  → list of conversations (latest 100), newest first.
 * Each conversation = unique (peer_phone, account_phone), with unread count.
 */
export function listConversations(req: Request, res: Response): void {
  const db = new Database(DB_PATH, { readonly: true });
  try {
    const rows = db.prepare(`
      WITH latest AS (
        SELECT peer_phone, account_phone, MAX(sent_at) AS last_at
          FROM wa_messages
         GROUP BY peer_phone, account_phone
      )
      SELECT
        m.peer_phone,
        m.account_phone,
        m.lead_id,
        b.name        AS lead_name,
        b.category    AS lead_category,
        b.city        AS lead_city,
        m.body        AS last_body,
        m.sent_at     AS last_at,
        m.direction   AS last_direction,
        (SELECT COUNT(*) FROM wa_messages
            WHERE peer_phone=m.peer_phone AND account_phone=m.account_phone
              AND direction='in' AND read_at IS NULL) AS unread_count,
        (SELECT COUNT(*) FROM wa_messages
            WHERE peer_phone=m.peer_phone AND account_phone=m.account_phone) AS total_count
      FROM latest l
      JOIN wa_messages m
        ON m.peer_phone = l.peer_phone
       AND m.account_phone = l.account_phone
       AND m.sent_at = l.last_at
      LEFT JOIN businesses b ON b.id = m.lead_id
      ORDER BY m.sent_at DESC
      LIMIT 200
    `).all() as ConversationRow[];

    res.json({ conversations: rows });
  } finally {
    db.close();
  }
}

/**
 * GET /api/inbox/:peerPhone → full thread for a conversation.
 * Marks unread inbound messages as read.
 */
export function getThread(req: Request, res: Response): void {
  const peer = req.params.peerPhone;
  const db = new Database(DB_PATH);
  try {
    const messages = db.prepare(`
      SELECT id, account_phone, lead_id, peer_phone, direction, status, body, media_path, sent_at, read_at
        FROM wa_messages
       WHERE peer_phone = ?
       ORDER BY sent_at ASC
    `).all(peer);

    // Mark inbound as read
    db.prepare(`
      UPDATE wa_messages SET read_at = datetime('now')
       WHERE peer_phone = ? AND direction='in' AND read_at IS NULL
    `).run(peer);

    // Lead info
    const lead = db.prepare(`
      SELECT b.id, b.name, b.phone, b.category, b.city, b.google_rating
        FROM wa_messages m
        JOIN businesses b ON b.id = m.lead_id
       WHERE m.peer_phone = ? AND m.lead_id IS NOT NULL
       LIMIT 1
    `).get(peer);

    res.json({ peer, messages, lead });
  } finally {
    db.close();
  }
}

/**
 * POST /api/inbox/reply
 * Body: { peer_phone: string, body: string }
 */
export async function sendReply(req: Request, res: Response): Promise<void> {
  try {
    const { peer_phone, body } = req.body as { peer_phone?: string; body?: string };
    if (!peer_phone || !body) {
      res.status(400).json({ error: "peer_phone and body are required" });
      return;
    }
    const result = await dispatcher.reply(peer_phone, body);
    res.json({
      ok: true,
      account_phone: result.accountPhone,
      raw_id: result.message.id._serialized,
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    res.status(500).json({ error: msg });
  }
}

/** GET /api/inbox/stats */
export function stats(req: Request, res: Response): void {
  const db = new Database(DB_PATH, { readonly: true });
  try {
    const today = new Date().toISOString().slice(0, 10);
    const accounts = db.prepare(`
      SELECT phone, label, status, daily_limit, daily_sent, daily_reset_date,
             branding_set, ban_reason
        FROM wa_accounts ORDER BY created_at
    `).all();
    // Normalize daily_sent for stale dates
    accounts.forEach((a: any) => {
      if (a.daily_reset_date !== today) a.daily_sent = 0;
    });
    const totalSent  = db.prepare(`SELECT COUNT(*) as n FROM wa_messages WHERE direction='out'`).get() as { n: number };
    const totalRecv  = db.prepare(`SELECT COUNT(*) as n FROM wa_messages WHERE direction='in'`).get() as { n: number };
    const unread     = db.prepare(`SELECT COUNT(*) as n FROM wa_messages WHERE direction='in' AND read_at IS NULL`).get() as { n: number };
    const responded  = db.prepare(`SELECT COUNT(DISTINCT peer_phone) as n FROM wa_messages WHERE direction='in'`).get() as { n: number };

    res.json({
      accounts,
      totals: {
        sent: totalSent.n,
        received: totalRecv.n,
        unread: unread.n,
        unique_responders: responded.n,
      },
    });
  } finally {
    db.close();
  }
}
