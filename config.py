"""
config.py — טוען את כל ההגדרות מקובץ .env

כל המידע הרגיש (סיסמאות, מפתחות API, פרטים אישיים) נמצא ב-.env בלבד.
קובץ .env לא עולה ל-GitHub (מוגן ב-.gitignore).

תומך גם ב-Streamlit Cloud secrets (כשמפורסם בענן).

Setup:
  1. העתק .env.example → .env
  2. מלא את הפרטים שלך ב-.env
  3. הרץ: python main.py
"""

import os
from dotenv import load_dotenv

# טען מ-.env (אם קיים)
load_dotenv()

# ── Streamlit Cloud secrets fallback ──
_st_secrets = {}
try:
    import streamlit as st
    _st_secrets = dict(st.secrets) if hasattr(st, "secrets") else {}
except Exception:
    pass


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, "") or _st_secrets.get(key, default)


def _env_int(key: str, default: int = 0) -> int:
    val = os.getenv(key, "")
    return int(val) if val.isdigit() else default


def _env_list(key: str, default: list = None) -> list:
    val = os.getenv(key, "")
    if not val:
        return default or []
    return [x.strip() for x in val.split(",") if x.strip()]


# ════════════════════════════════════════════════
#  SerpApi (אופציונלי)
# ════════════════════════════════════════════════
SERPAPI_KEY = _env("SERPAPI_KEY")

# ════════════════════════════════════════════════
#  הגדרות חיפוש — ניתן לערוך כאן
# ════════════════════════════════════════════════
SEARCH_QUERIES = [
    # ── יופי וטיפוח — נפוץ מאוד להיות פייסבוק-בלבד ──
    "מספרות בפתח תקווה",
    "מספרות ברמת גן",
    "קוסמטיקאיות בתל אביב",
    "קוסמטיקאיות בנתניה",
    "מכוני ציפורניים בראשון לציון",
    "מכוני גבות בתל אביב",
    "מכוני שיקום שיער ברמת גן",
    "ספא ועיסויים בהרצליה",
    "מכוני יופי בחיפה",
    "מאפרות בירושלים",

    # ── אוכל ומשקאות — פייסבוק-בלבד שכיח ──
    "קצביות בבני ברק",
    "מאפיות בפתח תקווה",
    "קייטרינג בתל אביב",
    "בתי קפה בנתניה",
    "מסעדות בכפר סבא",
    "גלידריות בראשון לציון",
    "מסעדות בחולון",
    "בתי קפה בהרצליה",

    # ── שיפוצים ובנייה — פייסבוק-בלבד שכיח ──
    "קבלני שיפוצים בתל אביב",
    "קבלני שיפוצים ברמת גן",
    "אינסטלטורים בפתח תקווה",
    "חשמלאים בגבעת שמואל",
    "שרברבים בחולון",
    "טכנאי מזגנים בראשון לציון",
    "גנני נוי בהרצליה",
    "חשמלאים בחיפה",
    "קבלני שיפוצים בירושלים",

    # ── שירותים מקצועיים ──
    "עורכי דין בפתח תקווה",
    "רואי חשבון בבני ברק",
    "מכוני כושר בחולון",
    "קליניקות בתל אביב",
    "פיזיותרפיסטים בנתניה",
    "רופאי שיניים ברמת גן",
    "פסיכולוגים בתל אביב",

    # ── מוסכים ורכב ──
    "מוסכים בפתח תקווה",
    "מוסכים בראשון לציון",
    "מוסכים בחיפה",
    "חנויות חלקי חילוף ברמת גן",

    # ── חנויות וקמעונאות ──
    "חנויות ביגוד בתל אביב",
    "חנויות תכשיטים ברמת גן",
    "פרחנות בתל אביב",
    "חנויות לחיות מחמד בפתח תקווה",

    # ── מנעולנים ──
    "מנעולנים ברמת גן",
    "מנעולנים בתל אביב",
]

