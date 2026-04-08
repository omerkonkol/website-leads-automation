"""
business_verifier.py — אימות שעסק פעיל לפני פנייה.

בדיקות (כולן חינמיות):
  1. טלפון תקין         — פורמט ישראלי נכון, לא מספר שירות
  2. Google Search      — שם העסק מופיע בתוצאות (לא סגור/נמחק)
  3. אתר מגיב           — HTTP 200 (אם יש אתר)
  4. WhatsApp           — הטלפון רשום ב-WhatsApp (סימן לעסק פעיל)
  5. פייסבוק פעיל       — דף הפייסבוק קיים ונגיש
  6. חוזר ב-2+ מקורות   — אם נמצא ביותר ממקור אחד = סביר שפעיל

מחזיר activity_score (0-100) + פירוט.
"""

import re
import time
import requests
from urllib.parse import quote

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "he-IL,he;q=0.9,en;q=0.8",
}


# ════════════════════════════════════════════════════════════════
#  1. אימות טלפון — פורמט ישראלי תקין
# ════════════════════════════════════════════════════════════════
# קידומות סלולר תקינות בישראל
MOBILE_PREFIXES = {"050", "051", "052", "053", "054", "055", "056", "058"}
LANDLINE_PREFIXES = {"02", "03", "04", "08", "09", "072", "073", "074", "076", "077"}
SERVICE_PREFIXES = {"1700", "1800", "1801", "1599", "*"}


def verify_phone(phone: str) -> dict:
    """בודק אם מספר הטלפון תקין ורלוונטי."""
    result = {"valid": False, "phone_type": "unknown", "score": 0, "reason": ""}

    if not phone:
        result["reason"] = "אין מספר טלפון"
        return result

    digits = re.sub(r"[^\d]", "", phone)

    # מספרי שירות — לא רלוונטי
    if any(digits.startswith(p) for p in ("1700", "1800", "1801", "1599")):
        result["reason"] = "מספר שירות (לא ישיר)"
        result["phone_type"] = "service"
        result["score"] = 5
        return result

    if phone.startswith("*"):
        result["reason"] = "מספר כוכבית (לא ישיר)"
        result["phone_type"] = "star"
        result["score"] = 5
        return result

    # סלולר — הכי טוב (אפשר WhatsApp)
    if len(digits) == 10 and digits[:3] in MOBILE_PREFIXES:
        result["valid"] = True
        result["phone_type"] = "mobile"
        result["score"] = 25
        result["reason"] = "סלולר תקין — אפשר WhatsApp"
        return result

    # נייח — עדיין טוב
    for prefix in LANDLINE_PREFIXES:
        if digits.startswith(prefix) and len(digits) in (9, 10):
            result["valid"] = True
            result["phone_type"] = "landline"
            result["score"] = 15
            result["reason"] = "טלפון נייח תקין"
            return result

    # מספר קצר או לא מזוהה
    if len(digits) < 7:
        result["reason"] = f"מספר קצר מדי ({len(digits)} ספרות)"
        result["score"] = 0
        return result

    # מספר ארוך אבל לא מזוהה
    result["valid"] = True
    result["phone_type"] = "unknown"
    result["score"] = 10
    result["reason"] = "מספר לא סטנדרטי"
    return result


