"""
scheduler.py — תזמון אוטומטי של סריקות, ניתוח, ו-follow-ups.

הרצה:
  python scheduler.py              — הרצה חד-פעמית של כל המשימות
  python scheduler.py --daemon     — רץ ברקע עם לולאת תזמון

משימות:
  1. סריקה יומית (06:00) — חיפוש עסקים חדשים
  2. re-analysis שבועי (שני 04:00) — ניתוח מחדש של לידים ישנים
  3. עיבוד drip campaigns — שליחת הודעות מתוזמנות
  4. Telegram alert — כשנמצאו 10+ לידים HOT חדשים
  5. Auto follow-up — אם לא ענו תוך 3 ימים
"""

import sys
import time
import json
import argparse
import sqlite3
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8")


# ════════════════════════════════════════════════════════════════
#  Telegram Bot — התראות
# ════════════════════════════════════════════════════════════════
def send_telegram(message: str, bot_token: str = "", chat_id: str = "") -> bool:
    """שולח הודעה דרך Telegram Bot."""
    if not bot_token or not chat_id:
        try:
            from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
            bot_token = bot_token or TELEGRAM_BOT_TOKEN
            chat_id = chat_id or TELEGRAM_CHAT_ID
        except (ImportError, AttributeError):
            return False

    if not bot_token or not chat_id:
        return False

    import requests
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
        }, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"  [Telegram] שגיאה: {e}")
        return False


def alert_hot_leads(min_count: int = 10):
    """שולח התראה אם נמצאו מספיק לידים HOT חדשים."""
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # לידים HOT שנוצרו ב-24 שעות האחרונות
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    rows = conn.execute(
        """SELECT name, lead_score, city, category FROM businesses
           WHERE lead_score >= 70 AND created_at >= ? AND blacklisted=0
           ORDER BY lead_score DESC LIMIT 20""",
        (yesterday,)
    ).fetchall()
    conn.close()

    if len(rows) >= min_count:
        msg = f"🔥 <b>{len(rows)} לידים HOT חדשים!</b>\n\n"
        for r in rows[:10]:
            msg += f"• {r['name']} ({r['city'] or r['category'] or '—'}) — {r['lead_score']}pt\n"
        if len(rows) > 10:
            msg += f"\n...ועוד {len(rows)-10} נוספים"
        msg += f"\n\n📊 פתח את הדשבורד לפרטים מלאים"
        send_telegram(msg)
        print(f"  [Telegram] נשלחה התראה: {len(rows)} לידים HOT")


# ════════════════════════════════════════════════════════════════
#  משימה 1: סריקה יומית
# ════════════════════════════════════════════════════════════════
def run_daily_scrape():
    """מריץ סריקת עסקים חדשים לכל השאילתות."""
    print(f"\n{'='*60}")
    print(f"  [{datetime.now():%H:%M}] סריקה יומית")
    print(f"{'='*60}")

    from main import run_scrape_and_analyze
    run_scrape_and_analyze()
    alert_hot_leads()


