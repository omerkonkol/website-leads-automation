"""
scraper.py — שליפת עסקים ממקורות מרובים (חינמי לגמרי).

מקורות:
  1. B144.co.il              — מאגר עסקים ישראלי מקיף, JSON מוטמע בדף
  2. דפי זהב (d.co.il)      — מאגר ישראלי, ללא API key
  3. Yad2 /b144              — בעלי מקצוע ונותני שירותים
  4. Google Maps / SerpApi   — אופציונלי, 100 חינם/חודש
  5. Google Search ישיר      — fallback (עובד חלקית)
"""

import re
import json
import time
import requests
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
from config import SERPAPI_KEY, MAX_RESULTS_PER_QUERY

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ════════════════════════════════════════════════════════════════
#  פונקציות עזר
# ════════════════════════════════════════════════════════════════
def _clean_phone(raw: str) -> str:
    if not raw:
        return ""
    digits = re.sub(r"[^\d]", "", str(raw))
    if len(digits) == 10 and digits.startswith("0"):
        return digits
    if len(digits) == 9:
        return "0" + digits
    if len(digits) == 7:
        return "0" + digits  # local number
    return digits if digits else ""


def _clean_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    if not url.startswith("http"):
        url = "https://" + url
    return url


def _make_biz(name, phone="", email="", website="", address="", category="", query="", source="") -> dict:
    return {
        "name":         name.strip(),
        "phone":        _clean_phone(phone),
        "email":        email.strip().lower() if email else "",
        "website":      _clean_url(website),
        "address":      address.strip(),
        "category":     category.strip(),
        "search_query": query,
        "source":       source,
    }


# ════════════════════════════════════════════════════════════════
#  מקור 1: B144.co.il — המקור העיקרי (חינמי, JSON מוטמע)
# ════════════════════════════════════════════════════════════════
def scrape_b144(query: str) -> list[dict]:
    """
    B144 — המאגר הגדול בישראל.
    משתמש ב-/api/search שמחזיר תוצאות ב-searchObj,
    ובדף הראשי שמחזיר initialNewBusinessesData.
    """
    results = []
    seen = set()

    def _add(biz_list, filter_query=False):
        """מוסיף עסקים מרשימת JSON של B144."""
        parts = query.lower().split()
        for biz in biz_list:
            name = biz.get("Name") or ""
            if not name or len(name) < 3:
                continue
            # סנן פריטי ניווט
            if name in ("המלצות", "עסקים", "תחומים", "כתבות", "קופונים", "מחירונים", "חנויות",
                         "חיפושים", "חיפוש עסקים", "חיפוש אנשים", "חיפוש חנויות אונליין", "חיפוש מפות"):
                continue
            key = name.strip().lower()
            if key in seen:
                continue
            seen.add(key)

            area = str(biz.get("Area_Code", ""))
            phone_raw = str(biz.get("Phone", ""))
            # B144 truncates phone in search — take area code as prefix
            phone = area + phone_raw.replace(area, "").replace("...", "").replace("-", "").strip()

            website = biz.get("Web") or ""
            city = biz.get("City") or ""
            street = biz.get("Street") or ""
            street_no = str(biz.get("Street_No") or "")
            address = f"{street} {street_no} {city}".strip()
            category = biz.get("CategoriesList") or biz.get("Cat_desc") or ""

            results.append(_make_biz(
                name=name, phone=phone, website=website,
                address=address, category=category,
                query=query, source="b144"
            ))

    try:
        # ניסיון 1: /api/search — מחזיר searchObj
        api_url = f"https://www.b144.co.il/api/search?query={quote(query)}"
        resp = requests.get(api_url, headers=HEADERS, timeout=15)
        json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            pp = data.get("props", {}).get("pageProps", {})
            _add(pp.get("searchObj", []))
            _add(pp.get("businessesToDisplay", []))

        # ניסיון 2: דף ראשי — initialNewBusinessesData
        if len(results) < 5:
            home_url = f"https://www.b144.co.il/?query={quote(query)}"
            resp2 = requests.get(home_url, headers=HEADERS, timeout=15)
            json_match2 = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp2.text, re.DOTALL)
            if json_match2:
                data2 = json.loads(json_match2.group(1))
                pp2 = data2.get("props", {}).get("pageProps", {})
                _add(pp2.get("initialNewBusinessesData", []))
                _add(pp2.get("initialUserRecommends", []))

    except Exception as e:
        print(f"    [B144] שגיאה: {e}")

    print(f"    [B144] '{query}' → {len(results)} עסקים")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 2: דפי זהב (d.co.il)
