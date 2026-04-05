"""
database.py — ניהול SQLite לכל הלידים.
מונע שליחה כפולה ושומר היסטוריה מלאה.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_PATH, EXCEL_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """יוצר את טבלאות הבסיס אם לא קיימות, ומוסיף עמודות חסרות ל-DB קיים."""
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS businesses (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            name             TEXT NOT NULL,
            -- קשר ישיר
            phone            TEXT,
            phone2           TEXT,
            email            TEXT,
            website          TEXT,
            address          TEXT,
            city             TEXT,
            -- מקור
            category         TEXT,
            search_query     TEXT,
            source           TEXT,   -- 'google_maps' / 'dapei_zahav' / 'facebook' / 'wolt' וכו'
            -- רשתות חברתיות (לשימוש בגנרטור האתר)
            facebook_url     TEXT,
            instagram_url    TEXT,
            -- ניתוח אתר
            has_website      INTEGER DEFAULT 0,
            has_ssl          INTEGER DEFAULT 0,
            is_responsive    INTEGER DEFAULT 0,
            has_cta          INTEGER DEFAULT 0,
            has_form         INTEGER DEFAULT 0,
            has_fb_pixel     INTEGER DEFAULT 0,
            has_analytics    INTEGER DEFAULT 0,
            load_time_ms     INTEGER,
            quality_score    INTEGER DEFAULT 0,
            issues           TEXT,
            -- אתר דמו שנוצר
            demo_html_path   TEXT,
            demo_public_url  TEXT,
            -- שליחות
            whatsapp_sent    INTEGER DEFAULT 0,
            whatsapp_sent_at TEXT,
            email_sent       INTEGER DEFAULT 0,
            email_sent_at    TEXT,
            -- מטא
            created_at       TEXT DEFAULT (datetime('now','localtime')),
            notes            TEXT,
            extra_info       TEXT    -- מידע נוסף חופשי לשימוש בגנרטור
        );

        CREATE TABLE IF NOT EXISTS outreach_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            channel     TEXT,   -- 'whatsapp' / 'email'
            status      TEXT,   -- 'sent' / 'failed'
            message     TEXT,
            sent_at     TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        );
    """)
    conn.commit()

    # ── Migration: הוסף עמודות חסרות ל-DB קיים ──
    new_columns = [
        ("phone2",          "TEXT"),
        ("city",            "TEXT"),
        ("source",          "TEXT"),
        ("facebook_url",    "TEXT"),
        ("instagram_url",   "TEXT"),
        ("demo_html_path",  "TEXT"),
        ("demo_public_url", "TEXT"),
        ("extra_info",      "TEXT"),
    ]
    existing = {row[1] for row in c.execute("PRAGMA table_info(businesses)").fetchall()}
    for col, col_type in new_columns:
        if col not in existing:
            c.execute(f"ALTER TABLE businesses ADD COLUMN {col} {col_type}")
    conn.commit()
    conn.close()
    print(f"[DB] מסד נתונים מוכן: {DB_PATH}")


def business_exists(phone: str, name: str) -> bool:
    """בודק אם עסק כבר קיים (לפי טלפון או שם מדויק)."""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT id FROM businesses WHERE phone=? OR name=? LIMIT 1",
        (phone or "", name)
    )
    row = c.fetchone()
    conn.close()
    return row is not None


def insert_business(data: dict) -> int:
    """מוסיף עסק חדש ומחזיר את ה-id שנוצר."""
    conn = get_conn()
    c = conn.cursor()
    # ערכי ברירת מחדל לשדות שאולי חסרים
    row = {
        "name": "", "phone": "", "phone2": "", "email": "",
        "website": "", "address": "", "city": "",
        "category": "", "search_query": "", "source": "",
        "facebook_url": "", "instagram_url": "",
        "has_website": 0, "has_ssl": 0, "is_responsive": 0,
        "has_cta": 0, "has_form": 0, "has_fb_pixel": 0, "has_analytics": 0,
        "load_time_ms": None, "quality_score": 0, "issues": "[]",
        "extra_info": "",
    }
    row.update(data)
    c.execute("""
        INSERT INTO businesses
            (name, phone, phone2, email, website, address, city,
             category, search_query, source, facebook_url, instagram_url,
             has_website, has_ssl, is_responsive, has_cta, has_form,
             has_fb_pixel, has_analytics, load_time_ms, quality_score, issues,
             extra_info)
        VALUES
            (:name, :phone, :phone2, :email, :website, :address, :city,
             :category, :search_query, :source, :facebook_url, :instagram_url,
             :has_website, :has_ssl, :is_responsive, :has_cta, :has_form,
             :has_fb_pixel, :has_analytics, :load_time_ms, :quality_score, :issues,
             :extra_info)
    """, row)
    new_id = c.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_business(business_id: int, updates: dict):
    """עדכון שדות של עסק קיים."""
    if not updates:
        return
    fields = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [business_id]
    conn = get_conn()
    conn.execute(f"UPDATE businesses SET {fields} WHERE id=?", values)
    conn.commit()
    conn.close()


