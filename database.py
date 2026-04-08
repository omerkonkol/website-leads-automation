"""
database.py — ניהול SQLite לכל הלידים + סנכרון ל-Supabase.
מונע שליחה כפולה ושומר היסטוריה מלאה.
אם Supabase מוגדר — כל insert/update עולה גם לענן (לדשבורד משותף).
"""

import sqlite3
import pandas as pd
from datetime import datetime
from config import DB_PATH, EXCEL_PATH, SUPABASE_URL, SUPABASE_KEY

# ── Supabase sync ──
_USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)
_sb_client = None


def _sb():
    """מחזיר חיבור Supabase (singleton)."""
    global _sb_client
    if _sb_client is None and _USE_SUPABASE:
        from db_engine import SupabaseREST
        _sb_client = SupabaseREST(SUPABASE_URL, SUPABASE_KEY)
    return _sb_client


def _sync_to_supabase(data: dict, local_id: int | None = None):
    """מסנכרן שורה ל-Supabase (ברקע, לא חוסם)."""
    if not _USE_SUPABASE:
        return
    try:
        sb = _sb()
        if not sb:
            return
        # נקה שדות שלא קיימים ב-Supabase
        clean = {k: v for k, v in data.items() if v is not None}
        clean.pop("id", None)  # id ב-Supabase הוא SERIAL
        # בדוק אם כבר קיים (לפי phone+name)
        phone = clean.get("phone", "")
        name = clean.get("name", "")
        existing = []
        if phone:
            existing = sb.select("businesses", filters=f"phone=eq.{phone}", limit=1)
        if not existing and name:
            existing = sb.select("businesses", filters=f"name=eq.{name}", limit=1)
        if existing:
            sb.update("businesses", f"id=eq.{existing[0]['id']}", clean)
        else:
            sb.insert("businesses", clean)
    except Exception as e:
        print(f"    [Supabase sync] {e}")


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
            source           TEXT,   -- 'google_maps' / 'dapei_zahav' / 'facebook' / 'gov_il' וכו'
            -- רשתות חברתיות
            facebook_url     TEXT,
            instagram_url    TEXT,
            linkedin_url     TEXT,
            -- ניתוח אתר — בסיסי
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
            -- ניתוח אתר — מתקדם (SEO, CMS, PageSpeed)
            cms_platform     TEXT,       -- 'wix' / 'wordpress' / 'webflow' / 'custom' / 'unknown'
            seo_score        INTEGER,    -- 0-100 ציון SEO
            has_title_tag    INTEGER DEFAULT 0,
            has_meta_desc    INTEGER DEFAULT 0,
            has_h1           INTEGER DEFAULT 0,
            has_robots_txt   INTEGER DEFAULT 0,
            has_sitemap      INTEGER DEFAULT 0,
            pagespeed_score  INTEGER,    -- 0-100 מ-PageSpeed Insights
            core_web_vitals  TEXT,       -- JSON: {lcp, fid, cls}
            copyright_year   INTEGER,    -- שנת copyright — אתר ישן = הזדמנות
            last_updated     TEXT,       -- תאריך עדכון אחרון משוער
            google_reviews   INTEGER,    -- מספר ביקורות Google
            google_rating    REAL,       -- דירוג Google (1-5)
            competitor_count INTEGER,    -- מספר מתחרים בתחום באזור
            -- אתר דמו שנוצר
            demo_html_path   TEXT,
            demo_public_url  TEXT,
            -- Pipeline / CRM
            pipeline_stage   TEXT DEFAULT 'new',  -- new/contacted/interested/demo_sent/negotiating/closed_won/closed_lost
            deal_value       REAL DEFAULT 0,      -- סכום העסקה ב-₪
            next_followup    TEXT,                 -- תאריך follow-up הבא
            assigned_to      TEXT,                 -- מי אחראי על הליד
            -- שליחות
            whatsapp_sent    INTEGER DEFAULT 0,
            whatsapp_sent_at TEXT,
            email_sent       INTEGER DEFAULT 0,
            email_sent_at    TEXT,
            followup_count   INTEGER DEFAULT 0,    -- מספר follow-ups שנשלחו
            last_response    TEXT,                  -- תגובה אחרונה מהלקוח
            response_date    TEXT,
            -- A/B Testing
            pitch_variant    TEXT DEFAULT 'A',     -- 'A' / 'B' — איזו גרסה נשלחה
            -- Blacklist
            blacklisted      INTEGER DEFAULT 0,    -- 1 = לא לשלוח יותר
            blacklist_reason TEXT,
            -- מטא
            created_at       TEXT DEFAULT (datetime('now','localtime')),
            updated_at       TEXT DEFAULT (datetime('now','localtime')),
            notes            TEXT,
            extra_info       TEXT,
            whatsapp_pitch   TEXT,
            full_pitch       TEXT,
            sales_summary    TEXT,
            lead_score       INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS outreach_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER,
            channel     TEXT,   -- 'whatsapp' / 'email' / 'phone_call'
            status      TEXT,   -- 'sent' / 'failed' / 'replied' / 'interested' / 'not_interested'
            message     TEXT,
            variant     TEXT,   -- A/B variant
            sent_at     TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        );

        -- טבלת drip campaigns — follow-ups אוטומטיים
        CREATE TABLE IF NOT EXISTS drip_campaigns (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id   INTEGER,
            step          INTEGER DEFAULT 1,   -- שלב: 1=WA, 2=email, 3=followup
            channel       TEXT,                 -- 'whatsapp' / 'email'
            scheduled_at  TEXT,                 -- מתי לשלוח
            sent_at       TEXT,                 -- מתי נשלח בפועל
            status        TEXT DEFAULT 'pending', -- pending/sent/cancelled/skipped
            message       TEXT,
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        );

        -- טבלת A/B test results
        CREATE TABLE IF NOT EXISTS ab_tests (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name    TEXT,
            variant      TEXT,     -- 'A' / 'B'
            sent_count   INTEGER DEFAULT 0,
            reply_count  INTEGER DEFAULT 0,
            close_count  INTEGER DEFAULT 0,
            created_at   TEXT DEFAULT (datetime('now','localtime'))
        );

        -- טבלת deals — מעקב עסקאות
        CREATE TABLE IF NOT EXISTS deals (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id   INTEGER,
            amount        REAL,
            status        TEXT DEFAULT 'open',  -- open/won/lost
            closed_at     TEXT,
            notes         TEXT,
            created_at    TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        );

    """)
    conn.commit()

    # ── Migration: הוסף עמודות חסרות ל-DB קיים ──
    new_columns = [
        ("phone2",           "TEXT"),
        ("city",             "TEXT"),
        ("source",           "TEXT"),
        ("facebook_url",     "TEXT"),
        ("instagram_url",    "TEXT"),
        ("linkedin_url",     "TEXT"),
        ("demo_html_path",   "TEXT"),
        ("demo_public_url",  "TEXT"),
        ("extra_info",       "TEXT"),
        ("whatsapp_pitch",   "TEXT"),
        ("full_pitch",       "TEXT"),
        ("sales_summary",    "TEXT"),
        ("lead_score",       "INTEGER DEFAULT 0"),
        # ניתוח מתקדם
        ("cms_platform",     "TEXT"),
        ("seo_score",        "INTEGER"),
        ("has_title_tag",    "INTEGER DEFAULT 0"),
        ("has_meta_desc",    "INTEGER DEFAULT 0"),
        ("has_h1",           "INTEGER DEFAULT 0"),
        ("has_robots_txt",   "INTEGER DEFAULT 0"),
        ("has_sitemap",      "INTEGER DEFAULT 0"),
        ("pagespeed_score",  "INTEGER"),
        ("core_web_vitals",  "TEXT"),
        ("copyright_year",   "INTEGER"),
        ("last_updated",     "TEXT"),
        ("google_reviews",   "INTEGER"),
        ("google_rating",    "REAL"),
        ("competitor_count", "INTEGER"),
        # Pipeline / CRM
        ("pipeline_stage",   "TEXT DEFAULT 'new'"),
        ("deal_value",       "REAL DEFAULT 0"),
        ("next_followup",    "TEXT"),
        ("assigned_to",      "TEXT"),
        ("followup_count",   "INTEGER DEFAULT 0"),
        ("last_response",    "TEXT"),
        ("response_date",    "TEXT"),
        # A/B + Blacklist
        ("pitch_variant",    "TEXT DEFAULT 'A'"),
        ("blacklisted",      "INTEGER DEFAULT 0"),
        ("blacklist_reason", "TEXT"),
        ("updated_at",       "TEXT"),
        # אימות פעילות
        ("activity_score",    "INTEGER"),
        ("activity_details",  "TEXT"),
        ("is_likely_active",  "INTEGER DEFAULT 1"),
        ("verified_at",       "TEXT"),
        # פייסבוק
        ("fb_followers",          "INTEGER DEFAULT 0"),
        ("fb_snippet_has_website","INTEGER DEFAULT 0"),
    ]
    existing = {row[1] for row in c.execute("PRAGMA table_info(businesses)").fetchall()}
    for col, col_type in new_columns:
        if col not in existing:
            c.execute(f"ALTER TABLE businesses ADD COLUMN {col} {col_type}")
    conn.commit()

    # ── אינדקסים — אחרי שכל העמודות קיימות ──
    try:
        c.executescript("""
            CREATE INDEX IF NOT EXISTS idx_biz_lead_score ON businesses(lead_score DESC);
            CREATE INDEX IF NOT EXISTS idx_biz_pipeline ON businesses(pipeline_stage);
            CREATE INDEX IF NOT EXISTS idx_biz_followup ON businesses(next_followup);
            CREATE INDEX IF NOT EXISTS idx_biz_blacklist ON businesses(blacklisted);
            CREATE INDEX IF NOT EXISTS idx_drip_scheduled ON drip_campaigns(scheduled_at, status);
            CREATE INDEX IF NOT EXISTS idx_outreach_biz ON outreach_log(business_id);
        """)
        conn.commit()
    except Exception:
        pass  # אינדקסים כבר קיימים

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
    # סנכרון ל-Supabase
    _sync_to_supabase(row, new_id)
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
    # סנכרון ל-Supabase (שלוף שם לזיהוי)
    row = conn.execute("SELECT name, phone FROM businesses WHERE id=?", (business_id,)).fetchone()
    conn.close()
    if row and _USE_SUPABASE:
        _sync_to_supabase({**updates, "name": row["name"], "phone": row["phone"]}, business_id)


def sync_all_to_supabase() -> int:
    """מעלה את כל ה-SQLite הקיים ל-Supabase (bulk sync)."""
    if not _USE_SUPABASE:
        print("[Sync] Supabase לא מוגדר — דולג")
        return 0
    conn = get_conn()
    rows = conn.execute("SELECT * FROM businesses ORDER BY id").fetchall()
    conn.close()
    synced = 0
    for row in rows:
        data = dict(row)
        try:
            _sync_to_supabase(data, data.get("id"))
            synced += 1
            if synced % 20 == 0:
                print(f"    [Sync] {synced}/{len(rows)}...")
        except Exception as e:
            print(f"    [Sync] שגיאה בשורה {data.get('id')}: {e}")
    print(f"✅ [Sync] הועלו {synced}/{len(rows)} לידים ל-Supabase")
    return synced


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
        ORDER BY lead_score DESC, quality_score DESC
    """, (min_score,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_all_businesses() -> list:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM businesses ORDER BY lead_score DESC, quality_score DESC")
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
        "lead_score": "ציון ליד",
        "pipeline_stage": "שלב בצינור",
        "cms_platform": "פלטפורמה",
        "seo_score": "ציון SEO",
        "copyright_year": "שנת Copyright",
        "source": "מקור",
        "city": "עיר",
        "facebook_url": "פייסבוק",
        "instagram_url": "אינסטגרם",
        "activity_score": "ציון פעילות",
        "is_likely_active": "עסק פעיל",
        "activity_details": "פרטי אימות",
        "verified_at": "תאריך אימות",
        "sales_summary": "סיכום מכירה",
        "google_reviews": "ביקורות Google",
        "google_rating": "דירוג Google",
        "pagespeed_score": "ציון PageSpeed",
        "deal_value": "שווי עסקה",
        "next_followup": "פולואפ הבא",
        "search_query": "שאילתת חיפוש",
        "fb_followers": "עוקבים בפייסבוק",
        "phone2": "טלפון 2",
        "linkedin_url": "לינקדאין",
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


# ════════════════════════════════════════════════════════════════
#  Pipeline & CRM
# ════════════════════════════════════════════════════════════════
PIPELINE_STAGES = [
    "new",           # ליד חדש
    "contacted",     # נשלח פנייה ראשונה
    "interested",    # הלקוח הביע עניין
    "demo_sent",     # נשלח אתר דמו
    "negotiating",   # במשא ומתן
    "closed_won",    # עסקה נסגרה
    "closed_lost",   # הלקוח סירב
]

PIPELINE_LABELS = {
    "new":         "חדש",
    "contacted":   "נשלח פנייה",
    "interested":  "מעוניין",
    "demo_sent":   "דמו נשלח",
    "negotiating": "במו\"מ",
    "closed_won":  "נסגר ✅",
    "closed_lost": "הפסד ❌",
}


def update_pipeline_stage(business_id: int, stage: str):
    """מעדכן את שלב ה-pipeline של ליד."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    conn.execute(
        "UPDATE businesses SET pipeline_stage=?, updated_at=? WHERE id=?",
        (stage, now, business_id)
    )
    conn.commit()
    conn.close()


def set_next_followup(business_id: int, followup_date: str):
    """קובע תאריך follow-up הבא."""
    conn = get_conn()
    conn.execute(
        "UPDATE businesses SET next_followup=? WHERE id=?",
        (followup_date, business_id)
    )
    conn.commit()
    conn.close()


def get_followups_due(date: str = None) -> list:
    """מחזיר לידים שצריך לעשות להם follow-up היום (או בתאריך נתון)."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    rows = conn.execute(
        """SELECT * FROM businesses
           WHERE next_followup <= ? AND blacklisted = 0
             AND pipeline_stage NOT IN ('closed_won','closed_lost')
           ORDER BY lead_score DESC""",
        (date,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def blacklist_business(business_id: int, reason: str = ""):
    """מוסיף עסק ל-blacklist — לא ישלחו אליו יותר."""
    conn = get_conn()
    conn.execute(
        "UPDATE businesses SET blacklisted=1, blacklist_reason=? WHERE id=?",
        (reason, business_id)
    )
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════════
#  Deals — מעקב עסקאות
# ════════════════════════════════════════════════════════════════
def create_deal(business_id: int, amount: float, notes: str = "") -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO deals (business_id, amount, notes) VALUES (?,?,?)",
        (business_id, amount, notes)
    )
    conn.execute(
        "UPDATE businesses SET pipeline_stage='closed_won', deal_value=? WHERE id=?",
        (amount, business_id)
    )
    deal_id = c.lastrowid
    conn.commit()
    conn.close()
    return deal_id


def get_revenue_stats() -> dict:
    """מחזיר סטטיסטיקות הכנסות."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM deals WHERE status='won'")
    won_count, total_revenue = c.fetchone()
    c.execute("SELECT COUNT(*) FROM deals WHERE status='open'")
    open_deals = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(amount),0) FROM deals WHERE status='open'")
    pipeline_value = c.fetchone()[0]
    conn.close()
    return {
        "won_count": won_count,
        "total_revenue": total_revenue,
        "open_deals": open_deals,
        "pipeline_value": pipeline_value,
    }


# ════════════════════════════════════════════════════════════════
#  Drip Campaigns
# ════════════════════════════════════════════════════════════════
def schedule_drip(business_id: int, steps: list[dict]):
    """
    יוצר drip campaign לעסק.
    steps = [{"step": 1, "channel": "whatsapp", "delay_days": 0, "message": "..."},
             {"step": 2, "channel": "email",    "delay_days": 3, "message": "..."},
             {"step": 3, "channel": "whatsapp", "delay_days": 7, "message": "..."}]
    """
    from datetime import timedelta
    now = datetime.now()
    conn = get_conn()
    for s in steps:
        scheduled = now + timedelta(days=s.get("delay_days", 0))
        conn.execute(
            """INSERT INTO drip_campaigns (business_id, step, channel, scheduled_at, message)
               VALUES (?,?,?,?,?)""",
            (business_id, s["step"], s["channel"],
             scheduled.strftime("%Y-%m-%d %H:%M:%S"), s.get("message", ""))
        )
    conn.commit()
    conn.close()


def get_pending_drips(date: str = None) -> list:
    """מחזיר drip messages שצריך לשלוח עכשיו."""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    rows = conn.execute(
        """SELECT dc.*, b.name, b.phone, b.email, b.blacklisted
           FROM drip_campaigns dc
           JOIN businesses b ON dc.business_id = b.id
           WHERE dc.status = 'pending' AND dc.scheduled_at <= ?
             AND b.blacklisted = 0
           ORDER BY dc.scheduled_at""",
        (date,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_drip_sent(drip_id: int):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    conn.execute(
        "UPDATE drip_campaigns SET status='sent', sent_at=? WHERE id=?",
        (now, drip_id)
    )
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════════
#  A/B Testing
# ════════════════════════════════════════════════════════════════
def get_ab_stats(test_name: str = "default") -> dict:
    """מחזיר סטטיסטיקות A/B test."""
    conn = get_conn()
    c = conn.cursor()
    stats = {}
    for variant in ("A", "B"):
        c.execute(
            "SELECT sent_count, reply_count, close_count FROM ab_tests WHERE test_name=? AND variant=?",
            (test_name, variant)
        )
        row = c.fetchone()
        if row:
            sent, replies, closes = row
            stats[variant] = {
                "sent": sent, "replies": replies, "closes": closes,
                "reply_rate": round(replies / sent * 100, 1) if sent > 0 else 0,
                "close_rate": round(closes / sent * 100, 1) if sent > 0 else 0,
            }
        else:
            stats[variant] = {"sent": 0, "replies": 0, "closes": 0, "reply_rate": 0, "close_rate": 0}
    conn.close()
    return stats


def increment_ab(test_name: str, variant: str, field: str = "sent_count"):
    """מעדכן מונה ב-A/B test (sent_count / reply_count / close_count)."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM ab_tests WHERE test_name=? AND variant=?", (test_name, variant))
    if c.fetchone():
        conn.execute(f"UPDATE ab_tests SET {field} = {field} + 1 WHERE test_name=? AND variant=?",
                     (test_name, variant))
    else:
        conn.execute(
            f"INSERT INTO ab_tests (test_name, variant, {field}) VALUES (?,?,1)",
            (test_name, variant)
        )
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════════
#  Analytics helpers
# ════════════════════════════════════════════════════════════════
def get_pipeline_counts() -> dict:
    """מחזיר מספר לידים בכל שלב pipeline."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT COALESCE(pipeline_stage,'new') AS stage, COUNT(*) AS cnt FROM businesses GROUP BY pipeline_stage"
    ).fetchall()
    conn.close()
    return {r["stage"]: r["cnt"] for r in rows}


def get_source_stats() -> list:
    """מחזיר סטטיסטיקות לפי מקור."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT COALESCE(source,'unknown') AS source,
               COUNT(*) AS total,
               SUM(CASE WHEN lead_score >= 70 THEN 1 ELSE 0 END) AS hot,
               AVG(lead_score) AS avg_score
        FROM businesses GROUP BY source ORDER BY total DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_stats() -> list:
    """מחזיר סטטיסטיקות לפי קטגוריה."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT COALESCE(category,'unknown') AS category,
               COUNT(*) AS total,
               SUM(CASE WHEN lead_score >= 70 THEN 1 ELSE 0 END) AS hot,
               AVG(lead_score) AS avg_score
        FROM businesses GROUP BY category ORDER BY total DESC LIMIT 20
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_city_stats() -> list:
    """מחזיר סטטיסטיקות לפי עיר."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT COALESCE(city,'לא ידוע') AS city,
               COUNT(*) AS total,
               SUM(CASE WHEN lead_score >= 70 THEN 1 ELSE 0 END) AS hot,
               AVG(lead_score) AS avg_score
        FROM businesses WHERE city IS NOT NULL AND city != ''
        GROUP BY city ORDER BY total DESC LIMIT 20
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversion_stats() -> dict:
    """מחזיר Conversion funnel stats."""
    conn = get_conn()
    c = conn.cursor()
    def q(sql): return c.execute(sql).fetchone()[0]
    stats = {
        "total_leads":   q("SELECT COUNT(*) FROM businesses"),
        "contacted":     q("SELECT COUNT(*) FROM businesses WHERE whatsapp_sent=1 OR email_sent=1"),
        "replied":       q("SELECT COUNT(*) FROM businesses WHERE last_response IS NOT NULL"),
        "demo_sent":     q("SELECT COUNT(*) FROM businesses WHERE demo_public_url IS NOT NULL AND demo_public_url != ''"),
        "deals_won":     q("SELECT COUNT(*) FROM deals WHERE status='won'"),
        "total_revenue": q("SELECT COALESCE(SUM(amount),0) FROM deals WHERE status='won'"),
    }
    conn.close()
    return stats
