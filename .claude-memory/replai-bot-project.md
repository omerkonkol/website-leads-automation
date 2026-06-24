---
name: replai-bot-project
description: "Replai - עסק בוטי וואטסאפ לעסקים שהמשתמש בונה, דף נחיתה + דמו עובד ב-e:\\system\\sites\\replai"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5a1581f8-4773-4700-840b-446bab82aee7
---

המשתמש בונה עסק שמוכר **בוטי וואטסאפ AI לעסקים** (כמו המתחרים botomati.co.il, botix.co.il). השם שנבחר: **Replai** (Reply+AI). חלופות שנשקלו: Botli, תכף.

**מודל עסקי שנבחר:** סוכנות / Done-For-You (לא SaaS) — בונים בוט מותאם לכל עסק, גובים דמי הקמה + ריטיינר. חיבור וואטסאפ: **לא רשמי (whatsapp-web.js / Baileys)** כמו המתחרים, לא Meta API.

**הארכיטקטורה הטכנית:** context stuffing (לא RAG) — כל הידע של העסק נדחף ל-system prompt; המודל עונה רק לפי זה; grounding שמונע הזיות; זיהוי handoff לאדם. לפרודקשן: Claude Sonnet 4.6 (~₪12/חודש לעסק, מרווח 90%+).

**מה נבנה (ב-e:\system\sites\replai):**
- `index.html` — דף נחיתה מלא בעברית RTL, מבנה בהשראת botix (ניסוח מקורי), מחירים: סטארטר ₪199, עסקי ₪399, Enterprise ₪1490. כולל צ'אט דמו חי בתוך הדף.
- `replai_server.py` — שרת Python stdlib שמגיש את הדף + מגשר ל-Ollama. ה-system prompt (מספרה לדוגמה) בצד השרת. handoff מזוהה לפי תוכן (לא לפי תג מהמודל).
- `start.ps1` — הפעלה בקליק.
- POC נוסף: `e:\system\bot-poc\bot_poc.py`.

**דפלוי:** דף הנחיתה חי ב-Cloudflare Pages — https://replai-a3i.pages.dev (פרויקט "replai", מדפלוים מ-`sites/replai/public/`). הדף המופץ משתמש בתשובות canned לדמו (אין שרת); הדף הלוקאלי משתמש בצ'אט חי.

**שכבת Claude:** `replai_server.py` תומך בשני ספקים דרך env `REPLAI_PROVIDER` (ollama/claude). claude משתמש ב-Sonnet 4.6 עם prompt caching, דורש `pip install anthropic` + `ANTHROPIC_API_KEY`. ollama = ברירת מחדל (חינם).

**חיבור ל-WhatsApp (whatsapp-api):** נוסף `src/services/bot_responder.ts` שמחובר ב-`whatsapp_pool.ts` כ-onInbound handler שני. opt-in דרך `REPLAI_BOT=on` (ברירת מחדל off, כדי לא להפריע לקמפיין לידים). מעביר הודעות נכנסות ל-`REPLAI_BOT_URL` (ברירת מחדל http://localhost:8080/api/chat), שולח תשובה, ומשתיק את הבוט ללקוח אחרי handoff (Set humanHandling). זהירות: החשבון החי 0525603365 משמש לקמפיין לידים — אל תדליק REPLAI_BOT=on עליו (יענה ללידים בתור מספרה). לבדיקה חיה צריך מספר ייעודי.

**סביבת פיתוח לוקאלית (חינם, לבדיקות):**
- Ollama מותקן. מודל מומלץ לעברית: **aya-expanse:8b** (עברית נקייה). qwen2.5:7b כתב תעתיק לטיני — לא טוב לעברית.
- **חובה `num_gpu: 0`** ב-options — ה-GPU (AMD R9 380) לא נתמך ומייצר ג'יבריש (@@@). רץ על CPU, ~15 שניות לתשובה.
- הרצה: `python replai_server.py` -> http://localhost:8080

קשור: [[whatsapp-campaign-server]], [[system-folder-layout]].
