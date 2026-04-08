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
 11. Midrag.co.il             — מדרג, אתר חוות דעת ודירוגים לבעלי מקצוע
 12. Easy.co.il              — מדריך עסקים ישראלי גדול (JSON-LD + HTML)
 13. iGal.co.il              — מדריך עסקים ונותני שירותים
 14. Freesearch.co.il        — חיפוש חופשי, מדריך עסקים חינמי
 15. Google Directories      — חיפוש מאוחד ב-9 מדריכי עסקים ישראליים
 16. 2All.co.il              — מדריך עסקים קטנים ובינוניים
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
    # מספר ישראלי תקין: 9-10 ספרות
    if len(digits) == 10 and digits.startswith("0"):
        return digits
    if len(digits) == 9 and not digits.startswith("0"):
        return "0" + digits
    # מספר קצר מדי = חלקי / לא תקין — פוסל
    if len(digits) < 9:
        return ""
    return digits if len(digits) <= 11 else ""


def _clean_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    if not url.startswith("http"):
        url = "https://" + url
    return url


_ISRAELI_CITIES = (
    "תל אביב|Tel Aviv|ירושלים|Jerusalem|חיפה|Haifa|באר שבע|ראשון לציון|"
    "פתח תקווה|אשדוד|נתניה|חולון|בני ברק|רמת גן|אשקלון|הרצליה|כפר סבא|"
    "בת ים|רחובות|מודיעין|נצרת|עפולה|טבריה|אילת|רעננה|הוד השרון|גבעתיים|"
    "כרמיאל|עכו|נהריה|צפת|רמלה|לוד|נס ציונה|יבנה|גבעת שמואל|"
    "Yafo|Rishon|Petah Tikva|Netanya|Ashdod"
)


def _extract_city(address: str, query: str = "") -> str:
    """חילוץ עיר מכתובת או שאילתת חיפוש."""
    for text in [address, query]:
        if not text:
            continue
        m = re.search(f"({_ISRAELI_CITIES})", text, re.IGNORECASE)
        if m:
            return m.group()
    return ""


