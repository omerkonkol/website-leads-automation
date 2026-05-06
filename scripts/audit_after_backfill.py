# -*- coding: utf-8 -*-
"""
audit_after_backfill.py — דוח high-ticket לאחר backfill.
מציג: כמה לידים נשארים אחרי סינון high-ticket, מהם פעילים מאומתים,
מהם בלי אתר/אתר גרוע, וכמה HOT.

Usage:
    py scripts/audit_after_backfill.py
"""
from __future__ import annotations

import sqlite3
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.lead_scorer import HIGH_TICKET_INDUSTRIES
from config import DB_PATH


def is_high_ticket(biz: dict) -> bool:
    cat = ((biz.get("category") or "") + " " + (biz.get("search_query") or "")).lower()
    return any(kw.lower() in cat for kw in HIGH_TICKET_INDUSTRIES)


def needs_website(biz: dict) -> str:
    has_site = bool(biz.get("website") or biz.get("has_website"))
    if not has_site:
        return "no_site"
    q = biz.get("quality_score") or 0
    if q == 0:
        return "site_unanalyzed"
    if q <= 4:
        return "bad_site"
    if q <= 6:
        return "mediocre_site"
    return "good_site"


def main():
    out = open(ROOT / "scripts" / "audit_report.txt", "w", encoding="utf-8")
    def p(*a): print(*a); print(*a, file=out)

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM businesses").fetchall()]
    n = len(rows)
    p(f"\n========== TOTAL: {n} leads ==========\n")

    # ── 1. signal coverage ──
    verified = sum(1 for r in rows if r.get("verified_at"))
    analyzed = sum(1 for r in rows if (r.get("quality_score") or 0) > 0)
    active   = sum(1 for r in rows if r.get("is_likely_active") == 1)
    inactive = sum(1 for r in rows if r.get("is_likely_active") == 0)
    p("--- 1. כיסוי signals ---")
    p(f"  verified_at:           {verified}/{n}  ({100*verified/n:.0f}%)")
    p(f"  quality_score > 0:     {analyzed}/{n}  ({100*analyzed/n:.0f}%)")
    p(f"  is_likely_active=1:    {active}/{n}")
    p(f"  is_likely_active=0:    {inactive}/{n}")

    # ── 2. high-ticket filter ──
    ht = [r for r in rows if is_high_ticket(r)]
    p(f"\n--- 2. high-ticket בלבד: {len(ht)}/{n} ({100*len(ht)/n:.0f}%) ---")

    if not ht:
        p("  אין לידים high-ticket במסד הנוכחי.")
        return

    by_cat: Counter = Counter()
    for r in ht:
        cat = (r.get("category") or "").strip() or (r.get("search_query") or "").strip() or "(unknown)"
        by_cat[cat[:40]] += 1
    for cat, c in by_cat.most_common(15):
        p(f"  {cat:42s}  {c}")

    # ── 3. high-ticket × tiers ──
    hot  = sum(1 for r in ht if (r.get("lead_score") or 0) >= 70)
    warm = sum(1 for r in ht if 45 <= (r.get("lead_score") or 0) < 70)
    cold = sum(1 for r in ht if (r.get("lead_score") or 0) < 45)
    p(f"\n--- 3. high-ticket × tier ---")
    p(f"  HOT  (70+):    {hot}")
    p(f"  WARM (45-69):  {warm}")
    p(f"  COLD (<45):    {cold}")

    # ── 4. high-ticket × website status ──
    p(f"\n--- 4. high-ticket × סטטוס אתר ---")
    site_status: Counter = Counter()
    for r in ht:
        site_status[needs_website(r)] += 1
    for k, v in site_status.most_common():
        p(f"  {k:20s}  {v}")

    # ── 5. high-ticket × activity ──
    p(f"\n--- 5. high-ticket × אימות פעילות ---")
    act_v = sum(1 for r in ht if r.get("verified_at"))
    act_a = sum(1 for r in ht if r.get("is_likely_active") == 1)
    act_i = sum(1 for r in ht if r.get("is_likely_active") == 0)
    p(f"  אומתו (verified_at):  {act_v}/{len(ht)}")
    p(f"  פעיל (is_likely=1):   {act_a}")
    p(f"  לא פעיל (=0):         {act_i}")

    # ── 6. הליד האידיאלי ──
    ideal = [
        r for r in ht
        if r.get("is_likely_active") == 1
        and (r.get("lead_score") or 0) >= 70
        and needs_website(r) in ("no_site", "bad_site", "site_unanalyzed")
    ]
    p(f"\n--- 6. ליד אידיאלי: high-ticket + פעיל מאומת + HOT + צריך אתר ---")
    p(f"  סה\"כ: {len(ideal)}")

    if ideal:
        ideal.sort(key=lambda r: r.get("lead_score") or 0, reverse=True)
        p(f"\n  TOP 20:")
        p(f"  {'score':>5}  {'name':40s}  {'category':25s}  {'site':20s}  {'phone':12s}  {'source':15s}")
        for r in ideal[:20]:
            p(f"  {r.get('lead_score') or 0:5d}  "
              f"{(r.get('name') or '')[:40]:40s}  "
              f"{(r.get('category') or '')[:25]:25s}  "
              f"{needs_website(r):20s}  "
              f"{(r.get('phone') or '')[:12]:12s}  "
              f"{(r.get('source') or '')[:15]:15s}")

    # ── 7. recommendation ──
    p(f"\n--- 7. המלצה ---")
    if len(ideal) >= 30:
        p(f"  יש {len(ideal)} לידי high-ticket אידיאליים. די להתחיל outreach. שלב 3 (מקורות חדשים) לא דחוף.")
    elif len(ideal) >= 10:
        p(f"  יש {len(ideal)} לידים אידיאליים. מספיק ל-batch ראשון, אבל כדאי להוסיף מקורות (שלב 3) במקביל.")
    else:
        p(f"  רק {len(ideal)} לידים אידיאליים. צריך להוסיף את שלב 3 (4 מקורות רשמיים) לפני outreach רציני.")

    out.close()
    con.close()


if __name__ == "__main__":
    main()
