import Database from "better-sqlite3";
import { Message } from "whatsapp-web.js";
import { accountPool } from "./whatsapp_pool";

const DB_PATH = "e:/system/leads.db";

export interface DispatchTarget {
  leadId: number;
  peerPhone: string;
}

export interface DispatchResult {
  message: Message;
  accountPhone: string;
}

class Dispatcher {
  /** Send a media message to a lead, choosing the right account. */
  async send(
    target: DispatchTarget,
    caption: string,
    imagePath: string,
  ): Promise<DispatchResult> {
    // 1. Sticky: previously contacted? use the same account.
    let pick = accountPool.pickSticky(target.peerPhone);

    // 2. Else lowest-load with capacity left.
    if (!pick) pick = accountPool.pickAvailable();

    if (!pick) {
      throw new Error("All accounts at daily limit or unavailable.");
    }

    const { account, row } = pick;
    const message = await account.sendMessageWithMedia(target.peerPhone, caption, imagePath);

    // Record outbound + bump daily counter
    accountPool.recordSend(account.phone);
    this.recordOutbound(account.phone, target, caption, imagePath, message.id._serialized);

    return { message, accountPhone: account.phone };
  }

  /** Send a plain reply (text) from the same account that received the original message. */
  async reply(peerPhone: string, body: string): Promise<DispatchResult> {
    // Find the most recent message in this conversation to recover the right account + chat id
    const db = new Database(DB_PATH, { readonly: true });
    const lastInbound = db.prepare(`
      SELECT account_phone, peer_chat_id FROM wa_messages
       WHERE peer_phone = ? AND direction = 'in'
       ORDER BY sent_at DESC LIMIT 1
    `).get(peerPhone) as { account_phone: string; peer_chat_id: string | null } | undefined;
    db.close();

    let chatId: string;
    let accountPhone: string;
    if (lastInbound && lastInbound.peer_chat_id) {
      chatId = lastInbound.peer_chat_id;
      accountPhone = lastInbound.account_phone;
    } else {
      const pick = accountPool.pickSticky(peerPhone);
      if (!pick) throw new Error(`No prior conversation with ${peerPhone}; cannot pick account.`);
      accountPhone = pick.account.phone;
      // Build chat id from phone for legacy outbound-only conversations
      const digits = peerPhone.replace(/\D/g, "");
      const intl = digits.startsWith("0") ? "972" + digits.slice(1) : digits;
      chatId = `${intl}@c.us`;
    }

    const acc = accountPool.get(accountPhone);
    if (!acc || !acc.isReady()) throw new Error(`Account ${accountPhone} not ready.`);
    const message = await acc.sendToChatId(chatId, body);
    accountPool.recordSend(accountPhone);
    this.recordOutbound(accountPhone, { leadId: 0, peerPhone }, body, null, message.id._serialized);
    return { message, accountPhone };
  }

  private recordOutbound(
    accountPhone: string,
    target: DispatchTarget,
    body: string,
    mediaPath: string | null,
    rawId: string,
  ): void {
    const db = new Database(DB_PATH);
    try {
      db.prepare(`
        INSERT INTO wa_messages
          (account_phone, lead_id, peer_phone, direction, status, body, media_path, raw_id, sent_at)
        VALUES (?, ?, ?, 'out', 'sent', ?, ?, ?, ?)
      `).run(
        accountPhone,
        target.leadId || null,
        target.peerPhone,
        body,
        mediaPath,
        rawId,
        new Date().toISOString(),
      );
    } finally {
      db.close();
    }
  }
}

export const dispatcher = new Dispatcher();
