import express from "express";
import * as path from "path";
import { accountPool } from "./services/whatsapp_pool";
import campaignRoutes from "./routes/campaign";
import leadsCampaignRoutes from "./routes/leads_campaign";
import inboxRoutes, { inboxHtmlPath } from "./routes/inbox";

const PORT = process.env.PORT ?? 3000;

async function main(): Promise<void> {
  // 1. Initialize the pool — boots all configured accounts in parallel
  await accountPool.initializeAll();

  // 2. Boot Express
  const app = express();
  app.use(express.json());

  // Health check
  app.get("/api/health", (_req, res) => {
    const ready = accountPool.ready();
    const all = accountPool.all();
    res.json({
      status: "ok",
      accounts_ready: ready.length,
      accounts_total: all.length,
      accounts: all.map((a) => ({ phone: a.phone, status: a.status() })),
    });
  });

  // Campaign + inbox routes
  app.use("/api/campaign", campaignRoutes);
  app.use("/api/leads-campaign", leadsCampaignRoutes);
  app.use("/api/inbox", inboxRoutes);

  // Serve the inbox HTML page at /inbox
  app.get("/inbox", (_req, res) => {
    res.sendFile(inboxHtmlPath);
  });
  // Redirect bare / to /inbox
  app.get("/", (_req, res) => res.redirect("/inbox"));

  app.listen(PORT, () => {
    console.log(`\n🚀 Server listening on http://localhost:${PORT}`);
    console.log(`   GET  /inbox                      — conversation inbox UI`);
    console.log(`   GET  /api/inbox                  — list conversations (JSON)`);
    console.log(`   POST /api/inbox/reply            — send reply`);
    console.log(`   POST /api/leads-campaign/send    — bulk leads campaign`);
    console.log(`   GET  /api/health                 — health check\n`);
  });
}

main().catch((err) => {
  console.error("Fatal error during startup:", err);
  process.exit(1);
});
