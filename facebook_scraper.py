"""
facebook_scraper.py — סריקת עסקים ישירות מפייסבוק עם Selenium.

שלא כמו חיפוש Google (שנחסם מהר), כאן אנחנו נכנסים ישירות לפייסבוק,
מחפשים עמודים עסקיים, ובודקים אם יש להם אתר או לא.

עסק פייסבוק פעיל ללא אתר = הליד הכי חם שיש.

הרצה:
  python facebook_scraper.py
"""

import sys
import os
import re
import time
import json
import subprocess
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

sys.stdout.reconfigure(encoding="utf-8")

FB_SESSION_DIR = "fb_session_data"


# ════════════════════════════════════════════════════════════════
#  Chrome driver — persistent session
# ════════════════════════════════════════════════════════════════
def init_driver():
    """פותח Chrome עם session שמור (כדי לא להתחבר כל פעם)."""
    subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe"],
                   capture_output=True, creationflags=0x08000000)

    lockfile = Path(FB_SESSION_DIR) / "lockfile"
    if lockfile.exists():
        try:
            lockfile.unlink()
        except PermissionError:
            pass

    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument(f"user-data-dir={os.path.abspath(FB_SESSION_DIR)}")
    opts.add_argument("--disable-notifications")  # חסום popup של FB
    opts.add_argument("--lang=he")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    return driver


def ensure_logged_in(driver):
    """מוודא שמחוברים לפייסבוק. אם לא — מבקש מהמשתמש להתחבר."""
    driver.get("https://m.facebook.com/me")
    time.sleep(3)

    if "login" in driver.current_url.lower() or "checkpoint" in driver.current_url.lower():
        print("\n" + "="*60)
        print("  צריך להתחבר לפייסבוק!")
        print("  התחבר בחלון Chrome שנפתח ואז לחץ ENTER כאן.")
        print("="*60)
        input(">>> לחץ ENTER אחרי שהתחברת...")
        time.sleep(2)

    # ודא שבאמת מחוברים
    driver.get("https://m.facebook.com/me")
    time.sleep(2)
    if "login" in driver.current_url.lower():
        print("❌ עדיין לא מחובר. נסה שוב.")
        return False

    print("✅ מחובר לפייסבוק!")
    return True