# ════════════════════════════════════════════════════════════════
#  2. Google Search — בדיקת נוכחות ופעילות
# ════════════════════════════════════════════════════════════════
def verify_google_presence(name: str, city: str = "") -> dict:
    """
    מחפש את שם העסק ב-Google ובודק:
    - האם יש תוצאות בכלל
    - האם מופיע "סגור לצמיתות" / "permanently closed"
    - האם יש תוצאות עדכניות
    """
    result = {"found": False, "closed": False, "score": 0, "reason": "", "details": ""}

    query = f'"{name}"'
    if city:
        query += f" {city}"

    url = f"https://www.google.com/search?q={quote(query)}&hl=he&gl=il&num=5"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            result["reason"] = "לא ניתן לחפש ב-Google"
            result["score"] = 10  # ניטרלי — לא מוריד
            return result

        html = resp.text.lower()

        # בדיקת חסימה
        if "detected unusual traffic" in html or "captcha" in html:
            result["reason"] = "Google חסם — לא ניתן לאמת"
            result["score"] = 10  # ניטרלי
            return result

        # בדוק אם העסק מופיע
        name_lower = name.lower()
        # חפש את שם העסק בתוצאות (חלקים ממנו לפחות)
        name_words = [w for w in name_lower.split() if len(w) > 2]
        matches = sum(1 for w in name_words if w in html)
        name_found = matches >= max(1, len(name_words) // 2)

        if not name_found:
            result["reason"] = "העסק לא נמצא ב-Google — ייתכן סגור"
            result["score"] = 0
            return result

        result["found"] = True

        # בדוק "סגור לצמיתות"
        closed_signals = [
            "סגור לצמיתות", "permanently closed", "closed permanently",
            "עסק סגור", "נסגר", "closed down", "out of business",
            "כבר לא קיים", "no longer exists",
        ]
        for signal in closed_signals:
            if signal in html:
                result["closed"] = True
                result["reason"] = f"Google מציג: '{signal}' — העסק כנראה סגור"
                result["score"] = -30  # עונש חמור
                return result

        # בדוק סימנים חיוביים
        positive_signals = 0
        if "google.com/maps" in html or "maps.google" in html:
            positive_signals += 1
            result["details"] += "מופיע ב-Google Maps; "
        if any(x in html for x in ["ביקורות", "reviews", "דירוג", "rating"]):
            positive_signals += 1
            result["details"] += "יש ביקורות; "
        if any(x in html for x in ["שעות פתיחה", "hours", "פתוח עכשיו"]):
            positive_signals += 1
            result["details"] += "שעות פתיחה מוצגות; "
        if any(x in html for x in ["facebook.com", "instagram.com"]):
            positive_signals += 1
            result["details"] += "פעיל ברשתות חברתיות; "

        if positive_signals >= 3:
            result["score"] = 25
            result["reason"] = "נוכחות חזקה ב-Google — עסק פעיל"
        elif positive_signals >= 1:
            result["score"] = 15
            result["reason"] = "נמצא ב-Google עם סימנים חיוביים"
        else:
            result["score"] = 8
            result["reason"] = "נמצא ב-Google — מידע מינימלי"

    except requests.exceptions.Timeout:
        result["reason"] = "timeout בחיפוש Google"
        result["score"] = 10
    except Exception as e:
        result["reason"] = f"שגיאה: {str(e)[:50]}"
        result["score"] = 10

    return result


# ════════════════════════════════════════════════════════════════
#  3. בדיקת אתר — האם מגיב בכלל
# ════════════════════════════════════════════════════════════════
def verify_website_alive(url: str) -> dict:
    """בודק אם האתר חי ומגיב."""
    result = {"alive": False, "score": 0, "reason": "", "status_code": None}

    if not url:
        result["reason"] = "אין אתר — לא ניתן לבדוק"
        result["score"] = 0  # ניטרלי — אין אתר זה לא רע (זה ליד!)
        return result

    if not url.startswith("http"):
        url = "https://" + url

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        result["status_code"] = resp.status_code

        if resp.status_code == 200:
            # בדוק שזה לא דף חניה / parked domain
            html_lower = resp.text.lower()
            parked_signals = [
                "this domain is for sale", "domain is parked",
                "buy this domain", "domain parking",
                "הדומיין למכירה", "אתר בבנייה", "coming soon",
                "under construction",
            ]
            is_parked = any(s in html_lower for s in parked_signals)

            if is_parked:
                result["alive"] = False
                result["reason"] = "דומיין חנוי / אתר בבנייה — העסק כנראה לא פעיל באונליין"
                result["score"] = 5
            elif len(resp.text) < 500:
                result["alive"] = False
                result["reason"] = "דף כמעט ריק — אתר נטוש"
                result["score"] = 5
            else:
                result["alive"] = True
                result["reason"] = "האתר חי ומגיב"
                result["score"] = 15
        elif resp.status_code in (301, 302):
            result["alive"] = True
            result["reason"] = "האתר מפנה (redirect)"
            result["score"] = 10
        elif resp.status_code == 403:
            result["alive"] = True  # קיים אבל חוסם
            result["reason"] = "האתר חוסם גישה (403) — קיים"
            result["score"] = 10
        elif resp.status_code == 404:
            result["reason"] = "דף לא נמצא (404) — אתר נטוש?"
            result["score"] = 0
        elif resp.status_code >= 500:
            result["reason"] = f"שגיאת שרת ({resp.status_code}) — אתר תקול"
            result["score"] = 3

    except requests.exceptions.ConnectionError:
        result["reason"] = "אתר לא מגיב — כנראה נסגר"
        result["score"] = 0
    except requests.exceptions.Timeout:
        result["reason"] = "אתר לא מגיב (timeout)"
        result["score"] = 3
    except Exception as e:
        result["reason"] = f"שגיאה: {str(e)[:50]}"
        result["score"] = 5

    return result


# ════════════════════════════════════════════════════════════════
#  4. WhatsApp — בדיקה אם המספר רשום
# ════════════════════════════════════════════════════════════════
def verify_whatsapp(phone: str) -> dict:
    """
    בודק אם מספר הטלפון רשום ב-WhatsApp.
    שיטה: wa.me/{number} מחזיר redirect אם קיים.
    עסק פעיל ב-2026 כמעט תמיד ב-WhatsApp.
    """
    result = {"on_whatsapp": False, "score": 0, "reason": ""}

    if not phone:
        result["reason"] = "אין טלפון"
        return result

    digits = re.sub(r"[^\d]", "", phone)

    # המר לפורמט בינלאומי
    if digits.startswith("0"):
        digits = "972" + digits[1:]
    elif not digits.startswith("972"):
        digits = "972" + digits

    # רק סלולר רלוונטי ל-WhatsApp
    if not digits.startswith("9725"):
        result["reason"] = "לא סלולר — WhatsApp לא רלוונטי"
        result["score"] = 0
        return result

    try:
        # wa.me returns 302 to api.whatsapp if valid, shows error page if not
        url = f"https://wa.me/{digits}"
        resp = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=False)

        if resp.status_code in (200, 302):
            # בדוק אם הדף מכיל "message" (חשבון קיים)
            if resp.status_code == 302:
                result["on_whatsapp"] = True
                result["score"] = 20
                result["reason"] = "מספר רשום ב-WhatsApp — עסק פעיל"
            else:
                # בדוק את תוכן הדף
                html = resp.text.lower()
                if "send a message" in html or "start a conversation" in html or "chat" in html:
                    result["on_whatsapp"] = True
                    result["score"] = 20
                    result["reason"] = "מספר רשום ב-WhatsApp — עסק פעיל"
                elif "phone number shared via url is invalid" in html:
                    result["reason"] = "מספר לא רשום ב-WhatsApp"
                    result["score"] = 0
                else:
                    result["on_whatsapp"] = True
                    result["score"] = 15
                    result["reason"] = "כנראה רשום ב-WhatsApp"
        else:
            result["reason"] = "לא ניתן לאמת WhatsApp"
            result["score"] = 5

    except Exception:
        result["reason"] = "שגיאה בבדיקת WhatsApp"
        result["score"] = 5

    return result