# ── שאילתות ממוקדות פייסבוק (מחפשות עסקים שכנראה ללא אתר) ──
FACEBOOK_FOCUSED_QUERIES = [
    # קטגוריות + ערים — בהן שיעור עסקי "פייסבוק בלבד" גבוה
    ("מספרה", "פתח תקווה"),
    ("קוסמטיקה", "רמת גן"),
    ("ציפורניים", "תל אביב"),
    ("מאפייה", "בני ברק"),
    ("קייטרינג", "ראשון לציון"),
    ("שיפוצים", "חולון"),
    ("מוסך", "נתניה"),
    ("גבינות", "שוק"),
    ("קצב", "פתח תקווה"),
    ("כושר", "הרצליה"),
    ("עיסוי", "תל אביב"),
    ("מאפר", "רמת גן"),
    ("גנן", "כפר סבא"),
    ("חשמלאי", "אשדוד"),
    ("שרברב", "ירושלים"),
]

MAX_RESULTS_PER_QUERY = _env_int("MAX_RESULTS_PER_QUERY", 20)

# ════════════════════════════════════════════════
#  הגדרות ניתוח אתר
# ════════════════════════════════════════════════
SITE_TIMEOUT      = _env_int("SITE_TIMEOUT", 10)
MIN_QUALITY_SCORE = _env_int("MIN_QUALITY_SCORE", 4)

# ════════════════════════════════════════════════
#  WhatsApp
# ════════════════════════════════════════════════
WHATSAPP_PAUSE_BETWEEN = _env_int("WHATSAPP_PAUSE_BETWEEN", 8)
SESSION_DATA_DIR       = _env("SESSION_DATA_DIR", "session_data")

# ════════════════════════════════════════════════
#  מייל (Gmail)
# ════════════════════════════════════════════════
EMAIL_SENDER       = _env("EMAIL_SENDER")
EMAIL_APP_PASSWORD = _env("EMAIL_APP_PASSWORD")
EMAIL_PAUSE_BETWEEN = _env_int("EMAIL_PAUSE_BETWEEN", 5)

# ════════════════════════════════════════════════
#  תיק עבודות
# ════════════════════════════════════════════════
PORTFOLIO_LINKS = _env_list("PORTFOLIO_LINKS", [
    "https://example-site-1.com",
    "https://example-site-2.com",
    "https://example-site-3.com",
])

# ════════════════════════════════════════════════
#  פרטי המציע
# ════════════════════════════════════════════════
YOUR_NAME         = _env("YOUR_NAME", "עומר")
YOUR_PHONE        = _env("YOUR_PHONE", "05X-XXXXXXX")
YOUR_WHATSAPP_URL = _env("YOUR_WHATSAPP_URL", "https://wa.me/972XXXXXXXXX")
PRICE_ILS         = _env_int("PRICE_ILS", 600)
YOUR_BIO          = _env("YOUR_BIO", "מפתח אתרים לעסקים קטנים")

# ════════════════════════════════════════════════
#  Anthropic API
# ════════════════════════════════════════════════
ANTHROPIC_API_KEY = _env("ANTHROPIC_API_KEY")

# ════════════════════════════════════════════════
#  GitHub Pages
# ════════════════════════════════════════════════
GITHUB_USERNAME = _env("GITHUB_USERNAME")
GITHUB_REPO     = _env("GITHUB_REPO", "website-leads-automation")

# ════════════════════════════════════════════════
#  Supabase (אופציונלי — לעבודת צוות)
# ════════════════════════════════════════════════
SUPABASE_URL        = _env("SUPABASE_URL")
SUPABASE_KEY        = _env("SUPABASE_KEY")
SUPABASE_MGMT_TOKEN = _env("SUPABASE_MGMT_TOKEN")
SUPABASE_PROJECT_REF = _env("SUPABASE_PROJECT_REF", "vinpsfqldlfcgbdajvym")

# ════════════════════════════════════════════════
#  Telegram (אופציונלי — התראות)
# ════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = _env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = _env("TELEGRAM_CHAT_ID")

# ════════════════════════════════════════════════
#  מסד נתונים
# ════════════════════════════════════════════════
DB_PATH    = _env("DB_PATH", "leads.db")
EXCEL_PATH = _env("EXCEL_PATH", "leads_export.xlsx")
