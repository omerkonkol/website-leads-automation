"""
Helper: rebuild landing pages with a new base URL and write the updated manifest.
Run AFTER `wrangler pages deploy` succeeds and you have the live URL.

Usage:
    python scripts/deploy_and_update_manifest.py https://leads-landing-v2.pages.dev
"""
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python scripts/deploy_and_update_manifest.py <BASE_URL>")
    sys.exit(1)

base_url = sys.argv[1].rstrip("/")
print(f"Regenerating manifest with base URL: {base_url}")

# Re-import to avoid caching
sys.path.insert(0, str(Path(__file__).parent.parent / "generators"))
from leads_landing_v2 import load_leads, write_site

leads = load_leads(Path("e:/system/leads.db"))
out = Path("e:/system/leads-landing-pages")
write_site(leads, out, base_url)
print(f"\n✅ Manifest updated. WhatsApp campaign will pick it up automatically next run.")