# ════════════════════════════════════════════════════════════════
#  5. פייסבוק — בדיקת דף עסקי
# ════════════════════════════════════════════════════════════════
def verify_facebook(facebook_url: str) -> dict:
    """בודק אם דף הפייסבוק קיים ופעיל."""
    result = {"active": False, "score": 0, "reason": ""}

    if not facebook_url:
        result["reason"] = "אין דף פייסבוק"
        return result

    try:
        resp = requests.get(facebook_url, headers=HEADERS, timeout=10, allow_redirects=True)

        if resp.status_code == 200:
            html_lower = resp.text.lower()
            # סימנים שהדף פעיל
            if any(x in html_lower for x in ["page_content", "usercontentWrapper", "feed"]):
                result["active"] = True
                result["score"] = 10
                result["reason"] = "דף פייסבוק פעיל"
            elif "this page isn't available" in html_lower or "this content isn't available" in html_lower:
                result["reason"] = "דף פייסבוק נמחק"
                result["score"] = -5
            else:
                result["active"] = True
                result["score"] = 8
                result["reason"] = "דף פייסבוק קיים"
        elif resp.status_code == 404:
            result["reason"] = "דף פייסבוק לא נמצא"
            result["score"] = -5
        else:
            result["reason"] = f"פייסבוק HTTP {resp.status_code}"
            result["score"] = 5

    except Exception:
        result["reason"] = "לא ניתן לבדוק פייסבוק"
        result["score"] = 5

    return result


