---
name: whois-suspension-diagnosis
description: איך לאבחן ולתקן אתר שנפל בגלל השעיית WHOIS verification ב-Namecheap
metadata: 
  node_type: memory
  type: reference
  originSessionId: 3d781542-1c43-4499-9737-2e2183bce51f
---

כשאתר של המשתמש "נופל", **לבדוק קודם DNS/דומיין, לא קוד**. ב-2026-06-22 gs-cocktails-bar.site נפל — האתר ב-Cloudflare Pages היה תקין לגמרי (HTTP 200 ב-`.pages.dev`), אבל הדומיין הוסט ל-parking של Namecheap.

**איך מזהים השעיית WHOIS:** `nslookup -type=NS <domain>` מחזיר nameservers `failed-whois-verification.namecheap.com` / `verify-contact-details.namecheap.com` (במקום `dns1/dns2.registrar-servers.com`), והדומיין מצביע ל-IP חניה `198.54.117.242` (= registrar-servers.com). בפאנל Namecheap הדומיין מראה ⚠️ ALERT + כפתור "VERIFY CONTACTS".

**הסיבה:** ICANN דורש אימות אימייל ה-registrant תוך 15 יום מרישום דומיין gTLD (.site וכו') או מכל שינוי פרטי קשר. בלי אימות — Namecheap משעה ומפנה לדף חניה. זה **לא** קשור לפקיעת תוקף/תשלום.

**התיקון (היחיד):** לאמת — האימות עצמו קורה רק דרך הקישור במייל מ-Namecheap (`support@namecheap.com`). הפאנל רק שולח מחדש ("Resend"/"VERIFY CONTACTS"). אחרי אימות מופיע "Registrant email address successfully verified" וההפעלה מחדש אוטומטית (רשמית עד 24-48 ש', בפועל דקות-שעות). אימות הוא **לפי אימייל registrant** — אם כל הדומיינים על אותו אימייל, אימות אחד מכסה את כולם; אם לא, צריך לאמת כל אחד. אזהרת "this verification link is no longer valid" = קישור ישן/פג — צריך Resend טרי, לא ללחוץ על מיילים ישנים. אפשר לבקש מ-live chat של Namecheap "manually expedite reactivation".

**סיכון נפרד — פקיעת תוקף:** לוודא Auto-Renew דלוק + כרטיס תקף ב-Billing. גם להשאיר Auto-Renew של Domain Privacy דלוק (חינמי ב-Namecheap), אחרת הפרטים האישיים נחשפים ב-WHOIS הציבורי.

רשימת הדומיינים: [[namecheap-domains]].