# ════════════════════════════════════════════════════════════════
def scrape_dapei_zahav(query: str) -> list[dict]:
    """דפי זהב — URL מעודכן + selectors מתוקנים + ללא כפילויות."""
    results = []
    seen_names = set()
    url = f"https://www.d.co.il/SearchResults/?query={quote(query)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        # selectors מעודכנים למבנה הנוכחי של d.co.il
        for card in soup.select("li[data-card], .card-item, .business-card")[:MAX_RESULTS_PER_QUERY * 2]:
            name_el = card.select_one(".card-desc h3 a, .card-desc h3, h3 a")
            phone_el = card.select_one(".btn-phone-yellow, .phone-info, [href^='tel:']")
            addr_el = card.select_one(".navigation-map, .location-title, [class*='address']")

            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 3:
                continue
            # מניעת כפילויות
            key = name.strip().lower()
            if key in seen_names:
                continue
            seen_names.add(key)

            phone = ""
            if phone_el:
                phone = phone_el.get("href", "").replace("tel:", "") or phone_el.get_text(strip=True)

            address = addr_el.get_text(strip=True) if addr_el else ""

            results.append(_make_biz(name, phone, address=address, query=query, source="dapei_zahav"))

        # fallback: חפש שמות עסקים בכל h3
        if not results:
            for el in soup.select(".card-desc h3 a, h3 a")[:MAX_RESULTS_PER_QUERY * 2]:
                name = el.get_text(strip=True)
                if not name or len(name) < 3:
                    continue
                key = name.strip().lower()
                if key in seen_names:
                    continue
                seen_names.add(key)
                results.append(_make_biz(name, query=query, source="dapei_zahav"))

            # חפש מספרי טלפון בדף
            phones = re.findall(r"0\d[\d\-]{7,9}", resp.text)
            for i, r in enumerate(results):
                if i < len(phones) and not r["phone"]:
                    r["phone"] = _clean_phone(phones[i])

    except Exception as e:
        print(f"    [דפי זהב] שגיאה: {e}")

    print(f"    [דפי זהב] '{query}' → {len(results)} עסקים")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 3: Yad2 /b144 — בעלי מקצוע
# ════════════════════════════════════════════════════════════════
def scrape_yad2(query: str) -> list[dict]:
    """Yad2 professionals directory — JSON מוטמע בדף."""
    results = []
    url = f"https://www.yad2.co.il/b144/search?text={quote(query)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        html = resp.text

        # חלץ JSON מוטמע
        json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            page_props = data.get("props", {}).get("pageProps", {})
            listings = (
                page_props.get("listings", [])
                or page_props.get("results", [])
                or page_props.get("businesses", [])
                or _find_businesses_in_json(page_props)
                or []
            )

            for item in listings[:MAX_RESULTS_PER_QUERY]:
                # Yad2 מבנה מקונן
                top = item.get("topSection", {}) if isinstance(item, dict) else {}
                details = item.get("details", {}) if isinstance(item, dict) else {}
                contact = item.get("contact", {}) if isinstance(item, dict) else {}

                name = (top.get("name") or item.get("name") or
                        item.get("Name") or item.get("businessName") or "")
                if not name or len(name) < 2:
                    continue
                phone = str(contact.get("phone") or item.get("phone") or item.get("Phone") or "")
                address = details.get("address") or item.get("address") or ""
                website = item.get("website") or item.get("Web") or ""

                results.append(_make_biz(
                    name=name, phone=phone, website=website,
                    address=address, query=query, source="yad2"
                ))

    except Exception as e:
        print(f"    [Yad2] שגיאה: {e}")

    print(f"    [Yad2] '{query}' → {len(results)} עסקים")
    return results


# ════════════════════════════════════════════════════════════════
#  מקור 4: Google Maps דרך SerpApi (אופציונלי, 100 חינם/חודש)
# ════════════════════════════════════════════════════════════════
def scrape_google_maps(query: str) -> list[dict]:
    results = []
    params = {
        "engine":  "google_maps",
        "q":       query,
        "hl":      "he",
        "gl":      "il",
        "type":    "search",
        "num":     MAX_RESULTS_PER_QUERY,
        "api_key": SERPAPI_KEY,
    }
    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=25)
        resp.raise_for_status()
        for p in resp.json().get("local_results", []):
            b = _make_biz(
                name=p.get("title", ""),
                phone=p.get("phone", ""),
                website=p.get("website", ""),
                address=p.get("address", ""),
                category=p.get("type", ""),
                query=query,
                source="google_maps",
            )
            results.append(b)
    except Exception as e:
        print(f"    [Google Maps] {e}")
    print(f"    [Google Maps] '{query}' → {len(results)} עסקים")
    return results


