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
#  הגדרות חיפוש
# ════════════════════════════════════════════════
SEARCH_QUERIES = [
    "מסעדות בפתח תקווה",
    "מוסכים בגבעת שמואל",
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
#  (אופציונלי — נדרש רק ליצירת אתר דמו)
#  מפתח מ: console.anthropic.com
#  אם מוגדר כ-env var ANTHROPIC_API_KEY — לא צריך למלא כאן
# ════════════════════════════════════════════════
ANTHROPIC_API_KEY = ""

# ════════════════════════════════════════════════
#  GitHub — לפרסום אתרי דמו ל-GitHub Pages
#  שם המשתמש שלך ב-GitHub
# ════════════════════════════════════════════════
GITHUB_USERNAME = "dev"
GITHUB_REPO     = "website-leads-automation"

# ════════════════════════════════════════════════
#  מסד הנתונים
# ════════════════════════════════════════════════
DB_PATH    = "leads.db"
EXCEL_PATH = "leads_export.xlsx"