# ════════════════════════════════════════════════════════════════
#  חיפוש עמודים עסקיים
# ════════════════════════════════════════════════════════════════
def search_pages(driver, query: str, max_results: int = 20) -> list[dict]:
    """
    מחפש עמודים עסקיים בפייסבוק לפי query.
    משתמש ב-3 שיטות שונות למציאת עמודים.
    """
    from urllib.parse import quote
    results = []
    seen_names = set()

    # סגור popup cookies
    def close_popups():
        for btn_text in ["Allow all cookies", "Allow essential and optional cookies",
                         "Decline optional cookies", "אישור כל העוגיות", "אישור"]:
            try:
                btn = driver.find_element(By.XPATH, f"//button[contains(., '{btn_text}')]")
                btn.click()
                time.sleep(1)
                return
            except Exception:
                pass

    # שיטה 1: חיפוש pages ישירות
    url = f"https://www.facebook.com/search/pages/?q={quote(query)}"
    driver.get(url)
    time.sleep(4)
    close_popups()
    time.sleep(2)

    # גלול 5 פעמים לטעינת תוצאות
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)

    # חלץ כל הלינקים מה-page source (יותר אמין מ-selectors)
    page_source = driver.page_source
    fb_skip = ["search", "login", "groups", "events", "marketplace", "watch",
               "reel", "stories", "hashtag", "photo", "video", "help",
               "settings", "notifications", "messages", "friends", "policies",
               "privacy", "terms", "ads", "pages/create", "page_internal",
               "profile.php", "/me", "bookmarks", "gaming"]

    # חפש URLs של עמודים ב-HTML
    page_urls = re.findall(
        r'href="(https?://(?:www\.)?facebook\.com/([a-zA-Z0-9._\-]{3,80})/?)"',
        page_source
    )

    for full_url, slug in page_urls:
        if any(skip in slug.lower() for skip in fb_skip):
            continue
        if slug in seen_names:
            continue
        seen_names.add(slug)

    # חפש גם שמות עסקים + URLs מה-JS data
    # פייסבוק מטמיע JSON עם נתוני חיפוש
    json_matches = re.findall(r'"name"\s*:\s*"([^"]{3,80})"[^}]*"url"\s*:\s*"(https?://[^"]+facebook[^"]+)"', page_source)
    for name, url in json_matches:
        if any(skip in url.lower() for skip in fb_skip):
            continue
        # Decode unicode escapes
        try:
            name = name.encode().decode("unicode_escape")
        except Exception:
            pass
        if name in seen_names or len(name) < 3:
            continue
        seen_names.add(name)
        results.append({
            "name": name,
            "url": url.split("?")[0].replace("\\", ""),
            "category": "",
            "followers_text": "",
        })

    # חלץ גם מ-aria-label ו-role="article" elements
    try:
        articles = driver.find_elements(By.CSS_SELECTOR, '[role="article"], [role="listitem"]')
        for article in articles:
            try:
                text = article.text.strip()
                if not text or len(text) < 5:
                    continue
                # חפש לינקים בתוך ה-article
                inner_links = article.find_elements(By.TAG_NAME, "a")
                for link in inner_links:
                    href = link.get_attribute("href") or ""
                    link_text = link.text.strip()
                    if not link_text or len(link_text) < 3:
                        continue
                    if "facebook.com/" not in href:
                        continue
                    if any(skip in href.lower() for skip in fb_skip):
                        continue
                    name = link_text.split("\n")[0].strip()
                    if name in seen_names:
                        continue
                    seen_names.add(name)

                    lines = text.split("\n")
                    category = ""
                    followers_text = ""
                    for line in lines:
                        line = line.strip()
                        if any(w in line for w in ["עוקבים", "followers", "likes", "אוהדים"]):
                            followers_text = line
                        elif line and line != name and not category and len(line) > 3:
                            category = line

                    results.append({
                        "name": name,
                        "url": href.split("?")[0].rstrip("/"),
                        "category": category,
                        "followers_text": followers_text,
                    })
            except Exception:
                continue
    except Exception:
        pass

    # שיטה 2: fallback — חפש בכל הלינקים שבדף
    if len(results) < 3:
        all_links = driver.find_elements(By.TAG_NAME, "a")
        for link in all_links:
            try:
                href = link.get_attribute("href") or ""
                text = link.text.strip()
                if not text or len(text) < 3 or "facebook.com/" not in href:
                    continue
                if any(skip in href.lower() for skip in fb_skip):
                    continue
                name = text.split("\n")[0].strip()
                if name in seen_names or len(name) < 3:
                    continue
                if name.lower() in ("facebook", "log in", "meta", "create", "sign up",
                                     "הרשמה", "התחברות", "חיפוש"):
                    continue
                seen_names.add(name)
                results.append({
                    "name": name,
                    "url": href.split("?")[0].rstrip("/"),
                    "category": "",
                    "followers_text": "",
                })
            except Exception:
                continue

    print(f"  [debug] page source length: {len(page_source)}, links found: {len(results)}")
    return results[:max_results]


