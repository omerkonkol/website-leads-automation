# -*- coding: utf-8 -*-
"""
backfill_existing.py — מריץ verify_business + analyze_website על כל הלידים
הקיימים, ומחשב מחדש lead_score. idempotent: דולג על מה שכבר נבדק.

Usage:
    py scripts/backfill_existing.py            # backfill כל מה שלא נבדק
    py scripts/backfill_existing.py --rescore  # רק מחשב מחדש ציונים
    py scripts/backfill_existing.py --limit 50 # רק 50 לידים (לבדיקה)
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from analysis.business_verifier import verify_business
from analysis.analyzer import analyze_website
from core.lead_scorer import compute_lead_score, score_tier_hebrew
from config import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _fetch_all(conn) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM businesses ORDER BY id").fetchall()]


def _update(conn, biz_id: int, updates: dict) -> None:
    if not updates:
        return
    fields = ", ".join(f"{k}=?" for k in updates)
    values = list(updates.values()) + [biz_id]
    conn.execute(f"UPDATE businesses SET {fields} WHERE id=?", values)
    conn.commit()


def backfill_verifier(conn, rows: list[dict], limit: int | None = None) -> dict:
    todo = [r for r in rows if r.get("verified_at") is None]
    if limit:
        todo = todo[:limit]

    print(f"\n=== verify_business: {len(todo)} leads need verification ===")
    stats = {"verified_active": 0, "verified_inactive": 0, "errors": 0}

    for i, biz in enumerate(todo, 1):
        try:
            result = verify_business(biz)
            updates = {
                "activity_score":   result["activity_score"],
                "is_likely_active": 1 if result["is_likely_active"] else 0,
                "activity_details": json.dumps(result["reasons"], ensure_ascii=False),
                "verified_at":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            _update(conn, biz["id"], updates)
            if result["is_likely_active"]:
                stats["verified_active"] += 1
            else:
                stats["verified_inactive"] += 1
            tag = "OK" if result["is_likely_active"] else "X"
            print(f"  [{i:3d}/{len(todo)}] [{tag}] {biz.get('name','?')[:40]:40s}  score={result['activity_score']}")
        except KeyboardInterrupt:
            print("\n  Interrupted — progress saved.")
            raise
        except Exception as e:
            stats["errors"] += 1
            print(f"  [{i:3d}/{len(todo)}] ERR  {biz.get('name','?')[:40]:40s}  {e}")
        time.sleep(0.2)

    return stats


def backfill_analyzer(conn, rows: list[dict], limit: int | None = None) -> dict:
    todo = [
        r for r in rows
        if (r.get("website") or r.get("has_website"))
        and not (r.get("quality_score") or 0) > 0
    ]
    if limit:
        todo = todo[:limit]

    print(f"\n=== analyze_website: {len(todo)} sites need analysis ===")
    stats = {"analyzed": 0, "errors": 0}

    for i, biz in enumerate(todo, 1):
        url = biz.get("website") or ""
        if not url:
            continue
        try:
            a = analyze_website(url)
            updates = {
                k: a.get(k) for k in [
                    "has_website", "has_ssl", "is_responsive",
                    "has_cta", "has_form", "has_fb_pixel",
                    "has_analytics", "load_time_ms", "quality_score",
                    "cms_platform", "seo_score", "has_title_tag",
                    "has_meta_desc", "has_h1", "has_robots_txt",
                    "has_sitemap", "copyright_year",
                    "pagespeed_score", "core_web_vitals",
                ] if a.get(k) is not None
            }
            if a.get("issues"):
                updates["issues"] = json.dumps(a["issues"], ensure_ascii=False)
            _update(conn, biz["id"], updates)
            stats["analyzed"] += 1
            print(f"  [{i:3d}/{len(todo)}] OK   {biz.get('name','?')[:35]:35s}  q={a.get('quality_score')}/10  cms={a.get('cms_platform') or '-'}")
        except KeyboardInterrupt:
            print("\n  Interrupted — progress saved.")
            raise
        except Exception as e:
            stats["errors"] += 1
            print(f"  [{i:3d}/{len(todo)}] ERR  {biz.get('name','?')[:35]:35s}  {e}")
        time.sleep(0.3)

    return stats


def rescore_all(conn) -> dict:
    rows = _fetch_all(conn)
    print(f"\n=== rescore: {len(rows)} leads ===")
    tiers = {"hot": 0, "warm": 0, "cold": 0}
    for r in rows:
        score, _ = compute_lead_score(r)
        _update(conn, r["id"], {"lead_score": score})
        if score >= 70:   tiers["hot"]  += 1
        elif score >= 45: tiers["warm"] += 1
        else:             tiers["cold"] += 1
    return tiers


def normalize_active_flag(conn) -> int:
    """לידים שלא עברו verify מקבלים is_likely_active=NULL (לא 1)."""
    cur = conn.execute(
        "UPDATE businesses SET is_likely_active=NULL "
        "WHERE verified_at IS NULL AND is_likely_active=1"
    )
    conn.commit()
    return cur.rowcount


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rescore", action="store_true", help="rescore only, no verify/analyze")
    ap.add_argument("--limit", type=int, default=None, help="cap leads (testing)")
    ap.add_argument("--skip-verify", action="store_true")
    ap.add_argument("--skip-analyze", action="store_true")
    args = ap.parse_args()

    print(f"DB: {DB_PATH}")
    conn = _connect()

    fixed = normalize_active_flag(conn)
    if fixed:
        print(f"Normalized is_likely_active on {fixed} unverified leads -> NULL")

    rows = _fetch_all(conn)
    print(f"Total leads: {len(rows)}")

    if not args.rescore:
        if not args.skip_verify:
            backfill_verifier(conn, rows, args.limit)
            rows = _fetch_all(conn)
        if not args.skip_analyze:
            backfill_analyzer(conn, rows, args.limit)

    tiers = rescore_all(conn)
    print(f"\nFinal tiers: HOT={tiers['hot']}  WARM={tiers['warm']}  COLD={tiers['cold']}")

    final = _fetch_all(conn)
    verified = sum(1 for r in final if r.get("verified_at"))
    analyzed = sum(1 for r in final if (r.get("quality_score") or 0) > 0)
    print(f"verified_at: {verified}/{len(final)}")
    print(f"quality_score>0: {analyzed}/{len(final)}")

    conn.close()


if __name__ == "__main__":
    main()
