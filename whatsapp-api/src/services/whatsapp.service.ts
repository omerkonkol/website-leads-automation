import { Client, LocalAuth, Message } from "whatsapp-web.js";
import qrcode from "qrcode-terminal";

class WhatsAppService {
  private client: Client;
  private isReady = false;
  private readyPromise: Promise<void>;
  private resolveReady!: () => void;

  constructor() {
    this.client = new Client({
      authStrategy: new LocalAuth({ dataPath: "./session_data" }),
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
      console.log("\n📱 Scan this QR code with WhatsApp:\n");
      qrcode.generate(qr, { small: true });
    });

    this.client.on("authenticated", () => {
      console.log("✅ WhatsApp authenticated successfully.");
    });

    this.client.on("auth_failure", (message: string) => {
      console.error("❌ WhatsApp authentication failed:", message);
    });

    this.client.on("ready", () => {
      console.log("✅ WhatsApp client is ready.");
      this.isReady = true;
      this.resolveReady();
    });

    this.client.on("disconnected", (reason: string) => {
      console.warn("⚠️  WhatsApp client disconnected:", reason);
      this.isReady = false;
    });
  }

  async initialize(): Promise<void> {
    console.log("⏳ Initializing WhatsApp client...");
    await this.client.initialize();
    await this.readyPromise;
  }

  getIsReady(): boolean {
    return this.isReady;
  }

  async sendMessage(
    phoneNumber: string,
    message: string
  ): Promise<Message> {
    if (!this.isReady) {
      throw new Error("WhatsApp client is not ready.");
    }

    const chatId = this.formatNumber(phoneNumber);
    return this.client.sendMessage(chatId, message);
  }

  private formatNumber(phone: string): string {
    // Strip everything that isn't a digit
    let cleaned = phone.replace(/\D/g, "");

    // Handle Israeli numbers: leading 0 → 972
    if (cleaned.startsWith("0")) {
      cleaned = "972" + cleaned.slice(1);
    }

    // Append the required whatsapp-web.js suffix
    if (!cleaned.endsWith("@c.us")) {
      cleaned += "@c.us";
    }

    return cleaned;
  }
}

export const whatsappService = new WhatsAppService();
