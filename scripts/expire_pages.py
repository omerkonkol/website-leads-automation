"""
expire_pages.py — weekly cleanup of expired landing pages.

Logic (runs 7 days after whatsapp_sent_at):
  - Responded leads  → delete page folder, keep lead in DB
  - Silent leads     → delete page folder + set blacklisted=1 (won't be contacted again)

Usage:
    py scripts/expire_pages.py                  # dry run (no changes)
    py scripts/expire_pages.py --apply          # actually delete + update DB
    py scripts/expire_pages.py --apply --deploy # also redeploy to Cloudflare Pages
"""
from __future__ import annotations
import argparse
import re
import shutil
import sqlite3
import subprocess
import sys
import unicodedata
from pathlib import Path

DB_PATH    = Path("e:/system/leads.db")
PAGES_DIR  = Path("e:/system/leads-landing-pages")
DEPLOY_DIR = PAGES_DIR  # same dir we deploy from
CF_PROJECT = "leads-landing-v2"

sys.stdout.reconfigure(encoding="utf-8")


def slug(name: str, lid: int) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    s = re.sub(r"-+", "-", s)
    return f"{s}-{lid}" if s else str(lid)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply",  action="store_true", help="Actually delete files and update DB")
    ap.add_argument("--deploy", action="store_true", help="Redeploy to Cloudflare Pages after cleanup")
    ap.add_argument("--days",   type=int, default=7, help="Expiry window in days (default: 7)")
    ap.add_argument("--db",     default=str(DB_PATH))
    args = ap.parse_args()

    db_path = Path(args.db)
    dry = not args.apply

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    # Leads that were sent to and have passed the expiry window
    expired = con.execute(f"""
        SELECT id, name, phone, category, pipeline_stage, last_response
        FROM businesses
        WHERE whatsapp_sent = 1
          AND whatsapp_sent_at IS NOT NULL
          AND whatsapp_sent_at < datetime('now', '-{args.days} days')
          AND (blacklisted IS NULL OR blacklisted = 0)
        ORDER BY id
    """).fetchall()

    if not expired:
        print("✓ No expired leads found.")
        con.close()
        return

    print(f"{'DRY RUN — ' if dry else ''}Found {len(expired)} expired leads\n")
    print(f"{'id':<6} {'name':<28} {'stage':<14} {'responded':<10} {'page':<6} {'action'}")
    print("-" * 90)

    deleted = 0
    blacklisted = 0

    for row in expired:
        responded = (
            row["pipeline_stage"] == "responded"
            or bool(row["last_response"])
        )
        sl = slug(row["name"] or "", row["id"])
        page_dir = PAGES_DIR / "l" / sl
        page_exists = page_dir.exists()

        action = "skip (no page)" if not page_exists else (
            "delete page — keep lead (responded)" if responded
            else "delete page + blacklist (no reply)"
        )

        print(
            f"{row['id']:<6} {(row['name'] or '')[:27]:<28} "
            f"{(row['pipeline_stage'] or '-')[:13]:<14} "
            f"{'YES' if responded else 'no':<10} "
            f"{'YES' if page_exists else 'no':<6} "
            f"{action}"
        )

        if dry or not page_exists:
            continue

        # Delete the page directory
        shutil.rmtree(page_dir)
        deleted += 1

        if not responded:
            con.execute(
                "UPDATE businesses SET blacklisted=1 WHERE id=?",
                (row["id"],),
            )
            blacklisted += 1

    if not dry:
        con.commit()
        print(f"\n✓ Deleted {deleted} page(s), blacklisted {blacklisted} lead(s).")
    else:
        print(f"\n(dry run) Would delete {sum(1 for r in expired if (PAGES_DIR/'l'/slug(r['name'] or '',r['id'])).exists())} page(s).")

    con.close()

    if args.deploy and not dry and deleted > 0:
        print("\nDeploying to Cloudflare Pages...")
        result = subprocess.run(
            ["wrangler", "pages", "deploy", str(DEPLOY_DIR),
             "--project-name", CF_PROJECT, "--branch", "main"],
            cwd=str(DEPLOY_DIR),
        )
        if result.returncode == 0:
            print("✓ Deployed successfully.")
        else:
            print("✗ Deploy failed — check wrangler output above.")


if __name__ == "__main__":
    main()
