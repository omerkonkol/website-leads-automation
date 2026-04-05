"""
demo_generator.py — יוצר אתר דמו אישי לכל עסק.

התהליך:
  1. מחפש עסק דומה בקטגוריה ומוצא אתר פשוט ונקי שלו
  2. שולף את ה-HTML של אותו אתר כ"תבנית עיצוב"
  3. Claude לוקח את העיצוב + נתוני העסק החדש → מייצר גרסה חדשה
  4. שומר כ-HTML יחיד, פותח בדפדפן, ומפרסם ל-Netlify (אם רוצים)
"""

import sys
import os
import re
import time
import webbrowser
import requests
from pathlib import Path
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8")

import anthropic

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
}


# ════════════════════════════════════════════════════════════════
#  שלב 1: מציאת אתר תבנית — עסק דומה עם אתר פשוט
# ════════════════════════════════════════════════════════════════
def find_template_sites(category: str, serpapi_key: str = "") -> list[str]:
    """
    מחפש אתרי עסקים בקטגוריה נתונה.
    מחזיר רשימת URLs לבחינה.
    """
    urls = []

    # ── ניסיון 1: SerpApi ──
    if serpapi_key and serpapi_key != "YOUR_SERPAPI_KEY_HERE":
        try:
            params = {
                "engine":  "google",
                "q":       f'{category} site:.co.il OR site:.com אתר עסקי',
                "hl":      "he",
                "gl":      "il",
                "num":     10,
                "api_key": serpapi_key,
            }
            resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
            data = resp.json()
            for r in data.get("organic_results", []):
                link = r.get("link", "")
                if link and _is_usable_url(link):
                    urls.append(link)
        except Exception as e:
            print(f"  [SerpApi] {e}")

    # ── ניסיון 2: Google ישיר (fallback) ──
    if not urls:
        try:
            q   = f"{category} אתר עסקי ישראל"
            url = f"https://www.google.com/search?q={requests.utils.quote(q)}&num=10&hl=he"
            r   = requests.get(url, headers=HEADERS, timeout=12)
            found = re.findall(r'href="(https?://[^"&]+)"', r.text)
            for u in found:
                if _is_usable_url(u) and u not in urls:
                    urls.append(u)
                if len(urls) >= 8:
                    break
        except Exception as e:
            print(f"  [Google fallback] {e}")

    return urls[:8]


def _is_usable_url(url: str) -> bool:
    """מסנן URLs של גוגל, ויקיפדיה וספריות."""
    skip = ["google.", "youtube.", "facebook.", "wikipedia.", "wix.com",
            "wordpress.com", "blogspot.", "maps.", "instagram.", "linkedin.",
            "yad2.", "zap.", "rami-levy.", "wolt.", "10bis."]
    return not any(s in url for s in skip)


