"""
scraper.py — שליפת עסקים ממקורות מרובים.

מקורות (לפי אפקטיביות):
  1. Google Maps / SerpApi          — הכי מדויק, מחיר: ~100 חינם/חודש
  2. דפי זהב (d.co.il)             — מאגר ישראלי מקיף, ללא API key
  3. בז"ן / Bizportal               — עסקים רשומים ברשות התאגידים
  4. Facebook Business Search       — עסקים עם עמוד FB אבל אולי בלי אתר
  5. Google Search ישיר             — fallback כללי
"""

import re
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
    # ישראל: 10 ספרות מתחיל ב-0, או 9 ספרות ישירות
    if len(digits) == 10 and digits.startswith("0"):
        return digits
    if len(digits) == 9:
        return "0" + digits
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


def _make_biz(name, phone="", email="", website="", address="", category="", query="") -> dict:
    return {
        "name":         name.strip(),
        "phone":        _clean_phone(phone),
        "email":        email.strip().lower(),
        "website":      _clean_url(website),
        "address":      address.strip(),
        "category":     category.strip(),
        "search_query": query,
    }


# ════════════════════════════════════════════════════════════════
#  מקור 1: Google Maps דרך SerpApi (הכי מדויק)
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
            )
            b["source"] = "google_maps"
            results.append(b)
    except Exception as e:
        print(f"    [Google Maps] {e}")
    print(f"    [Google Maps] '{query}' → {len(results)} עסקים")
    return results


# ════════════════════════════════════════════════════════════════
#  מקור 2: דפי זהב (d.co.il) — מאגר ישראלי ללא API
# ════════════════════════════════════════════════════════════════
def scrape_dapei_zahav(query: str) -> list[dict]:
    """
    חיפוש בדפי זהב — מאגר עסקים ישראלי מקיף.
    דוגמת שאילתה: "מסעדות פתח תקווה"
    """
    results = []
    # חלק את השאילתה לקטגוריה + עיר
    parts    = query.strip().split()
    category = " ".join(parts[:-1]) if len(parts) > 1 else query
    city     = parts[-1] if len(parts) > 1 else ""

    url = f"https://www.d.co.il/search/?q={quote(query)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select(".business-item, .result-item, [class*='business'], [class*='listing']")[:MAX_RESULTS_PER_QUERY]:
            name_el  = card.select_one("[class*='name'], [class*='title'], h2, h3")
            phone_el = card.select_one("[class*='phone'], [href^='tel:']")
            site_el  = card.select_one("a[href*='http']:not([href*='d.co.il'])")
            addr_el  = card.select_one("[class*='address'], [class*='addr']")

            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                continue

            phone   = ""
            if phone_el:
                phone = phone_el.get("href", "").replace("tel:", "") or phone_el.get_text(strip=True)

            website = site_el.get("href", "") if site_el else ""
            address = addr_el.get_text(strip=True) if addr_el else city

            results.append(_make_biz(name, phone, website=website, address=address,
                                     category=category, query=query))

    except Exception as e:
        print(f"    [דפי זהב] {e}")

    # אם לא הצליח עם selectors ספציפיים — חפש כל לינק שנראה כשם עסק
    if not results:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            phones = re.findall(r"0\d[\d\-]{7,9}", resp.text)
            links  = [a.get_text(strip=True) for a in soup.select("h2 a, h3 a, .name a") if len(a.get_text(strip=True)) > 2]
            for i, name in enumerate(links[:MAX_RESULTS_PER_QUERY]):
                phone = _clean_phone(phones[i]) if i < len(phones) else ""
                results.append(_make_biz(name, phone, category=category, query=query))
        except Exception:
            pass

    print(f"    [דפי זהב] '{query}' → {len(results)} עסקים")
    return results


# ════════════════════════════════════════════════════════════════
#  מקור 3: Bizportal / חיפוש חברות רשומות
# ════════════════════════════════════════════════════════════════
def scrape_bizportal(query: str) -> list[dict]:
    """חיפוש ב-Bizportal — עסקים רשומים ברשות התאגידים."""
    results = []
    url = f"https://www.bizportal.co.il/generalmarket/quote/market/searchresult?searchstring={quote(query)}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.select("tr, .company-row")[:MAX_RESULTS_PER_QUERY]:
            name_el = row.select_one("td:first-child a, .company-name")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if name and len(name) > 2:
                results.append(_make_biz(name, query=query))
    except Exception as e:
        print(f"    [Bizportal] {e}")
    print(f"    [Bizportal] '{query}' → {len(results)} עסקים")
    return results


