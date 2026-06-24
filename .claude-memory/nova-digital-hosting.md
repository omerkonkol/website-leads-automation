---
name: nova-digital-hosting
description: "איך מתארח nova-digital-il.com — Vercel ל-apex, DNS ב-Namecheap, פקודת deploy"
metadata: 
  node_type: memory
  type: project
  originSessionId: cc374c0f-7f61-45d3-b6bd-d50ff98b3a12
---

האתר [[nova-digital-project]] מתארח כך (נכון ל-1 ביוני 2026):

- **Vercel** מגיש את הדומיין הראשי `nova-digital-il.com` (apex, בלי www) — project `nova-digital` תחת ה-team `tryexamprep` (ExamPrep). זה הדומיין שאליו מפנה הודעת הוואטסאפ ללידים.
- **DNS ב-Namecheap** (nameservers: `dns1/dns2.registrar-servers.com`). ה-apex עובד דרך רשומת **A: `@` → `76.76.21.21`** (כתובת Vercel). זה הוחלף מ-URL Redirect Record קודם.
- **www.nova-digital-il.com** מצביע ל-**Cloudflare Pages** (`CNAME www → nova-digital.pages.dev`), אבל מוגדר שם **Pages Function** (`functions/_middleware.js`) שמבצע **301 redirect מ-www ל-apex** (canonical בלי www). כלומר www מפנה אוטומטית לדומיין האמיתי. דיפלוי ל-CF: `npx wrangler pages deploy . --project-name nova-digital --commit-dirty=true` (קובץ `.vercelignore` מחריג את `functions/` מ-Vercel).

**How to apply:** כשמעדכנים את האתר ומדפלוים — הפקודה (מ-`e:\system\sites\nova-digital` — הנתיב עודכן, יש גם `sites\nova-digital-v2` שהוא ייצוא WordPress ולא הלייב):
```
$env:NODE_TLS_REJECT_UNAUTHORIZED="0"
vercel deploy --prod --yes
```
זה מעלה אוטומטית ל-`nova-digital-il.com`.

**תקלת DNS שחזרה (20 ביוני 2026) — אם האתר נופל עם ERR_CONNECTION_REFUSED:** ב-Namecheap → Domain → NAMESERVERS, אם זה מוגדר "Custom DNS" (גם אם השרתים הם dns1/dns2.registrar-servers.com) — ה-Host Records לא פעילים וה-apex נופל לשרת חניה `198.54.117.242`. התיקון: לשנות ל-**"Namecheap BasicDNS"**, ואז רשומות ה-A (`@`→`76.76.21.21`) וה-CNAME (`www`→`nova-digital.pages.dev`) חוזרות. הדומיין תקף עד 31.5.2027.

**Why:** המשתמש רצה שהדומיין יעבוד ישירות **בלי www**. Cloudflare Pages לא יכול להגיש apex כשה-DNS לא אצלו, אז עברנו ל-Vercel שתומך ב-apex עם A record + SSL אוטומטי.

**אזהרה — Avast על המחשב המקומי מיירט TLS:** `curl` רגיל מחזיר HTTP 000 / שגיאות תעודה לחלק מהאתרים (ה-issuer יוצא "Avast Web/Mail Shield"). לבדיקות חיצוניות אמינות השתמש ב-`curl -k` או ב-WebFetch (רץ מהענן).
