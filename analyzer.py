"""
analyzer.py — בדיקת איכות אתרי עסקים.
מחזיר ציון 1-10 ורשימת בעיות שנמצאו.
"""

import time
import re
import ssl
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

CTA_PATTERNS = [
    r"התקשר[\s\S]{0,5}עכשיו", r"call[\s\S]{0,5}now", r"צור[\s\S]{0,3}קשר",
    r"השאר[\s\S]{0,3}פרטים", r"לחץ[\s\S]{0,3}כאן", r"קבל[\s\S]{0,3}הצעה",
    r"הזמן[\s\S]{0,3}עכשיו", r"book[\s\S]{0,5}now", r"contact[\s\S]{0,5}us",
    r"get[\s\S]{0,5}quote", r"whatsapp", r"שלח[\s\S]{0,3}הודעה",
    r"btn|button|cta",
]


def _check_ssl(url: str) -> bool:
    """בודק אם האתר עובד עם HTTPS תקין."""
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


def analyze_website(url: str) -> dict:
    """
    בודק אתר ומחזיר dict עם כל הבדיקות + ציון איכות.
    אם url ריק — מחזיר ציון 0 (ליד חם ביותר! אין אתר בכלל).
    """
    result = {
        "has_website":   0,
        "has_ssl":       0,
        "is_responsive": 0,
        "has_cta":       0,
        "has_form":      0,
        "has_fb_pixel":  0,
        "has_analytics": 0,
        "load_time_ms":  None,
        "quality_score": 0,
        "issues":        [],
    }

    # ── אין אתר בכלל ──
    if not url:
        result["issues"] = ["אין אתר אינטרנט — הזדמנות מצוינת לבניית אתר מאפס"]
        result["quality_score"] = 10   # ציון "דחיפות" גבוה — לא ציון איכות
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
        html = resp.text.lower()

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
    if 'name="viewport"' in html or "name='viewport'" in html:
        result["is_responsive"] = 1
    else:
        result["issues"].append("האתר לא מותאם לנייד (חסר Meta viewport)")

    # ── CTA (Call to Action) ──
    cta_found = any(re.search(p, html) for p in CTA_PATTERNS)
    result["has_cta"] = 1 if cta_found else 0
    if not cta_found:
        result["issues"].append("אין כפתורי CTA ברורים — האתר לא ממיר לידים")

    # ── טפסי יצירת קשר ──
    form_count = html.count("<form")
    result["has_form"] = 1 if form_count > 0 else 0
    if not result["has_form"]:
        result["issues"].append("אין טופס יצירת קשר — אין כלי לאיסוף לידים")

    # ── Facebook Pixel ──
    if "fbq(" in html or "facebook.net/en_us/fbevents" in html or "connect.facebook.net" in html:
        result["has_fb_pixel"] = 1
    else:
        result["issues"].append("אין Facebook Pixel — מפסידים אפשרות רימרקטינג")

    # ── Google Analytics / GTM ──
    if "google-analytics.com" in html or "gtag(" in html or "googletagmanager" in html:
        result["has_analytics"] = 1
    else:
        result["issues"].append("אין Google Analytics — אין מעקב אחר מבקרים")

    # ── חישוב ציון (1-10) ──
    # ציון נמוך = האתר גרוע = ליד חם יותר עבורנו
    # (אנחנו נשלח לעסקים עם ציון נמוך — הם צריכים אותנו)
    score = 10
    if not result["has_ssl"]:          score -= 2
    if not result["is_responsive"]:    score -= 2
    if not result["has_cta"]:          score -= 2
    if not result["has_form"]:         score -= 1
    if not result["has_fb_pixel"]:     score -= 1
    if not result["has_analytics"]:    score -= 1
    if result["load_time_ms"] and result["load_time_ms"] > 4000:
        score -= 1

    result["quality_score"] = max(1, score)
    result["issues"] = result["issues"] if result["issues"] else ["האתר נראה תקין"]
    return result


def build_issue_summary(analysis: dict) -> str:
    """מייצר תיאור קצר של הבעיות — לשימוש בהודעות הפנייה."""
    issues = analysis.get("issues", [])
    if not issues or issues == ["האתר נראה תקין"]:
        return "שיפורים טכניים כלליים"
    # החזר את הבעיה הבולטת ביותר
    priority = [i for i in issues if "נייד" in i or "SSL" in i or "CTA" in i or "טופס" in i]
    return priority[0] if priority else issues[0]
