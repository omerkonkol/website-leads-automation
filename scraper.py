"""
scraper.py — שליפת עסקים ממקורות מרובים (חינמי לגמרי).

מקורות:
  1. B144.co.il              — מאגר עסקים ישראלי מקיף, JSON מוטמע בדף
  2. דפי זהב (d.co.il)      — מאגר ישראלי, ללא API key
  3. Yad2 /b144              — בעלי מקצוע ונותני שירותים
  4. Google Maps / SerpApi   — אופציונלי, 100 חינם/חודש
  5. Google Search ישיר      — fallback (עובד חלקית)
  6. Google Search — Wix     — מחפש אתרי Wix ישנים (site:wixsite.com)
  7. Google Search — Old     — מחפש אתרים ישנים/נטושים
  8. data.gov.il             — רשם החברות (חברות חדשות)
  9. Facebook Pages          — דפי פייסבוק עסקיים ישראליים
 10. Zap.co.il               — עסקים עם ביקורות
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


def _make_biz(name, phone="", email="", website="", address="", city="",
              category="", query="", source="", **extra) -> dict:
    biz = {
        "name":         name.strip(),
        "phone":        _clean_phone(phone),
        "email":        email.strip().lower() if email else "",
        "website":      _clean_url(website),
        "address":      address.strip(),
        "city":         city.strip() if city else "",
        "category":     category.strip(),
        "search_query": query,
        "source":       source,
    }
    biz.update(extra)
    return biz


def _safe_request(url: str, timeout: int = 15, **kwargs) -> requests.Response | None:
    """HTTP GET עם טיפול בשגיאות ו-retry."""
    for attempt in range(2):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout, **kwargs)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                wait = min(2 ** attempt * 3, 10)
                print(f"    [Rate limit] ממתין {wait}s...")
                time.sleep(wait)
                continue
            return resp
        except requests.exceptions.Timeout:
            print(f"    [Timeout] {url[:60]}...")
        except Exception as e:
            print(f"    [Error] {url[:40]}: {e}")
        if attempt == 0:
            time.sleep(1)
    return None


# ════════════════════════════════════════════════════════════════
#  מקור 1: B144.co.il — המקור העיקרי (חינמי, JSON מוטמע)
# ════════════════════════════════════════════════════════════════
def scrape_b144(query: str) -> list[dict]:
    results = []
    seen = set()

    def _add(biz_list):
        for biz in biz_list:
            name = biz.get("Name") or ""
            if not name or len(name) < 3:
                continue
            if name in ("המלצות", "עסקים", "תחומים", "כתבות", "קופונים", "מחירונים", "חנויות",
                         "חיפושים", "חיפוש עסקים", "חיפוש אנשים", "חיפוש חנויות אונליין", "חיפוש מפות"):
                continue
            key = name.strip().lower()
            if key in seen:
                continue
            seen.add(key)

            area = str(biz.get("Area_Code", ""))
            phone_raw = str(biz.get("Phone", ""))
            phone = area + phone_raw.replace(area, "").replace("...", "").replace("-", "").strip()
            website = biz.get("Web") or ""
            city = biz.get("City") or ""
            street = biz.get("Street") or ""
            street_no = str(biz.get("Street_No") or "")
            address = f"{street} {street_no} {city}".strip()
            category = biz.get("CategoriesList") or biz.get("Cat_desc") or ""

            # ביקורות Google (אם קיים)
            reviews = biz.get("ReviewsCount") or biz.get("reviews_count")
            rating = biz.get("Rating") or biz.get("rating")

            extra = {}
            if reviews: extra["google_reviews"] = int(reviews)
            if rating:  extra["google_rating"] = float(rating)

            results.append(_make_biz(
                name=name, phone=phone, website=website,
                address=address, city=city, category=category,
                query=query, source="b144", **extra
            ))

    try:
        api_url = f"https://www.b144.co.il/api/search?query={quote(query)}"
        resp = _safe_request(api_url)
        if resp:
            json_match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(1))
                pp = data.get("props", {}).get("pageProps", {})
                _add(pp.get("searchObj", []))
                _add(pp.get("businessesToDisplay", []))

        if len(results) < 5:
            home_url = f"https://www.b144.co.il/?query={quote(query)}"
            resp2 = _safe_request(home_url)
            if resp2:
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
    results = []
    seen_names = set()
    url = f"https://www.d.co.il/SearchResults/?query={quote(query)}"
    try:
        resp = _safe_request(url)
        if not resp:
            return results
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select("li[data-card], .card-item, .business-card")[:MAX_RESULTS_PER_QUERY * 2]:
            name_el = card.select_one(".card-desc h3 a, .card-desc h3, h3 a")
            phone_el = card.select_one(".btn-phone-yellow, .phone-info, [href^='tel:']")
            addr_el = card.select_one(".navigation-map, .location-title, [class*='address']")

            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 3:
                continue
            key = name.strip().lower()
            if key in seen_names:
                continue
            seen_names.add(key)

            phone = ""
            if phone_el:
                phone = phone_el.get("href", "").replace("tel:", "") or phone_el.get_text(strip=True)
            address = addr_el.get_text(strip=True) if addr_el else ""

            results.append(_make_biz(name, phone, address=address, query=query, source="dapei_zahav"))

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
    results = []
    url = f"https://www.yad2.co.il/b144/search?text={quote(query)}"
    try:
        resp = _safe_request(url)
        if not resp:
            return results
        html = resp.text

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
        data = resp.json()
        for p in data.get("local_results", []):
            extra = {}
            if p.get("reviews"):   extra["google_reviews"] = int(p["reviews"])
            if p.get("rating"):    extra["google_rating"] = float(p["rating"])

            b = _make_biz(
                name=p.get("title", ""),
                phone=p.get("phone", ""),
                website=p.get("website", ""),
                address=p.get("address", ""),
                category=p.get("type", ""),
                query=query,
                source="google_maps",
                **extra,
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
    results = []
    url = f"https://www.google.com/search?q={quote(query)}&num=20&hl=he&gl=il"
    try:
        resp = _safe_request(url)
        if not resp:
            return results
        html = resp.text

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
#  מקור 6: חיפוש אתרי Wix ישנים — "site:wixsite.com" + קטגוריה
#  עסקים עם אתר Wix חינמי = מועמדים מצוינים לשדרוג
# ════════════════════════════════════════════════════════════════
def scrape_wix_sites(query: str) -> list[dict]:
    """מחפש אתרי Wix חינמיים בקטגוריה — עסקים שצריכים שדרוג."""
    results = []
    # חיפוש אתרי Wix חינמיים
    search_queries = [
        f'site:wixsite.com "{query}"',
        f'site:wix.com "{query}" ישראל',
    ]

    for sq in search_queries:
        url = f"https://www.google.com/search?q={quote(sq)}&num=15&hl=he&gl=il"
        resp = _safe_request(url)
        if not resp:
            continue
        html = resp.text
        if "detected unusual traffic" in html:
            break

        soup = BeautifulSoup(html, "html.parser")
        for el in soup.select("h3"):
            text = el.get_text(strip=True)
            if not text or len(text) < 3 or len(text) > 80:
                continue
            # מצא את ה-URL הקרוב
            parent_a = el.find_parent("a")
            wix_url = ""
            if parent_a and parent_a.get("href"):
                href = parent_a["href"]
                # Google wraps URLs
                url_match = re.search(r'https?://[^&"]+wix[^&"]*', href)
                if url_match:
                    wix_url = url_match.group(0)

            # חלץ שם עסק מהכותרת (הסר " | " ומילות Wix)
            name = re.sub(r"\s*\|.*$", "", text)
            name = re.sub(r"\s*[-–].*wix.*$", "", name, flags=re.IGNORECASE)
            name = name.strip()
            if len(name) < 3:
                continue

            # חלץ טלפון מה-snippet
            phones_in_page = re.findall(r"0\d[\d\-]{7,9}", html)

            results.append(_make_biz(
                name=name,
                website=wix_url,
                query=query,
                source="wix_search",
                category=query,
            ))

        time.sleep(1)  # נימוס כלפי Google

    print(f"    [Wix Search] '{query}' → {len(results)} עסקים עם Wix")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 7: חיפוש אתרים ישנים/נטושים
#  אתרים עם copyright ישן או טכנולוגיות ישנות = לידים חמים
# ════════════════════════════════════════════════════════════════
def scrape_old_sites(query: str) -> list[dict]:
    """מחפש אתרים ישנים (Flash, BusinessCatalyst, Copyright ישן)."""
    results = []
    search_queries = [
        f'"{query}" "© 2018" OR "© 2017" OR "© 2016" OR "© 2015" site:.co.il',
        f'"{query}" "בניית אתרים" OR "עיצוב אתר" site:.co.il inurl:home',
    ]

    for sq in search_queries:
        url = f"https://www.google.com/search?q={quote(sq)}&num=10&hl=he&gl=il"
        resp = _safe_request(url)
        if not resp:
            continue
        html = resp.text
        if "detected unusual traffic" in html:
            break

        # חלץ URLs ישירים
        found_urls = re.findall(
            r'href="(https?://(?!google|youtube|facebook|wikipedia|wix)[^"]{8,100}\.co\.il[^"]*)"',
            html
        )
        found_urls = list(dict.fromkeys(found_urls))

        soup = BeautifulSoup(html, "html.parser")
        names = [el.get_text(strip=True) for el in soup.select("h3") if 3 < len(el.get_text(strip=True)) < 60]

        for i, name in enumerate(names[:10]):
            website = found_urls[i] if i < len(found_urls) else ""
            results.append(_make_biz(
                name=name, website=website,
                query=query, source="old_site_search",
                category=query,
            ))

        time.sleep(1)

    print(f"    [Old Sites] '{query}' → {len(results)} אתרים ישנים")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 8: data.gov.il — רשם החברות (חברות חדשות ב-12 חודשים)
#  API ציבורי חינמי — https://data.gov.il
# ════════════════════════════════════════════════════════════════
def scrape_gov_companies(query: str) -> list[dict]:
    """
    מחפש חברות שנרשמו לאחרונה ברשם החברות הממשלתי.
    חברות חדשות = עדיין לא בנו אתר = ליד חם.
    """
    results = []
    try:
        # CKAN API of data.gov.il — company registry
        api_url = "https://data.gov.il/api/3/action/datastore_search"
        params = {
            "resource_id": "f004176c-b85f-4542-8901-7b3176f9a054",  # רשם החברות
            "q": query,
            "limit": MAX_RESULTS_PER_QUERY,
            "sort": "Company_Registration_Date desc",
        }
        resp = requests.get(api_url, params=params, timeout=20)
        if resp.status_code != 200:
            print(f"    [רשם חברות] HTTP {resp.status_code}")
            return results

        data = resp.json()
        records = data.get("result", {}).get("records", [])

        for rec in records:
            name = rec.get("Company_Name", "").strip()
            if not name or len(name) < 3:
                continue

            # סנן חברות שלא רלוונטיות (בע"מ, בינלאומי, השקעות...)
            skip_words = ["השקעות", "אחזקות", "נכסים", "ייעוץ", "ביטוח", "סחר בינלאומי"]
            if any(w in name for w in skip_words):
                continue

            city = rec.get("Company_City", "")
            reg_date = rec.get("Company_Registration_Date", "")

            results.append(_make_biz(
                name=name,
                city=city,
                query=query,
                source="gov_registry",
                category=query,
                registration_date=reg_date,
            ))

    except Exception as e:
        print(f"    [רשם חברות] שגיאה: {e}")

    print(f"    [רשם חברות] '{query}' → {len(results)} חברות חדשות")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 9: Facebook Pages — חיפוש דפי עסקים
# ════════════════════════════════════════════════════════════════
def scrape_facebook_pages(query: str) -> list[dict]:
    """
    מחפש דפי פייסבוק עסקיים דרך Google.
    עסקים שפעילים רק בפייסבוק = אין להם אתר = ליד.
    """
    results = []
    sq = f'site:facebook.com "{query}" ישראל -groups -events -marketplace'
    url = f"https://www.google.com/search?q={quote(sq)}&num=15&hl=he&gl=il"

    resp = _safe_request(url)
    if not resp:
        return results
    html = resp.text
    if "detected unusual traffic" in html:
        print("    [Facebook] Google חסם — דולג")
        return results

    soup = BeautifulSoup(html, "html.parser")
    for el in soup.select("h3"):
        text = el.get_text(strip=True)
        if not text or len(text) < 3:
            continue
        # סנן כותרות של Facebook עצמו
        if text.lower() in ("facebook", "log in", "meta"):
            continue

        # חלץ URL של דף הפייסבוק
        parent_a = el.find_parent("a")
        fb_url = ""
        if parent_a and parent_a.get("href"):
            fb_match = re.search(r'https?://(?:www\.)?facebook\.com/[^&"?]+', parent_a["href"])
            if fb_match:
                fb_url = fb_match.group(0)

        # חלץ שם עסק מהכותרת (הסר " | Facebook" וכו')
        name = re.sub(r"\s*[-|–].*(?:facebook|פייסבוק|meta).*$", "", text, flags=re.IGNORECASE)
        name = name.strip()
        if len(name) < 3:
            continue

        # חלץ טלפון מה-snippet
        phones = re.findall(r"0\d[\d\-]{7,9}", html)
        phone = _clean_phone(phones[0]) if phones else ""

        results.append(_make_biz(
            name=name,
            phone=phone,
            query=query,
            source="facebook",
            category=query,
            facebook_url=fb_url,
        ))

    print(f"    [Facebook] '{query}' → {len(results)} דפי עסקים")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 10: Zap.co.il — עסקים עם ביקורות
# ════════════════════════════════════════════════════════════════
def scrape_zap(query: str) -> list[dict]:
    """Zap.co.il — עסקים עם ביקורות ודירוגים."""
    results = []
    url = f"https://www.zap.co.il/search?keyword={quote(query)}"
    try:
        resp = _safe_request(url)
        if not resp:
            return results
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select(".SearchResult, .result-item, [class*='business']")[:MAX_RESULTS_PER_QUERY * 2]:
            name_el = card.select_one("h2, h3, .business-name, [class*='name']")
            phone_el = card.select_one("[href^='tel:'], .phone")

            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 3:
                continue

            phone = ""
            if phone_el:
                phone = phone_el.get("href", "").replace("tel:", "") or phone_el.get_text(strip=True)

            results.append(_make_biz(
                name=name, phone=phone,
                query=query, source="zap",
                category=query,
            ))

    except Exception as e:
        print(f"    [Zap] שגיאה: {e}")

    print(f"    [Zap] '{query}' → {len(results)} עסקים")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  העשרת נתונים מהאתר — מייל, רשתות חברתיות, עיר
# ════════════════════════════════════════════════════════════════
EMAIL_SKIP = ["example.com", "sentry.io", "googleapis", "w3.org", "schema.org",
              "wixpress.com", "squarespace.com", "shopify", "google.com"]


def enrich_from_website(url: str) -> dict:
    """שולף מהאתר: מייל, פייסבוק URL, אינסטגרם URL, לינקדאין, עיר."""
    result = {"email": "", "facebook_url": "", "instagram_url": "", "linkedin_url": "", "city": ""}
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

        for li in re.findall(r'href=["\']?(https?://(?:www\.)?linkedin\.com/(?:company|in)/[^"\'>\s?]{2,60})', html):
            result["linkedin_url"] = li.rstrip("/")
            break

        city_m = re.search(r'"addressLocality"\s*:\s*"([^"]{2,30})"', html)
        if city_m:
            result["city"] = city_m.group(1)

    except Exception:
        pass
    return result


def extract_email_from_website(url: str) -> str:
    return enrich_from_website(url).get("email", "")


def find_website_and_email(name: str, city: str = "") -> dict:
    """
    מחפש ב-Google את אתר העסק + מייל.
    משמש לעסקים שנמצאו בספרייה בלי אתר/מייל.
    """
    result = {"website": "", "email": "", "facebook_url": ""}

    query = f'"{name}"'
    if city:
        query += f" {city}"
    query += " site:.co.il OR site:.com"

    url = f"https://www.google.com/search?q={quote(query)}&num=5&hl=he&gl=il"
    try:
        resp = _safe_request(url)
        if not resp:
            return result
        html = resp.text

        if "detected unusual traffic" in html:
            return result

        # חלץ URLs
        found_urls = re.findall(
            r'href="(https?://(?!google|youtube|facebook|wikipedia|wix)[^"]{8,100})"',
            html
        )
        found_urls = list(dict.fromkeys(found_urls))

        # חפש אתר שנראה רלוונטי (עם שם דומיין קצר, .co.il/.com)
        for u in found_urls[:5]:
            if ".co.il" in u or (".com" in u and "google" not in u):
                result["website"] = u
                break

        # חפש מייל ב-snippet
        emails = re.findall(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", html)
        for em in emails:
            if not any(s in em for s in EMAIL_SKIP):
                result["email"] = em.lower()
                break

        # חפש דף פייסבוק
        fb_urls = re.findall(r'https?://(?:www\.)?facebook\.com/[a-zA-Z0-9.\-]{3,60}', html)
        if fb_urls:
            result["facebook_url"] = fb_urls[0]

        # אם מצאנו אתר אבל לא מייל — נסה לשלוף מהאתר עצמו
        if result["website"] and not result["email"]:
            enriched = enrich_from_website(result["website"])
            if enriched.get("email"):
                result["email"] = enriched["email"]
            if enriched.get("facebook_url") and not result["facebook_url"]:
                result["facebook_url"] = enriched["facebook_url"]

    except Exception:
        pass

    return result


# ════════════════════════════════════════════════════════════════
#  Helper: חיפוש JSON מקונן (fallback ל-Yad2)
# ════════════════════════════════════════════════════════════════
def _find_businesses_in_json(data, depth=0) -> list:
    """חיפוש רקורסיבי של רשימות עסקים ב-JSON מקונן."""
    if depth > 5:
        return []
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict) and any(k in data[0] for k in ("name", "Name", "businessName", "Phone")):
            return data
    if isinstance(data, dict):
        for v in data.values():
            found = _find_businesses_in_json(v, depth + 1)
            if found:
                return found
    return []


# ════════════════════════════════════════════════════════════════
#  נקודת כניסה ראשית
# ════════════════════════════════════════════════════════════════
def scrape_businesses(query: str, sources: list[str] | None = None) -> list[dict]:
    """
    מפעיל את כל המקורות לפי זמינות ומחזיר רשימה מאוחדת ללא כפילויות.
    כל המקורות חינמיים לגמרי (חוץ מ-SerpApi שאופציונלי).

    sources: רשימת מקורות ספציפיים להפעיל. None = הכל.
    אפשרויות: "b144", "dapei_zahav", "yad2", "google_maps", "google_search",
               "wix_search", "old_sites", "gov_registry", "facebook", "zap"
    """
    all_results: list[dict] = []
    seen_names: set[str]    = set()

    def add_results(source_results: list[dict]):
        for biz in source_results:
            key = biz["name"].strip().lower()
            if key and key not in seen_names:
                seen_names.add(key)
                all_results.append(biz)

    def should_run(source_name: str) -> bool:
        return sources is None or source_name in sources

    # ── מקורות עיקריים (חינמיים, אמינים) ──
    if should_run("b144"):
        add_results(scrape_b144(query))
        time.sleep(0.5)

    if should_run("dapei_zahav"):
        add_results(scrape_dapei_zahav(query))
        time.sleep(0.5)

    if should_run("yad2"):
        add_results(scrape_yad2(query))
        time.sleep(0.5)

    # ── Google Maps — רק אם יש SerpApi key ──
    if should_run("google_maps") and SERPAPI_KEY and SERPAPI_KEY != "YOUR_SERPAPI_KEY_HERE":
        add_results(scrape_google_maps(query))
        time.sleep(0.5)
    elif should_run("google_maps"):
        print("    [Google Maps] SERPAPI_KEY לא מוגדר — דולג (אופציונלי)")

    if should_run("google_search"):
        add_results(scrape_google_search(query))
        time.sleep(1)

    # ── מקורות חדשים — מאתרים לידים ייחודיים ──
    if should_run("wix_search"):
        add_results(scrape_wix_sites(query))
        time.sleep(1)

    if should_run("old_sites"):
        add_results(scrape_old_sites(query))
        time.sleep(1)

    if should_run("gov_registry"):
        add_results(scrape_gov_companies(query))
        time.sleep(0.5)

    if should_run("facebook"):
        add_results(scrape_facebook_pages(query))
        time.sleep(1)

    if should_run("zap"):
        add_results(scrape_zap(query))
        time.sleep(0.5)

    print(f"\n  ✅ סה\"כ '{query}': {len(all_results)} עסקים ייחודיים מכל המקורות")
    return all_results[:MAX_RESULTS_PER_QUERY * 5]
