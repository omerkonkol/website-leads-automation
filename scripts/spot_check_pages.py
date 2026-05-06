"""Spot-check generated pages: verify category-appropriate colors, ticker items, services."""
import sqlite3, pathlib, sys, re
sys.stdout.reconfigure(encoding='utf-8')

con = sqlite3.connect('e:/system/leads.db')
con.row_factory = sqlite3.Row
# Pick one lead from each major category
samples_q = """
WITH ranked AS (
  SELECT id, name, category,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY id) AS rn
  FROM businesses
  WHERE ((website IS NULL OR website='') OR (quality_score < 8))
    AND phone IS NOT NULL AND phone!=''
    AND (blacklisted IS NULL OR blacklisted=0)
    AND name LIKE '%א%' -- Hebrew names
)
SELECT id, name, category FROM ranked WHERE rn = 1 AND category IS NOT NULL
ORDER BY category LIMIT 14
"""
import unicodedata
def slug(name, lid):
    s = unicodedata.normalize("NFKD", name).encode("ascii","ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return f"{s}-{lid}" if s else str(lid)

print(f'{"category":<22} {"id":>5} {"name":<30} {"file?":<6} {"size_kb":>7} {"accent_color":<10}')
print('-' * 100)
for r in con.execute(samples_q):
    sl = slug(r['name'], r['id'])
    p = pathlib.Path(f'e:/system/leads-landing-pages/l/{sl}/index.html')
    if not p.exists():
        print(f"{(r['category'] or '-')[:21]:<22} {r['id']:>5} {(r['name'] or '-')[:29]:<30} {'NO':<6}")
        continue
    c = p.read_text(encoding='utf-8')
    # Find brand-primary color from tailwind config
    m = re.search(r"'brand-primary': '(#[0-9A-Fa-f]+)'", c)
    color = m.group(1) if m else '?'
    print(f"{(r['category'] or '-')[:21]:<22} {r['id']:>5} {(r['name'] or '-')[:29]:<30} {'YES':<6} {len(c)//1024:>7} {color:<10}")
con.close()
