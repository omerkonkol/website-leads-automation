"""
dashboard.py — פאנל ניהול לידים מתקדם.
הרצה: streamlit run dashboard.py

טאבים:
  1. 📋 לידים     — טבלת כל הלידים לפי דירוג
  2. 🚀 פעולות    — יצירת אתר + שליחת WA / מייל
  3. 📊 Pipeline   — תצוגת pipeline כמו CRM
  4. 📈 Analytics  — סטטיסטיקות, conversion, revenue
  5. 📅 Calendar   — follow-ups מתוזמנים
"""

import json
import os
import time
import subprocess
import sys
import sqlite3
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="לידים — בניית אתרים",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
  /* RTL base */
  html, body, [class*="css"] {
    direction: rtl;
    font-family: 'Segoe UI', sans-serif;
  }
  .stApp { background: #0F172A; }

  /* RTL for text elements */
  h1, h2, h3, h4, p, li, label, span,
  [data-testid="stMarkdownContainer"],
  [data-testid="stMetricLabel"],
  .stSelectbox label, .stTextInput label, .stTextArea label {
    direction: rtl !important;
    text-align: right !important;
  }

  /* Inputs RTL */
  textarea, input[type="text"], input[type="number"],
  [data-baseweb="select"] { direction: rtl !important; text-align: right !important; }

  /* Dataframe — DO NOT reverse, just align text */
  [data-testid="stDataFrame"] { direction: ltr !important; }
  [data-testid="stDataFrame"] th { text-align: right !important; }
  [data-testid="stDataFrame"] td { text-align: right !important; }

  /* Tabs */
  [data-baseweb="tab-list"] {
    background: #1E293B;
    border-radius: 12px 12px 0 0;
    padding: 6px 8px 0;
    gap: 4px;
  }
  [data-baseweb="tab"] {
    background: transparent !important;
    color: #94A3B8 !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
  }
  [aria-selected="true"][data-baseweb="tab"] {
    background: #0F172A !important;
    color: #F1F5F9 !important;
    border-bottom: 2px solid #6366F1 !important;
  }

  /* KPI cards */
  [data-testid="stMetric"] {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 16px 20px;
  }
  [data-testid="stMetricLabel"] { color: #94A3B8 !important; font-size: 13px; }
  [data-testid="stMetricValue"] { color: #F1F5F9 !important; font-size: 26px; font-weight: 700; }

  /* Score tiers */
  .tier-hot  { background:#7F1D1D; color:#FCA5A5; padding:3px 12px; border-radius:20px;
               font-size:13px; font-weight:700; border:1px solid #DC2626; white-space:nowrap; }
  .tier-warm { background:#78350F; color:#FCD34D; padding:3px 12px; border-radius:20px;
               font-size:13px; font-weight:700; border:1px solid #D97706; white-space:nowrap; }
  .tier-cold { background:#1E3A5F; color:#93C5FD; padding:3px 12px; border-radius:20px;
               font-size:13px; font-weight:700; border:1px solid #3B82F6; white-space:nowrap; }

  /* Issue chips */
  .chip { display:inline-block; background:#1E3A5F; color:#93C5FD;
          border:1px solid #3B82F6; border-radius:20px;
          padding:2px 10px; margin:2px; font-size:12px; }

  /* Pipeline stages */
  .pipeline-card { background:#1E293B; border:1px solid #334155; border-radius:12px;
                   padding:16px; margin:6px 0; }
  .pipeline-count { font-size:2rem; font-weight:900; color:#6366F1; }
  .pipeline-label { font-size:0.85rem; color:#94A3B8; }

  /* Buttons */
  .stButton > button {
    border-radius: 8px; font-weight: 600; font-size: 14px;
    padding: 10px 20px; width: 100%;
  }
  .stButton > button[kind="primary"] { background: #4F46E5 !important; border: none !important; }

  /* Text area / input */
  textarea, input[type="text"] {
    background: #1E293B !important; color: #F1F5F9 !important;
    border: 1px solid #334155 !important; border-radius: 8px !important;
  }
  p, li, label, span { color: #CBD5E1; }
  strong { color: #F1F5F9 !important; }
  h2, h3, h4 { color: #F1F5F9 !important; }

  /* Dataframe */
  [data-testid="stDataFrame"] thead th { background: #1E293B !important; color: #94A3B8 !important; }
  [data-testid="stDataFrame"] tbody tr:hover td { background: #1E3A5F !important; }

  /* Divider */
  hr { border-color: #334155 !important; margin: 16px 0; }

  /* Score bar background */
  .score-bar-bg { background:#1E293B; border-radius:6px; height:8px; overflow:hidden; margin:4px 0 12px; }
  .score-bar-fill { height:100%; border-radius:6px; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
#  DB helpers — Supabase + SQLite fallback
# ════════════════════════════════════════════════════════════════
from config import SUPABASE_URL, SUPABASE_KEY, DB_PATH

# תמיכה ב-Streamlit Cloud secrets (כשמפורסם בענן)
_CLOUD_SB_URL = SUPABASE_URL
_CLOUD_SB_KEY = SUPABASE_KEY
if not _CLOUD_SB_URL:
    try:
        _CLOUD_SB_URL = st.secrets.get("SUPABASE_URL", "")
        _CLOUD_SB_KEY = st.secrets.get("SUPABASE_KEY", "")
    except Exception:
        pass
_USE_SUPABASE = bool(_CLOUD_SB_URL and _CLOUD_SB_KEY)

def _sb():
    from db_engine import SupabaseREST
    return SupabaseREST(_CLOUD_SB_URL, _CLOUD_SB_KEY)

def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(ttl=30)
def load_df(tier="הכל", sent="הכל", site="הכל", score_range=(0,100), search="",
            pipeline_stage=None) -> pd.DataFrame:
    if _USE_SUPABASE:
        return _load_df_supabase(tier, sent, site, score_range, search, pipeline_stage)
    return _load_df_sqlite(tier, sent, site, score_range, search, pipeline_stage)


def _load_df_supabase(tier, sent, site, score_range, search, pipeline_stage) -> pd.DataFrame:
    sb = _sb()
    filters = "blacklisted=eq.0"
    if "HOT" in tier:    filters += "&lead_score=gte.70"
    elif "WARM" in tier: filters += "&lead_score=gte.45&lead_score=lt.70"
    elif "COLD" in tier: filters += "&lead_score=lt.45"
    if sent == "טרם נשלח":       filters += "&whatsapp_sent=eq.0&email_sent=eq.0"
    elif sent == "נשלח WhatsApp": filters += "&whatsapp_sent=eq.1"
    elif sent == "נשלח מייל":     filters += "&email_sent=eq.1"
    if site == "אין אתר": filters += "&has_website=eq.0"
    elif site == "יש אתר": filters += "&has_website=eq.1"
    if pipeline_stage and pipeline_stage != "הכל":
        filters += f"&pipeline_stage=eq.{pipeline_stage}"
    filters += f"&lead_score=gte.{score_range[0]}&lead_score=lte.{score_range[1]}"
    if search:
        filters += f"&name=ilike.*{search}*"
    rows = sb.select("businesses", filters=filters, order="lead_score.desc")
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _load_df_sqlite(tier, sent, site, score_range, search, pipeline_stage) -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    q = "SELECT * FROM businesses WHERE blacklisted = 0"
    p = []
    if "HOT"  in tier: q += " AND lead_score >= 70"
    elif "WARM" in tier: q += " AND lead_score >= 45 AND lead_score < 70"
    elif "COLD" in tier: q += " AND lead_score < 45"
    if sent == "טרם נשלח":       q += " AND whatsapp_sent=0 AND email_sent=0"
    elif sent == "נשלח WhatsApp": q += " AND whatsapp_sent=1"
    elif sent == "נשלח מייל":     q += " AND email_sent=1"
    if site == "אין אתר": q += " AND has_website=0"
    elif site == "יש אתר": q += " AND has_website=1"
    if pipeline_stage and pipeline_stage != "הכל":
        q += " AND pipeline_stage=?"
        p.append(pipeline_stage)
    q += " AND lead_score BETWEEN ? AND ?"
    p += list(score_range)
    if search:
        q += " AND (name LIKE ? OR category LIKE ? OR address LIKE ? OR city LIKE ?)"
        s = f"%{search}%"
        p += [s, s, s, s]
    q += " ORDER BY lead_score DESC, quality_score DESC"
    df = pd.read_sql_query(q, conn, params=p)
    conn.close()
    return df


def get_kpis() -> dict:
    if _USE_SUPABASE:
        sb = _sb()
        all_biz = sb.select("businesses", filters="blacklisted=eq.0")
        total = len(all_biz)
        hot = sum(1 for b in all_biz if (b.get("lead_score") or 0) >= 70)
        warm = sum(1 for b in all_biz if 45 <= (b.get("lead_score") or 0) < 70)
        no_site = sum(1 for b in all_biz if not b.get("has_website"))
        pending = sum(1 for b in all_biz if not b.get("whatsapp_sent") and not b.get("email_sent"))
        wa_sent = sum(1 for b in all_biz if b.get("whatsapp_sent"))
        active = sum(1 for b in all_biz if b.get("is_likely_active") is not False)
        try:
            deals = sb.select("deals", filters="status=eq.won")
            revenue = sum(d.get("amount", 0) for d in deals)
            deal_count = len(deals)
        except Exception:
            revenue, deal_count = 0, 0
        return {
            "total": total, "hot": hot, "warm": warm, "no_site": no_site,
            "pending": pending, "wa_sent": wa_sent, "revenue": revenue,
            "deals": deal_count, "active": active,
        }
    conn = _db()
    c = conn.cursor()
    def q(sql): return c.execute(sql).fetchone()[0]
    d = {
        "total":    q("SELECT COUNT(*) FROM businesses WHERE blacklisted=0"),
        "hot":      q("SELECT COUNT(*) FROM businesses WHERE lead_score >= 70 AND blacklisted=0"),
        "warm":     q("SELECT COUNT(*) FROM businesses WHERE lead_score >= 45 AND lead_score < 70 AND blacklisted=0"),
        "no_site":  q("SELECT COUNT(*) FROM businesses WHERE has_website=0 AND blacklisted=0"),
        "pending":  q("SELECT COUNT(*) FROM businesses WHERE whatsapp_sent=0 AND email_sent=0 AND blacklisted=0"),
        "wa_sent":  q("SELECT COUNT(*) FROM businesses WHERE whatsapp_sent=1"),
        "revenue":  q("SELECT COALESCE(SUM(amount),0) FROM deals WHERE status='won'"),
        "deals":    q("SELECT COUNT(*) FROM deals WHERE status='won'"),
        "active":   0,
    }
    conn.close()
    return d


def mark_sent_db(bid: int, channel: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = _db()
    if channel == "whatsapp":
        conn.execute("UPDATE businesses SET whatsapp_sent=1, whatsapp_sent_at=? WHERE id=?", (now, bid))
    else:
        conn.execute("UPDATE businesses SET email_sent=1, email_sent_at=? WHERE id=?", (now, bid))
    conn.execute(
        "INSERT INTO outreach_log (business_id,channel,status,sent_at) VALUES (?,?,?,?)",
        (bid, channel, "sent", now)
    )
    conn.commit()
    conn.close()


def save_notes(bid: int, notes: str):
    conn = _db()
    conn.execute("UPDATE businesses SET notes=? WHERE id=?", (notes, bid))
    conn.commit()
    conn.close()


def save_demo_url(bid: int, html_path: str, public_url: str):
    conn = _db()
    conn.execute(
        "UPDATE businesses SET demo_html_path=?, demo_public_url=?, pipeline_stage='demo_sent' WHERE id=?",
        (html_path, public_url, bid)
    )
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════════════
#  Helpers
# ════════════════════════════════════════════════════════════════
from lead_scorer import compute_lead_score, score_tier_hebrew

def tier_badge(score: int) -> str:
    if score >= 70: return f'<span class="tier-hot">🔥 HOT {score}</span>'
    if score >= 45: return f'<span class="tier-warm">⚡ WARM {score}</span>'
    return f'<span class="tier-cold">❄️ COLD {score}</span>'

def bool_icon(v): return "✅" if v else "❌"


def send_whatsapp(phone: str, message: str, links: list) -> bool:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    from config import SESSION_DATA_DIR

    def norm(p):
        d = "".join(c for c in str(p) if c.isdigit())
        return "972" + d.lstrip("0") if not d.startswith("972") else d

    def paste(drv, el, txt):
        drv.execute_script(
            "arguments[0].focus(); document.execCommand('insertText',false,arguments[1]);", el, txt)

    phone = norm(phone)
    subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe"], capture_output=True)
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument(f"user-data-dir={os.path.abspath(SESSION_DATA_DIR)}")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    wait = WebDriverWait(driver, 35)
    try:
        driver.get("https://web.whatsapp.com")
        st.info("ממתין ל-WhatsApp Web... (סרוק QR אם נדרש)")
        time.sleep(6)
        driver.get(f"https://web.whatsapp.com/send?phone={phone}")
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
        time.sleep(2)
        inp = wait.until(EC.element_to_be_clickable(
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
        inp.click(); paste(driver, inp, message); time.sleep(0.5)
        inp.send_keys(Keys.ENTER); time.sleep(1)
        for link in links:
            subprocess.run(["powershell", "-Command",
                f"Set-Clipboard -Value '{link}'"], capture_output=True)
            inp = wait.until(EC.element_to_be_clickable(
                (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')))
            inp.click(); inp.send_keys(Keys.CONTROL + "v"); time.sleep(0.8)
            inp.send_keys(Keys.ENTER); time.sleep(1)
        time.sleep(2); return True
    except Exception as e:
        st.error(f"שגיאה: {e}"); return False
    finally:
        driver.quit()


def send_email(to: str, biz_name: str, issue: str) -> bool:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email_sender import build_html_email, build_plain_text
    from config import EMAIL_SENDER, EMAIL_APP_PASSWORD, PORTFOLIO_LINKS, YOUR_NAME
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"שדרוג האתר של {biz_name}"
    msg["From"] = f"{YOUR_NAME} <{EMAIL_SENDER}>"
    msg["To"] = to
    msg.attach(MIMEText(build_plain_text(biz_name, issue, PORTFOLIO_LINKS), "plain", "utf-8"))
    msg.attach(MIMEText(build_html_email(biz_name, issue, PORTFOLIO_LINKS), "html",  "utf-8"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as srv:
            srv.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            srv.sendmail(EMAIL_SENDER, to, msg.as_string())
        return True
    except Exception as e:
        st.error(f"שגיאה: {e}"); return False


# ════════════════════════════════════════════════════════════════
#  Init DB
# ════════════════════════════════════════════════════════════════
from database import init_db
init_db()


# ════════════════════════════════════════════════════════════════
#  KPI ROW
# ════════════════════════════════════════════════════════════════
st.markdown("## 🎯 מערכת לידים — בניית אתרים")
kpis = get_kpis()
k1,k2,k3,k4,k5,k6,k7,k8 = st.columns(8)
k1.metric("סה\"כ",        kpis["total"])
k2.metric("🔥 HOT",       kpis["hot"])
k3.metric("⚡ WARM",      kpis["warm"])
k4.metric("🌐 ללא אתר",   kpis["no_site"])
k5.metric("✅ פעילים",    kpis.get("active", kpis["total"]))
k6.metric("⏳ ממתינים",   kpis["pending"])
k7.metric("💰 עסקאות",    kpis["deals"])
k8.metric("₪ הכנסות",    f"₪{kpis['revenue']:,.0f}")

st.markdown("---")


# ════════════════════════════════════════════════════════════════
#  TABS
# ════════════════════════════════════════════════════════════════
tab_leads, tab_actions, tab_pipeline, tab_analytics, tab_calendar = st.tabs([
    "📋  לידים",
    "🚀  פעולות",
    "📊  Pipeline",
    "📈  Analytics",
    "📅  Calendar",
])


# ════════════════════════════════════════════════════════════════
#  TAB 1 — LEADS TABLE
# ════════════════════════════════════════════════════════════════
with tab_leads:
    f1, f2, f3, f4, f5 = st.columns([3, 2, 2, 2, 2])
    search      = f1.text_input("🔍 חיפוש", "", placeholder="שם / קטגוריה / עיר")
    tier_filter = f2.selectbox("🎯 רמה", ["הכל", "🔥 HOT (70+)", "⚡ WARM (45–69)", "❄️ COLD (<45)"])
    sent_filter = f3.selectbox("📬 נשלח?", ["הכל", "טרם נשלח", "נשלח WhatsApp", "נשלח מייל"])
    site_filter = f4.selectbox("🌐 אתר?",  ["הכל", "אין אתר", "יש אתר"])
    score_range = f5.slider("ציון", 0, 100, (0, 100))

    df = load_df(tier_filter, sent_filter, site_filter, score_range, search)

    btn1, btn2, btn3, btn4, _ = st.columns([1,1,1,1,3])
    if btn1.button("🔄 רענן"):
        st.cache_data.clear(); st.rerun()
    if btn2.button("🎯 עדכן דירוגים"):
        from lead_scorer import rescore_all
        n = rescore_all()
        st.cache_data.clear()
        st.success(f"עודכנו {n} עסקים"); time.sleep(1); st.rerun()
    if btn3.button("📊 ייצא Excel"):
        from database import export_to_excel
        export_to_excel(); st.success("יוצא!")
    if btn4.button("🚀 סריקה חדשה"):
        subprocess.Popen(
            [sys.executable, "main.py"],
            creationflags=subprocess.CREATE_NEW_CONSOLE, cwd="e:/system"
        )
        st.info("סריקה רצה בחלון נפרד...")

    st.markdown(f"**{len(df)} עסקים** — ממוינים לפי ציון ליד ↓")

    if df.empty:
        st.info("אין עסקים עדיין — לחץ **🚀 סריקה חדשה** כדי להתחיל.")
    else:
        rows = []
        for _, r in df.iterrows():
            ls = r.get("lead_score") or 0
            if ls == 0:
                ls, _ = compute_lead_score(r.to_dict())

            if ls >= 70:   tier_str = f"🔥 {ls}"
            elif ls >= 45: tier_str = f"⚡ {ls}"
            else:          tier_str = f"❄️  {ls}"

            sent_str = []
            if r.get("whatsapp_sent"): sent_str.append("WA ✅")
            if r.get("email_sent"):    sent_str.append("מייל ✅")

            cms = r.get("cms_platform") or "—"
            seo = r.get("seo_score")
            seo_str = f"{seo}/100" if seo is not None else "—"

            act = r.get("activity_score")
            act_str = f"{act}/100" if act is not None else "—"

            rows.append({
                "דירוג":     tier_str,
                "שם עסק":    r["name"],
                "קטגוריה":   r.get("category") or r.get("search_query") or "—",
                "עיר":       r.get("city") or "—",
                "טלפון":     r.get("phone") or "—",
                "מייל":      "✅" if r.get("email") else "—",
                "אתר?":      bool_icon(r.get("has_website")),
                "CMS":       cms,
                "SEO":       seo_str,
                "פעילות":    act_str,
                "נשלח":      " | ".join(sent_str) if sent_str else "⏳",
                "מקור":      r.get("source") or "—",
            })
        disp = pd.DataFrame(rows)
        col_config = {
            "דירוג":   st.column_config.TextColumn("דירוג", width="small"),
            "שם עסק":  st.column_config.TextColumn("שם עסק", width="medium"),
            "קטגוריה": st.column_config.TextColumn("קטגוריה", width="small"),
            "עיר":     st.column_config.TextColumn("עיר", width="small"),
            "טלפון":   st.column_config.TextColumn("טלפון", width="medium"),
            "מייל":    st.column_config.TextColumn("מייל", width="small"),
            "אתר?":    st.column_config.TextColumn("אתר?", width="small"),
            "CMS":     st.column_config.TextColumn("CMS", width="small"),
            "SEO":     st.column_config.TextColumn("SEO", width="small"),
            "פעילות":  st.column_config.TextColumn("פעילות", width="small"),
            "נשלח":    st.column_config.TextColumn("נשלח", width="small"),
            "מקור":    st.column_config.TextColumn("מקור", width="small"),
        }
        st.dataframe(disp, use_container_width=True, height=480, hide_index=True,
                     column_config=col_config)

        # ── Lead detail expander ──
        st.markdown("---")
        st.markdown("#### פרטי ליד מלאים")
        opts = {f"{r['name']} | {r.get('city') or ''} | ציון {r.get('lead_score') or 0}": i
                for i, r in df.iterrows()}
        sel_label = st.selectbox("בחר עסק לפרטים:", list(opts.keys()), key="leads_detail_sel")
        sel_biz = df.loc[opts[sel_label]].to_dict()

        ls = sel_biz.get("lead_score") or 0
        _, breakdown = compute_lead_score(sel_biz)
        if ls == 0:
            ls = sum(breakdown.values())

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**{sel_biz['name']}**")
            st.markdown(f"📞 {sel_biz.get('phone') or '—'}  |  📧 {sel_biz.get('email') or '—'}")
            st.markdown(f"📍 {sel_biz.get('address') or '—'}")
            if sel_biz.get("website"):
                st.markdown(f"🌐 [{sel_biz['website']}]({sel_biz['website']})")
            if sel_biz.get("cms_platform"):
                st.markdown(f"🔧 CMS: **{sel_biz['cms_platform']}**")
            if sel_biz.get("copyright_year"):
                st.markdown(f"📅 Copyright: **{sel_biz['copyright_year']}**")
            if sel_biz.get("google_reviews"):
                st.markdown(f"⭐ Google: **{sel_biz['google_reviews']}** ביקורות ({sel_biz.get('google_rating', '—')})")

            bar_col = "#DC2626" if ls>=70 else ("#D97706" if ls>=45 else "#475569")
            st.markdown(f"""
            <div class="score-bar-bg">
              <div class="score-bar-fill" style="background:{bar_col};width:{ls}%"></div>
            </div>""", unsafe_allow_html=True)
            st.markdown(tier_badge(ls), unsafe_allow_html=True)

        with col_b:
            st.markdown("**פירוט הציון:**")
            for reason, pts in sorted(breakdown.items(), key=lambda x: -x[1]):
                sign  = "+" if pts > 0 else ""
                color = "#22c55e" if pts > 0 else "#ef4444"
                st.markdown(
                    f'<span style="color:{color};font-weight:700;min-width:36px;display:inline-block">'
                    f'{sign}{pts}</span> <span style="color:#94a3b8">{reason}</span>',
                    unsafe_allow_html=True
                )

        # ── Activity verification ──
        act_score = sel_biz.get("activity_score")
        if act_score is not None:
            act_col = "#22c55e" if act_score >= 50 else ("#D97706" if act_score >= 30 else "#ef4444")
            st.markdown(f"""
            <div style="margin:12px 0; padding:10px 16px; background:#1E293B; border-radius:8px;
                        border-right:4px solid {act_col}">
              <span style="color:{act_col}; font-weight:700; font-size:1.1rem">
                🏢 ציון פעילות: {act_score}/100
              </span>
            </div>""", unsafe_allow_html=True)
            # Show verification details
            details_raw = sel_biz.get("activity_details")
            if details_raw:
                try:
                    details = json.loads(details_raw) if isinstance(details_raw, str) else details_raw
                    for d in (details or []):
                        st.markdown(f"<span style='color:#94A3B8; font-size:13px'>• {d}</span>",
                                    unsafe_allow_html=True)
                except Exception:
                    pass

        # ── הודעה אישית (WhatsApp pitch) ──
        st.markdown("---")
        st.markdown("#### 💬 הודעה אישית לעסק")

        from pitch_builder import build_whatsapp_pitch, detect_issues, ISSUES, build_full_pitch

        pitch_issues = detect_issues(sel_biz)

        # יתרונות + חסרונות
        pros_cons_col1, pros_cons_col2 = st.columns(2)
        with pros_cons_col1:
            st.markdown("**❌ חסרונות שנמצאו:**")
            if not pitch_issues:
                st.markdown("<span style='color:#94A3B8'>לא נמצאו בעיות</span>", unsafe_allow_html=True)
            for key in pitch_issues:
                issue = ISSUES.get(key, {})
                st.markdown(
                    f"<div style='background:#7F1D1D22; border:1px solid #7F1D1D; border-radius:8px; "
                    f"padding:8px 12px; margin:4px 0'>"
                    f"<span style='color:#FCA5A5; font-weight:600'>❌ {issue.get('short', key)}</span><br>"
                    f"<span style='color:#94A3B8; font-size:12px'>{issue.get('impact', '')}</span></div>",
                    unsafe_allow_html=True
                )

        with pros_cons_col2:
            st.markdown("**✅ מה נציע:**")
            offers = [
                ("עיצוב מותאם אישית", "אתר שמשקף את העסק ומושך לקוחות"),
                ("מותאם לנייד 100%", "72% מהגלישה בישראל היא מהטלפון"),
                ("HTTPS מאובטח", "בטחון + דירוג גבוה בגוגל"),
                ("כפתורי WhatsApp + טלפון", "לקוח לוחץ → מתקשר מיד"),
                ("SEO מלא", "להיות ראשון בגוגל כשמחפשים את השירות שלך"),
                ("טעינה מהירה", "מתחת ל-2 שניות — אף לקוח לא עוזב"),
            ]
            for title, desc in offers:
                st.markdown(
                    f"<div style='background:#14532D22; border:1px solid #14532D; border-radius:8px; "
                    f"padding:8px 12px; margin:4px 0'>"
                    f"<span style='color:#86EFAC; font-weight:600'>✅ {title}</span><br>"
                    f"<span style='color:#94A3B8; font-size:12px'>{desc}</span></div>",
                    unsafe_allow_html=True
                )

        # הודעת WhatsApp מוכנה
        st.markdown("---")
        wa_pitch = sel_biz.get("whatsapp_pitch") or build_whatsapp_pitch(sel_biz)
        st.text_area("📱 הודעת WhatsApp מוכנה לשליחה:", value=wa_pitch, height=280, key="lead_wa_pitch")

        # פנייה מלאה (מייל)
        with st.expander("📧 פנייה מלאה למייל"):
            full_pitch = sel_biz.get("full_pitch") or build_full_pitch(sel_biz)
            st.text_area("", value=full_pitch, height=400, key="lead_full_pitch")

        st.session_state["action_biz_id"] = sel_biz.get("id")
        st.markdown("---")
        st.info("💡 לחץ על הטאב **🚀 פעולות** למעלה כדי לשלוח WhatsApp / מייל לעסק הזה.")


# ════════════════════════════════════════════════════════════════
#  TAB 2 — ACTIONS
# ════════════════════════════════════════════════════════════════
with tab_actions:
    all_df = load_df()
    if all_df.empty:
        st.info("אין לידים. הפעל סריקה בטאב הלידים.")
        st.stop()

    default_id = st.session_state.get("action_biz_id")
    opts2 = {}
    default_idx = 0
    for i, (_, r) in enumerate(all_df.iterrows()):
        ls = r.get("lead_score") or 0
        tier_s = "🔥" if ls>=70 else ("⚡" if ls>=45 else "❄️")
        label = f"{tier_s} {r['name']}  |  {r.get('city') or r.get('address','')[:15]}  |  {ls}pt"
        opts2[label] = r["id"]
        if r["id"] == default_id:
            default_idx = i

    sel_label2 = st.selectbox("בחר ליד:", list(opts2.keys()), index=default_idx, key="action_sel")
    sel_id = opts2[sel_label2]
    biz = all_df[all_df["id"] == sel_id].iloc[0].to_dict()

    ls = biz.get("lead_score") or 0
    _, breakdown = compute_lead_score(biz)
    if ls == 0:
        ls = max(0, sum(breakdown.values()))

    st.markdown("---")
    left, right = st.columns([1, 1], gap="large")

    # ════════════ LEFT — lead info + demo ════════════
    with left:
        st.markdown(f"### {biz['name']}")

        bar_col = "#DC2626" if ls>=70 else ("#D97706" if ls>=45 else "#475569")
        st.markdown(f"""
        <div class="score-bar-bg">
          <div class="score-bar-fill" style="background:{bar_col};width:{ls}%"></div>
        </div>""", unsafe_allow_html=True)
        st.markdown(tier_badge(ls) + f"  &nbsp; ציון ליד: <strong>{ls}/100</strong>",
                    unsafe_allow_html=True)

        # Pipeline stage selector
        from database import PIPELINE_LABELS, update_pipeline_stage
        current_stage = biz.get("pipeline_stage") or "new"
        stage_options = list(PIPELINE_LABELS.keys())
        stage_labels = [f"{PIPELINE_LABELS[s]}" for s in stage_options]
        current_idx = stage_options.index(current_stage) if current_stage in stage_options else 0
        new_stage_label = st.selectbox("שלב Pipeline:", stage_labels, index=current_idx, key="pipeline_select")
        new_stage = stage_options[stage_labels.index(new_stage_label)]
        if new_stage != current_stage:
            update_pipeline_stage(biz["id"], new_stage)
            st.success(f"עודכן ל: {PIPELINE_LABELS[new_stage]}")
            st.cache_data.clear()

        st.markdown(f"""
        📞 **{biz.get('phone') or '—'}**
        📧 {biz.get('email') or '—'}
        📍 {biz.get('address') or '—'}
        🌐 {'[' + biz['website'] + '](' + biz['website'] + ')' if biz.get('website') else '**אין אתר**'}
        """)

        if biz.get("cms_platform"):
            st.markdown(f"🔧 CMS: **{biz['cms_platform']}**")
        if biz.get("seo_score") is not None:
            st.markdown(f"📈 SEO: **{biz['seo_score']}/100**")

        # Issue chips
        issues_raw = biz.get("issues", "[]")
        try:
            issues = json.loads(issues_raw) if isinstance(issues_raw, str) else (issues_raw or [])
        except Exception:
            issues = []
        if issues:
            chips = "".join(f'<span class="chip">{i}</span>' for i in issues[:8])
            st.markdown(chips, unsafe_allow_html=True)

        if biz.get("full_pitch"):
            with st.expander("📄 פנייה מלאה (למייל)"):
                st.text(biz["full_pitch"])

        st.markdown("---")

        # ── DEMO GENERATOR ──
        st.markdown("#### ✨ צור אתר דמו")
        existing_url = biz.get("demo_public_url") or ""
        if existing_url:
            st.success(f"דמו קיים: [{existing_url}]({existing_url})")

        demo_extra = st.text_area(
            "מידע נוסף לאתר:", height=80, key="demo_extra",
            placeholder="ראשון–חמישי 9:00–18:00, מתמחים ב...",
        )
        deploy_gh = st.checkbox("פרסם ל-GitHub Pages", value=True, key="deploy_gh")

        if st.button("✨ בנה אתר דמו עכשיו", type="primary", key="build_demo"):
            with st.spinner(f"בונה אתר עבור {biz['name']}..."):
                try:
                    from demo_generator import create_demo_for_business
                    result = create_demo_for_business(biz, extra_info=demo_extra, deploy=deploy_gh)
                    html_path = result["html_path"]
                    public_url = result.get("public_url", "")
                    save_demo_url(biz["id"], html_path, public_url)
                    st.cache_data.clear()
                    st.success("✅ האתר נוצר!")
                    st.code(html_path, language=None)
                    if public_url:
                        st.markdown(f"**URL ציבורי:** [{public_url}]({public_url})")
                        st.session_state[f"demo_url_{biz['id']}"] = public_url
                except Exception as e:
                    st.error(f"שגיאה: {e}")

        # ── Blacklist button ──
        st.markdown("---")
        if st.button("🚫 הוסף ל-Blacklist", key="blacklist_btn"):
            from database import blacklist_business
            blacklist_business(biz["id"], "ידני מהדשבורד")
            st.warning("העסק הוסר מרשימת השליחה")
            st.cache_data.clear()

    # ════════════ RIGHT — send WA / email ════════════
    with right:
        st.markdown("#### 💬 שליחת WhatsApp")

        wa_done = bool(biz.get("whatsapp_sent"))
        em_done = bool(biz.get("email_sent"))

        if wa_done:
            at = biz.get("whatsapp_sent_at","")
            st.success(f"✅ WhatsApp נשלח {('ב-' + at) if at else ''}")

        saved_pitch = biz.get("whatsapp_pitch", "")
        default_msg = saved_pitch if saved_pitch and len(saved_pitch) > 20 else ""
        if not default_msg:
            from pitch_builder import build_whatsapp_pitch
            default_msg = build_whatsapp_pitch(biz)

        demo_url = (
            st.session_state.get(f"demo_url_{biz['id']}")
            or biz.get("demo_public_url")
            or ""
        )
        if demo_url:
            default_msg = default_msg.replace("{DEMO_URL}", demo_url)
        else:
            default_msg = default_msg.replace(
                "{DEMO_URL}", "[אתר הדמו יוכנס כאן אחרי יצירתו]"
            )

        wa_text = st.text_area(
            "הודעה לשליחה:", value=default_msg, height=260, key=f"wa_text_{biz['id']}"
        )

        from config import PORTFOLIO_LINKS
        if PORTFOLIO_LINKS:
            st.markdown("**🔗 לינקים שיישלחו אחרי ההודעה:**")
            for lnk in PORTFOLIO_LINKS:
                st.markdown(f"- `{lnk}`")

        wa_col1, wa_col2 = st.columns(2)
        with wa_col1:
            if st.button(
                "✅ נשלח כבר" if wa_done else "💬 שלח WhatsApp",
                disabled=wa_done, key=f"wa_btn_{biz['id']}", use_container_width=True
            ):
                if not biz.get("phone"):
                    st.error("אין מספר טלפון.")
                else:
                    with st.spinner("שולח..."):
                        ok = send_whatsapp(biz["phone"], wa_text, PORTFOLIO_LINKS)
                    if ok:
                        mark_sent_db(biz["id"], "whatsapp")
                        update_pipeline_stage(biz["id"], "contacted")
                        st.success("✅ נשלח!"); st.cache_data.clear()
                        time.sleep(1); st.rerun()

        with wa_col2:
            if st.button("סמן כנשלח ידנית", key=f"wa_manual_{biz['id']}", use_container_width=True):
                mark_sent_db(biz["id"], "whatsapp")
                update_pipeline_stage(biz["id"], "contacted")
                st.cache_data.clear(); st.rerun()

        st.markdown("---")
        st.markdown("#### 📧 שליחת מייל")

        if em_done:
            at = biz.get("email_sent_at","")
            st.success(f"✅ מייל נשלח {('ב-' + at) if at else ''}")

        email_addr = biz.get("email") or ""
        if not email_addr:
            st.warning("אין כתובת מייל לעסק זה.")
        else:
            st.markdown(f"**אל:** `{email_addr}`")
            em_col1, em_col2 = st.columns(2)
            with em_col1:
                if st.button(
                    "✅ נשלח כבר" if em_done else "📧 שלח מייל",
                    disabled=em_done or not email_addr,
                    key=f"em_btn_{biz['id']}", use_container_width=True
                ):
                    issue_str = issues[0] if issues else "שיפור האתר"
                    with st.spinner("שולח מייל..."):
                        ok = send_email(email_addr, biz["name"], issue_str)
                    if ok:
                        mark_sent_db(biz["id"], "email")
                        st.success("✅ נשלח!"); st.cache_data.clear()
                        time.sleep(1); st.rerun()
            with em_col2:
                if st.button("סמן כנשלח ידנית", key=f"em_manual_{biz['id']}", use_container_width=True):
                    mark_sent_db(biz["id"], "email")
                    st.cache_data.clear(); st.rerun()

        # ── Response tracking ──
        st.markdown("---")
        st.markdown("#### 📩 תגובת לקוח")
        response_text = st.text_area("הקלד את תגובת הלקוח:", key=f"response_{biz['id']}", height=80)
        resp_col1, resp_col2 = st.columns(2)
        with resp_col1:
            if st.button("✅ מעוניין", key=f"interested_{biz['id']}", use_container_width=True):
                if response_text:
                    from outreach_engine import record_response
                    record_response(biz["id"], response_text, interested=True)
                    st.success("נרשם! הליד עודכן ל'מעוניין'")
                    st.cache_data.clear()
        with resp_col2:
            if st.button("❌ לא מעוניין", key=f"not_interested_{biz['id']}", use_container_width=True):
                if response_text:
                    from outreach_engine import record_response
                    record_response(biz["id"], response_text, interested=False)
                    st.warning("נרשם.")
                    st.cache_data.clear()

        # ── Notes & Deal ──
        st.markdown("---")
        st.markdown("#### 📝 הערות")
        notes_val = st.text_area("", value=biz.get("notes") or "", height=80, key=f"notes_{biz['id']}")
        if st.button("💾 שמור הערות", key=f"save_notes_{biz['id']}"):
            save_notes(biz["id"], notes_val)
            st.success("נשמר"); st.cache_data.clear()

        # ── Close Deal ──
        st.markdown("---")
        st.markdown("#### 💰 סגור עסקה")
        deal_amount = st.number_input("סכום העסקה (₪):", min_value=0, value=600, key=f"deal_{biz['id']}")
        if st.button("💰 סגור עסקה!", type="primary", key=f"close_deal_{biz['id']}"):
            from database import create_deal
            create_deal(biz["id"], deal_amount, notes_val)
            st.balloons()
            st.success(f"🎉 עסקה נסגרה! ₪{deal_amount:,.0f}")
            st.cache_data.clear()

    # ── Outreach history ──
    with st.expander("📜 היסטוריית שליחות"):
        from config import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        log_df = pd.read_sql_query("""
            SELECT channel AS ערוץ, status AS סטטוס, sent_at AS תאריך
            FROM outreach_log WHERE business_id=?
            ORDER BY sent_at DESC
        """, conn, params=[biz["id"]])
        conn.close()
        if log_df.empty:
            st.info("אין היסטוריה עדיין.")
        else:
            st.dataframe(log_df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
#  TAB 3 — PIPELINE VIEW
# ════════════════════════════════════════════════════════════════
with tab_pipeline:
    st.markdown("### 📊 Pipeline — מעקב שלבים")
    from database import PIPELINE_STAGES, PIPELINE_LABELS, get_pipeline_counts

    counts = get_pipeline_counts()

    # Pipeline cards
    cols = st.columns(len(PIPELINE_STAGES))
    stage_colors = {
        "new": "#3B82F6", "contacted": "#8B5CF6", "interested": "#F59E0B",
        "demo_sent": "#06B6D4", "negotiating": "#EC4899",
        "closed_won": "#22C55E", "closed_lost": "#EF4444",
    }
    for i, stage in enumerate(PIPELINE_STAGES):
        count = counts.get(stage, 0)
        color = stage_colors.get(stage, "#6366F1")
        with cols[i]:
            st.markdown(f"""
            <div class="pipeline-card" style="border-top: 3px solid {color}; text-align:center;">
                <div class="pipeline-count" style="color:{color}">{count}</div>
                <div class="pipeline-label">{PIPELINE_LABELS[stage]}</div>
            </div>""", unsafe_allow_html=True)

    # Pipeline detailed view
    st.markdown("---")
    stage_filter = st.selectbox(
        "הצג לידים בשלב:",
        ["הכל"] + [PIPELINE_LABELS[s] for s in PIPELINE_STAGES],
        key="pipeline_filter"
    )

    # Map label back to stage key
    selected_stage = None
    if stage_filter != "הכל":
        for k, v in PIPELINE_LABELS.items():
            if v == stage_filter:
                selected_stage = k
                break

    pipe_df = load_df(pipeline_stage=selected_stage) if selected_stage else load_df()
    if not pipe_df.empty:
        pipe_rows = []
        for _, r in pipe_df.iterrows():
            stage = r.get("pipeline_stage") or "new"
            pipe_rows.append({
                "שלב": PIPELINE_LABELS.get(stage, stage),
                "שם עסק": r["name"],
                "ציון": r.get("lead_score") or 0,
                "טלפון": r.get("phone") or "—",
                "עיר": r.get("city") or "—",
                "Follow-up": r.get("next_followup") or "—",
                "תגובה": (r.get("last_response") or "—")[:40],
            })
        st.dataframe(pd.DataFrame(pipe_rows), use_container_width=True, hide_index=True, height=400)


# ════════════════════════════════════════════════════════════════
#  TAB 4 — ANALYTICS
# ════════════════════════════════════════════════════════════════
with tab_analytics:
    st.markdown("### 📈 Analytics & Insights")

    from database import get_conversion_stats, get_source_stats, get_category_stats, get_city_stats, get_revenue_stats

    # ── Conversion Funnel ──
    st.markdown("#### 🔄 Conversion Funnel")
    conv = get_conversion_stats()
    funnel_cols = st.columns(6)
    funnel_data = [
        ("לידים", conv["total_leads"], "#3B82F6"),
        ("נשלח פנייה", conv["contacted"], "#8B5CF6"),
        ("הגיבו", conv["replied"], "#F59E0B"),
        ("דמו נשלח", conv["demo_sent"], "#06B6D4"),
        ("עסקאות", conv["deals_won"], "#22C55E"),
        (f"₪{conv['total_revenue']:,.0f}", None, "#10B981"),
    ]
    for i, (label, value, color) in enumerate(funnel_data):
        with funnel_cols[i]:
            if value is not None:
                st.markdown(f"""
                <div style="text-align:center; padding:16px; background:#1E293B;
                            border-radius:12px; border-top:3px solid {color};">
                    <div style="font-size:2rem; font-weight:900; color:{color}">{value}</div>
                    <div style="font-size:0.85rem; color:#94A3B8">{label}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align:center; padding:16px; background:#1E293B;
                            border-radius:12px; border-top:3px solid {color};">
                    <div style="font-size:1.5rem; font-weight:900; color:{color}">{label}</div>
                    <div style="font-size:0.85rem; color:#94A3B8">הכנסות</div>
                </div>""", unsafe_allow_html=True)

    # ── Conversion rates ──
    if conv["total_leads"] > 0:
        contacted_rate = conv["contacted"] / conv["total_leads"] * 100
        reply_rate = conv["replied"] / max(conv["contacted"], 1) * 100
        close_rate = conv["deals_won"] / max(conv["contacted"], 1) * 100
        st.markdown(f"""
        **Conversion Rates:**
        - פנייה → תגובה: **{reply_rate:.1f}%**
        - פנייה → עסקה: **{close_rate:.1f}%**
        - סה"כ contacted: **{contacted_rate:.1f}%**
        """)

    st.markdown("---")

    # ── Source Performance ──
    an_col1, an_col2 = st.columns(2)

    with an_col1:
        st.markdown("#### 🌐 ביצועים לפי מקור")
        source_stats = get_source_stats()
        if source_stats:
            src_df = pd.DataFrame(source_stats)
            src_df.columns = ["מקור", "סה\"כ", "HOT", "ציון ממוצע"]
            src_df["ציון ממוצע"] = src_df["ציון ממוצע"].round(1)
            st.dataframe(src_df, use_container_width=True, hide_index=True)

    with an_col2:
        st.markdown("#### 🏷️ ביצועים לפי קטגוריה")
        cat_stats = get_category_stats()
        if cat_stats:
            cat_df = pd.DataFrame(cat_stats)
            cat_df.columns = ["קטגוריה", "סה\"כ", "HOT", "ציון ממוצע"]
            cat_df["ציון ממוצע"] = cat_df["ציון ממוצע"].round(1)
            st.dataframe(cat_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── City heatmap (table) ──
    st.markdown("#### 🗺️ ביצועים לפי עיר")
    city_stats = get_city_stats()
    if city_stats:
        city_df = pd.DataFrame(city_stats)
        city_df.columns = ["עיר", "סה\"כ", "HOT", "ציון ממוצע"]
        city_df["ציון ממוצע"] = city_df["ציון ממוצע"].round(1)
        st.dataframe(city_df, use_container_width=True, hide_index=True)

    # ── A/B Test Results ──
    st.markdown("---")
    st.markdown("#### 🔬 A/B Test Results")
    from database import get_ab_stats
    ab = get_ab_stats()
    ab_col1, ab_col2 = st.columns(2)
    for variant, col in [("A", ab_col1), ("B", ab_col2)]:
        with col:
            stats = ab[variant]
            st.markdown(f"""
            **גרסה {variant}:**
            - נשלחו: {stats['sent']}
            - תגובות: {stats['replies']} ({stats['reply_rate']}%)
            - עסקאות: {stats['closes']} ({stats['close_rate']}%)
            """)

    # ── Revenue tracking ──
    st.markdown("---")
    st.markdown("#### 💰 Revenue Tracker")
    rev = get_revenue_stats()
    rev_cols = st.columns(4)
    rev_cols[0].metric("עסקאות שנסגרו", rev["won_count"])
    rev_cols[1].metric("הכנסות", f"₪{rev['total_revenue']:,.0f}")
    rev_cols[2].metric("עסקאות פתוחות", rev["open_deals"])
    rev_cols[3].metric("Pipeline Value", f"₪{rev['pipeline_value']:,.0f}")


# ════════════════════════════════════════════════════════════════
#  TAB 5 — CALENDAR (Follow-ups)
# ════════════════════════════════════════════════════════════════
with tab_calendar:
    st.markdown("### 📅 Follow-ups מתוזמנים")

    from database import get_followups_due, set_next_followup

    # ── Today's follow-ups ──
    today = datetime.now().strftime("%Y-%m-%d")
    due_today = get_followups_due(today)

    if due_today:
        st.warning(f"📢 יש {len(due_today)} follow-ups להיום!")
        for biz in due_today:
            with st.expander(f"📞 {biz['name']} — ציון {biz.get('lead_score', 0)}"):
                st.markdown(f"""
                📞 {biz.get('phone') or '—'}  |  📧 {biz.get('email') or '—'}
                📍 {biz.get('address') or '—'}
                🗓️ Follow-up: **{biz.get('next_followup', '—')}**
                📝 הערות: {biz.get('notes') or '—'}
                """)
                if st.button(f"✅ בוצע — דחה שבוע", key=f"followup_done_{biz['id']}"):
                    next_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
                    set_next_followup(biz["id"], next_date)
                    conn = _db()
                    conn.execute(
                        "UPDATE businesses SET followup_count = COALESCE(followup_count,0) + 1 WHERE id=?",
                        (biz["id"],)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Follow-up הבא: {next_date}")
                    st.cache_data.clear()
    else:
        st.success("✅ אין follow-ups להיום!")

    # ── Upcoming follow-ups ──
    st.markdown("---")
    st.markdown("#### 📆 Follow-ups הקרובים")
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    upcoming = get_followups_due(next_week)
    if upcoming:
        up_rows = []
        for b in upcoming:
            up_rows.append({
                "שם עסק": b["name"],
                "תאריך": b.get("next_followup") or "—",
                "ציון": b.get("lead_score") or 0,
                "טלפון": b.get("phone") or "—",
                "שלב": PIPELINE_LABELS.get(b.get("pipeline_stage", "new"), "חדש"),
            })
        st.dataframe(pd.DataFrame(up_rows), use_container_width=True, hide_index=True)
    else:
        st.info("אין follow-ups מתוזמנים לשבוע הקרוב.")

    # ── Schedule new follow-up ──
    st.markdown("---")
    st.markdown("#### ➕ תזמן follow-up חדש")
    fu_df = load_df()
    if not fu_df.empty:
        fu_opts = {f"{r['name']} (ציון {r.get('lead_score',0)})": r["id"]
                   for _, r in fu_df.iterrows()}
        fu_sel = st.selectbox("בחר עסק:", list(fu_opts.keys()), key="fu_biz_sel")
        fu_date = st.date_input("תאריך Follow-up:", value=datetime.now() + timedelta(days=3), key="fu_date")
        if st.button("📅 תזמן", key="schedule_fu"):
            set_next_followup(fu_opts[fu_sel], fu_date.strftime("%Y-%m-%d"))
            st.success(f"Follow-up נקבע ל-{fu_date}")
            st.cache_data.clear()