# ════════════════════════════════════════════════════════════════
#  משימה 2: Re-analysis שבועי
# ════════════════════════════════════════════════════════════════
def run_weekly_reanalysis():
    """ניתוח מחדש של כל הלידים — בדיקה אם האתר השתנה."""
    print(f"\n{'='*60}")
    print(f"  [{datetime.now():%H:%M}] ניתוח מחדש שבועי")
    print(f"{'='*60}")

    from config import DB_PATH
    from analyzer import analyze_website
    from lead_scorer import compute_lead_score

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT id, name, website FROM businesses
           WHERE blacklisted=0 AND pipeline_stage NOT IN ('closed_won','closed_lost')
           ORDER BY lead_score DESC"""
    ).fetchall()

    updated = 0
    for row in rows:
        if not row["website"]:
            continue
        print(f"  🔎 מנתח מחדש: {row['name']}...")
        try:
            analysis = analyze_website(row["website"])
            updates = {
                k: analysis[k] for k in [
                    "has_ssl", "is_responsive", "has_cta", "has_form",
                    "has_fb_pixel", "has_analytics", "load_time_ms", "quality_score",
                    "has_title_tag", "has_meta_desc", "has_h1", "has_robots_txt",
                    "has_sitemap", "seo_score", "cms_platform", "copyright_year",
                ]
                if k in analysis and analysis[k] is not None
            }
            updates["issues"] = json.dumps(analysis["issues"], ensure_ascii=False)
            updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # עדכן DB
            fields = ", ".join(f"{k}=?" for k in updates)
            values = list(updates.values()) + [row["id"]]
            conn.execute(f"UPDATE businesses SET {fields} WHERE id=?", values)

            # חשב ציון מחדש
            biz = dict(conn.execute("SELECT * FROM businesses WHERE id=?", (row["id"],)).fetchone())
            score, _ = compute_lead_score(biz)
            conn.execute("UPDATE businesses SET lead_score=? WHERE id=?", (score, row["id"]))
            updated += 1

        except Exception as e:
            print(f"    שגיאה: {e}")

        time.sleep(0.5)

    conn.commit()
    conn.close()
    print(f"\n  ✅ ניתוח מחדש הסתיים: {updated} עסקים עודכנו")


# ════════════════════════════════════════════════════════════════
#  משימה 3: עיבוד drip campaigns
# ════════════════════════════════════════════════════════════════
def run_drip_processing():
    """מעבד drip messages ממתינים."""
    print(f"\n  [{datetime.now():%H:%M}] מעבד drip campaigns...")
    from outreach_engine import process_pending_drips
    sent = process_pending_drips()
    print(f"  ✅ נשלחו {sent} הודעות drip")


# ════════════════════════════════════════════════════════════════
#  משימה 4: Auto follow-up
# ════════════════════════════════════════════════════════════════
def run_auto_followup():
    """שולח follow-up אוטומטי לעסקים שלא ענו תוך 3 ימים."""
    print(f"\n  [{datetime.now():%H:%M}] בודק follow-ups...")
    from database import get_followups_due
    due = get_followups_due()

    if not due:
        print("  אין follow-ups ממתינים.")
        return

    print(f"  נמצאו {len(due)} follow-ups")
    # לוגיקת שליחה בפועל נעשית דרך drip campaigns
    # כאן רק מודיע ב-Telegram
    if len(due) >= 5:
        msg = f"📅 <b>{len(due)} follow-ups ממתינים להיום!</b>\n"
        for b in due[:5]:
            msg += f"• {b['name']} — ציון {b.get('lead_score', 0)}\n"
        send_telegram(msg)


# ════════════════════════════════════════════════════════════════
#  Daemon mode — לולאת תזמון
# ════════════════════════════════════════════════════════════════
def run_daemon():
    """רץ ברקע ומריץ משימות לפי תזמון."""
    from database import init_db
    init_db()

    print("\n" + "═"*60)
    print("  Scheduler — רץ ברקע")
    print("  Ctrl+C להפסקה")
    print("═"*60)

    last_daily = None
    last_weekly = None

    while True:
        now = datetime.now()
        current_day = now.strftime("%Y-%m-%d")
        current_weekday = now.weekday()  # 0=Monday

        try:
            # סריקה יומית — 06:00
            if now.hour == 6 and last_daily != current_day:
                run_daily_scrape()
                last_daily = current_day

            # ניתוח מחדש שבועי — יום שני 04:00
            if current_weekday == 0 and now.hour == 4 and last_weekly != current_day:
                run_weekly_reanalysis()
                last_weekly = current_day

            # עיבוד drips — כל שעה
            if now.minute == 0:
                run_drip_processing()
                run_auto_followup()

        except Exception as e:
            print(f"  [Scheduler Error] {e}")

        time.sleep(60)  # בדוק כל דקה


# ════════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════════
def run_all_now():
    """הרצה חד-פעמית של כל המשימות."""
    from database import init_db
    init_db()

    print("מריץ את כל המשימות עכשיו...\n")
    run_daily_scrape()
    run_drip_processing()
    run_auto_followup()
    print("\n✅ הכל הסתיים!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lead System Scheduler")
    parser.add_argument("--daemon", action="store_true", help="רוץ ברקע עם לולאת תזמון")
    parser.add_argument("--scrape", action="store_true", help="הרץ סריקה עכשיו")
    parser.add_argument("--reanalyze", action="store_true", help="הרץ ניתוח מחדש")
    parser.add_argument("--drips", action="store_true", help="עבד drip campaigns")
    parser.add_argument("--alert", action="store_true", help="שלח Telegram alert")
    args = parser.parse_args()

    if args.daemon:
        run_daemon()
    elif args.scrape:
        from database import init_db; init_db()
        run_daily_scrape()
    elif args.reanalyze:
        from database import init_db; init_db()
        run_weekly_reanalysis()
    elif args.drips:
        from database import init_db; init_db()
        run_drip_processing()
    elif args.alert:
        alert_hot_leads(min_count=1)
    else:
        run_all_now()
