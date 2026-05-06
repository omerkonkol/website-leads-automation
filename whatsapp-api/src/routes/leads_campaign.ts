import { Router } from "express";
import { sendLeadsCampaign, stopLeadsCampaign } from "../controllers/leads_campaign.controller";

const router = Router();

router.post("/send", (req, res) => {
  req.setTimeout(0);
  res.setTimeout(0);
  sendLeadsCampaign(req, res).catch((err) => {
    console.error("Unhandled leads campaign error:", err);
    if (!res.headersSent) {
      res.status(500).json({ error: "Internal error", details: String(err) });
    }
  });
});

router.post("/stop", stopLeadsCampaign);

export default router;
