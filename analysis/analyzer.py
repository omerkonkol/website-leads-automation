"""
analyzer.py — ניתוח מתקדם של אתרי עסקים.

בדיקות:
  - SSL, responsive, CTA, form, pixels, analytics (כמו קודם)
  - PageSpeed Insights API (חינם, ללא API key)
  - SEO: title, meta description, H1, robots.txt, sitemap.xml
  - CMS detection: Wix, WordPress, Webflow, Squarespace, custom
  - Copyright year — אתרים ישנים = הזדמנות
  - Core Web Vitals (LCP, FID, CLS)
  - Google Reviews count (מ-SerpApi או scraping)
"""

import time
import re
import ssl
import json
import socket
import requests
from urllib.parse import urlparse
from config import SITE_TIMEOUT


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
    )
}

DESKTOP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

CTA_PATTERNS = [
    r"התקשר[\s\S]{0,5}עכשיו", r"call[\s\S]{0,5}now", r"צור[\s\S]{0,3}קשר",
    r"השאר[\s\S]{0,3}פרטים", r"לחץ[\s\S]{0,3}כאן", r"קבל[\s\S]{0,3}הצעה",
    r"הזמן[\s\S]{0,3}עכשיו", r"book[\s\S]{0,5}now", r"contact[\s\S]{0,5}us",
    r"get[\s\S]{0,5}quote", r"whatsapp", r"שלח[\s\S]{0,3}הודעה",
    r"btn|button|cta",
]

# ── CMS Detection Signatures ──
CMS_SIGNATURES = {
    "wix": [
        "wixstatic.com", "wix.com", "wixpress.com", "X-Wix-",
        "_wix_browser_sess", "wix-code-sdk",
    ],
    "wordpress": [
        "wp-content", "wp-includes", "wp-json", "wordpress",
        'name="generator" content="WordPress',
    ],
    "webflow": [
        "webflow.com", "webflow.io", "wf-page", "w-webflow-badge",
    ],
    "squarespace": [
        "squarespace.com", "sqsp.net", "sqs-", "squarespace-cdn",
    ],
    "shopify": [
        "shopify.com", "shopifycdn.com", "Shopify.theme",
    ],
    "joomla": [
        "joomla", "/components/com_", "/media/jui/",
    ],
    "weebly": [
        "weebly.com", "weeblycloud.com",
    ],
    "godaddy_builder": [
        "godaddy.com/website-builder", "secureserver.net", "wsimg.com",
    ],
}


def _check_ssl(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return False
    hostname = parsed.hostname
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(5)
            s.connect((hostname, 443))
        return True
    except Exception:
        return False


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _detect_cms(html: str, resp_headers: dict = None) -> str:
    """מזהה את ה-CMS של האתר."""
    html_lower = html.lower()
    headers_str = str(resp_headers or {}).lower()
    combined = html_lower + " " + headers_str

    for cms, signatures in CMS_SIGNATURES.items():
        matches = sum(1 for sig in signatures if sig.lower() in combined)
        if matches >= 2:
            return cms
        if matches == 1 and cms in ("wix", "wordpress", "shopify"):
            return cms

    return "custom"


def _detect_copyright_year(html: str) -> int | None:
    """מחפש שנת copyright באתר — אתרים ישנים = הזדמנות."""
    patterns = [
        r'©\s*(\d{4})',
        r'copyright\s*(?:©)?\s*(\d{4})',
        r'כל\s*הזכויות\s*שמורות\s*©?\s*(\d{4})',
        r'(\d{4})\s*©',
        r'All\s*Rights?\s*Reserved\s*©?\s*(\d{4})',
    ]
    years = []
    for pattern in patterns:
        for match in re.finditer(pattern, html, re.IGNORECASE):
            year = int(match.group(1))
            if 2000 <= year <= 2030:
                years.append(year)
    return max(years) if years else None


def _check_seo(html: str, url: str) -> dict:
    """בדיקת SEO בסיסית — title, meta description, H1, robots.txt, sitemap."""
    seo = {
        "has_title_tag":  0,
        "has_meta_desc":  0,
        "has_h1":         0,
        "has_robots_txt": 0,
        "has_sitemap":    0,
        "seo_issues":     [],
    }

    # Title tag
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
    if title_match and len(title_match.group(1).strip()) > 3:
        seo["has_title_tag"] = 1
    else:
        seo["seo_issues"].append("חסר Title Tag — גוגל לא יודע על מה האתר")

    # Meta description
    meta_desc = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)', html, re.IGNORECASE)
    if not meta_desc:
        meta_desc = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+name=["\']description', html, re.IGNORECASE)
    if meta_desc and len(meta_desc.group(1).strip()) > 10:
        seo["has_meta_desc"] = 1
    else:
        seo["seo_issues"].append("חסר Meta Description — תיאור גרוע בגוגל")

    # H1
    h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.IGNORECASE)
    if h1_match and len(h1_match.group(1).strip()) > 2:
        seo["has_h1"] = 1
    else:
        seo["seo_issues"].append("חסר H1 — כותרת ראשית לגוגל")

    # robots.txt & sitemap.xml (בדיקה מהירה)
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.hostname}"
    try:
        robots = requests.get(f"{base}/robots.txt", timeout=5, headers=HEADERS)
        if robots.status_code == 200 and len(robots.text) > 10:
            seo["has_robots_txt"] = 1
    except Exception:
        pass

    try:
        sitemap = requests.get(f"{base}/sitemap.xml", timeout=5, headers=HEADERS)
        if sitemap.status_code == 200 and "<url" in sitemap.text.lower():
            seo["has_sitemap"] = 1
        elif seo["has_robots_txt"]:
            # חפש sitemap ב-robots.txt
            if "sitemap:" in robots.text.lower():
                seo["has_sitemap"] = 1
    except Exception:
        pass

    if not seo["has_robots_txt"]:
        seo["seo_issues"].append("חסר robots.txt")
    if not seo["has_sitemap"]:
        seo["seo_issues"].append("חסר sitemap.xml — גוגל לא סורק ביעילות")

    # חשב ציון SEO (0-100)
    seo_score = 0
    if seo["has_title_tag"]:  seo_score += 25
    if seo["has_meta_desc"]:  seo_score += 25
    if seo["has_h1"]:         seo_score += 20
    if seo["has_robots_txt"]: seo_score += 15
    if seo["has_sitemap"]:    seo_score += 15
    seo["seo_score"] = seo_score

    return seo


