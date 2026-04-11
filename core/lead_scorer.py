"""
lead_scorer.py — דירוג מסחרי מתקדם של לידים (0-100).

ציון גבוה = הכי כדאי לפנות אליו ראשון.

שלוש רמות:
  🔥 HOT   70+  — פנה ראשון, צור דמו, שלח עכשיו
  ⚡ WARM  45-69 — כדאי, לאחר ה-HOT
  ❄️ COLD  <45  — נמוך בתור, שמור למאוחר יותר

פרמטרים:
  - אימות פעילות — האם העסק בכלל פעיל? (Google, WhatsApp, טלפון)
  - Google Reviews (הרבה ביקורות + אתר גרוע = HOT)
  - SEO score (ציון SEO נמוך = הזדמנות)
  - CMS platform (Wix/ישן = שדרוג)
  - Copyright year (אתר ישן = ליד חם)
  - Category value (high-ticket industries)
  - בונוס מקור: מדרג (עד 12), SerpApi/Google Maps (עד 8),
    מדריכי עסקים (3), B144 (2), פייסבוק ללא אתר (עד 20)
"""

from __future__ import annotations
import json


# ════════════════════════════════════════════════════════════════
#  קטגוריות בעלות ערך גבוה — עסקים שמשלמים עבור אתר
# ════════════════════════════════════════════════════════════════
HIGH_VALUE_CATEGORIES = {
    "מסעדה", "מסעדות", "קפה", "בית קפה", "מזון",
    "מוסך", "מוסכים", "גרג'", "רכב",
    "קוסמטיקה", "קוסמטיקאית", "מכון יופי", "ספא",
    "מספרה", "ספר", "תספורת",
    "עורך דין", "עו\"ד", "משרד עורכי דין",
    "רואה חשבון", "רו\"ח", "הנהלת חשבונות",
    "מרפאה", "קליניקה", "רופא", "רופא שיניים", "דנטלי",
    "אדריכל", "אדריכלות", "עיצוב פנים",
    "קבלן", "שיפוצים", "בנייה",
    "פיזיותרפיה", "נטורופת", "אלטרנטיבי",
    "מלון", "צימר", "אירוח",
    "גן אירועים", "אולם אירועים",
    "חשמלאי", "שרברב", "מיזוג",
    "גינון", "גננות", "נוף",
    "רופא וטרינר", "וטרינר",
    "אופטיקה", "אופטיקאי",
    "פסיכולוג", "פסיכותרפיסט",
}

MEDIUM_VALUE_CATEGORIES = {
    "חנות", "מכירות", "אופנה", "ביגוד",
    "ספורט", "כושר", "חדר כושר", "יוגה", "פילאטיס",
    "הובלות", "הובלה", "משלוחים",
    "ניקיון", "אחזקה",
    "מחשבים", "טכנאי", "סלולר",
    "פרחים", "פרחנות",
    "צילום", "צלם",
    "תכשיטים",
    "מורה", "שיעורים פרטיים", "קורס",
    "מוזיקה", "DJ",
}

# ── תחומים high-ticket (הלקוח גובה הרבה = ישלם על אתר) ──
HIGH_TICKET_INDUSTRIES = {
    "עורך דין", "עו\"ד", "משרד עורכי דין",
    "רואה חשבון", "רו\"ח",
    "רופא שיניים", "דנטלי", "אורתודנט",
    "כירופרקטיקה", "ניתוח", "פלסטיקה",
    "אדריכל", "אדריכלות",
    "קבלן", "שיפוצים", "בנייה",
    "גן אירועים", "אולם אירועים", "חתונות",
    "צימר", "מלון", "צימרים",
}


def _str(val) -> str:
    """Safe string conversion — handles None, NaN, and float values."""
    if val is None or (isinstance(val, float) and val != val):
        return ""
    return str(val)


