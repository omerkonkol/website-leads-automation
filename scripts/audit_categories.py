"""Audit which categories exist in the DB and which are covered by our v3 dicts."""
import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'e:/system/generators')
from leads_landing_v3 import (
    CATEGORY_BRAND, CATEGORY_HERO, CATEGORY_PAINS, CATEGORY_CALLOUT,
    CATEGORY_PROMISE, CATEGORY_PROMISE_CARDS, CATEGORY_BADGE,
    CATEGORY_SERVICES, CATEGORY_STATS, CATEGORY_TICKER, CATEGORY_FINAL_CTA,
    _has_hebrew, _match,
)

con = sqlite3.connect('e:/system/leads.db')
con.row_factory = sqlite3.Row
rows = con.execute("""
    SELECT category, COUNT(*) as n FROM businesses
    WHERE ((website IS NULL OR website='') OR (quality_score < 8))
      AND phone IS NOT NULL AND phone!=''
      AND (blacklisted IS NULL OR blacklisted=0)
    GROUP BY category ORDER BY n DESC
""").fetchall()
con.close()

print(f'{"category":<30} {"leads":>6}  {"BRAND":<6}{"HERO":<6}{"PAINS":<6}{"PROM":<6}{"CARDS":<6}{"BADGE":<6}{"SVC":<6}{"STATS":<6}{"TICK":<6}{"CTA":<6}')
print('-' * 140)
total_covered = 0
total_default = 0
for r in rows:
    cat = (r['category'] or '').strip()
    n = r['n']
    if not cat:
        print(f'{"(none)":<30} {n:>6}  --- (will use DEFAULT for everything)')
        total_default += n
        continue
    def has(d):
        return any(k in cat for k in d.keys())
    flags = [has(d) for d in (CATEGORY_BRAND, CATEGORY_HERO, CATEGORY_PAINS,
             CATEGORY_PROMISE, CATEGORY_PROMISE_CARDS, CATEGORY_BADGE,
             CATEGORY_SERVICES, CATEGORY_STATS, CATEGORY_TICKER, CATEGORY_FINAL_CTA)]
    cells = ''.join('✓     ' if f else '·     ' for f in flags)
    print(f'{cat:<30} {n:>6}  {cells}')
    if all(flags): total_covered += n
    else: total_default += n

print()
print(f'Fully covered leads: {total_covered}')
print(f'Leads using some DEFAULTs: {total_default}')
