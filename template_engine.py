"""
template_engine.py — יוצר אתר דמו מתבנית HTML מוכנה.
ללא API, ללא טוקנים, תוך שנייה.
"""

import re
from pathlib import Path
from config import YOUR_NAME, YOUR_PHONE, YOUR_WHATSAPP_URL

# ── צבעים לפי קטגוריה ──────────────────────────────────────
CATEGORY_COLORS = {
    "מוסך":       ("#1a1a2e", "#e94560", "🔧"),
    "מסעדה":      ("#1a0a00", "#f97316", "🍽️"),
    "קפה":        ("#1a1200", "#ca8a04", "☕"),
    "קוסמטיקה":  ("#1a0a1a", "#a855f7", "✨"),
    "מספרה":      ("#0a0a1a", "#3b82f6", "✂️"),
    "שיפוצים":   ("#0a1a0a", "#22c55e", "🔨"),
    "שרברב":     ("#0a1a1a", "#06b6d4", "🔧"),
    "חשמלאי":    ("#0a0a1a", "#eab308", "⚡"),
    "עורך דין":  ("#0f172a", "#64748b", "⚖️"),
    "רואה חשבון":("#0f172a", "#475569", "📊"),
}
DEFAULT_COLORS = ("#0f172a", "#6366f1", "🏢")


def _get_colors(category: str):
    for key, val in CATEGORY_COLORS.items():
        if key in (category or ""):
            return val
    return DEFAULT_COLORS


def _services_for_category(category: str) -> list[tuple[str, str]]:
    """מחזיר 6 שירותים מותאמים לקטגוריה."""
    cats = {
        "מוסך": [
            ("🔧", "טיפול שוטף", "החלפת שמן, מסנן, ובדיקה מקיפה"),
            ("🛑", "מערכת בלמים", "בדיקה והחלפת רפידות ודיסקיות"),
            ("⚙️", "תיקון מנוע", "אבחון ותיקון כל תקלות המנוע"),
            ("❄️", "מיזוג אוויר", "טעינת גז ותיקון מערכת קירור"),
            ("🔌", "מערכת חשמל", "אבחון ותיקון בעיות חשמל ואלקטרוניקה"),
            ("🔩", "גיר ותיבה", "תיקון וכיוון מערכת ההנעה"),
        ],
        "מסעדה": [
            ("🥩", "מנות עיקריות", "בשרים טריים ומנות פרימיום"),
            ("🥗", "סלטים ומנות ראשונות", "ירקות טריים ורטבים ביתיים"),
            ("🍕", "מנות מיוחדות", "מנות השף המיוחדות של היום"),
            ("🍷", "בר ומשקאות", "מגוון יינות ומשקאות נבחרים"),
            ("🎂", "קינוחים", "קינוחים ביתיים ועוגות טריות"),
            ("📦", "משלוחים", "משלוח עד הבית תוך 30 דקות"),
        ],
        "קוסמטיקה": [
            ("✨", "טיפול פנים", "ניקוי עמוק ולחות לעור קורן"),
            ("💆", "עיסוי פנים", "טכניקות מרגיעות לעור מחודש"),
            ("💄", "מייקאפ", "איפור מקצועי לכל אירוע"),
            ("👁️", "טיפולי עיניים", "הרמת ריסים ועיצוב גבות"),
            ("🌿", "טיפולי גוף", "עיסוי ורפואה אלטרנטיבית"),
            ("💅", "מניקור פדיקור", "טיפוח ציפורניים מקצועי"),
        ],
    }
    for key, val in cats.items():
        if key in (category or ""):
            return val
    # ברירת מחדל
    return [
        ("⭐", "שירות מקצועי", "ניסיון של שנים בתחום"),
        ("🎯", "דיוק ואיכות", "תשומת לב לכל פרט"),
        ("⚡", "מהיר ויעיל", "עמידה בלוחות זמנים"),
        ("💰", "מחיר הוגן", "שקיפות מלאה בתמחור"),
        ("🤝", "שירות אישי", "ליווי צמוד לכל לקוח"),
        ("✅", "אחריות מלאה", "אחריות על כל העבודות"),
    ]