# ════════════════════════════════════════════════════════════════
#  שלב 2: דירוג פשטות האתר — מחזיר ציון גבוה לאתרים פשוטים
# ════════════════════════════════════════════════════════════════
def score_simplicity(url: str) -> tuple[int, str]:
    """
    מחזיר (ציון, html).
    ציון גבוה = אתר פשוט ונקי = טוב לשימוש כתבנית.
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if resp.status_code != 200:
            return 0, ""
        html = resp.text

        score = 100
        # אתרים עם המון JS — מורכבים מדי
        js_count  = html.count("<script")
        css_count = html.count("<link")
        score -= min(js_count * 4, 40)
        score -= min(css_count * 3, 30)

        # גודל: רצוי בין 5KB ל-200KB
        size_kb = len(html) / 1024
        if size_kb < 3 or size_kb > 500:
            score -= 30
        elif size_kb < 10:
            score -= 10

        # בונסים: RTL, פונט עברי, responsive
        if 'dir="rtl"' in html or "direction:rtl" in html: score += 15
        if "Heebo" in html or "Rubik" in html:              score += 10
        if "viewport" in html:                               score += 10
        if "whatsapp" in html.lower():                      score += 5

        # פנלטי: frameworks כבדים
        for fw in ["react", "angular", "vue", "next.js", "nuxt"]:
            if fw in html.lower():
                score -= 25

        return max(0, score), html

    except Exception:
        return 0, ""


def find_best_template(category: str, serpapi_key: str = "") -> tuple[str, str]:
    """
    מוצא את ה-URL + HTML של האתר הפשוט ביותר בקטגוריה.
    מחזיר (template_url, template_html).
    """
    print(f"  🔍 מחפש אתר תבנית לקטגוריה: {category}")
    candidates = find_template_sites(category, serpapi_key)

    if not candidates:
        print("  ⚠️  לא נמצאו מועמדים — יוצר ממש ב-Claude")
        return "", ""

    best_url, best_html, best_score = "", "", -1
    for url in candidates:
        print(f"    בודק: {url[:60]}...")
        score, html = score_simplicity(url)
        print(f"    ציון פשטות: {score}")
        if score > best_score:
            best_score, best_url, best_html = score, url, html
        if best_score >= 70:   # מספיק טוב — לא צריך להמשיך
            break
        time.sleep(0.3)

    print(f"  ✅ תבנית נבחרה: {best_url} (ציון {best_score})")
    return best_url, best_html


# ════════════════════════════════════════════════════════════════
#  שלב 3: עיבוד ה-HTML לנשלח ל-Claude (לא יותר מ-12K תווים)
# ════════════════════════════════════════════════════════════════
def extract_template_structure(html: str) -> str:
    """
    שומר את השלד העיצובי של האתר:
    - CSS (inline + style tags)
    - מבנה ה-HTML (ללא תוכן ספציפי)
    - מסיר JS כבד, תמונות base64, וסקריפטים
    """
    # הסר JS
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
    # הסר base64
    html = re.sub(r'data:[^;]+;base64,[A-Za-z0-9+/=]+', 'IMAGE_PLACEHOLDER', html)
    # הסר תגובות HTML
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    # צמצם רווחים
    html = re.sub(r"\n\s*\n", "\n", html)
    html = re.sub(r" {4,}", "  ", html)

    # קחו מקסימום 12000 תווים
    return html[:12000]


# ════════════════════════════════════════════════════════════════
#  שלב 4: Claude מסתגל לתבנית + ממלא תוכן חדש
# ════════════════════════════════════════════════════════════════
def generate_with_template(
    business_name: str,
    category: str,
    phone: str,
    address: str,
    template_url: str,
    template_html: str,
    extra_info: str = "",
    api_key: str = "",
) -> str:
    # קדימות: ארגומנט → env var → config.py
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        try:
            from config import ANTHROPIC_API_KEY
            api_key = ANTHROPIC_API_KEY
        except ImportError:
            pass
    client = anthropic.Anthropic(api_key=api_key)

    # מידע על העסק
    biz_info = "\n".join(filter(None, [
        f"שם: {business_name}",
        f"קטגוריה: {category}",
        f"טלפון: {phone}" if phone else "",
        f"כתובת: {address}" if address else "",
        f"מידע נוסף: {extra_info}" if extra_info else "",
    ]))

    if template_html:
        structure = extract_template_structure(template_html)
        prompt = f"""אתה מפתח ווב מומחה. המשימה שלך: קח את עיצוב האתר הבא ו**החלף את כל התוכן** בתוכן של עסק חדש.

## מקור ההשראה העיצובית:
URL: {template_url}

HTML של התבנית (שמור בדיוק את העיצוב, הצבעים, הלייאוט):
```html
{structure}
```

## העסק החדש — מלא את כל התוכן לפי הפרטים האלה:
{biz_info}