def _category_score(biz: dict) -> tuple[int, str]:
    cat = (_str(biz.get("category")) + " " + _str(biz.get("search_query"))).lower()

    for kw in HIGH_VALUE_CATEGORIES:
        if kw.lower() in cat:
            return 15, f"קטגוריה בעלת ערך גבוה ({kw})"

    for kw in MEDIUM_VALUE_CATEGORIES:
        if kw.lower() in cat:
            return 8, f"קטגוריה בינונית ({kw})"

    return 4, "קטגוריה כללית"


def _is_high_ticket(biz: dict) -> bool:
    """בודק אם העסק בתחום high-ticket."""
    cat = (_str(biz.get("category")) + " " + _str(biz.get("search_query"))).lower()
    return any(kw.lower() in cat for kw in HIGH_TICKET_INDUSTRIES)


# ════════════════════════════════════════════════════════════════
#  חישוב ציון ליד — מתקדם
# ════════════════════════════════════════════════════════════════
def compute_lead_score(biz: dict) -> tuple[int, dict]:
    """
    מקבל dict עסק (ממסד הנתונים) ומחזיר:
      (lead_score: int 0-100, breakdown: dict עם פירוט הניקוד)
    """
    breakdown: dict[str, int] = {}

    # ── 1. הזדמנות האתר (עד 40 נקודות) ──────────────────────────
    has_website = bool(biz.get("has_website")) or bool(biz.get("website"))
    quality     = int(biz.get("quality_score") or 0)
    website_analyzed = quality > 0  # 0 = not analyzed, not "bad"

    if not has_website:
        breakdown["אין אתר כלל"] = 40
    elif not website_analyzed:
        # יש אתר אבל לא נותח — לא יודעים אם טוב או גרוע
        breakdown["יש אתר — לא נותח"] = 12
    elif quality <= 2:
        breakdown["אתר גרוע מאוד"] = 32
    elif quality <= 4:
        breakdown["אתר גרוע"] = 22
    elif quality <= 6:
        breakdown["אתר בינוני"] = 10
    elif quality <= 8:
        breakdown["אתר סביר"] = 4
    else:
        breakdown["אתר טוב"] = 0

    # ── 2. בעיות ספציפיות (עד 15 נקודות, רק אם אתר נותח) ──────
    if has_website and website_analyzed:
        issue_pts = 0
        if not biz.get("has_ssl"):        issue_pts += 4
        if not biz.get("is_responsive"):  issue_pts += 5
        if not biz.get("has_cta"):        issue_pts += 3
        if not biz.get("has_form"):       issue_pts += 2
        if not biz.get("has_analytics"):  issue_pts += 2
        if not biz.get("has_fb_pixel"):   issue_pts += 1
        ms = biz.get("load_time_ms")
        if ms and ms > 3000:              issue_pts += 3
        issue_pts = min(issue_pts, 15)
        if issue_pts:
            breakdown["בעיות באתר"] = issue_pts

    # ── 3. SEO score (עד 10 נקודות) ──────────────────────────────
    seo_score = biz.get("seo_score")
    if seo_score is not None:
        if seo_score < 25:
            breakdown["SEO גרוע מאוד"] = 10
        elif seo_score < 50:
            breakdown["SEO חלש"] = 7
        elif seo_score < 75:
            breakdown["SEO בינוני"] = 3
        # SEO 75+ = אין נקודות (האתר כבר מותאם)

    # ── 4. CMS & גיל האתר (עד 8 נקודות) ─────────────────────────
    cms = _str(biz.get("cms_platform"))
    if cms == "wix":
        breakdown["אתר Wix — מוגבל"] = 5
    elif cms in ("weebly", "godaddy_builder"):
        breakdown[f"אתר {cms} — מיושן"] = 6
    elif cms == "custom" and has_website:
        # אתר custom — יכול להיות טוב, יכול להיות ישן
        pass

    copyright_year = biz.get("copyright_year")
    if copyright_year and copyright_year < 2021:
        years_old = 2026 - copyright_year
        pts = min(years_old, 8)
        breakdown[f"אתר ישן ({copyright_year})"] = pts

    # ── 5. Google Reviews (עד 10 נקודות) ─────────────────────────
    reviews = biz.get("google_reviews") or 0
    rating = biz.get("google_rating") or 0
    if reviews > 50 and not has_website:
        breakdown["עסק פופולרי ללא אתר"] = 10
    elif reviews > 50 and has_website and quality <= 5:
        breakdown["עסק פופולרי עם אתר גרוע"] = 8
    elif reviews > 20:
        breakdown["עסק מוכר עם ביקורות"] = 5
    elif reviews > 10:
        breakdown["יש ביקורות Google"] = 3
    elif reviews == 0 and has_website:
        breakdown["אפס ביקורות — חשיפה נמוכה"] = 2

    # ── 6. ניתן ליצור קשר (עד 15 נקודות) ────────────────────────
    contact_pts = 0
    phone = _str(biz.get("phone"))
    if phone:
        # נייד (05X) שווה יותר — אפשר WA
        if phone.startswith("05"):
            contact_pts += 12
        else:
            contact_pts += 7
    if biz.get("email"):  contact_pts += 5
    if contact_pts:
        breakdown["ניתן ליצור קשר"] = min(contact_pts, 15)

    # ── 7. קטגוריה (עד 15 נקודות) ────────────────────────────────
    cat_pts, cat_reason = _category_score(biz)
    breakdown[cat_reason] = cat_pts

    # ── 8. בונוס high-ticket (עד 5 נקודות) ───────────────────────
    if _is_high_ticket(biz):
        breakdown["תחום high-ticket"] = 5

    # ── 9. עשירות מידע (עד 5 נקודות) / עונש חוסר מידע ────────────
    data_pts = 0
    if biz.get("address"):       data_pts += 1
    if biz.get("city"):          data_pts += 1
    if biz.get("facebook_url"):  data_pts += 1
    if biz.get("instagram_url"): data_pts += 1
    if biz.get("source"):        data_pts += 1
    if data_pts:
        breakdown["עשירות מידע"] = data_pts

    # עונש: חוסר מידע בסיסי — ליד עם שם+טלפון בלבד שווה פחות
    missing_penalty = 0
    if not biz.get("city") and not biz.get("address"):
        missing_penalty += 5
    if not biz.get("email"):
        missing_penalty += 3
    if not biz.get("category"):
        missing_penalty += 3
    if missing_penalty:
        breakdown["חוסר מידע (עיר/מייל/קטגוריה)"] = -missing_penalty

    # ── 10a. בונוס מקור איכותי (עד 12 נקודות) ─────────────────────
    # מקורות שמספקים לידים עם סיכוי סגירה גבוה יותר
    source = biz.get("source", "")

    # מדרג — אתר חוות דעת; דירוג גבוה = עסק פעיל ופופולרי
    if source == "midrag":
        midrag_rating = biz.get("google_rating") or 0
        midrag_reviews = biz.get("google_reviews") or 0
        if midrag_rating >= 9.0 and midrag_reviews >= 50:
            breakdown["מדרג — עסק מדורג גבוה עם הרבה חוות דעת"] = 12
        elif midrag_rating >= 8.0 and midrag_reviews >= 20:
            breakdown["מדרג — עסק מדורג טוב"] = 8
        elif midrag_reviews >= 10:
            breakdown["מדרג — עסק עם חוות דעת"] = 5
        else:
            breakdown["מדרג — עסק רשום"] = 3

    # Google Maps / SerpApi — מידע אמין ועשיר
    elif source == "google_maps":
        gm_reviews = biz.get("google_reviews") or 0
        if gm_reviews >= 50:
            breakdown["Google Maps — עסק פופולרי (SerpApi)"] = 8
        elif gm_reviews >= 10:
            breakdown["Google Maps — עסק עם ביקורות (SerpApi)"] = 5
        else:
            breakdown["Google Maps — ליד SerpApi"] = 3

    # מדריכי עסקים ישראליים — רשומים = פעילים
    elif source in ("easy", "igal", "freesearch", "2all", "directory_search"):
        breakdown["מדריך עסקים ישראלי — עסק רשום"] = 3

    # B144 — מאגר גדול ואמין
    elif source == "b144":
        breakdown["B144 — מקור אמין"] = 2

    # ── 10b. בונוס עסק פייסבוק ללא אתר (עד 20 נקודות) ──────────
    # עסקים שנמצאו דרך פייסבוק ואין להם אתר = הלידים הכי חמים
    if source == "facebook" and not has_website:
        # אין אתר בכלל — ליד מושלם
        breakdown["עסק פייסבוק ללא אתר — ליד מושלם"] = 20
    elif source == "facebook" and not biz.get("fb_snippet_has_website") and not has_website:
        breakdown["עסק פייסבוק — ככל הנראה ללא אתר"] = 15

    # בונוס עוקבים בפייסבוק (עסק פעיל + ללא אתר = ממש חם)
    fb_followers = biz.get("fb_followers") or 0
    if fb_followers > 2000 and not has_website:
        breakdown["דף פייסבוק פופולרי מאוד ללא אתר"] = 12
    elif fb_followers > 500 and not has_website:
        breakdown["דף פייסבוק פעיל ללא אתר"] = 7
    elif fb_followers > 200 and not has_website:
        breakdown["דף פייסבוק בינוני ללא אתר"] = 4

    # ── 10. PageSpeed bonus ──────────────────────────────────────
    ps_score = biz.get("pagespeed_score")
    if ps_score is not None and ps_score < 40:
        breakdown["PageSpeed גרוע"] = 5

    # ── 11. אימות פעילות (עד 20 נקודות / עונש עד -40) ───────────
    activity_score = biz.get("activity_score")
    is_active = biz.get("is_likely_active")
    if is_active == 0 or is_active is False:
        # עסק שזוהה כלא פעיל — עונש חמור
        breakdown["עסק כנראה לא פעיל"] = -40
    elif activity_score is not None:
        if activity_score >= 70:
            breakdown["עסק פעיל ומאומת"] = 20
        elif activity_score >= 45:
            breakdown["סביר שהעסק פעיל"] = 12
        elif activity_score >= 25:
            breakdown["לא ברור אם פעיל — לבדוק ידנית"] = -15
        else:
            breakdown["חשש — עסק לא פעיל"] = -35
    else:
        # לא נבדק כלל — לא מאומת, מוריד קצת
        breakdown["פעילות לא נבדקה"] = -5

    # ── עונשים ────────────────────────────────────────────────────
    if biz.get("whatsapp_sent"):
        breakdown["כבר נשלח WA"] = -25
    if biz.get("email_sent"):
        breakdown["כבר נשלח מייל"] = -15
    if biz.get("blacklisted"):
        breakdown["ב-blacklist"] = -100

    # בונוס: כבר יצרנו לו דמו — השקענו, כדאי לסגור
    if biz.get("demo_public_url") or biz.get("demo_html_path"):
        breakdown["דמו כבר נוצר"] = 5

    # בונוס: הלקוח הגיב
    if biz.get("last_response"):
        breakdown["הלקוח הגיב"] = 10

    # ── סיכום ────────────────────────────────────────────────────
    total = max(0, min(100, sum(breakdown.values())))
    return total, breakdown


def score_tier(score: int) -> tuple[str, str]:
    """מחזיר (emoji_label, color_class)."""
    if score >= 70:
        return "🔥 HOT",  "hot"
    if score >= 45:
        return "⚡ WARM", "warm"
    return "❄️ COLD",     "cold"


def score_tier_hebrew(score: int) -> str:
    if score >= 70: return "🔥 חם"
    if score >= 45: return "⚡ בינוני"
    return "❄️ קר"


def rescore_all() -> int:
    """מחשב מחדש lead_score לכל העסקים במסד הנתונים."""
    import sqlite3
    from config import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM businesses").fetchall()
    updated = 0
    for row in rows:
        biz = dict(row)
        score, _ = compute_lead_score(biz)
        conn.execute(
            "UPDATE businesses SET lead_score=? WHERE id=?",
            (score, biz["id"])
        )
        updated += 1
    conn.commit()
    conn.close()
    return updated
