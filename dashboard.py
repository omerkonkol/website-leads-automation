"""
dashboard.py — פאנל ניהול לידים דו-שלבי.
הרצה: streamlit run dashboard.py

טאב 1 — 📋 לידים     : טבלת כל הלידים לפי דירוג
טאב 2 — 🚀 פעולות    : יצירת אתר + שליחת WA / מייל לליד שנבחר
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
  html, body, [class*="css"] { direction: rtl; font-family: 'Segoe UI', sans-serif; }
  .stApp { background: #0F172A; }

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
#  DB helpers
# ════════════════════════════════════════════════════════════════
def _db():
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@st.cache_data(ttl=30)
def load_df(tier="הכל", sent="הכל", site="הכל", score_range=(0,100), search="") -> pd.DataFrame:
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    q = "SELECT * FROM businesses WHERE 1=1"
    p = []
    if "HOT"  in tier: q += " AND lead_score >= 70"
    elif "WARM" in tier: q += " AND lead_score >= 45 AND lead_score < 70"
    elif "COLD" in tier: q += " AND lead_score < 45"
    if sent == "טרם נשלח":       q += " AND whatsapp_sent=0 AND email_sent=0"
    elif sent == "נשלח WhatsApp": q += " AND whatsapp_sent=1"
    elif sent == "נשלח מייל":     q += " AND email_sent=1"
    if site == "אין אתר": q += " AND has_website=0"
    elif site == "יש אתר": q += " AND has_website=1"
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
    conn = _db()
    c = conn.cursor()
    def q(sql): return c.execute(sql).fetchone()[0]
    d = {
        "total":   q("SELECT COUNT(*) FROM businesses"),
        "hot":     q("SELECT COUNT(*) FROM businesses WHERE lead_score >= 70"),
        "warm":    q("SELECT COUNT(*) FROM businesses WHERE lead_score >= 45 AND lead_score < 70"),
        "no_site": q("SELECT COUNT(*) FROM businesses WHERE has_website=0"),
        "pending": q("SELECT COUNT(*) FROM businesses WHERE whatsapp_sent=0 AND email_sent=0"),
        "wa_sent": q("SELECT COUNT(*) FROM businesses WHERE whatsapp_sent=1"),
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
        "UPDATE businesses SET demo_html_path=?, demo_public_url=? WHERE id=?",
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
#  KPI ROW — הצג תמיד בראש הדף
# ════════════════════════════════════════════════════════════════
st.markdown("## 🎯 מערכת לידים — בניית אתרים")
kpis = get_kpis()
k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("סה\"כ עסקים",   kpis["total"])
k2.metric("🔥 HOT",        kpis["hot"],    help="ציון ≥ 70 — פנה ראשון")
k3.metric("⚡ WARM",       kpis["warm"],   help="ציון 45–69")
k4.metric("🌐 ללא אתר",    kpis["no_site"])
k5.metric("⏳ ממתינים",    kpis["pending"])
k6.metric("✅ WA נשלח",    kpis["wa_sent"])

st.markdown("---")


# ════════════════════════════════════════════════════════════════
#  TABS
# ════════════════════════════════════════════════════════════════
tab_leads, tab_actions = st.tabs(["📋  לידים לפי דירוג", "🚀  בניית אתר + שליחה"])


# ════════════════════════════════════════════════════════════════
#  TAB 1 — LEADS TABLE
# ════════════════════════════════════════════════════════════════
with tab_leads:
    # ── Filters row ──────────────────────────────────────────────
    f1, f2, f3, f4, f5 = st.columns([3, 2, 2, 2, 2])
    search      = f1.text_input("🔍 חיפוש", "", placeholder="שם / קטגוריה / עיר")
    tier_filter = f2.selectbox("🎯 רמה", ["הכל", "🔥 HOT (70+)", "⚡ WARM (45–69)", "❄️ COLD (<45)"])
    sent_filter = f3.selectbox("📬 נשלח?", ["הכל", "טרם נשלח", "נשלח WhatsApp", "נשלח מייל"])
    site_filter = f4.selectbox("🌐 אתר?",  ["הכל", "אין אתר", "יש אתר"])
    score_range = f5.slider("ציון", 0, 100, (0, 100))

    df = load_df(tier_filter, sent_filter, site_filter, score_range, search)

    # ── Action buttons ───────────────────────────────────────────
    btn1, btn2, btn3, _ = st.columns([1,1,1,3])
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

    st.markdown(f"**{len(df)} עסקים** — ממוינים לפי ציון ליד ↓")

    if df.empty:
        st.info("אין עסקים עדיין — לחץ **🚀 הפעל סריקה** כדי להתחיל.")
        if st.button("🚀 הפעל סריקה חדשה"):
            subprocess.Popen(
                ["C:/Users/user/AppData/Local/Programs/Python/Python314/python.exe", "main.py"],
                creationflags=subprocess.CREATE_NEW_CONSOLE, cwd="e:/system"
            )
    else:
        # ── Build display DataFrame ───────────────────────────────
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

            rows.append({
                "דירוג":    tier_str,
                "שם עסק":   r["name"],
                "קטגוריה":  r.get("category") or r.get("search_query") or "—",
                "עיר":      r.get("city") or "—",
                "טלפון":    r.get("phone") or "—",
                "אתר?":     bool_icon(r.get("has_website")),
                "נייד?":    bool_icon(r.get("is_responsive")),
                "SSL?":     bool_icon(r.get("has_ssl")),
                "CTA?":     bool_icon(r.get("has_cta")),
                "נשלח":     " | ".join(sent_str) if sent_str else "⏳",
            })
        disp = pd.DataFrame(rows)
        st.dataframe(disp, use_container_width=True, height=480, hide_index=True)

        # ── Lead detail expander ──────────────────────────────────
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

            # Score bar
            bar_col = "#DC2626" if ls>=70 else ("#D97706" if ls>=45 else "#475569")
            st.markdown(f"""
            <div class="score-bar-bg">
              <div class="score-bar-fill" style="background:{bar_col};width:{ls}%"></div>
            </div>""", unsafe_allow_html=True)
            st.markdown(
                tier_badge(ls),
                unsafe_allow_html=True
            )

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

        # Store selected biz id in session for Tab 2
        st.session_state["action_biz_id"] = sel_biz.get("id")

        # Quick-jump button
        st.markdown("---")
        st.info("💡 לחץ על הטאב **🚀 בניית אתר + שליחה** למעלה כדי לפעול על הליד הזה.")


# ════════════════════════════════════════════════════════════════
#  TAB 2 — ACTIONS
# ════════════════════════════════════════════════════════════════
with tab_actions:
    # Load all businesses for selector
    all_df = load_df()   # no filters
    if all_df.empty:
        st.info("אין לידים. הפעל סריקה בטאב הלידים.")
        st.stop()

    # Build selector — default to the one chosen in Tab 1
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

    sel_label2 = st.selectbox(
        "בחר ליד:",
        list(opts2.keys()),
        index=default_idx,
        key="action_sel"
    )
    sel_id = opts2[sel_label2]
    biz = all_df[all_df["id"] == sel_id].iloc[0].to_dict()

    ls = biz.get("lead_score") or 0
    _, breakdown = compute_lead_score(biz)
    if ls == 0:
        ls = max(0, sum(breakdown.values()))

    st.markdown("---")

    # ── Two main columns ─────────────────────────────────────────
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

        st.markdown(f"""
        📞 **{biz.get('phone') or '—'}**
        📧 {biz.get('email') or '—'}
        📍 {biz.get('address') or '—'}
        🌐 {'[' + biz['website'] + '](' + biz['website'] + ')' if biz.get('website') else '**אין אתר**'}
        """)

        # Issue chips
        issues_raw = biz.get("issues", "[]")
        try:
            issues = json.loads(issues_raw) if isinstance(issues_raw, str) else (issues_raw or [])
        except Exception:
            issues = []
        if issues:
            chips = "".join(f'<span class="chip">{i}</span>' for i in issues[:5])
            st.markdown(chips, unsafe_allow_html=True)

        # Full pitch (email)
        if biz.get("full_pitch"):
            with st.expander("📄 פנייה מלאה (למייל)"):
                st.text(biz["full_pitch"])

        st.markdown("---")

        # ── DEMO GENERATOR ──────────────────────────────────────
        st.markdown("#### ✨ צור אתר דמו")

        existing_url = biz.get("demo_public_url") or ""
        if existing_url:
            st.success(f"דמו קיים: [{existing_url}]({existing_url})")

        demo_extra = st.text_area(
            "מידע נוסף לאתר (שעות פתיחה, מחירים, התמחויות...):",
            height=80, key="demo_extra",
            placeholder="ראשון–חמישי 9:00–18:00, מתמחים ב...",
        )
        deploy_gh  = st.checkbox("פרסם ל-GitHub Pages (URL לשיתוף)", value=True, key="deploy_gh")

        if st.button("✨ בנה אתר דמו עכשיו", type="primary", key="build_demo"):
            with st.spinner(f"בונה אתר עבור {biz['name']}..."):
                try:
                    from demo_generator import create_demo_for_business
                    result = create_demo_for_business(
                        biz, extra_info=demo_extra, deploy=deploy_gh
                    )
                    html_path  = result["html_path"]
                    public_url = result.get("public_url", "")
                    save_demo_url(biz["id"], html_path, public_url)
                    st.cache_data.clear()

                    st.success("✅ האתר נוצר ונפתח בדפדפן!")
                    st.code(html_path, language=None)
                    if public_url:
                        st.markdown(f"**URL ציבורי:** [{public_url}]({public_url})")
                        st.session_state[f"demo_url_{biz['id']}"] = public_url
                    else:
                        st.info("האתר נשמר מקומית. סמן 'פרסם ל-GitHub Pages' ולחץ שוב לקבלת URL.")
                except Exception as e:
                    st.error(f"שגיאה: {e}")

    # ════════════ RIGHT — send WA / email ════════════
    with right:
        st.markdown("#### 💬 שליחת WhatsApp")

        wa_done = bool(biz.get("whatsapp_sent"))
        em_done = bool(biz.get("email_sent"))

        if wa_done:
            at = biz.get("whatsapp_sent_at","")
            st.success(f"✅ WhatsApp נשלח {('ב-' + at) if at else ''}")

        # Build default message
        saved_pitch = biz.get("whatsapp_pitch", "")
        default_msg = saved_pitch if saved_pitch and len(saved_pitch) > 20 else ""
        if not default_msg:
            from pitch_builder import build_whatsapp_pitch
            default_msg = build_whatsapp_pitch(biz)

        # Auto-fill demo URL if exists
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
                        st.success("✅ נשלח!"); st.cache_data.clear()
                        time.sleep(1); st.rerun()

        with wa_col2:
            if st.button("סמן כנשלח ידנית", key=f"wa_manual_{biz['id']}", use_container_width=True):
                mark_sent_db(biz["id"], "whatsapp")
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
                    else:
                        st.error("נכשל — בדוק EMAIL_APP_PASSWORD ב-config.py")
            with em_col2:
                if st.button("סמן כנשלח ידנית", key=f"em_manual_{biz['id']}", use_container_width=True):
                    mark_sent_db(biz["id"], "email")
                    st.cache_data.clear(); st.rerun()

        st.markdown("---")
        st.markdown("#### 📝 הערות")
        notes_val = st.text_area(
            "", value=biz.get("notes") or "", height=80, key=f"notes_{biz['id']}",
            placeholder="הערות על הלקוח, תגובות, סטטוס..."
        )
        if st.button("💾 שמור הערות", key=f"save_notes_{biz['id']}"):
            save_notes(biz["id"], notes_val)
            st.success("נשמר"); st.cache_data.clear()

    # ── Outreach history ─────────────────────────────────────────
    with st.expander("📜 היסטוריית שליחות לליד זה"):
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