def _make_biz(name, phone="", email="", website="", address="", city="",
              category="", query="", source="", **extra) -> dict:
    clean_city = city.strip() if city else ""
    # Auto-extract city from address or query if missing
    if not clean_city:
        clean_city = _extract_city(address, query)
    biz = {
        "name":         name.strip(),
        "phone":        _clean_phone(phone),
        "email":        email.strip().lower() if email else "",
        "website":      _clean_url(website),
        "address":      address.strip(),
        "city":         clean_city,
        "category":     category.strip(),
        "search_query": query,
        "has_website":  1 if website else 0,
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
        "gl":      "il",
        "type":    "search",
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

            # תמונות, תיאור, שעות, מחיר — ישירות מ-SerpApi
            thumb = p.get("thumbnail")
            if thumb:
                extra["logo_url"] = thumb
            photos = p.get("photos")
            if photos:
                extra["photos"] = json.dumps(
                    [ph.get("image") or ph.get("thumbnail", "") for ph in photos[:10]]
                )
            desc = p.get("description") or p.get("snippet") or ""
            if desc:
                extra["description"] = desc
            hours = p.get("operating_hours") or p.get("hours")
            if hours:
                extra["opening_hours"] = json.dumps(hours, ensure_ascii=False)
            price = p.get("price")
            if price:
                extra["price_range"] = price
            ptype = p.get("type") or p.get("types")
            if ptype:
                if isinstance(ptype, list):
                    extra["services"] = json.dumps(ptype, ensure_ascii=False)
                else:
                    extra["services"] = json.dumps([ptype], ensure_ascii=False)

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
#  מקור 9: Facebook Pages — חיפוש דפי עסקים (משופר)
# ════════════════════════════════════════════════════════════════

def _extract_fb_page_data(fb_url: str) -> dict:
    """
    מנסה לשלוף מידע בסיסי מדף פייסבוק ישירות (ללא API).
    מחזיר: website, phone, followers, has_website
    """
    out = {"fb_website": "", "fb_phone": "", "fb_followers": 0, "fb_has_website": False}
    if not fb_url or "facebook.com" not in fb_url:
        return out
    try:
        resp = _safe_request(fb_url, timeout=10)
        if not resp:
            return out
        html = resp.text

        # אתר מוטמע ב-JSON של הדף
        for pat in [r'"website"\s*:\s*"(https?://[^"]{5,200})"',
                     r'"WebPage"\s*[^}]*"url"\s*:\s*"(https?://(?!.*facebook)[^"]{5,200})"']:
            m = re.search(pat, html)
            if m:
                site = m.group(1)
                if "facebook" not in site and "instagram" not in site:
                    out["fb_website"] = site
                    out["fb_has_website"] = True
                    break

        # כמות עוקבים
        for pat in [r'"fan_count"\s*:\s*(\d+)', r'"follower_count"\s*:\s*(\d+)',
                     r'([\d,]+)\s*(?:עוקבים|followers|likes|אוהדים)']:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                try:
                    out["fb_followers"] = int(m.group(1).replace(",", ""))
                    break
                except ValueError:
                    pass

        # טלפון
        for pat in [r'"phone"\s*:\s*"([^"]{7,20})"',
                     r'(?:tel:|phone:|טלפון:?)\s*(0\d[\d\-]{7,9})']:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                cleaned = _clean_phone(m.group(1))
                if cleaned:
                    out["fb_phone"] = cleaned
                    break

    except Exception:
        pass
    return out


def scrape_facebook_pages(query: str) -> list[dict]:
    """
    מחפש דפי פייסבוק עסקיים דרך Google (3 תבניות שונות).
    מנתח snippets כדי לזהות:
      • אם יש לעסק אתר (fb_snippet_has_website)
      • טלפון, עוקבים מה-snippet
    עסקים שפעילים רק בפייסבוק = אין להם אתר = ליד חם.
    """
    results: list[dict] = []
    seen_names: set[str] = set()

    # 3 תבניות dork שונות ← יותר כיסוי
    dork_patterns = [
        f'site:facebook.com "{query}" ישראל -groups -events -marketplace',
        f'site:facebook.com/pages/ {query} ישראל',
        f'site:facebook.com {query} ישראל "התקשרו" OR "טלפון" OR "לפרטים"',
    ]

    for sq in dork_patterns:
        if len(results) >= MAX_RESULTS_PER_QUERY:
            break

        url = f"https://www.google.com/search?q={quote(sq)}&num=15&hl=he&gl=il"
        resp = _safe_request(url)
        if not resp:
            continue
        html = resp.text
        if "detected unusual traffic" in html:
            print("    [Facebook] Google חסם — דולג")
            break

        soup = BeautifulSoup(html, "html.parser")

        # נסה לחפש בלוקי תוצאות
        result_blocks = soup.select("div.g") or soup.select("div[data-hveid]") or []
        if not result_blocks:
            # fallback: רק כותרות h3
            result_blocks = [el.find_parent("div") or el for el in soup.select("h3")]

        for block in result_blocks:
            if not block:
                continue

            h3 = block.find("h3")
            if not h3:
                continue
            text = h3.get_text(strip=True)
            if not text or len(text) < 3:
                continue
            if text.lower() in ("facebook", "log in", "meta", "log into facebook"):
                continue

            # חלץ URL של דף הפייסבוק
            a_tag = block.find("a", href=True) or h3.find_parent("a")
            fb_url = ""
            if a_tag:
                href = a_tag.get("href", "")
                fb_match = re.search(r'https?://(?:www\.)?facebook\.com/(?!groups|events|marketplace|login|sharer)[^&"?]+', href)
                if fb_match:
                    fb_url = fb_match.group(0).rstrip("/")

            # נסה לחלץ שם עסק מהכותרת
            name = re.sub(r"\s*[-|–|·].*(?:facebook|פייסבוק|meta).*$", "", text, flags=re.IGNORECASE)
            name = re.sub(r"\s*\|\s*פייסבוק$", "", name, flags=re.IGNORECASE)
            name = name.strip()
            if len(name) < 3:
                continue

            name_key = name.lower()
            if name_key in seen_names:
                continue
            seen_names.add(name_key)

            # ניתוח ה-snippet
            snippet_el = (
                block.select_one(".VwiC3b") or
                block.select_one("span[data-sncf]") or
                block.select_one(".lEBKkf") or
                block.select_one("div[style*='webkit-line-clamp']")
            )
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

            # זיהוי: האם ה-snippet מזכיר אתר? (= יש להם אתר)
            has_website_signal = bool(re.search(
                r'(?:website|אתר|www\.|\.co\.il|\.com[/\s])',
                snippet, re.IGNORECASE
            ))

            # חלץ טלפון מה-snippet
            phones_found = re.findall(r"0\d[\d\-]{7,9}", snippet)
            phone = _clean_phone(phones_found[0]) if phones_found else ""

            # חלץ עוקבים מה-snippet (לפעמים Google מציג "X עוקבים")
            fb_followers = 0
            followers_m = re.search(
                r'([\d,]+)\s*(?:עוקבים|followers|likes|אוהדים|אנשים אוהבים)',
                snippet, re.IGNORECASE
            )
            if followers_m:
                try:
                    fb_followers = int(followers_m.group(1).replace(",", ""))
                except ValueError:
                    pass

            biz = _make_biz(
                name=name,
                phone=phone,
                query=query,
                source="facebook",
                category=query,
                facebook_url=fb_url,
            )
            biz["fb_snippet_has_website"] = has_website_signal
            biz["fb_followers"] = fb_followers
            results.append(biz)

        time.sleep(1.5)  # עיכוב בין dorks למניעת חסימה

    print(f"    [Facebook] '{query}' → {len(results)} דפי עסקים")
    return results[:MAX_RESULTS_PER_QUERY]


def scrape_facebook_no_website(category: str, city: str) -> list[dict]:
    """
    חיפוש ממוקד לעסקי פייסבוק ללא אתר — הלידים הכי חמים.
    מחפש עסקים בפייסבוק שה-snippet שלהם לא מזכיר אתר.
    """
    query = f"{category} {city}"
    all_results = scrape_facebook_pages(query)

    # מחזיר קודם את אלה שה-snippet שלהם לא מזכיר אתר
    no_website = [b for b in all_results if not b.get("fb_snippet_has_website")]
    with_website = [b for b in all_results if b.get("fb_snippet_has_website")]
    return no_website + with_website


# ════════════════════════════════════════════════════════════════
#  מקור 11: Midrag.co.il — מדרג, אתר חוות דעת ודירוגים לבעלי מקצוע
# ════════════════════════════════════════════════════════════════
# מיפוי קטגוריות לקטגוריות מדרג (sectorId)
_MIDRAG_SECTORS = {
    "הובלות": 1, "שיפוצים": 11, "שיפוצניק": 11, "חשמלאי": 14,
    "אינסטלטור": 15, "שרברב": 15, "מיזוג אוויר": 16, "צביעה": 17,
    "ריצוף": 18, "אלומיניום": 19, "מנעולן": 20, "גינון": 21, "גנן": 21,
    "הדברה": 22, "ניקיון": 23, "מוסך": 24, "רכב": 24, "גרירה": 25,
    "עורך דין": 26, "רואה חשבון": 27, "ביטוח": 28, "אדריכל": 29,
    "מעצב פנים": 30, "צלם": 31, "צילום": 31, "הפקות": 32, "דיג'יי": 33,
    "קייטרינג": 34, "אולם אירועים": 35, "מוזיקה": 36, "עיצוב שיער": 37,
    "מספרה": 37, "ספר": 37, "קוסמטיקה": 38, "טיפוח": 38,
    "מורה נהיגה": 39, "חשמל": 14, "ריהוט": 40, "מטבחים": 41,
}


def scrape_midrag(query: str) -> list[dict]:
    """
    Midrag.co.il — אתר מדרג, מאגר בעלי מקצוע עם חוות דעת ודירוגים.
    שולף שמות עסקים, דירוגים, מספר ביקורות, קטגוריה ואזור.
    """
    results = []
    seen = set()

    # ── שלב 1: מצא sectorId מתאים לשאילתה ──
    sector_id = None
    query_lower = query.strip()
    for keyword, sid in _MIDRAG_SECTORS.items():
        if keyword in query_lower:
            sector_id = sid
            break

    # ── שלב 2: שלוף עסקים מדף הסקטור ──
    urls_to_try = []
    if sector_id:
        urls_to_try.append(f"https://www.midrag.co.il/Content/SectorPortal/{sector_id}")
    # תמיד ננסה גם חיפוש חופשי
    urls_to_try.append(f"https://www.midrag.co.il/Search/InSector?ntla={quote(query)}")

    sp_ids = []  # (spId, rating, reviews)
    for page_url in urls_to_try:
        try:
            resp = _safe_request(page_url)
            if not resp:
                continue
            html = resp.text

            # שלוף קישורים לדפי עסקים: /SpCard/Sp/{id}?...
            # HTML encodes & as &amp; so we handle both
            cleaned_html = html.replace("&amp;", "&")
            for m in re.finditer(
                r'/SpCard/Sp/(\d+)\?([^"\'>\s]+)', cleaned_html
            ):
                sp_id = m.group(1)
                params = m.group(2)
                if sp_id not in {s[0] for s in sp_ids}:
                    sp_ids.append((sp_id, params))

            # שלוף דירוגים מהדף (מופיעים כטקסט ליד הקישורים)
            # Pattern: 9.66 | 2,695 חוות דעת
        except Exception as e:
            print(f"    [מדרג] שגיאה בשליפת רשימה: {e}")

    if not sp_ids:
        print(f"    [מדרג] '{query}' → 0 עסקים (לא נמצא סקטור)")
        return results

    # ── שלב 3: שלוף פרטים מכל דף עסק (עד 15 עסקים) ──
    for sp_id, params in sp_ids[:15]:
        try:
            sp_url = f"https://www.midrag.co.il/SpCard/Sp/{sp_id}?{params}"
            resp = _safe_request(sp_url, timeout=10)
            if not resp or resp.status_code != 200:
                continue
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # שם העסק — title tag (אמין ביותר, פורמט: "שם - תיאור | מדרג")
            name = ""
            title_tag = soup.select_one("title")
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                # "עמרן - שיפוצניק מומלץ באזור חיפה | ..."
                name = title_text.split("-")[0].split("|")[0].strip()

            # fallback: breadcrumbs (שם בסוף: "חיפה > שיפוצניק מומלץ - עמרן")
            if not name or len(name) < 2 or "חוות דעת" in name or "מדרג" in name:
                breadcrumb = soup.select_one(".breadcrumb, [class*='breadcrumb']")
                if breadcrumb:
                    crumb_text = breadcrumb.get_text(" > ", strip=True)
                    parts = [p.strip() for p in crumb_text.split(">")]
                    if parts:
                        last = parts[-1].strip()
                        # "שיפוצניק מומלץ - עמרן" → "עמרן"
                        if " - " in last:
                            name = last.split(" - ")[-1].strip()
                        elif len(last) >= 2:
                            name = last

            # fallback: h1 (רק אם לא מכיל "חוות דעת")
            if not name or len(name) < 2 or "חוות דעת" in name:
                h1 = soup.select_one("h1")
                if h1:
                    h1_text = h1.get_text(strip=True)
                    if "חוות דעת" not in h1_text and len(h1_text) >= 2:
                        name = h1_text

            if not name or len(name) < 2 or name.lower() in seen:
                continue
            # Skip generic/navigation names
            if any(skip in name for skip in ("מדרג", "חוות דעת", "דף הבית", "חיפוש")):
                continue
            seen.add(name.lower())

            # דירוג וביקורות
            extra = {}
            rating_match = re.search(r'(\d+\.\d+)\s*/\s*10', html)
            if not rating_match:
                rating_match = re.search(r'class="[^"]*rank[^"]*"[^>]*>\s*(\d+\.?\d*)', html, re.IGNORECASE)
            if rating_match:
                extra["google_rating"] = float(rating_match.group(1))

            reviews_match = re.search(r'(\d[\d,]*)\s*חוות דעת', html)
            if reviews_match:
                extra["google_reviews"] = int(reviews_match.group(1).replace(",", ""))

            # אזור/עיר
            city = ""
            area_match = re.search(
                r'(תל[- ]?אביב|ירושלים|חיפה|באר[- ]?שבע|ראשון לציון|פתח תקווה|'
                r'אשדוד|נתניה|חולון|בני ברק|רמת גן|אשקלון|הרצליה|כפר סבא|'
                r'בת ים|רחובות|מודיעין|נצרת|עפולה|טבריה|אילת|רמלה|לוד|'
                r'רעננה|הוד השרון|גבעתיים|כרמיאל|עכו|נהריה|צפת|דימונה|'
                r'קריית \S+|נס ציונה|יבנה|אור יהודה|גבעת שמואל)',
                html
            )
            if area_match:
                city = area_match.group()

            # קטגוריה מ-breadcrumbs
            category = query
            breadcrumb = soup.select_one(".breadcrumb, [class*='breadcrumb']")
            if breadcrumb:
                crumbs = breadcrumb.get_text(" > ", strip=True)
                parts = [p.strip() for p in crumbs.split(">") if len(p.strip()) > 2]
                if len(parts) >= 2:
                    category = parts[-1] if parts[-1] != name else (parts[-2] if len(parts) > 2 else query)

            results.append(_make_biz(
                name=name, city=city, category=category,
                query=query, source="midrag", **extra
            ))
            time.sleep(0.3)  # נימוס כלפי השרת

        except Exception as e:
            print(f"    [מדרג] שגיאה בדף עסק {sp_id}: {e}")
            continue

    print(f"    [מדרג] '{query}' → {len(results)} עסקים")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 12: Easy.co.il — מדריך עסקים ישראלי גדול (מספור המשכי)
# ════════════════════════════════════════════════════════════════
def scrape_easy(query: str) -> list[dict]:
    """Easy.co.il — מדריך עסקים עם טלפון, כתובת וקטגוריה."""
    results = []
    seen = set()
    url = f"https://www.easy.co.il/s/{quote(query)}"
    try:
        resp = _safe_request(url)
        if not resp:
            return results
        soup = BeautifulSoup(resp.text, "html.parser")

        # Easy uses JSON-LD structured data for businesses
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                ld = json.loads(script.string or "")
                items = ld if isinstance(ld, list) else [ld]
                for item in items:
                    if item.get("@type") not in ("LocalBusiness", "Organization", "Store",
                                                   "Restaurant", "HealthAndBeautyBusiness",
                                                   "ProfessionalService", "HomeAndConstructionBusiness"):
                        continue
                    name = item.get("name", "")
                    if not name or len(name) < 3 or name.lower() in seen:
                        continue
                    seen.add(name.lower())
                    addr_obj = item.get("address", {})
                    address = addr_obj.get("streetAddress", "") if isinstance(addr_obj, dict) else ""
                    city = addr_obj.get("addressLocality", "") if isinstance(addr_obj, dict) else ""
                    phone = item.get("telephone", "")
                    website = item.get("url", "")
                    results.append(_make_biz(
                        name=name, phone=phone, website=website,
                        address=address, city=city, category=query,
                        query=query, source="easy",
                    ))
            except (json.JSONDecodeError, TypeError):
                continue

        # Fallback: parse HTML cards
        if not results:
            for card in soup.select(".biz-card, .business-item, .listing-item, [class*='result']")[:MAX_RESULTS_PER_QUERY * 2]:
                name_el = card.select_one("h2, h3, .biz-name, [class*='name'] a, [class*='title'] a")
                phone_el = card.select_one("[href^='tel:'], .phone, [class*='phone']")
                addr_el = card.select_one(".address, [class*='address'], [class*='location']")

                name = name_el.get_text(strip=True) if name_el else ""
                if not name or len(name) < 3 or name.lower() in seen:
                    continue
                seen.add(name.lower())

                phone = ""
                if phone_el:
                    phone = phone_el.get("href", "").replace("tel:", "") or phone_el.get_text(strip=True)
                address = addr_el.get_text(strip=True) if addr_el else ""

                # Try to get website from link
                website = ""
                link_el = card.select_one("a[href*='redirect'], a[href*='website'], a.website-link")
                if link_el:
                    website = link_el.get("href", "")

                results.append(_make_biz(
                    name=name, phone=phone, website=website,
                    address=address, category=query,
                    query=query, source="easy",
                ))

        # Second fallback: regex phone extraction
        if results and not any(r["phone"] for r in results):
            phones = re.findall(r"0[2-9]\d[\d\-]{6,8}", resp.text)
            for i, r in enumerate(results):
                if i < len(phones) and not r["phone"]:
                    r["phone"] = _clean_phone(phones[i])

    except Exception as e:
        print(f"    [Easy] שגיאה: {e}")

    print(f"    [Easy] '{query}' → {len(results)} עסקים")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 12: iGal.co.il — מדריך עסקים ונותני שירותים
# ════════════════════════════════════════════════════════════════
def scrape_igal(query: str) -> list[dict]:
    """iGal.co.il — ספריית עסקים ישראלית עם פרטי קשר."""
    results = []
    seen = set()
    url = f"https://www.igal.co.il/search.php?q={quote(query)}"
    try:
        resp = _safe_request(url)
        if not resp:
            return results
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select(".result, .business, .listing, [class*='card'], [class*='item']")[:MAX_RESULTS_PER_QUERY * 2]:
            name_el = card.select_one("h2, h3, h4, .name, [class*='name'] a, [class*='title']")
            phone_el = card.select_one("[href^='tel:'], .phone, [class*='phone']")
            addr_el = card.select_one(".address, [class*='address'], [class*='city']")
            web_el = card.select_one("a[href*='http']:not([href*='igal.co.il']), a.website")

            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 3 or name.lower() in seen:
                continue
            seen.add(name.lower())

            phone = ""
            if phone_el:
                phone = phone_el.get("href", "").replace("tel:", "") or phone_el.get_text(strip=True)
            address = addr_el.get_text(strip=True) if addr_el else ""
            website = web_el.get("href", "") if web_el else ""

            results.append(_make_biz(
                name=name, phone=phone, website=website,
                address=address, category=query,
                query=query, source="igal",
            ))

        # Fallback: general text mining
        if not results:
            # Look for any structured listing patterns
            for h_tag in soup.select("h2, h3, h4")[:MAX_RESULTS_PER_QUERY * 2]:
                name = h_tag.get_text(strip=True)
                if not name or len(name) < 3 or len(name) > 80 or name.lower() in seen:
                    continue
                # Skip navigation/header elements
                if h_tag.find_parent(["nav", "header", "footer"]):
                    continue
                seen.add(name.lower())
                results.append(_make_biz(name=name, query=query, source="igal", category=query))

            phones = re.findall(r"0[2-9]\d[\d\-]{6,8}", resp.text)
            for i, r in enumerate(results):
                if i < len(phones) and not r["phone"]:
                    r["phone"] = _clean_phone(phones[i])

    except Exception as e:
        print(f"    [iGal] שגיאה: {e}")

    print(f"    [iGal] '{query}' → {len(results)} עסקים")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 13: Freesearch.co.il — חיפוש חופשי, מדריך עסקים
# ════════════════════════════════════════════════════════════════
def scrape_freesearch(query: str) -> list[dict]:
    """Freesearch.co.il — מדריך עסקים חינמי עם טלפון וכתובת."""
    results = []
    seen = set()
    url = f"https://www.freesearch.co.il/search?q={quote(query)}"
    try:
        resp = _safe_request(url)
        if not resp:
            return results
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select(".result-item, .business, .listing, [class*='result'], [class*='card']")[:MAX_RESULTS_PER_QUERY * 2]:
            name_el = card.select_one("h2, h3, h4, .name, [class*='name'], [class*='title']")
            phone_el = card.select_one("[href^='tel:'], .phone, [class*='phone']")
            addr_el = card.select_one(".address, [class*='address']")

            name = name_el.get_text(strip=True) if name_el else ""
            if not name or len(name) < 3 or name.lower() in seen:
                continue
            seen.add(name.lower())

            phone = ""
            if phone_el:
                phone = phone_el.get("href", "").replace("tel:", "") or phone_el.get_text(strip=True)
            address = addr_el.get_text(strip=True) if addr_el else ""

            results.append(_make_biz(
                name=name, phone=phone, address=address,
                category=query, query=query, source="freesearch",
            ))

        # Fallback: mine phones from text
        if results and not any(r["phone"] for r in results):
            phones = re.findall(r"0[2-9]\d[\d\-]{6,8}", resp.text)
            for i, r in enumerate(results):
                if i < len(phones) and not r["phone"]:
                    r["phone"] = _clean_phone(phones[i])

    except Exception as e:
        print(f"    [Freesearch] שגיאה: {e}")

    print(f"    [Freesearch] '{query}' → {len(results)} עסקים")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 14: Google Search — מדריכי עסקים (מאגד תוצאות ממדרגים)
# ════════════════════════════════════════════════════════════════
def scrape_directories_google(query: str) -> list[dict]:
    """
    חיפוש Google ממוקד למדריכי עסקים ישראליים.
    מחפש תוצאות מאתרי מדרג שונים ושולף שמות + טלפונים.
    """
    results = []
    seen = set()

    # Target multiple directory sites in a single Google search
    directory_sites = [
        "easy.co.il", "igal.co.il", "freesearch.co.il",
        "yp.co.il", "2all.co.il", "bizportal.co.il",
        "infomed.co.il", "hamefaked.co.il", "call2all.co.il", "midrag.co.il",
    ]
    site_query = " OR ".join(f"site:{s}" for s in directory_sites)
    search_url = f"https://www.google.com/search?q={quote(query)}+({quote(site_query)})&num=30&hl=he&gl=il"

    try:
        resp = _safe_request(search_url)
        if not resp:
            return results
        html = resp.text

        if "detected unusual traffic" in html:
            print("    [Directories Google] חסום — rate limit")
            return results

        soup = BeautifulSoup(html, "html.parser")

        for g in soup.select(".g, [data-sokoban-container]")[:MAX_RESULTS_PER_QUERY * 2]:
            title_el = g.select_one("h3")
            snippet_el = g.select_one(".VwiC3b, .IsZvec, [data-content-feature]")
            link_el = g.select_one("a[href^='http']")

            name = title_el.get_text(strip=True) if title_el else ""
            # Clean directory prefixes from names
            for prefix in ("מידע על ", "עסקים - ", "חיפוש: "):
                name = name.removeprefix(prefix)
            # Remove trailing site names
            name = re.sub(r'\s*[-–|]\s*(easy|igal|freesearch|bizportal|2all|yp).*$', '', name, flags=re.IGNORECASE)

            if not name or len(name) < 3 or len(name) > 80 or name.lower() in seen:
                continue
            # Skip obvious non-business results
            if any(skip in name for skip in ("חיפוש", "מדריך", "תוצאות", "רשימת", "דף הבית")):
                continue
            seen.add(name.lower())

            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

            # Extract phone from snippet
            phone_match = re.search(r"0[2-9]\d[\d\-]{6,8}", snippet)
            phone = _clean_phone(phone_match.group()) if phone_match else ""

            # Extract city from snippet (common Israeli cities)
            city = ""
            city_match = re.search(
                r"(תל[- ]?אביב|ירושלים|חיפה|באר[- ]?שבע|ראשון לציון|פתח תקווה|"
                r"אשדוד|נתניה|חולון|בני ברק|רמת גן|אשקלון|הרצליה|כפר סבא|"
                r"בת ים|רחובות|מודיעין|נצרת|עפולה|טבריה|אילת|קריית|רמלה|לוד|"
                r"רעננה|הוד השרון|גבעתיים|כרמיאל|עכו|נהריה|צפת|דימונה)",
                snippet
            )
            if city_match:
                city = city_match.group()

            # Get source URL for reference
            source_url = link_el.get("href", "") if link_el else ""

            results.append(_make_biz(
                name=name, phone=phone, city=city,
                category=query, query=query,
                source="directory_search",
            ))

    except Exception as e:
        print(f"    [Directories Google] שגיאה: {e}")

    print(f"    [Directories Google] '{query}' → {len(results)} עסקים")
    return results[:MAX_RESULTS_PER_QUERY]


# ════════════════════════════════════════════════════════════════
#  מקור 15: WinWin / 2All — מדריכי עסקים קטנים
# ════════════════════════════════════════════════════════════════
def scrape_2all(query: str) -> list[dict]:
    """2All.co.il — מדריך עסקים קטנים ובינוניים."""
    results = []
    seen = set()
    url = f"https://www.2all.co.il/web/Sites/search.asp?q={quote(query)}"
    try:
        resp = _safe_request(url)
        if not resp:
            return results
        soup = BeautifulSoup(resp.text, "html.parser")

        for card in soup.select("table tr, .site-item, .result, [class*='listing']")[:MAX_RESULTS_PER_QUERY * 3]:
            # 2all uses table-based layouts
            links = card.select("a[href]")
            name = ""
            website = ""
            for link in links:
                href = link.get("href", "")
                text = link.get_text(strip=True)
                if text and len(text) >= 3 and "2all.co.il" not in href:
                    if href.startswith("http") and "2all" not in href:
                        website = href
                    if not name and len(text) < 80:
                        name = text

            if not name or len(name) < 3 or name.lower() in seen:
                continue
            seen.add(name.lower())

            # Extract phone from row text
            row_text = card.get_text(" ", strip=True)
            phone_match = re.search(r"0[2-9]\d[\d\-]{6,8}", row_text)
            phone = _clean_phone(phone_match.group()) if phone_match else ""

            results.append(_make_biz(
                name=name, phone=phone, website=website,
                category=query, query=query, source="2all",
            ))

    except Exception as e:
        print(f"    [2All] שגיאה: {e}")

    print(f"    [2All] '{query}' → {len(results)} עסקים")
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
#  העשרת נתוני עסק — תמונות, לוגו, תיאור, שעות, ביקורות
# ════════════════════════════════════════════════════════════════
def enrich_business_profile(biz: dict) -> dict:
    """
    שולף נתונים מורחבים על העסק מ-Google Maps (SerpApi) ומהאתר שלו.
    מחזיר dict עם: logo_url, photos, owner_name, description,
    opening_hours, top_reviews, services, price_range.
    """
    result = {}
    name = biz.get("name", "")
    city = biz.get("city", "")
    website = biz.get("website", "")

    # ── SerpApi — Google Maps place details ──
    if SERPAPI_KEY and SERPAPI_KEY != "YOUR_SERPAPI_KEY_HERE" and name:
        try:
            query = name
            if city:
                query += f" {city}"
            params = {
                "engine": "google_maps",
                "q": query,
                "gl": "il",
                "type": "search",
                "api_key": SERPAPI_KEY,
            }
            resp = requests.get("https://serpapi.com/search", params=params, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                places = data.get("local_results", [])
                # Find the matching place
                place = None
                for p in places:
                    if name.lower() in (p.get("title", "")).lower():
                        place = p
                        break
                if not place and places:
                    place = places[0]  # Best match

                if place:
                    # Photos
                    thumb = place.get("thumbnail")
                    if thumb:
                        result["logo_url"] = thumb
                    photos = place.get("photos", [])
                    if photos:
                        result["photos"] = json.dumps(
                            [ph.get("image") or ph.get("thumbnail", "") for ph in photos[:10]]
                        )

                    # Description
                    desc = place.get("description") or place.get("snippet") or ""
                    if desc:
                        result["description"] = desc

                    # Opening hours
                    hours = place.get("operating_hours") or place.get("hours")
                    if hours:
                        result["opening_hours"] = json.dumps(hours, ensure_ascii=False)

                    # Price range
                    price = place.get("price")
                    if price:
                        result["price_range"] = price

                    # Services / types
                    ptype = place.get("type") or place.get("types")
                    if ptype:
                        if isinstance(ptype, list):
                            result["services"] = json.dumps(ptype, ensure_ascii=False)
                        else:
                            result["services"] = json.dumps([ptype], ensure_ascii=False)

                    # Reviews
                    if place.get("reviews"):
                        result["google_reviews"] = int(place["reviews"])
                    if place.get("rating"):
                        result["google_rating"] = float(place["rating"])

        except Exception:
            pass

    # ── Website scraping — logo, description, owner name ──
    if website:
        try:
            resp = requests.get(website, headers=HEADERS, timeout=10, allow_redirects=True)
            html = resp.text
            soup = BeautifulSoup(html, "html.parser")

            # Logo
            if not result.get("logo_url"):
                logo_el = soup.select_one(
                    "img[class*='logo'], img[alt*='logo'], img[src*='logo'], "
                    "link[rel='icon'], link[rel='shortcut icon']"
                )
                if logo_el:
                    logo_src = logo_el.get("src") or logo_el.get("href", "")
                    if logo_src:
                        if logo_src.startswith("/"):
                            from urllib.parse import urljoin
                            logo_src = urljoin(website, logo_src)
                        result["logo_url"] = logo_src

            # Description from meta tags
            if not result.get("description"):
                meta_desc = soup.select_one('meta[name="description"], meta[property="og:description"]')
                if meta_desc:
                    result["description"] = meta_desc.get("content", "")[:500]

            # Owner name from structured data
            for script in soup.select('script[type="application/ld+json"]'):
                try:
                    ld = json.loads(script.string or "")
                    items = ld if isinstance(ld, list) else [ld]
                    for item in items:
                        if item.get("founder"):
                            founder = item["founder"]
                            if isinstance(founder, dict):
                                result["owner_name"] = founder.get("name", "")
                            elif isinstance(founder, str):
                                result["owner_name"] = founder
                        if item.get("openingHoursSpecification") and not result.get("opening_hours"):
                            result["opening_hours"] = json.dumps(
                                item["openingHoursSpecification"], ensure_ascii=False
                            )
                except (json.JSONDecodeError, TypeError):
                    continue

            # Photos from og:image and other images
            if not result.get("photos"):
                photo_urls = []
                og_img = soup.select_one('meta[property="og:image"]')
                if og_img and og_img.get("content"):
                    photo_urls.append(og_img["content"])
                for img in soup.select("img[src]")[:20]:
                    src = img.get("src", "")
                    if src and not any(skip in src.lower() for skip in
                                       ["logo", "icon", "pixel", "tracking", "avatar",
                                        "1x1", "spacer", "blank"]):
                        if src.startswith("/"):
                            src = urljoin(website, src)
                        if src.startswith("http") and len(src) > 20:
                            photo_urls.append(src)
                    if len(photo_urls) >= 8:
                        break
                if photo_urls:
                    result["photos"] = json.dumps(photo_urls[:8])

        except Exception:
            pass

    return result


# ════════════════════════════════════════════════════════════════
#  מציאת מתחרים — לפי קטגוריה + עיר דרך SerpApi / Google
# ════════════════════════════════════════════════════════════════
def find_competitors(biz: dict, max_results: int = 5) -> list[dict]:
    """
    מוצא מתחרים לעסק — עסקים באותה קטגוריה ועיר שיש להם אתר טוב.
    מחזיר רשימת dicts: [{name, website, rating, reviews, phone}]
    """
    category = biz.get("category") or biz.get("search_query") or ""
    city = biz.get("city") or ""
    biz_name = (biz.get("name") or "").strip().lower()

    if not category:
        return []

    query = category
    if city:
        query += f" {city}"

    competitors = []
    seen = set()

    # Method 1: SerpApi Google Maps (best data — name, website, rating, reviews)
    if SERPAPI_KEY and SERPAPI_KEY != "YOUR_SERPAPI_KEY_HERE":
        try:
            params = {
                "engine": "google_maps",
                "q": query,
                "gl": "il",
                "type": "search",
                "api_key": SERPAPI_KEY,
            }
            resp = requests.get("https://serpapi.com/search", params=params, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                for p in data.get("local_results", []):
                    name = p.get("title", "").strip()
                    if not name or name.lower() == biz_name:
                        continue
                    if name.lower() in seen:
                        continue
                    seen.add(name.lower())
                    website = p.get("website", "")
                    if not website:
                        continue  # מתחרה בלי אתר לא מעניין אותנו
                    competitors.append({
                        "name": name,
                        "website": website,
                        "rating": p.get("rating"),
                        "reviews": p.get("reviews"),
                        "phone": p.get("phone", ""),
                    })
                    if len(competitors) >= max_results:
                        break
        except Exception:
            pass

    # Method 2: B144 fallback (if SerpApi didn't return enough)
    if len(competitors) < max_results:
        try:
            b144_results = scrape_b144(query)
            for b in b144_results:
                name = b.get("name", "").strip()
                if not name or name.lower() == biz_name or name.lower() in seen:
                    continue
                seen.add(name.lower())
                website = b.get("website", "")
                if not website:
                    continue
                competitors.append({
                    "name": name,
                    "website": website,
                    "rating": b.get("google_rating"),
                    "reviews": b.get("google_reviews"),
                    "phone": b.get("phone", ""),
                })
                if len(competitors) >= max_results:
                    break
        except Exception:
            pass

    return competitors[:max_results]


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
               "wix_search", "old_sites", "gov_registry", "facebook", "zap",
               "easy", "igal", "freesearch", "2all", "directory_search", "midrag"
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

    # ── מדריכי עסקים ישראליים — מקורות עשירים בעסקים קטנים ──
    if should_run("easy"):
        add_results(scrape_easy(query))
        time.sleep(0.5)

    if should_run("igal"):
        add_results(scrape_igal(query))
        time.sleep(0.5)

    if should_run("freesearch"):
        add_results(scrape_freesearch(query))
        time.sleep(0.5)

    if should_run("2all"):
        add_results(scrape_2all(query))
        time.sleep(0.5)

    if should_run("directory_search"):
        add_results(scrape_directories_google(query))
        time.sleep(1)

    if should_run("midrag"):
        add_results(scrape_midrag(query))
        time.sleep(0.5)

    print(f"\n  ✅ סה\"כ '{query}': {len(all_results)} עסקים ייחודיים מכל המקורות")
    return all_results[:MAX_RESULTS_PER_QUERY * 5]
