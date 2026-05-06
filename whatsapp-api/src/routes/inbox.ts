import { Router } from "express";
import * as path from "path";
import { listConversations, getThread, sendReply, stats } from "../controllers/inbox.controller";

const router = Router();

router.get("/", listConversations);
router.get("/stats", stats);
router.get("/:peerPhone", getThread);
router.post("/reply", sendReply);

export default router;

// Static HTML page handler — registered separately in index.ts at /inbox
export const inboxHtmlPath = path.resolve(process.cwd(), "src", "views", "inbox.html");
