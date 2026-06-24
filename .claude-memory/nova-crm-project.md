---
name: nova-crm-project
description: "Nova Digital CRM — מערכת ניהול לקוחות/כספים/קבלות/Meta Ads, נבנית ב-e:\\system\\nova-crm"
metadata: 
  node_type: memory
  type: project
  originSessionId: 28c90e22-9145-4ba6-87bf-56acf9351766
---

מערכת CRM + ניהול כספים + קבלות + מעקב רווחיות Meta/Facebook עבור Nova Digital, ב-`e:\system\nova-crm`.
Stack: Next.js 16 (App Router, proxy.ts במקום middleware.ts), React 19, Tailwind v4 (CSS @theme), Supabase (Postgres+Auth+Storage), Recharts, sonner. עברית מלאה RTL, פונט Assistant.

נבנה בשלבים (1-11). הושלמו: שלב 1 (יסודות+auth+RTL+sidebar) ושלב 2 (db/schema.sql מלא עם RLS+generated remaining_amount+Storage bucket פרטי "receipts"). `npm run build` עובר.

3 הקבלות מ-`e:\system\קבלות-לאתרים` מוטמעות ב-`db/seed.sql` (gscocktails 575₪, איציק וינשטיין 580₪, עמית אבוחצירה 540₪ = 1,695₪) כלקוחות+עסקאות Website משולמות+קבלות. ה-PDF עולים ל-Storage דרך `scripts/import-receipts.mjs`. נוסף שדה `website` ל-clients (לא היה במפרט המקורי).

חוסם: למשתמש אין עדיין פרויקט Supabase — חייב להקים לפני הרצת schema/seed. ראה README.md לצעדים. נותרו שלבים 3-11 (לקוחות, עסקאות, קבלות UI, הוצאות, דשבורד, קמפיינים mock→real Meta, דוחות).
