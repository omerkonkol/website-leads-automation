"""
outreach_engine.py — מנוע outreach אוטומטי ומחוכם.

פיצ'רים:
  - Drip Campaign: יום 1 → WhatsApp, יום 3 → Email, יום 7 → follow-up
  - A/B Testing: 2 גרסאות הודעה, מעקב איזו עובדת יותר
  - Smart Timing: שליחה בשעות אופטימליות לפי קטגוריה
  - Blacklist: עסקים שביקשו להסיר לא מקבלים הודעות
  - Personalization: ציטוט ביקורות, בעיות ספציפיות
"""

import random
from datetime import datetime, timedelta
from database import (
    get_conn, schedule_drip, get_pending_drips, mark_drip_sent,
    blacklist_business, update_business, mark_sent, increment_ab,
    update_pipeline_stage,
)
from pitch_builder import build_whatsapp_pitch, build_full_pitch


# ════════════════════════════════════════════════════════════════
#  Smart Timing — שעות אופטימליות לפי קטגוריה
# ════════════════════════════════════════════════════════════════
OPTIMAL_HOURS = {
    # מסעדות/קפה — אחרי שעות עבודה (לא בשעות לחץ)
    "מסעדה":    (15, 17),
    "קפה":      (15, 17),
    "בית קפה":  (15, 17),
    # שירותים מקצועיים — בוקר
    "עורך דין": (9, 11),
    "רואה חשבון": (9, 11),
    "רופא":     (8, 10),
    "מרפאה":    (8, 10),
    # שירותי בית — צהריים
    "שיפוצים":  (12, 14),
    "חשמלאי":   (12, 14),
    "שרברב":    (12, 14),
    "מוסך":     (12, 14),
    # יופי — לפני הצהריים
    "קוסמטיקה": (10, 12),
    "מספרה":    (10, 12),
    "ספא":      (10, 12),
}

DEFAULT_HOURS = (10, 14)  # ברירת מחדל


def get_optimal_send_time(category: str) -> tuple[int, int]:
    """מחזיר (hour_start, hour_end) אופטימלי לשליחה."""
    cat_lower = (category or "").lower()
    for key, hours in OPTIMAL_HOURS.items():
        if key in cat_lower:
            return hours
    return DEFAULT_HOURS


def is_good_time_to_send(category: str) -> bool:
    """בודק אם עכשיו זמן טוב לשלוח הודעה לקטגוריה זו."""
    now = datetime.now()
    # לא בשבת
    if now.weekday() == 5:  # Saturday
        return False
    # לא לפני 8 או אחרי 20
    if now.hour < 8 or now.hour > 20:
        return False
    h_start, h_end = get_optimal_send_time(category)
    return h_start <= now.hour <= h_end


def next_optimal_time(category: str) -> datetime:
    """מחזיר את הזמן האופטימלי הבא לשליחה."""
    now = datetime.now()
    h_start, h_end = get_optimal_send_time(category)

    target = now.replace(hour=h_start, minute=random.randint(0, 30), second=0)
    if target <= now:
        target += timedelta(days=1)

    # דלג על שבת
    while target.weekday() == 5:
        target += timedelta(days=1)

    return target


# ════════════════════════════════════════════════════════════════
#  A/B Testing — בחירת variant
# ════════════════════════════════════════════════════════════════
def choose_variant() -> str:
    """בוחר variant A או B באופן אקראי (50/50)."""
    return random.choice(["A", "B"])


def build_pitch_variant(biz: dict, variant: str, channel: str = "whatsapp") -> str:
    """
    מייצר הודעה בגרסה A או B.
    A = הגרסה הסטנדרטית
    B = גרסה קצרה וישירה יותר
    """
    from config import YOUR_NAME, YOUR_PHONE, YOUR_BIO

    if channel == "whatsapp":
        if variant == "A":
            return build_whatsapp_pitch(biz)
        else:
            # גרסה B — קצרה יותר, ישירה יותר
            name = biz.get("name", "")
            issues = []
            if not biz.get("has_website"):
                issues.append("אין לכם אתר")
            else:
                if not biz.get("is_responsive"):
                    issues.append("האתר לא מותאם לנייד")
                if not biz.get("has_ssl"):
                    issues.append("האתר לא מאובטח")
                if not biz.get("has_cta"):
                    issues.append("אין כפתורי יצירת קשר")

            issue_text = issues[0] if issues else "האתר שלכם יכול להשתפר"

            return (
                f"שלום {name},\n\n"
                f"שמתי לב ש{issue_text}.\n\n"
                f"אני בונה אתרים לעסקים קטנים — הכנתי דוגמה עבורכם:\n"
                f"{{DEMO_URL}}\n\n"
                f"מעוניינים לשמוע עוד?\n\n"
                f"{YOUR_NAME} | {YOUR_PHONE}"
            )
    else:
        return build_full_pitch(biz)


# ════════════════════════════════════════════════════════════════
#  Drip Campaign — הגדרת רצפים
# ════════════════════════════════════════════════════════════════
def create_default_drip(biz: dict) -> list[dict]:
    """
    יוצר drip campaign סטנדרטי:
      שלב 1 (יום 0): WhatsApp — פנייה ראשונה
      שלב 2 (יום 3): Email — פנייה מלאה
      שלב 3 (יום 7): WhatsApp — follow-up
    """
    variant = choose_variant()
    category = biz.get("category") or biz.get("search_query") or ""

    steps = [
        {
            "step": 1,
            "channel": "whatsapp",
            "delay_days": 0,
            "message": build_pitch_variant(biz, variant, "whatsapp"),
        },
        {
            "step": 2,
            "channel": "email",
            "delay_days": 3,
            "message": build_pitch_variant(biz, variant, "email"),
        },
        {
            "step": 3,
            "channel": "whatsapp",
            "delay_days": 7,
            "message": _build_followup(biz),
        },
    ]
    return steps


