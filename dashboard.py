"""
dashboard.py — פאנל ניהול לידים.
הרצה: streamlit run dashboard.py
"""

import json
import os
import time
import subprocess
import sys
import sqlite3
from datetime import datetime
import pandas as pd
import streamlit as st

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="פאנל לידים — בניית אתרים",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── RTL + Custom CSS ──────────────────────────────────────────
st.markdown("""
<style>
  /* RTL global */
  html, body, [class*="css"] { direction: rtl; }
  .stApp { background: #0F172A; }

  /* Metric cards */
  [data-testid="stMetric"] {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px 20px;
  }
  [data-testid="stMetricLabel"] { color: #94A3B8 !important; font-size: 13px; }
  [data-testid="stMetricValue"] { color: #F1F5F9 !important; font-size: 28px; font-weight: 700; }

  /* Sidebar */
  [data-testid="stSidebar"] { background: #1E293B; border-left: 1px solid #334155; }
  [data-testid="stSidebar"] * { color: #CBD5E1 !important; }

  /* Dataframe */
  [data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

  /* Score badge colors via markdown */
  .badge-hot  { background:#DC2626; color:#fff; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }
  .badge-warm { background:#D97706; color:#fff; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }
  .badge-cold { background:#059669; color:#fff; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:700; }

  /* Issue chips */
  .chip { display:inline-block; background:#1E3A5F; color:#93C5FD;
          border:1px solid #3B82F6; border-radius:20px;
          padding:3px 12px; margin:3px; font-size:12px; }

  /* Section headers */
  h2, h3 { color: #F1F5F9 !important; }

  /* Send buttons */
  .stButton > button {
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
    padding: 8px 20px;
    width: 100%;
  }

  /* Text area */
  textarea { background: #1E293B !important; color: #F1F5F9 !important;
             border: 1px solid #334155 !important; border-radius: 8px !important; }

  /* General text */
  p, li, label, span { color: #CBD5E1; }
  strong { color: #F1F5F9 !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  DB helpers
# ════════════════════════════════════════════════════════════════
@st.cache_resource
def get_conn():
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def load_businesses(filters: dict) -> pd.DataFrame:
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM businesses WHERE 1=1"
    params = []

    if filters.get("sent_filter") == "טרם נשלח":
        query += " AND whatsapp_sent=0 AND email_sent=0"
    elif filters.get("sent_filter") == "נשלח WhatsApp":
        query += " AND whatsapp_sent=1"
    elif filters.get("sent_filter") == "נשלח מייל":
        query += " AND email_sent=1"

    if filters.get("has_website") == "אין אתר":
        query += " AND has_website=0"
    elif filters.get("has_website") == "יש אתר":
        query += " AND has_website=1"

    score_min, score_max = filters.get("score_range", (1, 10))
    query += " AND quality_score BETWEEN ? AND ?"
    params += [score_min, score_max]

    if filters.get("search"):
        query += " AND (name LIKE ? OR category LIKE ? OR address LIKE ?)"
        s = f"%{filters['search']}%"
        params += [s, s, s]

    query += " ORDER BY quality_score DESC, id DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def get_stats() -> dict:
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    def q(sql): return c.execute(sql).fetchone()[0]
    stats = {
        "total":    q("SELECT COUNT(*) FROM businesses"),
        "no_site":  q("SELECT COUNT(*) FROM businesses WHERE has_website=0"),
        "hot":      q("SELECT COUNT(*) FROM businesses WHERE quality_score >= 7"),
        "wa_sent":  q("SELECT COUNT(*) FROM businesses WHERE whatsapp_sent=1"),
        "em_sent":  q("SELECT COUNT(*) FROM businesses WHERE email_sent=1"),
        "pending":  q("SELECT COUNT(*) FROM businesses WHERE whatsapp_sent=0 AND email_sent=0"),
    }
    conn.close()
    return stats


def mark_sent_db(business_id: int, channel: str):
    from config import DB_PATH
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    if channel == "whatsapp":
        conn.execute("UPDATE businesses SET whatsapp_sent=1, whatsapp_sent_at=? WHERE id=?", (now, business_id))
    else:
        conn.execute("UPDATE businesses SET email_sent=1, email_sent_at=? WHERE id=?", (now, business_id))
    conn.execute(
        "INSERT INTO outreach_log (business_id, channel, status, sent_at) VALUES (?,?,?,?)",
        (business_id, channel, "sent", now)
    )
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════════
#  WhatsApp sender (inline, no window needed for status update)
# ════════════════════════════════════════════════════════════════
def send_whatsapp_now(phone: str, message: str, portfolio_links: list) -> bool:
    """פותח WhatsApp Web ושולח — חוזר True אם הצליח."""
    import os
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from config import SESSION_DATA_DIR

    def normalize(p):
        digits = "".join(c for c in str(p) if c.isdigit())
        return "972" + digits.lstrip("0") if not digits.startswith("972") else digits

    def paste(driver, el, txt):
        driver.execute_script(
            "arguments[0].focus(); document.execCommand('insertText', false, arguments[1]);",
            el, txt
        )

    def clip(txt):
        subprocess.run(["powershell", "-Command", f"Set-Clipboard -Value '{txt}'"], capture_output=True)

    phone = normalize(phone)
    subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe"], capture_output=True)

    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument(f"user-data-dir={os.path.abspath(SESSION_DATA_DIR)}")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    wait   = WebDriverWait(driver, 35)

    try:
        driver.get("https://web.whatsapp.com")
        st.info("🔄 ממתין ל-WhatsApp Web... (סרוק QR אם נדרש)")
        time.sleep(6)

        driver.get(f"https://web.whatsapp.com/send?phone={phone}")
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        ))
        time.sleep(2)

        inp = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        ))
        inp.click()
        paste(driver, inp, message)
        time.sleep(0.5)
        inp.send_keys(Keys.ENTER)
        time.sleep(1)

        for link in portfolio_links:
            clip(link)
            inp = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
            ))
            inp.click()
            inp.send_keys(Keys.CONTROL + "v")
            time.sleep(0.8)
            inp.send_keys(Keys.ENTER)
            time.sleep(1)

        time.sleep(2)
        return True
    except Exception as e:
        st.error(f"שגיאה בשליחת WhatsApp: {e}")
        return False
    finally:
        driver.quit()


def send_email_now(to: str, business_name: str, issue: str) -> bool:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email_sender import build_html_email, build_plain_text
    from config import EMAIL_SENDER, EMAIL_APP_PASSWORD, PORTFOLIO_LINKS, YOUR_NAME

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"💡 שדרוג האתר של {business_name}"
    msg["From"]    = f"{YOUR_NAME} <{EMAIL_SENDER}>"
    msg["To"]      = to
    msg.attach(MIMEText(build_plain_text(business_name, issue, PORTFOLIO_LINKS), "plain", "utf-8"))
    msg.attach(MIMEText(build_html_email(business_name, issue, PORTFOLIO_LINKS),  "html",  "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as srv:
            srv.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            srv.sendmail(EMAIL_SENDER, to, msg.as_string())
        return True
    except Exception as e:
        st.error(f"שגיאה בשליחת מייל: {e}")
        return False


# ════════════════════════════════════════════════════════════════
#  Build personalized message
# ════════════════════════════════════════════════════════════════
def build_personal_message(biz: dict) -> str:
    from config import YOUR_NAME, PRICE_ILS
    issues_raw = biz.get("issues", "[]")
    issues = json.loads(issues_raw) if isinstance(issues_raw, str) else (issues_raw or [])

    if not biz.get("has_website"):
        problem = "אין לכם אתר אינטרנט — כך לקוחות לא מוצאים אתכם בגוגל"
    elif issues and issues[0] != "האתר נראה תקין":
        problem = issues[0]
    else:
        problem = "האתר הקיים ניתן לשיפור משמעותי"

    return (
        f"שלום, אני פונה אליך בנוגע לעסק *{biz['name']}* 👋\n\n"
        f"שמתי לב ש{problem}.\n\n"
        f"אני בונה אתרים מודרניים ומותאמים לנייד במחיר מיוחד של *{PRICE_ILS} ₪* בלבד.\n"
        f"תיק העבודות שלי 👇"
    )


# ════════════════════════════════════════════════════════════════
#  Score & status display helpers
# ════════════════════════════════════════════════════════════════
def score_emoji(score):
    if score >= 8:  return f"🔥 {score}"
    if score >= 5:  return f"⚡ {score}"
    return f"✅ {score}"


def sent_badge(wa, em):
    parts = []
    if wa: parts.append("✅ WA")
    if em: parts.append("📧 Mail")
    return " | ".join(parts) if parts else "⏳ טרם נשלח"


# ════════════════════════════════════════════════════════════════
#  SIDEBAR — filters
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎛️ פילטרים")
    search        = st.text_input("🔍 חיפוש שם / קטגוריה / עיר", "")
    sent_filter   = st.selectbox("📬 סטטוס שליחה", ["הכל", "טרם נשלח", "נשלח WhatsApp", "נשלח מייל"])
    site_filter   = st.selectbox("🌐 אתר", ["הכל", "אין אתר", "יש אתר"])
    score_range   = st.slider("ציון ליד (1=גרוע ביותר = הכי חם לנו)", 1, 10, (1, 10))

    st.markdown("---")
    st.markdown("### ⚡ פעולות מהירות")
    if st.button("🔄 רענן נתונים"):
        st.cache_data.clear()
        st.rerun()
    if st.button("📊 ייצא Excel"):
        from database import export_to_excel
        export_to_excel()
        st.success("יוצא ל-leads_export.xlsx")
    if st.button("🚀 הפעל סריקה חדשה"):
        st.info("מריץ סריקה... (ייתכן שייקח כמה דקות)")
        subprocess.Popen([sys.executable, "main.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)


# ════════════════════════════════════════════════════════════════
#  MAIN HEADER
# ════════════════════════════════════════════════════════════════
st.markdown("# 🌐 פאנל ניהול לידים — בניית אתרים")
st.markdown("---")

# ── KPI Cards ──
stats = get_stats()
c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("סה\"כ עסקים",   stats["total"])
c2.metric("🔥 לידים חמים", stats["hot"],    help="ציון 7+")
c3.metric("🌐 ללא אתר",    stats["no_site"], help="הזדמנות מצוינת")
c4.metric("⏳ ממתינים",    stats["pending"])
c5.metric("✅ WA נשלח",    stats["wa_sent"])
c6.metric("📧 מייל נשלח",  stats["em_sent"])

st.markdown("---")

# ════════════════════════════════════════════════════════════════
#  LOAD DATA
# ════════════════════════════════════════════════════════════════
filters = {
    "search":       search,
    "sent_filter":  sent_filter if sent_filter != "הכל" else None,
    "has_website":  site_filter if site_filter != "הכל" else None,
    "score_range":  score_range,
}
from database import init_db
init_db()   # וודא שה-DB קיים (ראשונה + migration)

df = load_businesses(filters)

if df.empty:
    st.info("📭 אין עסקים עדיין — לחץ על **'הפעל סריקה חדשה'** בסרגל השמאלי כדי להתחיל.")
    st.markdown("""
    #### איך מתחילים?
    1. ערוך את **`config.py`** — הוסף את הקטגוריות והערים שאתה רוצה לסרוק
    2. לחץ **🚀 הפעל סריקה חדשה** בסרגל השמאלי
    3. המתן כמה דקות — העסקים יופיעו כאן אוטומטית
    """)
    st.stop()

# ════════════════════════════════════════════════════════════════
#  BUSINESS TABLE
# ════════════════════════════════════════════════════════════════
st.markdown(f"### 📋 עסקים ({len(df)} תוצאות)")

# Build display table
display_cols = {
    "name":          "שם עסק",
    "category":      "קטגוריה",
    "phone":         "טלפון",
    "email":         "מייל",
    "quality_score": "ציון",
    "has_website":   "אתר?",
    "is_responsive": "נייד?",
    "has_ssl":       "SSL?",
    "has_cta":       "CTA?",
    "whatsapp_sent": "WA נשלח",
    "email_sent":    "מייל נשלח",
}
disp = df[list(display_cols.keys())].copy()
disp.rename(columns=display_cols, inplace=True)

# Convert booleans to icons
for col_he, col_icon in [("אתר?","🌐"), ("נייד?","📱"), ("SSL?","🔒"), ("CTA?","📣"),
                          ("WA נשלח","✅"), ("מייל נשלח","📧")]:
    if col_he in disp.columns:
        disp[col_he] = disp[col_he].apply(lambda v: col_icon if v else "❌")

# Color score
disp["ציון"] = df["quality_score"].apply(score_emoji)

st.dataframe(
    disp,
    use_container_width=True,
    height=320,
    hide_index=True,
)

# ════════════════════════════════════════════════════════════════
#  BUSINESS DETAIL — select from dropdown
# ════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🔍 פרטי עסק + שליחת הודעה אישית")

biz_options = {f"{row['name']} | {row.get('category','') or ''} | ציון: {row['quality_score']}": idx
               for idx, row in df.iterrows()}
selected_label = st.selectbox("בחר עסק:", list(biz_options.keys()))
selected_idx   = biz_options[selected_label]
biz            = df.loc[selected_idx].to_dict()

# ── Two-column layout ──
left, right = st.columns([1, 1], gap="large")

with left:
    st.markdown(f"#### {biz['name']}")

    # Status row
    wa_done = bool(biz.get("whatsapp_sent"))
    em_done = bool(biz.get("email_sent"))
    col_a, col_b = st.columns(2)
    col_a.markdown(f"**WhatsApp:** {'✅ נשלח' if wa_done else '⏳ לא נשלח'}")
    col_b.markdown(f"**מייל:** {'✅ נשלח' if em_done else '⏳ לא נשלח'}")

    st.markdown("**פרטי קשר:**")
    st.markdown(f"📞 {biz.get('phone') or '—'}  |  📧 {biz.get('email') or '—'}")
    st.markdown(f"📍 {biz.get('address') or '—'}")
    if biz.get("website"):
        st.markdown(f"🌐 [{biz['website']}]({biz['website']})")
    else:
        st.markdown("🌐 **אין אתר**")

    st.markdown("---")
    st.markdown("**📊 ניתוח האתר:**")

    checks = [
        ("🌐 יש אתר",        biz.get("has_website")),
        ("🔒 SSL (HTTPS)",    biz.get("has_ssl")),
        ("📱 מותאם לנייד",   biz.get("is_responsive")),
        ("📣 יש כפתורי CTA", biz.get("has_cta")),
        ("📝 יש טופס",       biz.get("has_form")),
        ("📈 Facebook Pixel", biz.get("has_fb_pixel")),
        ("📊 Google Analytics", biz.get("has_analytics")),
    ]
    check_cols = st.columns(2)
    for i, (label, val) in enumerate(checks):
        check_cols[i % 2].markdown(f"{'✅' if val else '❌'} {label}")

    if biz.get("load_time_ms"):
        ms = biz["load_time_ms"]
        color = "🟢" if ms < 2000 else ("🟡" if ms < 4000 else "🔴")
        st.markdown(f"{color} זמן טעינה: **{ms}ms**")

    # Issues
    issues_raw = biz.get("issues", "[]")
    issues = json.loads(issues_raw) if isinstance(issues_raw, str) else (issues_raw or [])
    if issues and issues[0] != "האתר נראה תקין":
        st.markdown("**⚠️ בעיות שנמצאו:**")
        for issue in issues:
            st.markdown(f"<span class='chip'>⚠️ {issue}</span>", unsafe_allow_html=True)

with right:
    st.markdown("#### ✏️ הודעה אישית")

    default_msg = build_personal_message(biz)
    message_text = st.text_area(
        "ערוך את ההודעה לפני שליחה:",
        value=default_msg,
        height=220,
        key=f"msg_{biz['id']}",
    )

    from config import PORTFOLIO_LINKS
    st.markdown("**🔗 לינקים לתיק עבודות (יישלחו אחרי ההודעה):**")
    for link in PORTFOLIO_LINKS:
        st.markdown(f"- {link}")

    st.markdown("---")

    # ── Send buttons ──
    btn_col1, btn_col2 = st.columns(2)

    with btn_col1:
        wa_label = "✅ נשלח כבר" if wa_done else "💬 שלח WhatsApp"
        if st.button(wa_label, disabled=wa_done, key=f"wa_{biz['id']}", use_container_width=True):
            if not biz.get("phone"):
                st.error("אין מספר טלפון לעסק זה.")
            else:
                with st.spinner("שולח WhatsApp..."):
                    ok = send_whatsapp_now(biz["phone"], message_text, PORTFOLIO_LINKS)
                if ok:
                    mark_sent_db(biz["id"], "whatsapp")
                    st.success("✅ נשלח בהצלחה!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("נכשל — בדוק את חלון ה-Chrome")

    with btn_col2:
        em_label = "✅ נשלח כבר" if em_done else "📧 שלח מייל"
        if st.button(em_label, disabled=em_done, key=f"em_{biz['id']}", use_container_width=True):
            if not biz.get("email"):
                st.error("אין כתובת מייל לעסק זה.")
            else:
                issues_list = json.loads(biz.get("issues","[]")) if isinstance(biz.get("issues"), str) else []
                issue_str   = issues_list[0] if issues_list else "שיפור האתר"
                with st.spinner("שולח מייל..."):
                    ok = send_email_now(biz["email"], biz["name"], issue_str)
                if ok:
                    mark_sent_db(biz["id"], "email")
                    st.success("✅ נשלח בהצלחה!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("נכשל — בדוק EMAIL_APP_PASSWORD ב-config.py")

    # Mark as sent manually (if sent outside the system)
    with st.expander("⚙️ סמן ידנית כנשלח"):
        mc1, mc2 = st.columns(2)
        if mc1.button("סמן WA ✓", key=f"mwa_{biz['id']}"):
            mark_sent_db(biz["id"], "whatsapp")
            st.rerun()
        if mc2.button("סמן מייל ✓", key=f"mem_{biz['id']}"):
            mark_sent_db(biz["id"], "email")
            st.rerun()

# ════════════════════════════════════════════════════════════════
#  DEMO WEBSITE GENERATOR
# ════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 🎨 יצירת אתר דמו אישי לעסק")
st.markdown(
    "צור אתר דמו מקצועי שנראה כאילו כבר בנית לעסק — "
    "שלח את הלינק לבעל העסק כדי לשכנע אותו לסגור איתך."
)

demo_col1, demo_col2 = st.columns([2, 1], gap="large")

with demo_col1:
    demo_biz_options = {
        f"{row['name']} | {row.get('category','') or ''}": idx
        for idx, row in df.iterrows()
    }
    demo_selected_label = st.selectbox(
        "בחר עסק ליצירת אתר דמו:",
        list(demo_biz_options.keys()),
        key="demo_biz_select"
    )
    demo_idx = demo_biz_options[demo_selected_label]
    demo_biz = df.loc[demo_idx].to_dict()

    demo_extra = st.text_area(
        "מידע נוסף שתרצה לכלול באתר (שעות פעילות, התמחויות, מחירים...):",
        height=100,
        key="demo_extra",
        placeholder="לדוגמה: פתוח א-ה 9:00-18:00, מתמחים בטיפולי פנים, מחיר טיפול 150 ₪..."
    )
    deploy_netlify = st.checkbox("📤 פרסם ל-Netlify (URL ציבורי לשיתוף עם לקוח)", value=True)

with demo_col2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not anthropic_key:
        anthropic_key = st.text_input(
            "🔑 Anthropic API Key:",
            type="password",
            key="anthropic_key_input",
            help="מפתח מ-console.anthropic.com"
        )

    if st.button("✨ צור אתר דמו עכשיו", use_container_width=True, type="primary"):
        if not anthropic_key:
            st.error("נדרש Anthropic API Key")
        else:
            with st.spinner(f"🤖 Claude בונה אתר עבור {demo_biz['name']}... (30-60 שניות)"):
                try:
                    from demo_generator import create_demo_for_business
                    result = create_demo_for_business(
                        demo_biz,
                        api_key=anthropic_key,
                        extra_info=demo_extra,
                        deploy=deploy_netlify,
                    )
                    st.success(f"✅ האתר נוצר ונפתח בדפדפן!")
                    st.code(result["html_path"], language=None)

                    if result.get("public_url"):
                        pub_url = result["public_url"]
                        st.markdown(f"### 🌐 URL לשיתוף:\n[{pub_url}]({pub_url})")
                        # הצע הודעת WhatsApp עם הלינק
                        wa_with_demo = (
                            f"שלום {demo_biz['name']} 👋\n\n"
                            f"הכנתי לך דמו של האתר שאוכל לבנות עבורך — "
                            f"ראה איך זה ייראה:\n{pub_url}\n\n"
                            f"מחיר: {600} ₪ בלבד. מעניין אותך?"
                        )
                        st.markdown("**📋 העתק הודעת WhatsApp עם הלינק:**")
                        st.text_area("", value=wa_with_demo, height=130, key="demo_wa_msg")
                except Exception as e:
                    st.error(f"שגיאה: {e}")

# ════════════════════════════════════════════════════════════════
#  NOTES — add notes per business
# ════════════════════════════════════════════════════════════════
st.markdown("---")
with st.expander(f"📝 הערות על {biz['name']} (לקוח, תגובה, סטטוס)"):
    current_notes = biz.get("notes") or ""
    new_notes = st.text_area("הוסף / ערוך הערות:", value=current_notes, height=100, key=f"notes_{biz['id']}")
    if st.button("💾 שמור הערות", key=f"save_notes_{biz['id']}"):
        from config import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        conn.execute("UPDATE businesses SET notes=? WHERE id=?", (new_notes, biz["id"]))
        conn.commit()
        conn.close()
        st.success("✅ הערות נשמרו")

# ════════════════════════════════════════════════════════════════
#  OUTREACH LOG — bottom section
# ════════════════════════════════════════════════════════════════
with st.expander("📜 היסטוריית שליחות"):
    from config import DB_PATH
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    log_df = pd.read_sql_query("""
        SELECT b.name AS עסק, l.channel AS ערוץ, l.status AS סטטוס, l.sent_at AS תאריך
        FROM outreach_log l
        JOIN businesses b ON b.id = l.business_id
        ORDER BY l.sent_at DESC
        LIMIT 100
    """, conn)
    conn.close()
    if log_df.empty:
        st.info("אין היסטוריה עדיין.")
    else:
        st.dataframe(log_df, use_container_width=True, hide_index=True)
