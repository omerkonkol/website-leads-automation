---
name: aliza-goldberg-project
description: "אתר לעליזה גולדברג — מאמנת/מנחת סדנאות/מטפלת LICBT, ב-sites/aliza-goldberg, Cloudflare Pages"
metadata: 
  node_type: memory
  type: project
  originSessionId: f829a942-cb64-4f57-8366-e9ad69ce9a90
---

אתר תדמית לעליזה גולדברג — מאמנת אישית, מנחת סדנאות ומטפלת LICBT לנשים ונערות. נבנה ב-`e:\system\sites\aliza-goldberg\` (index.html יחיד + עמודי חובה: accessibility.html, privacy.html, terms.html).

- **עיצוב:** מינימליסטי רך, RTL עברית, פלטת מרווה (sage) + זהב חם + קרם. גופנים Frank Ruhl Libre + Heebo.
- **Hero:** תמונות מוכנות (assets/img/hero-desktop.webp 16:9, hero-mobile.webp 9:16) עם `<picture>` + אנימציית fade/zoom. כוללות כבר כותרת/שם/מחברת.
- **לוגו:** assets/img/logo.png (וריאקולור "Aliza Goldberg Life Coach", רקע הולבן לשקוף).
- **מחברת הדגל:** "מחברת בוקר 40 יום" — assets/img/notebook-preview.webp. סקשן ייעודי כהה.
- **קרוסלות (גנרי, RTL, autoplay+swipe+dots):** תעודות (6, assets/img/certificates/*.webp) + המלצות וידאו (8 סרטוני יוטיוב עם posters מותאמים לפי פרצוף ב-assets/img/posters/p1-p8.webp, facade שטוען iframe בלחיצה).
- **וואטסאפ:** 052-6041162 (קבוע PHONE=972526041162 בראש ה-JS ב-index.html).
- **Cloudflare:** פרויקט Pages בשם `aliza-goldberg` → https://aliza-goldberg.pages.dev . דפלוי: `cd sites\aliza-goldberg; $env:NODE_TLS_REJECT_UNAUTHORIZED="0"; npx wrangler pages deploy . --project-name aliza-goldberg --branch main --commit-dirty=true`

מקור התוכן: Google Drive של הלקוחה (מסמכי "מי אני"/"שרותים", תעודות, מחברת). הורדה מ-Drive עובדת רק עם `curl -k` (פרוקסי TLS) + חילוץ file IDs מ-`data-id="..."` ב-HTML של תיקיית הדרייב. ראה [[system-folder-layout]].
