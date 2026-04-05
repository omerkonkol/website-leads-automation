"""
demo_generator.py — יוצר אתר דמו מקצועי אישי לכל עסק.
משתמש ב-Claude API ליצירת HTML/CSS/JS מלא.
הרצה: python demo_generator.py  (או מתוך הדשבורד)

הפלט: קובץ HTML שנפתח בדפדפן — אפשר לשלוח ל-GitHub Pages / Netlify בחינם.
"""

import sys
import os
import re
import json
import time
import webbrowser
import requests
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import anthropic


# ════════════════════════════════════════════════════════════════
#  שליפת תוכן מהאתר הקיים (אם יש)
# ════════════════════════════════════════════════════════════════
def scrape_existing_site(url: str) -> str:
    """מחלץ טקסט גולמי מהאתר הקיים של העסק."""
    if not url:
        return ""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        # הסר HTML tags, השאר טקסט בלבד
        text = re.sub(r"<script[^>]*>.*?</script>", "", resp.text, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:3000]   # מקסימום 3000 תווים
    except Exception:
        return ""


# ════════════════════════════════════════════════════════════════
#  יצירת HTML ע"י Claude
# ════════════════════════════════════════════════════════════════
def generate_demo_site(
    business_name: str,
    category: str,
    phone: str,
    address: str,
    existing_url: str = "",
    extra_info: str = "",
    api_key: str = "",
) -> str:
    """
    מחזיר קוד HTML מלא לאתר דמו מקצועי.
    """
    existing_content = scrape_existing_site(existing_url)

    context_parts = [f"שם העסק: {business_name}", f"קטגוריה: {category}"]
    if phone:    context_parts.append(f"טלפון: {phone}")
    if address:  context_parts.append(f"כתובת: {address}")
    if extra_info: context_parts.append(f"מידע נוסף: {extra_info}")
    if existing_content:
        context_parts.append(f"\nתוכן מהאתר הקיים (לשם השראה בלבד):\n{existing_content}")

    context = "\n".join(context_parts)

    prompt = f"""אתה מפתח ווב מומחה ומעצב UI/UX. צור אתר landing page מושלם עבור העסק הבא.

מידע על העסק:
{context}

דרישות:
- קוד HTML יחיד ומלא (HTML + CSS + JS מובנה, ללא קבצים חיצוניים למעט Google Fonts)
- עיצוב מודרני, נקי ומרשים — dark mode עם accent color שמתאים לקטגוריה
- RTL (עברית) מלא
- מותאם לנייד (responsive) — mobile-first
- Sections: Hero עם CTA, שירותים/מוצרים, "למה לבחור בנו", המלצות, יצירת קשר
- כפתור WhatsApp צף (float) בפינה ימנית למטה, צבע ירוק #25D366
- טפסי יצירת קשר עם שדות: שם, טלפון, הודעה
- אנימציות כניסה עדינות (CSS animations)
- Google Fonts עם פונט עברי (Heebo)
- Footer עם שעות פעילות, כתובת, טלפון
- SEO meta tags בסיסיים
- הכל בעברית, תוכן שנשמע אמיתי ומשכנע
- אל תכלול placeholder text — כתוב תוכן אמיתי שמתאים לעסק

חשוב מאוד: החזר אך ורק את קוד ה-HTML המלא, ללא הסברים, ללא markdown, ללא ```html.
התחל ישירות עם <!DOCTYPE html> וסיים עם </html>.
"""

    client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""))

    print(f"  🤖 Claude יוצר אתר עבור {business_name}...")
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )
    html = message.content[0].text.strip()

    # ניקוי אם הגיע עם markdown בכל זאת
    if html.startswith("```"):
        html = re.sub(r"^```[a-z]*\n?", "", html)
        html = re.sub(r"\n?```$", "", html)

    return html


# ════════════════════════════════════════════════════════════════
#  שמירה + פתיחה בדפדפן
# ════════════════════════════════════════════════════════════════
def save_and_open(html: str, business_name: str) -> str:
    """שומר את ה-HTML ופותח בדפדפן. מחזיר את הנתיב."""
    demos_dir = Path("demos")
    demos_dir.mkdir(exist_ok=True)

    safe_name = re.sub(r"[^\w\u0590-\u05FF]", "_", business_name)
    filename  = demos_dir / f"demo_{safe_name}.html"

    filename.write_text(html, encoding="utf-8")
    abs_path = str(filename.resolve())
    print(f"  ✅ נשמר: {abs_path}")

    webbrowser.open(f"file:///{abs_path.replace(chr(92), '/')}")
    return abs_path


