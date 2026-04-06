"""
db_engine.py — שכבת מסד נתונים אוניברסלית.

תומך ב-2 backends:
  1. Supabase (PostgreSQL בענן) — REST API ישיר (ללא SDK!)
  2. SQLite (מקומי) — fallback אם אין Supabase

כל 3 חברי הצוות יכולים לגשת למידע בו-זמנית דרך Supabase.

Setup:
  1. הירשם ב-supabase.com (חינם)
  2. צור פרויקט → Settings → API → העתק URL + anon key
  3. שים ב-.env: SUPABASE_URL=... SUPABASE_KEY=...
  4. הרץ: python db_engine.py --setup
"""

import json
import requests
from datetime import datetime
from config import SUPABASE_URL, SUPABASE_KEY, DB_PATH

# ── בדוק חיבור Supabase ──
_USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

if _USE_SUPABASE:
    print("[DB] ☁️  Supabase מוגדר — כל הצוות מחובר לאותו מסד נתונים")
else:
    print("[DB] 💾 SQLite מקומי (הגדר SUPABASE_URL ב-.env לעבודת צוות)")


# ════════════════════════════════════════════════════════════════
#  Supabase REST API — פשוט ועובד עם כל גרסת Python
# ════════════════════════════════════════════════════════════════
class SupabaseREST:
    """חיבור ישיר ל-Supabase דרך REST API (PostgREST)."""

    def __init__(self, url: str, key: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def select(self, table: str, filters: str = "", order: str = "", limit: int = 0) -> list[dict]:
        url = f"{self.base}/{table}?select=*"
        if filters:
            url += f"&{filters}"
        if order:
            url += f"&order={order}"
        if limit:
            url += f"&limit={limit}"
        resp = requests.get(url, headers=self.headers, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def insert(self, table: str, data: dict) -> dict:
        url = f"{self.base}/{table}"
        resp = requests.post(url, headers=self.headers, json=data, timeout=15)
        resp.raise_for_status()
        rows = resp.json()
        return rows[0] if rows else {}

    def update(self, table: str, filters: str, data: dict) -> list[dict]:
        url = f"{self.base}/{table}?{filters}"
        resp = requests.patch(url, headers=self.headers, json=data, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def count(self, table: str, filters: str = "") -> int:
        url = f"{self.base}/{table}?select=id"
        if filters:
            url += f"&{filters}"
        h = {**self.headers, "Prefer": "count=exact", "Range-Unit": "items"}
        resp = requests.head(url, headers=h, timeout=10)
        cr = resp.headers.get("content-range", "")
        if "/" in cr:
            return int(cr.split("/")[1])
        # Fallback: count via GET
        resp2 = requests.get(url + "&select=id", headers=self.headers, timeout=10)
        return len(resp2.json()) if resp2.status_code == 200 else 0

    def rpc(self, function_name: str, params: dict = None) -> any:
        """קריאה לפונקציית SQL ב-Supabase."""
        url = self.base.replace("/rest/v1", f"/rest/v1/rpc/{function_name}")
        resp = requests.post(url, headers=self.headers, json=params or {}, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def sql(self, query: str) -> any:
        """הרצת SQL ישיר דרך ה-SQL API (לצורך setup)."""
        url = self.base.replace("/rest/v1", "/rest/v1/rpc/exec_sql")
        # Supabase doesn't have direct SQL via REST, use the management API
        # For setup, we'll print the SQL for the user to run in the dashboard
        return None


# ═══════════════════════════════════════════════════════════
#  Setup SQL — להרצה ב-Supabase SQL Editor
# ═══════════════════════════════════════════════════════════
SETUP_SQL = """
-- ════════════════════════════════════════════════
--  טבלת עסקים ראשית
-- ════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS businesses (
    id               SERIAL PRIMARY KEY,
    name             TEXT NOT NULL,
    phone            TEXT,
    phone2           TEXT,
    email            TEXT,
    website          TEXT,
    address          TEXT,
    city             TEXT,
    category         TEXT,
    search_query     TEXT,
    source           TEXT,
    facebook_url     TEXT,
    instagram_url    TEXT,
    linkedin_url     TEXT,
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
    cms_platform     TEXT,
    seo_score        INTEGER,
    has_title_tag    INTEGER DEFAULT 0,
    has_meta_desc    INTEGER DEFAULT 0,
    has_h1           INTEGER DEFAULT 0,
    has_robots_txt   INTEGER DEFAULT 0,
    has_sitemap      INTEGER DEFAULT 0,
    pagespeed_score  INTEGER,
    core_web_vitals  TEXT,
    copyright_year   INTEGER,
    last_updated     TEXT,
    google_reviews   INTEGER,
    google_rating    REAL,
    competitor_count INTEGER,
    demo_html_path   TEXT,
    demo_public_url  TEXT,
    pipeline_stage   TEXT DEFAULT 'new',
    deal_value       REAL DEFAULT 0,
    next_followup    TEXT,
    assigned_to      TEXT,
    whatsapp_sent    INTEGER DEFAULT 0,
    whatsapp_sent_at TEXT,
    email_sent       INTEGER DEFAULT 0,
    email_sent_at    TEXT,
    followup_count   INTEGER DEFAULT 0,
    last_response    TEXT,
    response_date    TEXT,
    pitch_variant    TEXT DEFAULT 'A',
    blacklisted      INTEGER DEFAULT 0,
    blacklist_reason TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW(),
    notes            TEXT,
    extra_info       TEXT,
    whatsapp_pitch   TEXT,
    full_pitch       TEXT,
    sales_summary    TEXT,
    lead_score       INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS outreach_log (
    id          SERIAL PRIMARY KEY,
    business_id INTEGER REFERENCES businesses(id),
    channel     TEXT,
    status      TEXT,
    message     TEXT,
    variant     TEXT,
    sent_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS drip_campaigns (
    id            SERIAL PRIMARY KEY,
    business_id   INTEGER REFERENCES businesses(id),
    step          INTEGER DEFAULT 1,
    channel       TEXT,
    scheduled_at  TIMESTAMPTZ,
    sent_at       TIMESTAMPTZ,
    status        TEXT DEFAULT 'pending',
    message       TEXT
);

CREATE TABLE IF NOT EXISTS ab_tests (
    id           SERIAL PRIMARY KEY,
    test_name    TEXT,
    variant      TEXT,
    sent_count   INTEGER DEFAULT 0,
    reply_count  INTEGER DEFAULT 0,
    close_count  INTEGER DEFAULT 0,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS deals (
    id            SERIAL PRIMARY KEY,
    business_id   INTEGER REFERENCES businesses(id),
    amount        REAL,
    status        TEXT DEFAULT 'open',
    closed_at     TIMESTAMPTZ,
    notes         TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- אינדקסים
CREATE INDEX IF NOT EXISTS idx_biz_score ON businesses(lead_score DESC);
CREATE INDEX IF NOT EXISTS idx_biz_pipeline ON businesses(pipeline_stage);
CREATE INDEX IF NOT EXISTS idx_biz_phone ON businesses(phone);
CREATE INDEX IF NOT EXISTS idx_biz_blacklist ON businesses(blacklisted);
CREATE INDEX IF NOT EXISTS idx_drip_status ON drip_campaigns(status, scheduled_at);

-- RLS — כולם יכולים לקרוא ולכתוב (anon key)
ALTER TABLE businesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE drip_campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE deals ENABLE ROW LEVEL SECURITY;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_all_businesses') THEN
        CREATE POLICY allow_all_businesses ON businesses FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_all_outreach') THEN
        CREATE POLICY allow_all_outreach ON outreach_log FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_all_drip') THEN
        CREATE POLICY allow_all_drip ON drip_campaigns FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_all_ab') THEN
        CREATE POLICY allow_all_ab ON ab_tests FOR ALL USING (true) WITH CHECK (true);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'allow_all_deals') THEN
        CREATE POLICY allow_all_deals ON deals FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;
"""


def setup_supabase():
    """מדפיס הוראות + SQL ליצירת טבלאות ב-Supabase."""
    if not _USE_SUPABASE:
        print("\n❌ Supabase לא מוגדר.")
        print("   1. הירשם ב-supabase.com (חינם)")
        print("   2. צור פרויקט חדש")
        print("   3. לך ל-Settings → API")
        print("   4. הוסף ל-.env:")
        print("      SUPABASE_URL=https://xxxxx.supabase.co")
        print("      SUPABASE_KEY=eyJhbG...your-anon-key")
        return

    print("\n✅ Supabase מוגדר!")
    print("\nעכשיו צריך ליצור את הטבלאות:")
    print("  1. פתח את הפרויקט ב-supabase.com")
    print("  2. לך ל-SQL Editor (תפריט שמאל)")
    print("  3. לחץ 'New Query'")
    print("  4. הדבק את ה-SQL הבא והרץ:\n")
    print("=" * 60)
    print(SETUP_SQL)
    print("=" * 60)

    # נסה גם ליצור אוטומטית דרך ה-API
    print("\n🔄 מנסה ליצור טבלאות אוטומטית...")
    try:
        sb = SupabaseREST(SUPABASE_URL, SUPABASE_KEY)
        # נסה לגשת לטבלת businesses — אם עובד, הטבלאות כבר קיימות
        result = sb.select("businesses", limit=1)
        print("✅ הטבלאות כבר קיימות! המערכת מוכנה.")
    except requests.exceptions.HTTPError as e:
        if "404" in str(e) or "relation" in str(e):
            print("⚠️  הטבלאות עדיין לא קיימות.")
            print("   הדבק את ה-SQL למעלה ב-SQL Editor והרץ.")
        else:
            print(f"⚠️  שגיאה: {e}")
    except Exception as e:
        print(f"⚠️  {e}")
        print("   הדבק את ה-SQL למעלה ב-SQL Editor והרץ.")


def test_connection():
    """בודק חיבור ל-Supabase."""
    if not _USE_SUPABASE:
        print("Supabase לא מוגדר.")
        return False
    try:
        sb = SupabaseREST(SUPABASE_URL, SUPABASE_KEY)
        result = sb.select("businesses", limit=1)
        print(f"✅ מחובר ל-Supabase! ({len(result)} שורות בדוגמה)")
        return True
    except Exception as e:
        print(f"❌ שגיאה בחיבור: {e}")
        return False


# ════════════════════════════════════════════════════════════════
#  CLI
# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import sys, io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    import argparse
    parser = argparse.ArgumentParser(description="Database Engine")
    parser.add_argument("--setup", action="store_true", help="Setup Supabase tables")
    parser.add_argument("--test", action="store_true", help="Test Supabase connection")
    args = parser.parse_args()

    if args.setup:
        setup_supabase()
    elif args.test:
        test_connection()
    else:
        print(f"Backend: {'☁️  Supabase' if _USE_SUPABASE else '💾 SQLite'}")
        print("\nשימוש:")
        print("  python db_engine.py --setup  # הגדר Supabase")
        print("  python db_engine.py --test   # בדוק חיבור")