# ════════════════════════════════════════════════════════════════
#  תבנית ה-HTML
# ════════════════════════════════════════════════════════════════
def generate_html(
    name: str,
    category: str,
    phone: str,
    address: str,
    city: str = "",
    extra_info: str = "",
) -> str:

    bg, accent, icon = _get_colors(category)
    services = _services_for_category(category)
    wa_number = re.sub(r"[^\d]", "", phone)
    if wa_number.startswith("0"):
        wa_number = "972" + wa_number[1:]

    services_html = "\n".join(f"""
      <div class="card">
        <div class="card-icon">{s[0]}</div>
        <h3>{s[1]}</h3>
        <p>{s[2]}</p>
      </div>""" for s in services)

    year_est = "2005"   # ניתן לשנות
    city_display = city or (address.split()[-1] if address else "")

    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{name} — {category}</title>
  <link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;600;700;900&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg:     {bg};
      --accent: {accent};
      --text:   #f1f5f9;
      --muted:  #94a3b8;
      --card:   rgba(255,255,255,0.05);
      --border: rgba(255,255,255,0.08);
    }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: 'Heebo', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
    }}

    /* ── NAV ── */
    nav {{
      position: fixed; top: 0; width: 100%; z-index: 100;
      background: rgba(0,0,0,0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 0 5%;
      display: flex; align-items: center; justify-content: space-between;
      height: 60px;
    }}
    .nav-brand {{ font-weight: 900; font-size: 1.1rem; color: var(--text); }}
    .nav-phone {{
      background: var(--accent); color: #fff;
      padding: 8px 20px; border-radius: 25px;
      text-decoration: none; font-weight: 600; font-size: 0.9rem;
      transition: opacity .2s;
    }}
    .nav-phone:hover {{ opacity: 0.85; }}

    /* ── HERO ── */
    .hero {{
      min-height: 100vh;
      display: flex; align-items: center;
      padding: 80px 5% 60px;
      background:
        linear-gradient(135deg, {bg}ee 0%, {bg}99 60%, transparent 100%),
        url('https://images.unsplash.com/photo-1486262715619-67b85e0b08d3?w=1400&auto=format&fit=crop&q=80') center/cover no-repeat;
    }}
    .hero-content {{ max-width: 600px; }}
    .hero-badge {{
      display: inline-block;
      background: rgba(255,255,255,0.1);
      border: 1px solid var(--accent);
      color: var(--accent);
      padding: 4px 16px; border-radius: 20px;
      font-size: 0.85rem; font-weight: 600; margin-bottom: 20px;
    }}
    .hero h1 {{
      font-size: clamp(2rem, 5vw, 3.5rem);
      font-weight: 900; line-height: 1.15;
      margin-bottom: 16px;
    }}
    .hero h1 span {{ color: var(--accent); }}
    .hero p {{ color: var(--muted); font-size: 1.1rem; margin-bottom: 36px; max-width: 480px; }}
    .btn-primary {{
      display: inline-flex; align-items: center; gap: 8px;
      background: var(--accent); color: #fff;
      padding: 15px 32px; border-radius: 50px;
      text-decoration: none; font-weight: 700; font-size: 1rem;
      transition: transform .2s, box-shadow .2s;
      box-shadow: 0 0 30px {accent}55;
    }}
    .btn-primary:hover {{ transform: translateY(-2px); box-shadow: 0 8px 40px {accent}77; }}
    .btn-ghost {{
      display: inline-flex; align-items: center; gap: 8px;
      border: 2px solid var(--border); color: var(--text);
      padding: 13px 28px; border-radius: 50px;
      text-decoration: none; font-weight: 600; font-size: 1rem;
      margin-right: 12px;
      transition: border-color .2s;
    }}
    .btn-ghost:hover {{ border-color: var(--accent); }}
    .hero-stats {{
      display: flex; gap: 40px; margin-top: 48px;
      padding-top: 32px; border-top: 1px solid var(--border);
    }}
    .stat-num {{ font-size: 1.8rem; font-weight: 900; color: var(--accent); }}
    .stat-label {{ font-size: 0.8rem; color: var(--muted); }}

    /* ── SECTIONS ── */
    section {{ padding: 80px 5%; }}
    .section-label {{
      color: var(--accent); font-size: 0.85rem; font-weight: 700;
      text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px;
    }}
    h2 {{ font-size: clamp(1.6rem, 3vw, 2.4rem); font-weight: 900; margin-bottom: 16px; }}
    .section-sub {{ color: var(--muted); max-width: 520px; margin-bottom: 48px; }}

    /* ── SERVICES GRID ── */
    .services-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 20px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 28px 24px;
      transition: transform .25s, border-color .25s;
    }}
    .card:hover {{ transform: translateY(-4px); border-color: var(--accent); }}
    .card-icon {{ font-size: 2rem; margin-bottom: 16px; }}
    .card h3 {{ font-size: 1.05rem; font-weight: 700; margin-bottom: 8px; }}
    .card p {{ color: var(--muted); font-size: 0.9rem; }}

    /* ── WHY US ── */
    .why-grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 24px;
    }}
    .why-item {{ text-align: center; padding: 32px 20px; }}
    .why-num {{
      font-size: 2.5rem; font-weight: 900; color: var(--accent);
      line-height: 1; margin-bottom: 12px;
    }}
    .why-item h3 {{ font-size: 1rem; font-weight: 700; margin-bottom: 8px; }}
    .why-item p {{ color: var(--muted); font-size: 0.88rem; }}

    /* ── CONTACT ── */
    .contact-wrap {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 48px;
      align-items: start;
    }}
    @media (max-width: 680px) {{ .contact-wrap {{ grid-template-columns: 1fr; }} }}
    .contact-info h3 {{ font-size: 1.3rem; font-weight: 700; margin-bottom: 20px; }}
    .contact-row {{
      display: flex; align-items: center; gap: 12px;
      padding: 14px 0; border-bottom: 1px solid var(--border);
      color: var(--muted); font-size: 0.95rem;
    }}
    .contact-row strong {{ color: var(--text); }}
    form {{ display: flex; flex-direction: column; gap: 14px; }}
    input, textarea, select {{
      background: var(--card); border: 1px solid var(--border);
      color: var(--text); border-radius: 10px;
      padding: 13px 16px; font-family: inherit; font-size: 0.95rem;
      outline: none; transition: border-color .2s;
    }}
    input:focus, textarea:focus, select:focus {{ border-color: var(--accent); }}
    textarea {{ resize: vertical; min-height: 110px; }}
    input::placeholder, textarea::placeholder {{ color: var(--muted); }}
    .submit-btn {{
      background: var(--accent); color: #fff; border: none;
      padding: 14px; border-radius: 10px;
      font-weight: 700; font-size: 1rem; cursor: pointer;
      transition: opacity .2s;
    }}
    .submit-btn:hover {{ opacity: 0.88; }}

    /* ── FOOTER ── */
    footer {{
      border-top: 1px solid var(--border);
      padding: 32px 5%; text-align: center;
      color: var(--muted); font-size: 0.85rem;
    }}
    footer a {{ color: var(--muted); text-decoration: none; }}

    /* ── WHATSAPP FLOAT ── */
    .wa-float {{
      position: fixed; bottom: 28px; left: 28px; z-index: 999;
      background: #25D366; color: #fff;
      width: 56px; height: 56px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      font-size: 1.5rem; text-decoration: none;
      box-shadow: 0 4px 20px rgba(37,211,102,.5);
      transition: transform .2s;
    }}
    .wa-float:hover {{ transform: scale(1.1); }}

    /* ── ANIMATIONS ── */
    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(24px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .hero-content > * {{ animation: fadeUp .6s ease both; }}
    .hero-badge   {{ animation-delay: .1s; }}
    .hero h1      {{ animation-delay: .2s; }}
    .hero p       {{ animation-delay: .3s; }}
    .hero-ctas    {{ animation-delay: .4s; }}
    .hero-stats   {{ animation-delay: .5s; }}

    @media (max-width: 600px) {{
      .hero-stats {{ flex-wrap: wrap; gap: 24px; }}
      nav {{ padding: 0 4%; }}
    }}
  </style>
</head>
<body>

<!-- NAV -->
<nav>
  <span class="nav-brand">{icon} {name}</span>
  <a href="tel:{phone}" class="nav-phone">📞 {phone}</a>
</nav>

<!-- HERO -->
<section class="hero">
  <div class="hero-content">
    <span class="hero-badge">{icon} {category} מקצועי</span>
    <h1>{name}<br><span>{city_display}</span></h1>
    <p>שירות מקצועי ואמין, ניסיון של שנים, מחירים הוגנים. אנחנו כאן בשבילכם.</p>
    <div class="hero-ctas">
      <a href="#contact" class="btn-ghost">השאר פרטים</a>
      <a href="tel:{phone}" class="btn-primary">📞 התקשר עכשיו</a>
    </div>
    <div class="hero-stats">
      <div><div class="stat-num">18+</div><div class="stat-label">שנות ניסיון</div></div>
      <div><div class="stat-num">2,400+</div><div class="stat-label">לקוחות מרוצים</div></div>
      <div><div class="stat-num">98%</div><div class="stat-label">שביעות רצון</div></div>
    </div>
  </div>
</section>

<!-- SERVICES -->
<section id="services">
  <div class="section-label">השירותים שלנו</div>
  <h2>מה אנחנו מציעים</h2>
  <p class="section-sub">פתרונות מקצועיים לכל הצרכים שלכם, עם ציוד מתקדם וצוות מנוסה.</p>
  <div class="services-grid">
    {services_html}
  </div>
</section>

<!-- WHY US -->
<section style="background: rgba(255,255,255,0.02); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);">
  <div class="section-label">למה לבחור בנו</div>
  <h2>היתרון שלנו</h2>
  <div class="why-grid">
    <div class="why-item">
      <div class="why-num">18+</div>
      <h3>שנות ניסיון</h3>
      <p>בנינו מוניטין על בסיס איכות ואמינות לאורך שנים</p>
    </div>
    <div class="why-item">
      <div class="why-num">24/7</div>
      <h3>זמינות גבוהה</h3>
      <p>אנחנו זמינים לכם בכל עת, גם בשעות הערב</p>
    </div>
    <div class="why-item">
      <div class="why-num">100%</div>
      <h3>אחריות מלאה</h3>
      <p>אחריות על כל עבודה, שביעות רצון מובטחת</p>
    </div>
    <div class="why-item">
      <div class="why-num">₪</div>
      <h3>מחיר הוגן</h3>
      <p>שקיפות מלאה בתמחור, ללא הפתעות</p>
    </div>
  </div>
</section>

<!-- CONTACT -->
<section id="contact">
  <div class="section-label">צרו קשר</div>
  <h2>דברו איתנו</h2>
  <div class="contact-wrap">
    <div class="contact-info">
      <h3>פרטי התקשרות</h3>
      <div class="contact-row">📞 <span><strong>טלפון:</strong> {phone}</span></div>
      <div class="contact-row">📍 <span><strong>כתובת:</strong> {address}</span></div>
      <div class="contact-row">🕐 <span><strong>ראשון–חמישי:</strong> 8:00–18:00</span></div>
      <div class="contact-row">🕐 <span><strong>שישי:</strong> 8:00–14:00</span></div>
      <br>
      <a href="https://wa.me/{wa_number}" class="btn-primary" style="display:inline-flex; margin-top:8px;">
        💬 WhatsApp
      </a>
    </div>
    <form onsubmit="handleSubmit(event)">
      <input type="text"  placeholder="שם מלא"     required>
      <input type="tel"   placeholder="מספר טלפון"  required>
      <input type="email" placeholder="מייל (אופציונלי)">
      <textarea placeholder="איך נוכל לעזור לך?"></textarea>
      <button type="submit" class="submit-btn">שלח פנייה</button>
    </form>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <p>{name} | {address} | {phone}</p>
  <p style="margin-top:8px; font-size:0.8rem;">
    אתר זה נבנה על ידי <a href="tel:{YOUR_PHONE}">{YOUR_NAME}</a>
  </p>
</footer>

<!-- WHATSAPP FLOAT -->
<a href="https://wa.me/{wa_number}" class="wa-float" title="WhatsApp">💬</a>

<script>
function handleSubmit(e) {{
  e.preventDefault();
  e.target.innerHTML = '<p style="text-align:center;color:#22c55e;font-size:1.1rem;padding:20px">✅ הפנייה נשלחה! נחזור אליך בקרוב.</p>';
}}
// Smooth scroll for nav links
document.querySelectorAll('a[href^="#"]').forEach(a =>
  a.addEventListener('click', e => {{
    e.preventDefault();
    document.querySelector(a.getAttribute('href'))?.scrollIntoView({{behavior:'smooth'}});
  }})
);
</script>
</body>
</html>"""


# ════════════════════════════════════════════════════════════════
#  שמירה ופתיחה
# ════════════════════════════════════════════════════════════════
def create_demo(business: dict, open_browser: bool = True) -> str:
    """מקבל dict עסק → מחזיר נתיב לקובץ HTML שנוצר."""
    import webbrowser
    html = generate_html(
        name=business.get("name", ""),
        category=business.get("category") or business.get("search_query", "עסק"),
        phone=business.get("phone", ""),
        address=business.get("address", ""),
        city=business.get("city", ""),
        extra_info=business.get("extra_info", ""),
    )
    demos_dir = Path("demos")
    demos_dir.mkdir(exist_ok=True)
    safe = re.sub(r"[^\w\u0590-\u05FF]", "_", business.get("name", "demo"))
    path = demos_dir / f"demo_{safe}.html"
    path.write_text(html, encoding="utf-8")
    abs_path = str(path.resolve()).replace("\\", "/")
    if open_browser:
        webbrowser.open(f"file:///{abs_path}")
    return str(path.resolve())
