import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect("e:/system/leads.db")
c = conn.cursor()

c.execute("PRAGMA table_info(businesses)")
cols = [row[1] for row in c.fetchall()]
print("columns:", cols)
print()

needle = "אור גבאי"
c.execute(
    "SELECT id, name, phone, category, city, owner_name, google_rating, google_reviews "
    "FROM businesses WHERE name LIKE ? OR owner_name LIKE ?",
    (f"%{needle}%", f"%{needle}%"),
)
rows = c.fetchall()
print(f"matches for '{needle}': {len(rows)}")
for r in rows:
    print(r)

print()
c.execute(
    "SELECT id, name, phone, category, city, owner_name "
    "FROM businesses WHERE category LIKE ? LIMIT 5",
    ("%מאמן%",),
)
rows2 = c.fetchall()
print(f"first 5 'מאמן*' category: {len(rows2)}")
for r in rows2:
    print(r)

print()
c.execute("SELECT DISTINCT category FROM businesses WHERE category LIKE ? OR category LIKE ?", ("%כושר%", "%fitness%"))
print("fitness-related categories:", c.fetchall())

conn.close()
