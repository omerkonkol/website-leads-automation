"""
lead_scorer.py — דירוג מסחרי של לידים (0-100).
מחשב כמה שווה להשקיע בכל עסק: האם לבנות לו דמו, לשלוח הודעה, לתעדף.

ציון גבוה = הכי כדאי לפנות אליו ראשון.

שלוש רמות:
  🔥 HOT   70+  — פנה ראשון, צור דמו, שלח עכשיו
  ⚡ WARM  45-69 — כדאי, לאחר ה-HOT
  ❄️ COLD  <45  — נמוך בתור, שמור למאוחר יותר
"""

from __future__ import annotations


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
}


def _category_score(biz: dict) -> tuple[int, str]:
    """מחזיר (ניקוד, תיאור)."""
    cat = (
        (biz.get("category") or "") + " " +
        (biz.get("search_query") or "")
    ).lower()

    for kw in HIGH_VALUE_CATEGORIES:
        if kw.lower() in cat:
            return 15, f"קטגוריה בעלת ערך גבוה ({kw})"

    for kw in MEDIUM_VALUE_CATEGORIES:
        if kw.lower() in cat:
            return 8, f"קטגוריה בינונית ({kw})"

    return 4, "קטגוריה כללית"


# ════════════════════════════════════════════════════════════════
#  חישוב ציון ליד
# ════════════════════════════════════════════════════════════════
def compute_lead_score(biz: dict) -> tuple[int, dict]:
    """
    מקבל dict עסק (ממסד הנתונים) ומחזיר:
      (lead_score: int 0-100, breakdown: dict עם פירוט הניקוד)
    """
    breakdown: dict[str, int] = {}

    # ── 1. הזדמנות האתר (עד 45 נקודות) ──────────────────────────
    has_website  = bool(biz.get("has_website"))
    quality      = int(biz.get("quality_score") or 0)

    if not has_website:
        breakdown["אין אתר כלל"] = 45
    elif quality <= 2:
        breakdown["אתר גרוע מאוד"] = 35
    elif quality <= 4:
        breakdown["אתר גרוע"] = 25
    elif quality <= 6:
        breakdown["אתר בינוני"] = 12
    elif quality <= 8:
        breakdown["אתר סביר"] = 5
    else:
        breakdown["אתר טוב"] = 0

    # ── 2. בעיות ספציפיות (עד 20 נקודות, רק אם יש אתר) ──────────
    if has_website:
        issue_pts = 0
        if not biz.get("has_ssl"):        issue_pts += 5
        if not biz.get("is_responsive"):  issue_pts += 7
        if not biz.get("has_cta"):        issue_pts += 4
        if not biz.get("has_form"):       issue_pts += 3
        if not biz.get("has_analytics"):  issue_pts += 3
        if not biz.get("has_fb_pixel"):   issue_pts += 2
        ms = biz.get("load_time_ms")
        if ms and ms > 3000:              issue_pts += 5
        issue_pts = min(issue_pts, 20)
        if issue_pts:
            breakdown["בעיות באתר"] = issue_pts

    # ── 3. ניתן ליצור קשר (עד 20 נקודות) ────────────────────────
    contact_pts = 0
    if biz.get("phone"):  contact_pts += 12
    if biz.get("email"):  contact_pts += 8
    if contact_pts:
        breakdown["ניתן ליצור קשר"] = contact_pts

    # ── 4. קטגוריה (עד 15 נקודות) ────────────────────────────────
    cat_pts, cat_reason = _category_score(biz)
    breakdown[cat_reason] = cat_pts

    # ── 5. עשירות מידע (עד 5 נקודות) ────────────────────────────
    data_pts = 0
    if biz.get("address"):      data_pts += 2
    if biz.get("city"):         data_pts += 1
    if biz.get("facebook_url"): data_pts += 1
    if biz.get("source"):       data_pts += 1
    if data_pts:
        breakdown["עשירות מידע"] = data_pts

    # ── 6. עונשים ────────────────────────────────────────────────
    if biz.get("whatsapp_sent"):
        breakdown["כבר נשלח WA"] = -30
    if biz.get("email_sent"):
        breakdown["כבר נשלח מייל"] = -20

    # בונוס: כבר יצרנו לו דמו — השקענו, כדאי לסגור
    if biz.get("demo_public_url") or biz.get("demo_html_path"):
        breakdown["דמו כבר נוצר"] = 5

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
    """
    מחשב מחדש lead_score לכל העסקים במסד הנתונים.
    מחזיר כמה עסקים עודכנו.
    """
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