# ════════════════════════════════════════════════════════════════
#  6. ריבוי מקורות — נמצא ביותר ממקור אחד
# ════════════════════════════════════════════════════════════════
def verify_multi_source(biz: dict, all_sources: list[str] = None) -> dict:
    """
    עסק שנמצא ביותר ממקור אחד = סביר יותר שפעיל.
    """
    result = {"multi_source": False, "source_count": 0, "score": 0, "reason": ""}

    source = biz.get("source", "")
    if not source:
        return result

    result["source_count"] = 1

    # אם יש רשימת מקורות חיצונית (מה-DB), בדוק כפילויות
    if all_sources:
        name_lower = biz.get("name", "").lower()
        matching = sum(1 for s in all_sources if s.lower() == name_lower)
        result["source_count"] = max(matching, 1)

    # הערכה לפי מקור
    reliable_sources = {"b144", "dapei_zahav", "google_maps"}
    if source in reliable_sources:
        result["score"] = 10
        result["reason"] = f"נמצא במקור אמין ({source})"
    elif source in ("gov_registry",):
        result["score"] = 12
        result["reason"] = "רשום ברשם החברות — חברה פעילה"
    else:
        result["score"] = 5
        result["reason"] = f"מקור: {source}"

    if result["source_count"] >= 3:
        result["multi_source"] = True
        result["score"] += 10
        result["reason"] += " + מופיע ב-3+ מקורות"
    elif result["source_count"] >= 2:
        result["multi_source"] = True
        result["score"] += 5
        result["reason"] += " + מופיע ב-2 מקורות"

    return result


# ════════════════════════════════════════════════════════════════
#  אימות מלא — מריץ את כל הבדיקות
# ════════════════════════════════════════════════════════════════
def verify_business(biz: dict, quick: bool = False) -> dict:
    """
    מריץ את כל בדיקות האימות ומחזיר:
    {
        "activity_score": int (0-100),
        "is_likely_active": bool,
        "checks": { ... פירוט כל בדיקה ... },
        "summary": str
    }

    quick=True: רק בדיקות מהירות (טלפון + מקור), בלי Google/WhatsApp.
    """
    checks = {}
    reasons = []

    # ── 1. טלפון (תמיד) ──
    phone_check = verify_phone(biz.get("phone", ""))
    checks["phone"] = phone_check
    if phone_check["reason"]:
        reasons.append(phone_check["reason"])

    # ── 2. ריבוי מקורות (תמיד) ──
    source_check = verify_multi_source(biz)
    checks["source"] = source_check
    if source_check["reason"]:
        reasons.append(source_check["reason"])

    # ── 3. אתר (תמיד, אם יש) ──
    website_check = verify_website_alive(biz.get("website", ""))
    checks["website"] = website_check
    if website_check["reason"]:
        reasons.append(website_check["reason"])

    if not quick:
        # ── 4. Google (איטי יותר) ──
        google_check = verify_google_presence(
            biz.get("name", ""),
            biz.get("city", "")
        )
        checks["google"] = google_check
        if google_check["reason"]:
            reasons.append(google_check["reason"])
        time.sleep(0.5)

        # ── 5. WhatsApp ──
        wa_check = verify_whatsapp(biz.get("phone", ""))
        checks["whatsapp"] = wa_check
        if wa_check["reason"]:
            reasons.append(wa_check["reason"])

        # ── 6. פייסבוק ──
        fb_check = verify_facebook(biz.get("facebook_url", ""))
        checks["facebook"] = fb_check
        if fb_check["reason"]:
            reasons.append(fb_check["reason"])

    # ── חישוב ציון פעילות (0-100) ──
    raw_score = sum(c.get("score", 0) for c in checks.values())

    # נרמול: הציון המקסימלי האפשרי תלוי בבדיקות שרצו
    if quick:
        max_possible = 50  # phone(25) + source(22) + website(15)
    else:
        max_possible = 100  # phone(25) + source(22) + website(15) + google(25) + wa(20) + fb(10)

    # נרמל ל-0-100
    activity_score = max(0, min(100, int(raw_score / max_possible * 100)))

    # קביעת סטטוס פעילות
    is_active = activity_score >= 30  # סף מינימלי

    # בדוק סימנים שליליים חזקים שעוקפים את הציון
    if checks.get("google", {}).get("closed"):
        is_active = False
        activity_score = max(0, activity_score - 40)
    if checks.get("website", {}).get("status_code") in (404,) and biz.get("website"):
        activity_score = max(0, activity_score - 15)

    # סיכום טקסטואלי
    if activity_score >= 70:
        summary = "עסק פעיל ומאומת — ליד איכותי"
    elif activity_score >= 45:
        summary = "סביר שהעסק פעיל — כדאי לפנות"
    elif activity_score >= 25:
        summary = "לא ברור אם פעיל — יש לבדוק ידנית"
    else:
        summary = "חשש שהעסק לא פעיל — עדיפות נמוכה"

    return {
        "activity_score": activity_score,
        "is_likely_active": is_active,
        "checks": checks,
        "reasons": reasons,
        "summary": summary,
    }


def verify_business_quick(biz: dict) -> dict:
    """אימות מהיר (בלי Google/WhatsApp) — לשימוש בסריקה המונית."""
    return verify_business(biz, quick=True)
