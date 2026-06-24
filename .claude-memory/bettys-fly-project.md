---
name: bettys-fly-project
description: "דף נחיתה לסוכנות נסיעות Betty's fly, ב-sites/bettys-fly, Cloudflare Pages, dark+gold, RTL"
metadata: 
  node_type: memory
  type: project
  originSessionId: ccf4d3e2-1cd6-485e-8e40-7f597e8bad39
---

דף נחיתה יוקרתי לסוכנות נסיעות **Betty's fly** (בעלים: בטי), ב-`e:\system\sites\bettys-fly`.

- **טכ׳:** עמוד-אחד `index.html` סטטי, עברית RTL, theme dark navy (#0a0e1a) + gold. פונטים Frank Ruhl Libre / Heebo / Great Vibes.
- **אירוח:** Cloudflare Pages, project name `bettys-fly` → https://bettys-fly.pages.dev (דפלוי עם `npx wrangler pages deploy . --project-name bettys-fly --commit-dirty=true`, צריך `$env:NODE_TLS_REJECT_UNAUTHORIZED="0"`).
- **תמונות:** משתמשים אך ורק בחבילת התמונות של הלקוחה (לוגו, hero, 10 גלריה) — אין Unsplash/סטוק (דרישת הלקוח: בלי זכויות יוצרים). מקור ה-zip: `e:\הורדות\bettys_fly_landing_assets.zip`. הקבצים אופטמו ל-WebP ב-`assets/img/` (22MB→1.3MB) עם ffmpeg.
- **קשר:** טלפון 053-7207998, מייל bettyhudeda@gmail.com, מעלה אדומים.
- **דפים משפטיים:** privacy.html, terms.html, accessibility.html (מקושרים מה-footer).
- הלוגו האמיתי ב-loader (עם רקע hero), navbar, footer.

קשור ל-[[system-folder-layout]], [[website-receipts]].