# ════════════════════════════════════════════════════════════════
#  מקור 4: Facebook Places Search (ללא login)
# ════════════════════════════════════════════════════════════════
def scrape_facebook_places(query: str) -> list[dict]:
    """
    מחפש עמודי עסקים בפייסבוק — עסקים עם פייסבוק אבל לפעמים בלי אתר.
    """
    results = []
    search_url = f"https://www.facebook.com/search/pages/?q={quote(query)}"
    try:
        resp = requests.get(search_url, headers={
            **HEADERS,
            "User-Agent": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)"
        }, timeout=12)
        # Facebook מגן עם JS — ננסה לחלץ JSON מוטמע
        phones  = re.findall(r'"formatted_phone":\s*"([^"]+)"', resp.text)
        names   = re.findall(r'"name":\s*"([^"]{3,60})"', resp.text)
        websites = re.findall(r'"website":\s*"([^"]+)"', resp.text)

        for i, name in enumerate(names[:MAX_RESULTS_PER_QUERY]):
            if any(skip in name.lower() for skip in ["facebook", "meta", "page", "group"]):
                continue
            phone   = _clean_phone(phones[i])   if i < len(phones)   else ""
            website = websites[i]               if i < len(websites) else ""
            results.append(_make_biz(name, phone, website=website, query=query))

    except Exception as e:
        print(f"    [Facebook] {e}")
    print(f"    [Facebook] '{query}' → {len(results)} עסקים")
    return results


# ════════════════════════════════════════════════════════════════
#  מקור 5: Google Search ישיר — fallback
# ════════════════════════════════════════════════════════════════
def scrape_google_search(query: str) -> list[dict]:
    """Google Search — מחלץ Knowledge Panel ו-Local Pack."""
    results = []
    url = f"https://www.google.com/search?q={quote(query)}&num=20&hl=he&gl=il"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        html = resp.text

        # מספרי טלפון ישראליים
        phones = list(dict.fromkeys(re.findall(r"0\d[\d\-]{7,9}", html)))

        # שמות עסקים מה-Knowledge Panel / Local Pack
        soup  = BeautifulSoup(html, "html.parser")
        names = []
        for el in soup.select("h3, [class*='name'], [class*='title']"):
            t = el.get_text(strip=True)
            if 3 < len(t) < 60 and not t.startswith("http"):
                names.append(t)

        # URLs שנראים כאתרי עסקים
        found_urls = re.findall(r'href="(https?://(?!google|youtube|facebook)[^"]{8,80})"', html)
        found_urls = [u for u in dict.fromkeys(found_urls) if ".co.il" in u or ".com" in u]

        for i, name in enumerate(names[:MAX_RESULTS_PER_QUERY]):
            phone   = _clean_phone(phones[i])   if i < len(phones)   else ""
            website = found_urls[i]             if i < len(found_urls) else ""
            results.append(_make_biz(name, phone, website=website, query=query))

    except Exception as e:
        print(f"    [Google Search] {e}")
    print(f"    [Google Search] '{query}' → {len(results)} עסקים")
    return results


# ════════════════════════════════════════════════════════════════
#  מקור 6: Wolt / 10bis — מסעדות ובתי קפה (ללא אתר בד"כ)
# ════════════════════════════════════════════════════════════════
def scrape_wolt(city: str) -> list[dict]:
    """שולף מסעדות מ-Wolt API — הרבה מהן ללא אתר עצמאי."""
    results = []
    try:
        url = f"https://restaurant-api.wolt.com/v1/pages/restaurants?city={quote(city)}&limit={MAX_RESULTS_PER_QUERY}"
        resp = requests.get(url, headers={"User-Agent": "Wolt/1.0"}, timeout=12)
        data = resp.json()
        for item in data.get("sections", [{}])[0].get("items", [])[:MAX_RESULTS_PER_QUERY]:
            venue = item.get("venue", {})
            name  = venue.get("name", "")
            phone = venue.get("phone", "")
            addr  = venue.get("address", "")
            if name:
                results.append(_make_biz(name, phone, address=addr,
                                         category="מסעדה", query=f"מסעדות {city}"))
    except Exception as e:
        print(f"    [Wolt] {e}")
    print(f"    [Wolt] {city} → {len(results)} מסעדות")
    return results