# ════════════════════════════════════════════════════════════════
#  Deploy ל-Netlify Drop (ללא חשבון — drag & drop API)
# ════════════════════════════════════════════════════════════════
def deploy_to_netlify(html_path: str) -> str:
    """
    מעלה את ה-HTML ל-Netlify Drop ומחזיר URL ציבורי.
    אין צורך בחשבון — שירות חינמי של Netlify.
    """
    print("  📤 מעלה ל-Netlify...")
    try:
        with open(html_path, "rb") as f:
            resp = requests.post(
                "https://api.netlify.com/api/v1/sites",
                headers={"Content-Type": "application/zip"},
                files={"file": ("index.html", f, "text/html")},
                timeout=30,
            )
        # Netlify Drop - try alternative endpoint
        with open(html_path, "rb") as f:
            html_content = f.read()

        # Use Netlify's public deploy API
        boundary = "----FormBoundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="zip"; filename="index.html"\r\n'
            f"Content-Type: text/html\r\n\r\n"
        ).encode() + html_content + f"\r\n--{boundary}--\r\n".encode()

        resp = requests.post(
            "https://api.netlify.com/api/v1/sites",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            timeout=30
        )
        if resp.status_code in (200, 201):
            site_url = resp.json().get("ssl_url") or resp.json().get("url", "")
            if site_url:
                print(f"  🌐 פורסם: {site_url}")
                return site_url
    except Exception as e:
        print(f"  ⚠️  Netlify נכשל ({e}) — האתר נשמר מקומית")
    return ""


# ════════════════════════════════════════════════════════════════
#  פונקציה ראשית לשימוש מהדשבורד
# ════════════════════════════════════════════════════════════════
def create_demo_for_business(
    business: dict,
    api_key: str = "",
    extra_info: str = "",
    deploy: bool = False,
) -> dict:
    """
    מקבל dict של עסק (מה-DB) ומחזיר:
    {
        "html_path": "demos/demo_XYZ.html",
        "public_url": "https://..."  (אם deploy=True)
    }
    """
    html = generate_demo_site(
        business_name=business.get("name", ""),
        category=business.get("category", ""),
        phone=business.get("phone", ""),
        address=business.get("address", ""),
        existing_url=business.get("website", ""),
        extra_info=extra_info,
        api_key=api_key,
    )
    path = save_and_open(html, business.get("name", "business"))

    result = {"html_path": path, "public_url": ""}
    if deploy:
        url = deploy_to_netlify(path)
        result["public_url"] = url

    return result


# ════════════════════════════════════════════════════════════════
#  הרצה עצמאית
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("  גנרטור אתר דמו לעסקים")
    print("=" * 55)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        api_key = input("הזן Anthropic API Key: ").strip()

    print("\nמקור מידע:")
    print("  1. URL של אתר קיים")
    print("  2. פרטים ידניים")
    choice = input("בחר (1/2): ").strip()

    if choice == "1":
        url  = input("URL של האתר הקיים: ").strip()
        name = input("שם העסק: ").strip()
        cat  = input("קטגוריה (למשל: מסעדה, מוסך): ").strip()
        phone = input("טלפון: ").strip()
        addr  = input("כתובת: ").strip()
        extra = input("מידע נוסף (אופציונלי): ").strip()
    else:
        url   = ""
        name  = input("שם העסק: ").strip()
        cat   = input("קטגוריה: ").strip()
        phone = input("טלפון: ").strip()
        addr  = input("כתובת: ").strip()
        extra = input("תאר את העסק בקצרה: ").strip()

    deploy_choice = input("\nלפרסם ל-Netlify (URL ציבורי לשיתוף)? (כן/לא): ").strip()
    should_deploy = deploy_choice in ("כן", "yes", "y")

    biz = {"name": name, "category": cat, "phone": phone, "address": addr, "website": url}
    result = create_demo_for_business(biz, api_key=api_key, extra_info=extra, deploy=should_deploy)

    print(f"\n✅ נשמר ב: {result['html_path']}")
    if result.get("public_url"):
        print(f"🌐 URL ציבורי: {result['public_url']}")
        print("\nשלח את הלינק הזה לבעל העסק ב-WhatsApp!")
