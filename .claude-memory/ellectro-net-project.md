---
name: ellectro-net-project
description: "אתר מסחר למוצרי חשמל אלקטרו.נט (מותג FJ), sites/demos/electro-net, Cloudflare Pages ellectro-net, WhatsApp-only"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2b163775-ce4b-443e-b5f5-7a6797a63ba7
---

אתר חנות למוצרי חשמל לבית **אלקטרו.נט / ellectro.net** (לקוח: שמעון, 050-249-7225), ב-`e:\system\sites\demos\electro-net`.

- **טכ׳:** `index.html` סטטי, עברית RTL, עיצוב בהיר/אמין (לא ניאון "AI"). header כהה (#0d1b24) שהלוגו יושב עליו, גוף בהיר. פונטים Assistant/Heebo. אנימציות reveal מדורגות.
- **אירוח:** Cloudflare Pages, project `ellectro-net` → https://ellectro-net.pages.dev (דפלוי: `$env:NODE_TLS_REJECT_UNAUTHORIZED="0"; npx wrangler pages deploy . --project-name ellectro-net --commit-dirty=true`). account = Landingpageforu@gmail.com. הדומיין ellectro.net עצמו עדיין לא מחובר (DNS לא פעיל).
- **מוצרים:** מותג **FJ** (חשמל לבן + טלוויזיות). 9 קטגוריות אמיתיות: טלוויזיות/מסכים, מקררים, מקפיאים, מכונות כביסה, מייבשים, מדיחים, תנורים, כיריים, קולטי אדים. **אין** סמארטפונים/לפטופים (זה היה fake בסקיצה הישנה).
- **כרגע מוצגים 20 מוצרים** מתוך 98, **+דף מוצר נפרד לכל אחד** ב-`product/{דגם}.html` (גלריה, מפרט, תיאור, Product schema, מוצרים קשורים). מחירים: `__מחירון ינואר 2025_ (1).xlsx` עמודת **"מחיר צרכן מומלץ"** (עמ' D). אין מחיר-לפני מזויף.
- **תמונות מוצר ברזולוציה גבוהה** מחולצות מ-`e:\system\מחירון-ינואר-2025\מחירון-ינואר-2025-מעודכן.zip` (177 קבצים). זהירות: שמות הקבצים כאוטיים — לפעמים תווית האנרגיה היא דווקא `{דגם}.png`; צריך בחירה ויזואלית (בניתי גיליונות אימות). למייבשים, NF777XE, WM5090T, DW80BK, FNF377WE, CHT50W — **אין תמונת מוצר** בחבילה (רק תווית אנרגיה/לוגו). חבילת נכסי עיצוב (carousel/section/לוגו PNG) ב-`e:\הורדות\electro_net_assets_and_claude_instructions.zip`.
- **תיאורים ומפרט אמיתיים** מבוססים על האתר הרשמי fujicom.co.il + רשתות (לא מומצא) — לפי דרישת המשתמש. מקודדים ב-FACTS/VERIFIED בגנרטור.
- **WhatsApp-only:** אין עגלה/סליקה. כל CTA פותח wa.me/972502497225 עם הודעה מוכנה. carousel בעמוד הבית מתמונות העסק.
- **תקנונים** (מקוריים, מבוססי חוק הגנת הצרכן): terms, shipping, returns, warranty, privacy, accessibility (+`assets/legal.css`). **מחירי הובלה ללקוח:** לבן 150₪, מוצר נוסף +50₪, מקררים 300־350₪ (לא עלות האקסל!).
- חסר להשלמה: פרטי ישות משפטית (ע.מ/ח.פ, שם בעל עסק) בתקנון; אם רוצים תצוגת "מבצע" צריך מחירי מכירה אמיתיים מתחת ל-RRP.

קשור ל-[[system-folder-layout]], [[website-receipts]].