# ════════════════════════════════════════════════════════════════
#  מקור 5: Google Search ישיר — fallback
# ════════════════════════════════════════════════════════════════
def scrape_google_search(query: str) -> list[dict]:
    """Google Search — מנסה לחלץ תוצאות, אבל Google חוסם לפעמים."""
    results = []
    url = f"https://www.google.com/search?q={quote(query)}&num=20&hl=he&gl=il"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        html = resp.text

        # בדוק אם Google חסם אותנו
        if "detected unusual traffic" in html or "captcha" in html.lower():
            print("    [Google Search] חסום — Google זיהה תנועה אוטומטית")
            return results

        phones = list(dict.fromkeys(re.findall(r"0\d[\d\-]{7,9}", html)))

        soup = BeautifulSoup(html, "html.parser")
        names = []
        for el in soup.select("h3"):
            t = el.get_text(strip=True)
            if 3 < len(t) < 60 and not t.startswith("http"):
                names.append(t)

        found_urls = re.findall(r'href="(https?://(?!google|youtube|facebook|wikipedia)[^"]{8,80})"', html)
        found_urls = [u for u in dict.fromkeys(found_urls) if ".co.il" in u or ".com" in u]

        for i, name in enumerate(names[:MAX_RESULTS_PER_QUERY]):
            phone   = _clean_phone(phones[i]) if i < len(phones) else ""
            website = found_urls[i]           if i < len(found_urls) else ""
            results.append(_make_biz(name, phone, website=website, query=query, source="google_search"))

    except Exception as e:
        print(f"    [Google Search] {e}")
    print(f"    [Google Search] '{query}' → {len(results)} עסקים")
    return results


# ════════════════════════════════════════════════════════════════
#  העשרת נתונים מהאתר — מייל, רשתות חברתיות, עיר
# ══════���═════════════════════════════════════════════════════════
EMAIL_SKIP = ["example.com", "sentry.io", "googleapis", "w3.org", "schema.org",
              "wixpress.com", "squarespace.com", "shopify", "google.com"]


def enrich_from_website(url: str) -> dict:
    """שולף מהאתר: מייל, פייסבוק URL, אינסטגרם URL, עיר."""
    result = {"email": "", "facebook_url": "", "instagram_url": "", "city": ""}
    if not url:
        return result
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        html = resp.text

        for em in re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html):
            if not any(s in em for s in EMAIL_SKIP):
                result["email"] = em.lower()
                break

        for fb in re.findall(r'href=["\']?(https?://(?:www\.)?facebook\.com/[^"\'>\s?]{3,80})', html):
            if "/sharer" not in fb and "/share?" not in fb and "pages/create" not in fb:
                result["facebook_url"] = fb.rstrip("/")
                break

        for ig in re.findall(r'href=["\']?(https?://(?:www\.)?instagram\.com/[^"\'>\s?]{2,60})', html):
            if "/p/" not in ig and "accounts" not in ig:
                result["instagram_url"] = ig.rstrip("/")
                break

        city_m = re.search(r'"addressLocality"\s*:\s*"([^"]{2,30})"', html)
        if city_m:
            result["city"] = city_m.group(1)

    except Exception:
        pass
    return result


def extract_email_from_website(url: str) -> str:
    return enrich_from_website(url).get("email", "")


# ════════════════════════════════════════════════════════════════
#  נקודת כניסה ראשית
# ════════════════════════════════════════════════════════════════
def scrape_businesses(query: str) -> list[dict]:
    """
    מפעיל את כל המקורות לפי זמינות ומחזיר רשימה מאוחדת ללא כפילויות.
    כל המקורות חינמיים לגמרי (חוץ מ-SerpApi שאופציונלי).
    """
    all_results: list[dict] = []
    seen_names: set[str]    = set()

    def add_results(source_results: list[dict]):
        for biz in source_results:
            key = biz["name"].strip().lower()
            if key and key not in seen_names:
                seen_names.add(key)
                all_results.append(biz)

    # ── מקור 1: B144 — המקור העיקרי (חינמי) ──
    add_results(scrape_b144(query))
    time.sleep(0.5)

    # ── מקור 2: דפי זהב (חינמי) ──
    add_results(scrape_dapei_zahav(query))
    time.sleep(0.5)

    # ── מקור 3: Yad2 (חינמי) ──
    add_results(scrape_yad2(query))
    time.sleep(0.5)

    # ── מקור 4: Google Maps — רק אם יש SerpApi key ──
    if SERPAPI_KEY and SERPAPI_KEY != "YOUR_SERPAPI_KEY_HERE":
        add_results(scrape_google_maps(query))
        time.sleep(0.5)
    else:
        print("    [Google Maps] SERPAPI_KEY לא מוגדר — דולג (אופציונלי)")

    # ── מקור 5: Google Search ישיר (חינמי, עובד חלקית) ──
    add_results(scrape_google_search(query))

    print(f"\n  ✅ סה\"כ '{query}': {len(all_results)} עסקים ייחודיים מכל המקורות")
    return all_results[:MAX_RESULTS_PER_QUERY * 3]