# ════════════════════════════════════════════════════════════════
#  העשרת נתונים מהאתר — מייל, רשתות חברתיות, עיר
# ════════════════════════════════════════════════════════════════
EMAIL_SKIP = ["example.com", "sentry.io", "googleapis", "w3.org", "schema.org",
              "wixpress.com", "squarespace.com", "shopify", "google.com"]


def enrich_from_website(url: str) -> dict:
    """
    שולף מהאתר: מייל, פייסבוק URL, אינסטגרם URL, עיר.
    מחזיר dict ריק אם נכשל.
    """
    result = {"email": "", "facebook_url": "", "instagram_url": "", "city": ""}
    if not url:
        return result
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        html = resp.text

        # ── מייל ──
        for em in re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html):
            if not any(s in em for s in EMAIL_SKIP):
                result["email"] = em.lower()
                break

        # ── פייסבוק ──
        for fb in re.findall(r'href=["\']?(https?://(?:www\.)?facebook\.com/[^"\'>\s?]{3,80})', html):
            if "/sharer" not in fb and "/share?" not in fb and "pages/create" not in fb:
                result["facebook_url"] = fb.rstrip("/")
                break

        # ── אינסטגרם ──
        for ig in re.findall(r'href=["\']?(https?://(?:www\.)?instagram\.com/[^"\'>\s?]{2,60})', html):
            if "/p/" not in ig and "accounts" not in ig:
                result["instagram_url"] = ig.rstrip("/")
                break

        # ── עיר (מ-schema.org) ──
        city_m = re.search(r'"addressLocality"\s*:\s*"([^"]{2,30})"', html)
        if city_m:
            result["city"] = city_m.group(1)

    except Exception:
        pass
    return result


def extract_email_from_website(url: str) -> str:
    return enrich_from_website(url).get("email", "")


# legacy — kept for compatibility
def _extract_email_old(url: str) -> str:
    if not url:
        return ""
    try:
        resp    = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=True)
        emails  = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", resp.text)
        for em in emails:
            if not any(s in em for s in EMAIL_SKIP):
                return em.lower()
    except Exception:
        pass
    return ""


# ════════════════════════════════════════════════════════════════
#  נקודת כניסה ראשית
# ════════════════════════════════════════════════════════════════
def scrape_businesses(query: str) -> list[dict]:
    """
    מפעיל את כל המקורות לפי זמינות ומחזיר רשימה מאוחדת ללא כפילויות.
    """
    all_results: list[dict] = []
    seen_names: set[str]    = set()

    def add_results(source_results: list[dict]):
        for biz in source_results:
            key = biz["name"].strip().lower()
            if key and key not in seen_names:
                seen_names.add(key)
                all_results.append(biz)

    # ── מקור 1: Google Maps (הכי טוב) ──
    if SERPAPI_KEY and SERPAPI_KEY != "YOUR_SERPAPI_KEY_HERE":
        add_results(scrape_google_maps(query))
        time.sleep(0.5)
    else:
        print("    [!] SERPAPI_KEY לא מוגדר — דולג על Google Maps")

    # ── מקור 2: דפי זהב ──
    add_results(scrape_dapei_zahav(query))
    time.sleep(0.5)

    # ── מקור 3: Google Search ──
    add_results(scrape_google_search(query))
    time.sleep(0.5)

    # ── מקור 4: Facebook (אם השאילתה כוללת קטגוריה ספציפית) ──
    add_results(scrape_facebook_places(query))
    time.sleep(0.5)

    # ── מקור 5: Wolt — רק אם שאילתה כוללת "מסעדה" / "קפה" / "אוכל" ──
    food_keywords = ["מסעד", "קפה", "אוכל", "פיצ", "בורגר", "סושי", "שווארמה"]
    if any(kw in query for kw in food_keywords):
        city = query.split()[-1]  # המילה האחרונה = עיר
        add_results(scrape_wolt(city))

    print(f"\n  ✅ סה\"כ '{query}': {len(all_results)} עסקים ייחודיים מכל המקורות")
    return all_results[:MAX_RESULTS_PER_QUERY * 3]  # מקסימום 3x מהכמות הרגילה
