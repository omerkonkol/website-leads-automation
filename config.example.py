"""
config.example.py — העתק קובץ זה ל-config.py ומלא את הפרטים שלך.
קובץ config.py לא עולה ל-GitHub (gitignore) — הפרטים שלך נשארים אצלך בלבד.
"""

# ════════════════════════════════════════════════
#  SerpApi (אופציונלי)
#  ללא KEY — המערכת עובדת עם Google Search ישיר
#  עם KEY — תוצאות מדויקות יותר (100 חינם/חודש: serpapi.com)
# ════════════════════════════════════════════════
SERPAPI_KEY = ""

# ════════════════════════════════════════════════
#  הגדרות חיפוש — כל שאילתה = עיר + קטגוריה
# ════════════════════════════════════════════════
SEARCH_QUERIES = [
    "מוסכים בפתח תקווה",
    "חשמלאים ברמת גן",
    "מספרות בחולון",
    "עורכי דין בתל אביב",
    "רופא שיניים בירושלים",
    "קבלן שיפוצים בנתניה",
    "מסעדות בהרצליה",
    "קוסמטיקאית בראשון לציון",
]

MAX_RESULTS_PER_QUERY = 20

# ════════════════════════════════════════════════
#  הגדרות ניתוח אתר
# ════════════════════════════════════════════════
SITE_TIMEOUT      = 10
MIN_QUALITY_SCORE = 4

# ════════════════════════════════════════════════
#  הגדרות WhatsApp
# ════════════════════════════════════════════════
WHATSAPP_PAUSE_BETWEEN = 8
SESSION_DATA_DIR       = "session_data"

# ════════════════════════════════════════════════
#  הגדרות מייל
#  צור App Password ב: myaccount.google.com/apppasswords
# ════════════════════════════════════════════════
EMAIL_SENDER        = "dev@gmail.com"
EMAIL_APP_PASSWORD  = "xxxx xxxx xxxx xxxx"
EMAIL_PAUSE_BETWEEN = 5

# ════════════════════════════════════════════════
#  תיק עבודות
# ════════════════════════════════════════════════
PORTFOLIO_LINKS = [
    "https://your-portfolio-site-1.com",
    "https://your-portfolio-site-2.com",
    "https://your-portfolio-site-3.com",
]

# ════════════════════════════════════════════════
#  פרטי המציע — מלא את הפרטים שלך
# ════════════════════════════════════════════════
YOUR_NAME         = "dev"
YOUR_PHONE        = "05X-XXXXXXX"
YOUR_WHATSAPP_URL = "https://wa.me/972XXXXXXXXX"
PRICE_ILS         = 600
YOUR_BIO          = "dev bio here"

# ════════════════════════════════════════════════
#  Anthropic API — לגנרטור אתר הדמו
# ════════════════════════════════════════════════
ANTHROPIC_API_KEY = ""

# ════════════════════════════════════════════════
#  GitHub — לפרסום אתרי דמו ל-GitHub Pages
# ════════════════════════════════════════════════
GITHUB_USERNAME = "dev"
GITHUB_REPO     = "website-leads-automation"

# ════════════════════════════════════════════════
#  Supabase — מסד נתונים בענן (עבודת צוות)
#  הירשם בחינם: supabase.com
#  צור פרויקט → Settings → API → העתק URL + anon key
#  אחרי הגדרה: python db_engine.py --setup
# ════════════════════════════════════════════════
SUPABASE_URL = ""    # https://xxxxx.supabase.co
SUPABASE_KEY = ""    # anon/public key

# ════════════════════════════════════════════════
#  Telegram Bot — התראות אוטומטיות
#  צור בוט: https://t.me/BotFather → /newbot
#  קבל chat_id: שלח הודעה לבוט, ואז: https://api.telegram.org/bot<TOKEN>/getUpdates
# ════════════════════════════════════════════════
TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID   = ""

# ════════════════════════════════════════════════
#  מסד הנתונים (SQLite — fallback אם אין Supabase)
# ════════════════════════════════════════════════
DB_PATH    = "leads.db"
EXCEL_PATH = "leads_export.xlsx"