def mark_sent(business_id: int, channel: str, message: str = "", status: str = "sent"):
    """מסמן שליחה ומוסיף רשומה ל-outreach_log."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    # עדכן טבלת businesses
    if channel == "whatsapp":
        conn.execute(
            "UPDATE businesses SET whatsapp_sent=1, whatsapp_sent_at=? WHERE id=?",
            (now, business_id)
        )
    elif channel == "email":
        conn.execute(
            "UPDATE businesses SET email_sent=1, email_sent_at=? WHERE id=?",
            (now, business_id)
        )
    # הוסף ל-log
    conn.execute(
        "INSERT INTO outreach_log (business_id, channel, status, message, sent_at) VALUES (?,?,?,?,?)",
        (business_id, channel, status, message, now)
    )
    conn.commit()
    conn.close()


def get_pending_outreach(min_score: int = 4, channel: str = "whatsapp") -> list:
    """
    מחזיר רשימת עסקים שעדיין לא נשלחה אליהם הודעה בערוץ הנבחר,
    עם ציון מינימלי.
    """
    conn = get_conn()
    c = conn.cursor()
    if channel == "whatsapp":
        sent_col = "whatsapp_sent"
    else:
        sent_col = "email_sent"
    c.execute(f"""
        SELECT * FROM businesses
        WHERE quality_score >= ? AND {sent_col} = 0 AND phone IS NOT NULL AND phone != ''
        ORDER BY quality_score DESC
    """, (min_score,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_all_businesses() -> list:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM businesses ORDER BY quality_score DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def export_to_excel():
    """מייצא את כל הנתונים ל-Excel."""
    businesses = get_all_businesses()
    if not businesses:
        print("[DB] אין נתונים לייצוא.")
        return
    df = pd.DataFrame(businesses)
    # עמודות בעברית לקריאות
    rename_map = {
        "id": "מזהה",
        "name": "שם עסק",
        "phone": "טלפון",
        "email": "מייל",
        "website": "אתר",
        "address": "כתובת",
        "category": "קטגוריה",
        "quality_score": "ציון (1-10)",
        "issues": "בעיות שנמצאו",
        "has_website": "יש אתר",
        "has_ssl": "SSL",
        "is_responsive": "מותאם נייד",
        "has_cta": "יש CTA",
        "has_form": "יש טופס",
        "has_fb_pixel": "Facebook Pixel",
        "has_analytics": "Google Analytics",
        "load_time_ms": "זמן טעינה (ms)",
        "whatsapp_sent": "WhatsApp נשלח",
        "whatsapp_sent_at": "תאריך WhatsApp",
        "email_sent": "מייל נשלח",
        "email_sent_at": "תאריך מייל",
        "created_at": "נוסף בתאריך",
        "notes": "הערות",
    }
    df.rename(columns=rename_map, inplace=True)
    df.to_excel(EXCEL_PATH, index=False)
    print(f"[DB] יוצא ל: {EXCEL_PATH}  ({len(df)} שורות)")


def get_stats() -> dict:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM businesses")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM businesses WHERE has_website=0")
    no_site = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM businesses WHERE quality_score <= 5 AND has_website=1")
    bad_site = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM businesses WHERE whatsapp_sent=1")
    wa_sent = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM businesses WHERE email_sent=1")
    em_sent = c.fetchone()[0]
    conn.close()
    return {
        "סה\"כ עסקים": total,
        "ללא אתר": no_site,
        "אתר גרוע": bad_site,
        "WhatsApp נשלח": wa_sent,
        "מייל נשלח": em_sent,
    }