# ════════════════════════════════════════════════════════════════
#  חילוץ מידע מעמוד עסקי
# ════════════════════════════════════════════════════════════════
def extract_page_info(driver, page_url: str) -> dict:
    """
    נכנס לעמוד עסקי בפייסבוק ומחלץ:
    - website (אם יש)
    - phone
    - address
    - followers count
    - has_recent_posts (פעיל?)
    """
    info = {
        "website": "",
        "phone": "",
        "address": "",
        "followers": 0,
        "has_website": False,
        "is_active": False,
        "last_post_hint": "",
    }

    # נסה גרסת About
    about_url = page_url.rstrip("/") + "/about"
    driver.get(about_url)
    time.sleep(3)

    page_text = driver.find_element(By.TAG_NAME, "body").text

    # חלץ אתר
    # פייסבוק מציג את האתר בפורמט: "האתר\nwww.example.com" או "Website\nwww.example.com"
    website_patterns = [
        r'(?:אתר|Website|אתר אינטרנט)\s*\n\s*((?:https?://)?(?:www\.)?[a-zA-Z0-9][a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}[^\s]*)',
        r'(https?://(?!facebook\.com|instagram\.com|wa\.me)[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}[^\s]*)',
    ]
    for pat in website_patterns:
        m = re.search(pat, page_text, re.IGNORECASE)
        if m:
            site = m.group(1).strip()
            if "facebook" not in site and "instagram" not in site and "wa.me" not in site:
                info["website"] = site if site.startswith("http") else "https://" + site
                info["has_website"] = True
                break

    # חלץ טלפון
    phone_patterns = [
        r'(?:טלפון|Phone|נייד|מספר טלפון)\s*\n\s*(0\d[\d\- ]{7,12})',
        r'(0[2-9]\d[\d\- ]{6,10})',
    ]
    for pat in phone_patterns:
        m = re.search(pat, page_text)
        if m:
            digits = re.sub(r"[^\d]", "", m.group(1))
            if 9 <= len(digits) <= 11:
                info["phone"] = digits
                break

    # חלץ כתובת
    addr_m = re.search(r'(?:כתובת|Address|מיקום)\s*\n\s*(.+?)(?:\n|$)', page_text)
    if addr_m:
        info["address"] = addr_m.group(1).strip()[:100]

    # חלץ עוקבים
    followers_m = re.search(r'([\d,\.]+)\s*(?:עוקבים|followers|people follow)', page_text, re.IGNORECASE)
    if followers_m:
        try:
            info["followers"] = int(followers_m.group(1).replace(",", "").replace(".", ""))
        except ValueError:
            pass

    likes_m = re.search(r'([\d,\.]+)\s*(?:אוהדים|likes|people like)', page_text, re.IGNORECASE)
    if likes_m and not info["followers"]:
        try:
            info["followers"] = int(likes_m.group(1).replace(",", "").replace(".", ""))
        except ValueError:
            pass

    # בדוק פעילות — חזור לעמוד הראשי
    driver.get(page_url)
    time.sleep(2)
    main_text = driver.find_element(By.TAG_NAME, "body").text

    # חפש סימנים של פוסטים אחרונים
    recent_indicators = ["שעה", "שעות", "דקות", "אתמול", "yesterday",
                         "hour", "minute", "יום", "days ago", "Just now"]
    for indicator in recent_indicators:
        if indicator in main_text:
            info["is_active"] = True
            info["last_post_hint"] = indicator
            break

    # גם אם לא מצאנו מילים ספציפיות, אם יש הרבה עוקבים זה סימן חיים
    if info["followers"] > 100:
        info["is_active"] = True

    return info


def parse_followers_text(text: str) -> int:
    """ממיר '2.3K followers' ל-2300."""
    if not text:
        return 0
    m = re.search(r'([\d,.]+)\s*([KkMm]?)', text)
    if not m:
        return 0
    num = float(m.group(1).replace(",", ""))
    suffix = m.group(2).upper()
    if suffix == "K":
        num *= 1000
    elif suffix == "M":
        num *= 1_000_000
    return int(num)


