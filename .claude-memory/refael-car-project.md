---
name: refael-car-project
description: "דף נחיתה יוקרתי לעסק REFAEL CAR (רכבים יד שנייה), ב-sites/refael-car, מתארח ב-Cloudflare Pages"
metadata: 
  node_type: memory
  type: project
  originSessionId: d8abaf93-d61f-481a-b350-56ced920aecb
---

אתר/דף נחיתה חד-עמודי לעסק **REFAEL CAR / רפאל קאר** — קנייה, מכירה וטרייד אין של רכבים יד שנייה.

- **מיקום:** `e:\system\sites\refael-car\` (index.html יחיד + assets/). ראה [[system-folder-layout]].
- **אירוח:** Cloudflare Pages, פרויקט בשם `refael-car` → https://refael-car.pages.dev (פרויקט נפרד, לא קשור ל-leads-landing).
- **דפלוי:** `$env:NODE_TLS_REJECT_UNAUTHORIZED="0"; npx wrangler pages deploy "e:\system\sites\refael-car" --project-name refael-car --commit-dirty=true`
- **טלפון:** 054-9488535 · tel:0549488535 · wa.me/972549488535
- **עיצוב:** dark luxury, שחור/כסף/אדום (לפי הלוגו), עברית RTL, וניל JS בלבד (אין ספריות/CDN — נטען אופליין).
- **HERO:** וידאו קולנועי (`assets/hero.mp4`, ~2.5MB) שנוצר עם ffmpeg מתמונות המגרש, **scrubbed לפי גלילה** (טכניקת scroll-scrub, currentTime לפי scroll). במובייל מתנגן בלופ.
- תמונות הומרו מ-PNG כבד ל-JPG מותאם (האתר ~4MB סה"כ). לוגו שקוף: `refael_logo_t.png` (הוסר רקע שחור עם ffmpeg colorkey).
- מקור התמונות/הוראות: `e:\refael_extract\refael_car_package\` (מתוך ZIP בהורדות).
