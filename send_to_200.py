"""
send_to_200.py — שולח הודעות לידים דרך WhatsApp API עד 200 הודעות היום.
הרץ: py send_to_200.py
דרישה: שרת ה-API רץ — cd whatsapp-api && npm start
"""

import sys
import requests
import sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

API_URL = "http://localhost:3000"
DAILY_TARGET = 200
DB_PATH = "leads.db"


def get_sent_today() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM outreach_log WHERE DATE(sent_at) = ? AND channel = 'whatsapp' AND status = 'sent'",
        (today,),
    ).fetchone()
    conn.close()
    return row["cnt"]


def check_server():
    try:
        r = requests.get(f"{API_URL}/api/health", timeout=5)
        data = r.json()
        if not data.get("whatsappReady"):
            print("❌ WhatsApp לא מחובר. סרוק QR בטרמינל של השרת.")
            return False
        print(f"✅ שרת מחובר ({data.get('accountCount', '?')} חשבונות)")
        return True
    except requests.ConnectionError:
        print("❌ שרת לא רץ. הפעל: cd whatsapp-api && npm start")
        return False


def main():
    sent_today = get_sent_today()
    remaining = DAILY_TARGET - sent_today

    print(f"נשלחו היום: {sent_today}")
    print(f"יעד יומי:   {DAILY_TARGET}")
    print(f"נדרש עוד:   {remaining}")

    if remaining <= 0:
        print("✅ הגענו ל-200 הודעות היום!")
        return

    if not check_server():
        return

    print(f"\nשולח {remaining} הודעות דרך WhatsApp API...")
    try:
        resp = requests.post(
            f"{API_URL}/api/leads-campaign/send",
            json={"dailyLimit": DAILY_TARGET},
            timeout=7200,
        )
    except requests.Timeout:
        print("⏱ הקמפיין עדיין רץ (timeout) — בדוק בלוג השרת.")
        return
    except requests.ConnectionError:
        print("❌ חיבור לשרת נותק.")
        return

    if resp.status_code == 200:
        data = resp.json()
        print(f"\n✅ נשלחו: {data.get('sent', 0)}")
        print(f"❌ נכשלו:  {data.get('failed', 0)}")
        print(f"📊 סהכ היום: {data.get('dailySent', '?')}")
    elif resp.status_code == 429:
        print(f"⛔ הגבלה יומית: {resp.json()}")
    elif resp.status_code == 503:
        print("❌ WhatsApp לא מחובר — סרוק QR.")
    else:
        print(f"❌ שגיאה {resp.status_code}: {resp.text[:300]}")


if __name__ == "__main__":
    main()
