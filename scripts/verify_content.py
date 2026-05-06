"""Verify category-specific content (ticker items, services, pains) in a few pages."""
import sqlite3, pathlib, sys, re, unicodedata
sys.stdout.reconfigure(encoding='utf-8')

def slug(name, lid):
    s = unicodedata.normalize("NFKD", name).encode("ascii","ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return f"{s}-{lid}" if s else str(lid)

con = sqlite3.connect('e:/system/leads.db')
con.row_factory = sqlite3.Row

# Pick one lead from key categories with full coverage
categories_to_check = [
    ('מסעדה', 'אווירה ביתית'),
    ('מספרה', 'סטיילינג מותאם'),
    ('מכון יופי', 'אבחון אישי לפני טיפול'),
    ('עורך דין', 'דיסקרטיות מלאה'),
    ('שרברב', 'איתור נזילות'),
    ('חשמלאי', 'התקנות חשמל'),
    ('שיפוצניק', 'שיפוצים כלליים'),
    ('מוסך', 'אבחון מחשב'),
    ('בית קפה', 'קפה אומנותי'),
    ('מרפאת שיניים', 'בדיקות וניקוי'),
]

for cat, expected_text in categories_to_check:
    row = con.execute("""SELECT id, name FROM businesses
        WHERE category LIKE ? AND ((website IS NULL OR website='') OR (quality_score < 8))
          AND phone IS NOT NULL AND phone!=''
          AND (blacklisted IS NULL OR blacklisted=0)
          AND name LIKE '%א%' OR name LIKE '%מ%'
        LIMIT 1""", (f'%{cat}%',)).fetchone()
    if not row:
        print(f"  {cat:<20} no lead found"); continue
    p = pathlib.Path(f"e:/system/leads-landing-pages/l/{slug(row['name'], row['id'])}/index.html")
    if not p.exists():
        print(f"  {cat:<20} {row['id']:>5} file missing"); continue
    c = p.read_text(encoding='utf-8')
    has_text = expected_text in c
    has_pains = 'pain-list' in c
    has_ticker = 'ticker-track' in c
    has_services = 'מדויקים לכל צורך' in c
    has_swiper = 'testi-swiper' in c
    has_aos = c.count('data-aos') > 30
    print(f"  {cat:<20} {row['id']:>5} content_match={has_text!s:<5} pains={has_pains!s:<5} ticker={has_ticker!s:<5} services={has_services!s:<5} swiper={has_swiper!s:<5} aos={has_aos!s}")
con.close()
