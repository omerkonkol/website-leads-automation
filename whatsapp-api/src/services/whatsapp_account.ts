import { Client, LocalAuth, Message, MessageMedia } from "whatsapp-web.js";
import qrcode from "qrcode-terminal";
import * as QRCode from "qrcode";
import * as path from "path";

export type AccountStatus = "pending" | "ready" | "disconnected" | "banned";

export interface InboundMessage {
  raw: Message;
  accountPhone: string;
  peerPhone: string;       // cleaned: digits-only or LID id without @suffix
  peerChatId: string;      // full WhatsApp chat id (e.g. "972547546790@c.us" or "22922@lid"), required to send replies
  pushname: string | null;
  body: string;
  mediaPath: string | null;
  rawId: string;
  receivedAt: Date;
}

export type InboundHandler = (msg: InboundMessage) => Promise<void> | void;

/**
 * Single WhatsApp account instance (one phone number, one whatsapp-web.js client).
 * Multiple instances coexist via the AccountPool — each gets its own session_data
 * subfolder keyed on the phone number.
 */
export class WhatsAppAccount {
  readonly phone: string;
  readonly label: string;
  private client: Client;
  private _status: AccountStatus = "pending";
  private readyPromise: Promise<void>;
  private resolveReady!: () => void;
  private inboundHandlers: InboundHandler[] = [];
  private qrPath: string;

  constructor(phone: string, label = "primary") {
    this.phone = phone;
    this.label = label;
    // LocalAuth restricts clientId to [A-Za-z0-9_-]; strip "+" / spaces.
    const safeClientId = phone.replace(/[^A-Za-z0-9_-]/g, "");
    this.qrPath = path.resolve(process.cwd(), "..", `qr_${safeClientId}.png`);

    this.client = new Client({
      authStrategy: new LocalAuth({
        dataPath: "./session_data",
        clientId: safeClientId,
      }),
      puppeteer: {
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"],
      },
    });

    this.readyPromise = new Promise((resolve) => {
      this.resolveReady = resolve;
    });

    this.registerEvents();
  }

  private registerEvents(): void {
    this.client.on("qr", (qr: string) => {
      console.log(`\n📱 [${this.phone}] Scan QR with WhatsApp:\n`);
      qrcode.generate(qr, { small: true });
      QRCode.toFile(this.qrPath, qr, { width: 400, margin: 2 })
        .then(() => console.log(`   💾 [${this.phone}] QR PNG: ${this.qrPath}\n`))
        .catch((err) => console.error(`   ⚠️  [${this.phone}] failed to save QR PNG:`, err));
    });

    this.client.on("authenticated", () => {
      console.log(`✅ [${this.phone}] authenticated.`);
    });

    this.client.on("auth_failure", (msg: string) => {
      console.error(`❌ [${this.phone}] auth failed:`, msg);
    });

    this.client.on("ready", () => {
      console.log(`✅ [${this.phone}] client ready.`);
      this._status = "ready";
      this.resolveReady();
    });

    this.client.on("disconnected", (reason: string) => {
      console.warn(`⚠️  [${this.phone}] disconnected:`, reason);
      this._status = "disconnected";
    });

    // ── Inbox: capture inbound messages ────────────────────────────────
    this.client.on("message", async (raw: Message) => {
      try {
        // Skip messages we sent (fromMe=true) and group/status/broadcast
        if (raw.fromMe) return;
        if (raw.from.endsWith("@g.us")) return;        // group
        if (raw.from === "status@broadcast") return;
        if (raw.from.endsWith("@broadcast")) return;

        // Resolve real phone via Contact (WhatsApp returns @lid for some accounts).
        let peerPhone = raw.from.replace(/@(c\.us|lid|s\.whatsapp\.net)$/, "");
        let pushname: string | null = null;
        try {
          const contact = await raw.getContact();
          if (contact.number) {
            // Convert "972525603365" → "0525603365"
            const digits = contact.number.replace(/\D/g, "");
            peerPhone = digits.startsWith("972") ? "0" + digits.slice(3) : digits;
          }
          pushname = contact.pushname || contact.name || null;
        } catch (e) {
          // Contact lookup may fail for LID-only accounts; keep stripped LID as peerPhone.
        }
        let mediaPath: string | null = null;
        if (raw.hasMedia) {
          // Download media into ./media/<accountPhone>/<rawId>.<ext>
          try {
            const m = await raw.downloadMedia();
            if (m && m.data) {
              const fs = await import("fs");
              const dir = path.resolve(process.cwd(), "..", "media", this.phone);
              fs.mkdirSync(dir, { recursive: true });
              const ext = (m.mimetype.split("/")[1] || "bin").split(";")[0];
              const file = path.join(dir, `${raw.id._serialized.replace(/[^A-Za-z0-9_-]/g, "_")}.${ext}`);
              fs.writeFileSync(file, Buffer.from(m.data, "base64"));
              mediaPath = file;
            }
          } catch (mediaErr) {
            console.error(`[${this.phone}] media download failed:`, mediaErr);
          }
        }

        const inbound: InboundMessage = {
          raw,
          accountPhone: this.phone,
          peerPhone,
          peerChatId: raw.from,
          pushname,
          body: raw.body || "",
          mediaPath,
          rawId: raw.id._serialized,
          receivedAt: new Date((raw.timestamp || Date.now() / 1000) * 1000),
        };

        for (const h of this.inboundHandlers) {
          try {
            await h(inbound);
          } catch (e) {
            console.error(`[${this.phone}] inbound handler error:`, e);
          }
        }
      } catch (e) {
        console.error(`[${this.phone}] message event error:`, e);
      }
    });
  }

  onInbound(handler: InboundHandler): void {
    this.inboundHandlers.push(handler);
  }

  async initialize(): Promise<void> {
    console.log(`⏳ [${this.phone}] initializing client...`);
    await this.client.initialize();
    await this.readyPromise;
  }

  isReady(): boolean { return this._status === "ready"; }
  status(): AccountStatus { return this._status; }
  setStatus(s: AccountStatus): void { this._status = s; }

  async sendMessage(phoneNumber: string, message: string): Promise<Message> {
    if (!this.isReady()) throw new Error(`Account ${this.phone} not ready (${this._status}).`);
    return this.client.sendMessage(this.formatNumber(phoneNumber), message);
  }

  /** Send a message to an exact WhatsApp chat id (already includes @c.us / @lid). Used for replies. */
  async sendToChatId(chatId: string, message: string): Promise<Message> {
    if (!this.isReady()) throw new Error(`Account ${this.phone} not ready (${this._status}).`);
    return this.client.sendMessage(chatId, message);
  }

  async sendMessageWithMedia(
    phoneNumber: string,
    caption: string,
    imagePath: string
  ): Promise<Message> {
    if (!this.isReady()) throw new Error(`Account ${this.phone} not ready (${this._status}).`);
    const media = MessageMedia.fromFilePath(imagePath);
    return this.client.sendMessage(this.formatNumber(phoneNumber), media, { caption });
  }

  private formatNumber(phone: string): string {
    let cleaned = phone.replace(/\D/g, "");
    if (cleaned.startsWith("0")) cleaned = "972" + cleaned.slice(1);
    if (!cleaned.endsWith("@c.us")) cleaned += "@c.us";
    return cleaned;
  }

  async destroy(): Promise<void> {
    try { await this.client.destroy(); } catch (e) { /* ignore */ }
  }
}