def _get_pagespeed(url: str) -> dict | None:
    """
    PageSpeed Insights API — חינם לחלוטין, ללא API key.
    מחזיר ציון ביצועים ו-Core Web Vitals.
    """
    try:
        api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeedTest"
        params = {
            "url": url,
            "category": "performance",
            "strategy": "mobile",
        }
        resp = requests.get(api_url, params=params, timeout=30)
        if resp.status_code != 200:
            return None

        data = resp.json()
        lighthouse = data.get("lighthouseResult", {})
        score = lighthouse.get("categories", {}).get("performance", {}).get("score")
        if score is not None:
            score = int(score * 100)

        # Core Web Vitals
        audits = lighthouse.get("audits", {})
        cwv = {}
        if "largest-contentful-paint" in audits:
            cwv["lcp"] = audits["largest-contentful-paint"].get("numericValue")
        if "total-blocking-time" in audits:
            cwv["tbt"] = audits["total-blocking-time"].get("numericValue")
        if "cumulative-layout-shift" in audits:
            cwv["cls"] = audits["cumulative-layout-shift"].get("numericValue")

        return {
            "pagespeed_score": score,
            "core_web_vitals": json.dumps(cwv),
        }

    except Exception as e:
        print(f"    [PageSpeed] {e}")
        return None