# ════════════════════════════════════════════════════════════════
#  סריקה מלאה — חיפוש + חילוץ + שמירה
# ════════════════════════════════════════════════════════════════
def run_facebook_scan(queries: list[tuple[str, str]], max_per_query: int = 15):
    """
    סריקת פייסבוק מלאה.
    queries = [(category, city), ...]

    עבור כל query:
      1. חפש עמודים עסקיים
      2. לכל עמוד — חלץ מידע (אתר, טלפון, עוקבים)
      3. עסק ללא אתר + פעיל = ליד HOT
      4. שמור ב-DB + סנכרן ל-Supabase
    """
    from database import init_db, business_exists, insert_business, update_business
    from lead_scorer import compute_lead_score, score_tier_hebrew
    from pitch_builder import build_whatsapp_pitch, build_full_pitch, build_sales_summary
    from scraper import _clean_phone

    init_db()

    print("\n" + "="*60)
    print("  Facebook Scraper — לידים ישירות מפייסבוק")
    print("="*60)

    driver = init_driver()
    if not ensure_logged_in(driver):
        driver.quit()
        return

    new_count = 0
    hot_count = 0
    skip_count = 0

    try:
        for qi, (category, city) in enumerate(queries):
            query = f"{category} {city}"
            print(f"\n[{qi+1}/{len(queries)}] FB: {query}")

            pages = search_pages(driver, query, max_results=max_per_query)
            print(f"  נמצאו {len(pages)} עמודים")

            for pi, page in enumerate(pages):
                name = page["name"]
                fb_url = page["url"]

                if business_exists("", name):
                    skip_count += 1
                    continue

                print(f"  [{pi+1}/{len(pages)}] {name}...", end=" ", flush=True)

                # חלץ מידע מהעמוד
                try:
                    info = extract_page_info(driver, fb_url)
                except Exception as e:
                    print(f"ERR: {e}")
                    continue

                phone = _clean_phone(info["phone"])
                website = info["website"]
                has_website = info["has_website"]
                followers = info["followers"] or parse_followers_text(page.get("followers_text", ""))
                is_active = info["is_active"]

                # סנן עסקים לא פעילים בלי טלפון
                if not is_active and followers < 50:
                    print("SKIP (inactive)")
                    skip_count += 1
                    continue

                # ניתוח אתר אם יש
                analysis = {
                    "has_website": 1 if has_website else 0,
                    "has_ssl": 0, "is_responsive": 0, "has_cta": 0,
                    "has_form": 0, "has_fb_pixel": 0, "has_analytics": 0,
                    "load_time_ms": None, "quality_score": 0,
                    "issues": [],
                }

                if has_website and website:
                    try:
                        from analyzer import analyze_website
                        analysis = analyze_website(website)
                    except Exception:
                        analysis["quality_score"] = 5  # assume average

                # Build pitches
                partial = {
                    "name": name, "website": website,
                    **{k: analysis.get(k, 0) for k in [
                        "has_website", "has_ssl", "is_responsive", "has_cta",
                        "has_form", "has_fb_pixel", "has_analytics", "load_time_ms",
                    ]},
                }
                wa = build_whatsapp_pitch(partial)
                fp = build_full_pitch(partial)
                ss = build_sales_summary(partial)

                # Activity score based on FB signals
                activity = 40  # base: found on FB
                if is_active:      activity += 30
                if followers > 500: activity += 15
                elif followers > 100: activity += 10
                if phone:          activity += 15
                activity = min(activity, 100)

                row = {
                    "name": name, "phone": phone, "phone2": "",
                    "email": "", "website": website,
                    "address": info.get("address", ""),
                    "city": city,
                    "category": page.get("category") or category,
                    "search_query": query,
                    "source": "facebook_direct",
                    "facebook_url": fb_url,
                    "instagram_url": "",
                    "fb_followers": followers,
                    "fb_snippet_has_website": 1 if has_website else 0,
                    "whatsapp_pitch": wa, "full_pitch": fp, "sales_summary": ss,
                    **{k: analysis.get(k, 0) for k in [
                        "has_website", "has_ssl", "is_responsive",
                        "has_cta", "has_form", "has_fb_pixel",
                        "has_analytics", "load_time_ms", "quality_score",
                    ]},
                    "issues": json.dumps(analysis.get("issues", []), ensure_ascii=False),
                    "cms_platform": analysis.get("cms_platform"),
                    "seo_score": analysis.get("seo_score"),
                    "activity_score": activity,
                    "is_likely_active": 1 if is_active else 0,
                    "activity_details": json.dumps([
                        f"FB followers: {followers}",
                        f"FB active: {is_active}",
                        f"FB website: {'yes' if has_website else 'no'}",
                    ], ensure_ascii=False),
                }

                bid = insert_business(row)
                lead_score, _ = compute_lead_score({**row, "id": bid})
                update_business(bid, {"lead_score": lead_score})

                tier = score_tier_hebrew(lead_score)
                site_tag = f"SITE:{website[:30]}" if has_website else "NO-SITE"
                if lead_score >= 70:
                    hot_count += 1
                print(f"{tier} {lead_score}/100 | {site_tag} | f:{followers}")
                new_count += 1

                time.sleep(1)  # השהייה בין עמודים

            time.sleep(2)  # השהייה בין חיפושים

    except KeyboardInterrupt:
        print("\n⏹️ נעצר.")
    finally:
        driver.quit()

    print(f"\n{'='*60}")
    print(f"Facebook scan DONE: {new_count} new | {hot_count} HOT | {skip_count} skipped")
    return new_count


# ════════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    from config import FACEBOOK_FOCUSED_QUERIES
    run_facebook_scan(FACEBOOK_FOCUSED_QUERIES)
