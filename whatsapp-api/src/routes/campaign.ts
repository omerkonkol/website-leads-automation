import { Router } from "express";
import multer from "multer";
import { sendCampaign, sendCampaignJson } from "../controllers/campaign.controller";

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB max
  fileFilter: (_req, file, cb) => {
    if (
      file.mimetype ===
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" ||
      file.originalname.endsWith(".xlsx")
    ) {
      cb(null, true);
    } else {
      cb(new Error("Only .xlsx files are accepted."));
    }
  },
});

const router = Router();

router.post("/send", upload.single("file"), sendCampaign);
router.post("/send-json", sendCampaignJson);

export default router;
