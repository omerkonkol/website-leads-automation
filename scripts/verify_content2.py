"""Better verification — fix OR/AND priority bug, use parameterized properly."""
import sqlite3, pathlib, sys, re, unicodedata
sys.stdout.reconfigure(encoding='utf-8')

def slug(name, lid):
    s = unicodedata.normalize("NFKD", name).encode("ascii","ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return f"{s}-{lid}" if s else str(lid)

con = sqlite3.connect('e:/system/leads.db')
con.row_factory = sqlite3.Row

categories = [
    ('מסעדה', 'אווירה ביתית', '#C44536'),
    ('מספרה', 'סטיילינג מותאם', '#3D5468'),
    ('מכון יופי', 'אבחון אישי לפני טיפול', '#C9849A'),
    ('עורך דין', 'דיסקרטיות מלאה', '#A47551'),
    ('שרברב', 'איתור נזילות', '#3E92CC'),
    ('חשמלאי', 'התקנות חשמל', '#D4A33C'),
    ('שיפוצים', 'שיפוצים כלליים', '#7CA982'),
    ('מוסך', 'אבחון מחשב', '#5C7A88'),
    ('בית קפה', 'קפה אומנותי', '#9B5E3F'),
    ('מרפאת שיניים', 'בדיקות וניקוי', '#3E92CC'),
    ('רואה חשבון', 'הנהלת חשבונות', '#5C8374'),
]

print(f'{"category":<18} {"id":>5}  {"text_ok":<8}{"color_ok":<9}{"unique_ticker":<14}')
print('-' * 80)

for cat, expected_text, expected_color in categories:
    row = con.execute("""
        SELECT id, name FROM businesses
        WHERE category LIKE ?
          AND ((website IS NULL OR website='') OR (quality_score < 8))
          AND phone IS NOT NULL AND phone != ''
          AND (blacklisted IS NULL OR blacklisted = 0)
          AND name GLOB '*[א-ת]*'
        ORDER BY id LIMIT 1
    """, (f'%{cat}%',)).fetchone()
    if not row:
        print(f"  {cat:<18} no Hebrew lead found")
        continue
    p = pathlib.Path(f"e:/system/leads-landing-pages/l/{slug(row['name'], row['id'])}/index.html")
    if not p.exists():
        print(f"  {cat:<18} {row['id']:>5}  file missing"); continue
    c = p.read_text(encoding='utf-8')
    text_ok = expected_text in c
    color_ok = expected_color in c
    # Check ticker has 5 distinct items (not all from default)
    ticker_titles = re.findall(r'font-black text-white text-base sm:text-xl whitespace-nowrap">([^<]+)<', c)
    unique_titles = len(set(ticker_titles[:5]))  # first 5 (before duplicate)
    print(f"  {cat:<18} {row['id']:>5}  {'OK' if text_ok else 'NO':<8}{'OK' if color_ok else 'NO':<9}{unique_titles}/5")

con.close()