## הוראות:
1. **שמור את העיצוב, הצבעים, ה-CSS, הפונטים** — אלה יישארו כמו שהם
2. **החלף הכל**: שם, כתובת, טלפון, תיאורים, כותרות, שירותים — הכל יהיה של העסק החדש
3. **הוסף** כפתור WhatsApp צף בפינה ימנית למטה (ירוק #25D366) עם הטלפון: {phone or 'הטלפון של העסק'}
4. וודא שהאתר **עובד ב-RTL עברית** מלאה
5. **הפוך אותו ל-self-contained** — הטמע את כל ה-CSS inline, הפנה לתמונות מ-Unsplash/Pexels עם keywords באנגלית שמתאימים לקטגוריה "{category}"
6. **הוסף section** "צרו קשר" עם שדות: שם, טלפון, הודעה
7. אל תשתמש ב-placeholder text — כתוב תוכן אמיתי ומשכנע בעברית

**החזר HTML מלא בלבד** — ללא הסברים, ללא ```markdown. התחל ב-<!DOCTYPE html>."""

    else:
        # אין תבנית — בנה פשוט ונקי בעצמך
        prompt = f"""אתה מפתח ווב. בנה landing page **פשוט, נקי ומהיר** לעסק הבא.

{biz_info}

## דרישות עיצוב — פשוט ומקצועי:
- HTML + CSS inline בלבד (ללא frameworks, ללא JS מורכב)
- RTL עברית, פונט Heebo מ-Google Fonts
- צבע ראשי שמתאים לקטגוריה "{category}"
- Layout: Hero → שירותים (3 כרטיסים) → "למה אנחנו" → צרו קשר → Footer
- כפתור WhatsApp צף ירוק (#25D366)
- מותאם לנייד (responsive)
- תמונות מ-Unsplash (src="https://source.unsplash.com/800x500/?{category.replace(' ','+')}")
- טופס יצירת קשר: שם, טלפון, הודעה
- תוכן אמיתי ומשכנע בעברית — לא placeholder

**החזר HTML מלא בלבד.** התחל ב-<!DOCTYPE html>."""

    print(f"  🤖 Claude מסתגל לתבנית ומייצר אתר עבור {business_name}...")
    msg = client.messages.create(
        model="claude-sonnet-4-6",   # Sonnet מהיר יותר לעבודה הזו
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}]
    )
    html = msg.content[0].text.strip()

    # ניקוי markdown אם הגיע
    html = re.sub(r"^```[a-z]*\n?", "", html)
    html = re.sub(r"\n?```$", "", html)
    return html


# ════════════════════════════════════════════════════════════════
#  שמירה + פתיחה בדפדפן
# ════════════════════════════════════════════════════════════════
def save_and_open(html: str, business_name: str) -> str:
    demos_dir = Path("demos")
    demos_dir.mkdir(exist_ok=True)
    safe_name = re.sub(r"[^\w\u0590-\u05FF]", "_", business_name)
    path = demos_dir / f"demo_{safe_name}.html"
    path.write_text(html, encoding="utf-8")
    abs_path = str(path.resolve()).replace("\\", "/")
    print(f"  ✅ נשמר: {abs_path}")
    webbrowser.open(f"file:///{abs_path}")
    return str(path.resolve())


# ════════════════════════════════════════════════════════════════
#  Deploy ל-GitHub Pages — ללא טוקן נוסף
# ════════════════════════════════════════════════════════════════
def _github_config():
    try:
        from config import GITHUB_USERNAME, GITHUB_REPO
        return GITHUB_USERNAME, GITHUB_REPO
    except ImportError:
        return "dev", "website-leads-automation"


def _get_github_token() -> str:
    """שולף את ה-token מ-git credential manager (כבר קיים מההתקנה)."""
    import subprocess
    try:
        result = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n",
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if line.startswith("password="):
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return ""


def deploy_to_github_pages(html_path: str, business_name: str = "") -> str:
    """
    מעלה את קובץ ה-HTML ל-GitHub Pages דרך GitHub API.
    לא דורש שום הגדרה נוספת — משתמש ב-token הקיים מ-git credentials.
    מחזיר URL ציבורי: https://USERNAME.github.io/REPO/demos/NAME.html
    """
    import base64, re as _re

    token = _get_github_token()
    if not token:
        print("  [GitHub Pages] לא נמצא token — האתר נשמר מקומית בלבד")
        return ""

    safe_name = _re.sub(r"[^\w\u0590-\u05FF]", "_", business_name or Path(html_path).stem)
    remote_path = f"demos/demo_{safe_name}.html"

    html_content  = Path(html_path).read_bytes()
    encoded       = base64.b64encode(html_content).decode()

    GITHUB_USER, GITHUB_REPO = _github_config()
    api_url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{remote_path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept":        "application/vnd.github.v3+json",
        "User-Agent":    "Python",
    }

    # בדוק אם הקובץ כבר קיים (כדי לעדכן ולא ליצור מחדש)
    sha = ""
    try:
        existing = requests.get(api_url, headers=headers, timeout=10)
        if existing.status_code == 200:
            sha = existing.json().get("sha", "")
    except Exception:
        pass

    payload = {
        "message": f"Add demo for {business_name}",
        "content": encoded,
        "branch":  "main",
    }
    if sha:
        payload["sha"] = sha

    print(f"  מעלה ל-GitHub Pages: {remote_path}...")
    try:
        resp = requests.put(api_url, json=payload, headers=headers, timeout=30)
        if resp.status_code in (200, 201):
            public_url = (
                f"https://{GITHUB_USER}.github.io/{GITHUB_REPO}/{remote_path}"
            )
            print(f"  פורסם: {public_url}")
            print(f"  (יכול לקחת עד דקה עד שGitHub Pages מעדכן)")
            return public_url
        else:
            print(f"  [GitHub Pages] שגיאה {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"  [GitHub Pages] נכשל: {e}")
    return ""


# ════════════════════════════════════════════════════════════════
#  נקודת כניסה ראשית — לשימוש מהדשבורד
# ════════════════════════════════════════════════════════════════
def create_demo_for_business(
    business: dict,
    api_key: str = "",
    extra_info: str = "",
    deploy: bool = False,
) -> dict:
    """
    מקבל dict עסק → מוצא תבנית → מייצר HTML → מחזיר:
    { "html_path": "...", "public_url": "..." }
    """
    from config import SERPAPI_KEY

    category = business.get("category") or business.get("search_query", "עסק")

    # מצא תבנית מאתר עסק דומה
    template_url, template_html = find_best_template(category, serpapi_key=SERPAPI_KEY)

    html = generate_with_template(
        business_name=business.get("name", ""),
        category=category,
        phone=business.get("phone", ""),
        address=business.get("address", ""),
        template_url=template_url,
        template_html=template_html,
        extra_info=extra_info,
        api_key=api_key,
    )

    path   = save_and_open(html, business.get("name", "business"))
    result = {"html_path": path, "public_url": ""}

    if deploy:
        result["public_url"] = deploy_to_github_pages(path, business_name=business.get("name", ""))

    return result


# ════════════════════════════════════════════════════════════════
#  הרצה עצמאית
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 55)
    print("  גנרטור אתר דמו — מבוסס תבנית אתר דומה")
    print("=" * 55)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        api_key = input("Anthropic API Key: ").strip()

    name   = input("שם העסק: ").strip()
    cat    = input("קטגוריה (מסעדה / מוסך / קוסמטיקה...): ").strip()
    phone  = input("טלפון: ").strip()
    addr   = input("כתובת (אופציונלי): ").strip()
    extra  = input("מידע נוסף (אופציונלי): ").strip()
    dep    = input("לפרסם ל-Netlify? (כן/לא): ").strip() in ("כן","yes","y")

    biz    = {"name": name, "category": cat, "phone": phone, "address": addr, "website": ""}
    result = create_demo_for_business(biz, api_key=api_key, extra_info=extra, deploy=dep)

    print(f"\n✅ {result['html_path']}")
    if result.get("public_url"):
        print(f"🌐 {result['public_url']}")