def _build_followup(biz: dict) -> str:
    """הודעת follow-up — קצרה ואישית."""
    from config import YOUR_NAME, YOUR_PHONE
    name = biz.get("name", "")
    return (
        f"שלום {name},\n\n"
        f"אני {YOUR_NAME} — שלחתי לכם הודעה לפני כמה ימים לגבי האתר.\n\n"
        f"רציתי לבדוק אם הייתם מעוניינים לשמוע עוד?\n"
        f"אשמח לענות על כל שאלה.\n\n"
        f"{YOUR_NAME} | {YOUR_PHONE}"
    )


def setup_drip_for_business(business_id: int, biz: dict):
    """מגדיר drip campaign לעסק ומעדכן pipeline."""
    steps = create_default_drip(biz)
    variant = choose_variant()

    # עדכן variant בעסק
    update_business(business_id, {"pitch_variant": variant})

    # תזמן את הצעדים
    schedule_drip(business_id, steps)

    # עדכן pipeline stage
    update_pipeline_stage(business_id, "contacted")


# ════════════════════════════════════════════════════════════════
#  מעבד drips ממתינים — להרצה מ-scheduler
# ════════════════════════════════════════════════════════════════
def process_pending_drips() -> int:
    """
    מעבד את כל ה-drip messages הממתינים.
    מחזיר כמה נשלחו.
    """
    pending = get_pending_drips()
    sent_count = 0

    for drip in pending:
        # בדוק blacklist
        if drip.get("blacklisted"):
            conn = get_conn()
            conn.execute(
                "UPDATE drip_campaigns SET status='cancelled' WHERE id=?",
                (drip["id"],)
            )
            conn.commit()
            conn.close()
            continue

        channel = drip["channel"]
        business_id = drip["business_id"]

        # בדוק אם הלקוח כבר הגיב (לא צריך follow-up)
        conn = get_conn()
        biz = conn.execute(
            "SELECT last_response, pipeline_stage FROM businesses WHERE id=?",
            (business_id,)
        ).fetchone()
        conn.close()

        if biz and biz["last_response"]:
            # הלקוח הגיב — דלג
            mark_drip_sent(drip["id"])
            continue

        if biz and biz["pipeline_stage"] in ("closed_won", "closed_lost"):
            mark_drip_sent(drip["id"])
            continue

        # שלח את ההודעה
        try:
            if channel == "whatsapp":
                _send_whatsapp_drip(drip)
            elif channel == "email":
                _send_email_drip(drip)

            mark_drip_sent(drip["id"])
            mark_sent(business_id, channel, drip.get("message", ""))

            # עדכן A/B stats
            variant = "A"  # default
            conn = get_conn()
            row = conn.execute("SELECT pitch_variant FROM businesses WHERE id=?", (business_id,)).fetchone()
            conn.close()
            if row:
                variant = row["pitch_variant"] or "A"
            increment_ab("default", variant, "sent_count")

            sent_count += 1
            print(f"  ✅ Drip #{drip['id']} sent ({channel}) to {drip.get('name', '?')}")

        except Exception as e:
            print(f"  ❌ Drip #{drip['id']} failed: {e}")

    return sent_count


def _send_whatsapp_drip(drip: dict):
    """שולח הודעת WhatsApp מ-drip campaign."""
    from whatsapp_sender import send_single_message
    phone = drip.get("phone", "")
    message = drip.get("message", "")
    if phone and message:
        send_single_message(phone, message)


def _send_email_drip(drip: dict):
    """שולח מייל מ-drip campaign."""
    from email_sender import send_single_email
    email = drip.get("email", "")
    name = drip.get("name", "")
    message = drip.get("message", "")
    if email and message:
        send_single_email(email, name, message)


# ════════════════════════════════════════════════════════════════
#  Response Tracking
# ════════════════════════════════════════════════════════════════
def record_response(business_id: int, response: str, interested: bool = False):
    """מתעד תגובה מלקוח ומעדכן pipeline."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    updates = {
        "last_response": response,
        "response_date": now,
    }

    if interested:
        updates["pipeline_stage"] = "interested"
        # עדכן A/B stats
        conn = get_conn()
        row = conn.execute("SELECT pitch_variant FROM businesses WHERE id=?", (business_id,)).fetchone()
        conn.close()
        if row:
            increment_ab("default", row["pitch_variant"] or "A", "reply_count")
    else:
        updates["pipeline_stage"] = "closed_lost"
        # בדוק אם ביקש להסיר
        decline_words = ["לא מעוניין", "הסר", "תפסיק", "חסום", "spam", "הורד"]
        if any(w in response.lower() for w in decline_words):
            blacklist_business(business_id, f"לקוח ביקש: {response[:50]}")

    update_business(business_id, updates)

    # רשום ב-outreach_log
    conn = get_conn()
    conn.execute(
        """INSERT INTO outreach_log (business_id, channel, status, message, sent_at)
           VALUES (?, 'response', ?, ?, ?)""",
        (business_id, "interested" if interested else "not_interested", response, now)
    )
    conn.commit()
    conn.close()