# ════════════════════════════════════════════════════════════════
#  ניתוח ראשי
# ════════════════════════════════════════════════════════════════
def analyze_website(url: str, run_pagespeed: bool = False) -> dict:
    """
    בודק אתר ומחזיר dict עם כל הבדיקות + ציון איכות.
    אם url ריק — מחזיר ציון 0 (ליד חם ביותר! אין אתר בכלל).

    run_pagespeed: True = הפעל PageSpeed Insights (איטי יותר, ~10-20 שניות).
    """
    result = {
        "has_website":    0,
        "has_ssl":        0,
        "is_responsive":  0,
        "has_cta":        0,
        "has_form":       0,
        "has_fb_pixel":   0,
        "has_analytics":  0,
        "load_time_ms":   None,
        "quality_score":  0,
        "issues":         [],
        # חדש — SEO
        "has_title_tag":  0,
        "has_meta_desc":  0,
        "has_h1":         0,
        "has_robots_txt": 0,
        "has_sitemap":    0,
        "seo_score":      None,
        # חדש — CMS & age
        "cms_platform":    None,
        "copyright_year":  None,
        # חדש — PageSpeed
        "pagespeed_score": None,
        "core_web_vitals": None,
    }

    # ── אין אתר בכלל ──
    if not url:
        result["issues"] = ["אין אתר אינטרנט — הזדמנות מצוינת לבניית אתר מאפס"]
        result["quality_score"] = 10
        return result

    url = _normalize_url(url)
    result["has_website"] = 1

    # ── SSL ──
    result["has_ssl"] = 1 if _check_ssl(url) else 0
    if not result["has_ssl"]:
        result["issues"].append("אין תעודת SSL (HTTPS) — בעיית אבטחה ודירוג גוגל")

    # ── טעינת האתר ──
    try:
        start = time.time()
        resp = requests.get(url, headers=HEADERS, timeout=SITE_TIMEOUT, allow_redirects=True)
        elapsed_ms = int((time.time() - start) * 1000)
        result["load_time_ms"] = elapsed_ms
        html = resp.text
        html_lower = html.lower()

        if elapsed_ms > 4000:
            result["issues"].append(f"טעינה איטית: {elapsed_ms}ms (מעל 4 שניות)")
        elif elapsed_ms > 2000:
            result["issues"].append(f"טעינה בינונית: {elapsed_ms}ms")

    except requests.exceptions.Timeout:
        result["issues"].append("האתר לא נטען (Timeout) — כנראה לא פעיל")
        result["quality_score"] = 8
        return result
    except Exception as e:
        result["issues"].append(f"שגיאה בטעינה: {str(e)[:60]}")
        result["quality_score"] = 7
        return result

    # ── רספונסיביות (Meta viewport) ──
    if 'name="viewport"' in html_lower or "name='viewport'" in html_lower:
        result["is_responsive"] = 1
    else:
        result["issues"].append("האתר לא מותאם לנייד (חסר Meta viewport)")

    # ── CTA (Call to Action) ──
    cta_found = any(re.search(p, html_lower) for p in CTA_PATTERNS)
    result["has_cta"] = 1 if cta_found else 0
    if not cta_found:
        result["issues"].append("אין כפתורי CTA ברורים — האתר לא ממיר לידים")

    # ── טפסי יצירת קשר ──
    form_count = html_lower.count("<form")
    result["has_form"] = 1 if form_count > 0 else 0
    if not result["has_form"]:
        result["issues"].append("אין טופס יצירת קשר — אין כלי לאיסוף לידים")

    # ── Facebook Pixel ──
    if "fbq(" in html_lower or "facebook.net/en_us/fbevents" in html_lower or "connect.facebook.net" in html_lower:
        result["has_fb_pixel"] = 1
    else:
        result["issues"].append("אין Facebook Pixel — מפסידים אפשרות רימרקטינג")

    # ── Google Analytics / GTM ──
    if "google-analytics.com" in html_lower or "gtag(" in html_lower or "googletagmanager" in html_lower:
        result["has_analytics"] = 1
    else:
        result["issues"].append("אין Google Analytics — אין מעקב אחר מבקרים")

    # ── CMS Detection ──
    result["cms_platform"] = _detect_cms(html, dict(resp.headers))
    if result["cms_platform"] == "wix":
        result["issues"].append("האתר בנוי על Wix — מוגבל בהתאמה אישית ו-SEO")
    elif result["cms_platform"] in ("godaddy_builder", "weebly"):
        result["issues"].append(f"האתר בנוי על {result['cms_platform']} — פלטפורמה מיושנת")

    # ── Copyright Year ──
    result["copyright_year"] = _detect_copyright_year(html)
    if result["copyright_year"] and result["copyright_year"] < 2022:
        years_old = 2026 - result["copyright_year"]
        result["issues"].append(f"האתר לא עודכן {years_old} שנים (copyright {result['copyright_year']})")

    # ── SEO Analysis ──
    seo = _check_seo(html, url)
    result["has_title_tag"]  = seo["has_title_tag"]
    result["has_meta_desc"]  = seo["has_meta_desc"]
    result["has_h1"]         = seo["has_h1"]
    result["has_robots_txt"] = seo["has_robots_txt"]
    result["has_sitemap"]    = seo["has_sitemap"]
    result["seo_score"]      = seo["seo_score"]
    result["issues"].extend(seo["seo_issues"])

    # ── PageSpeed Insights (אופציונלי — איטי) ──
    if run_pagespeed:
        ps = _get_pagespeed(url)
        if ps:
            result["pagespeed_score"] = ps["pagespeed_score"]
            result["core_web_vitals"] = ps["core_web_vitals"]
            if ps["pagespeed_score"] is not None and ps["pagespeed_score"] < 50:
                result["issues"].append(
                    f"ציון PageSpeed נמוך: {ps['pagespeed_score']}/100 — האתר איטי מאוד"
                )

    # ── חישוב ציון (1-10) ──
    score = 10
    if not result["has_ssl"]:          score -= 2
    if not result["is_responsive"]:    score -= 2
    if not result["has_cta"]:          score -= 2
    if not result["has_form"]:         score -= 1
    if not result["has_fb_pixel"]:     score -= 1
    if not result["has_analytics"]:    score -= 1
    if result["load_time_ms"] and result["load_time_ms"] > 4000:
        score -= 1
    # בונוסים SEO (ציון נמוך = אתר גרוע = ליד טוב לנו)
    if result["seo_score"] is not None and result["seo_score"] < 50:
        score -= 1

    result["quality_score"] = max(1, score)
    result["issues"] = result["issues"] if result["issues"] else ["האתר נראה תקין"]
    return result


def build_issue_summary(analysis: dict) -> str:
    """מייצר תיאור קצר של הבעיות — לשימוש בהודעות הפנייה."""
    issues = analysis.get("issues", [])
    if not issues or issues == ["האתר נראה תקין"]:
        return "שיפורים טכניים כלליים"
    priority = [i for i in issues if "נייד" in i or "SSL" in i or "CTA" in i or "טופס" in i]
    return priority[0] if priority else issues[0]


def analyze_website_full(url: str) -> dict:
    """ניתוח מלא כולל PageSpeed — משמש מהדשבורד לניתוח מעמיק."""
    return analyze_website(url, run_pagespeed=True)
