import express from "express";
import { whatsappService } from "./services/whatsapp.service";
import campaignRoutes from "./routes/campaign";

const PORT = process.env.PORT ?? 3000;

async function main(): Promise<void> {
  // 1. Initialize WhatsApp (prints QR on first run, loads session after)
  await whatsappService.initialize();

  // 2. Boot Express only after WhatsApp is ready
  const app = express();

  app.use(express.json());

  // Health check
  app.get("/api/health", (_req, res) => {
    res.json({
      status: "ok",
      whatsapp: whatsappService.getIsReady() ? "connected" : "disconnected",
    });
  });

  // Campaign routes
  app.use("/api/campaign", campaignRoutes);

  app.listen(PORT, () => {
    console.log(`\n🚀 Server listening on http://localhost:${PORT}`);
    console.log(`   POST /api/campaign/send  — upload .xlsx to send messages`);
    console.log(`   GET  /api/health         — health check\n`);
  });
}

main().catch((err) => {
  console.error("Fatal error during startup:", err);
  process.exit(1);
});
