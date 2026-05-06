"""
leads_email_campaign.py — Email parallel of the WhatsApp leads campaign.

Mirrors whatsapp-api/src/controllers/leads_campaign.controller.ts and
whatsapp-api/src/utils/leads_message.ts: same Hebrew message body, same
manifest-driven per-lead URL, same DB filter (excludes already-contacted leads),
but sent via Gmail SMTP instead of WhatsApp Web.

Email has no daily quota like WhatsApp does, but we still apply a sane
default cap and a small delay between sends to stay under Gmail's
reputation thresholds.

Usage:
    py -c "from outreach.leads_email_campaign import run; run(dry_run=True)"
    py -c "from outreach.leads_email_campaign import run; run(dry_run=False, daily_limit=200)"
    py -c "from outreach.leads_email_campaign import run; run(dry_run=False, only_lead_id=868)"
"""

import csv
import re
import smtplib
import sys
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid
from pathlib import Path

from config import EMAIL_SENDER, EMAIL_APP_PASSWORD, YOUR_NAME, SMTP_HOST, SMTP_PORT
from core.database import get_conn, mark_sent

sys.stdout.reconfigure(encoding="utf-8")

MANIFEST_PATH = Path("e:/system/leads-landing-pages/manifest.csv")
SEND_DELAY_SECONDS = 4
DEFAULT_DAILY_LIMIT = 100

# ── Hebrew helpers — Python ports of whatsapp-api/src/utils/leads_message.ts ──

CITY_HE = {
    "jerusalem": "ירושלים", "tel aviv": "תל אביב", "tel-aviv": "תל אביב",
    "tel aviv-yafo": "תל אביב", "petah tikva": "פתח תקווה",
    "petach tikva": "פתח תקווה", "petah-tikva": "פתח תקווה",
    "haifa": "חיפה", "rishon": "ראשון לציון", "rishon lezion": "ראשון לציון",
    "rishon le zion": "ראשון לציון", "rishon-lezion": "ראשון לציון",
    "ramat gan": "רמת גן", "ramat-gan": "רמת גן", "bnei brak": "בני ברק",
    "holon": "חולון", "bat yam": "בת ים", "ashdod": "אשדוד",
    "netanya": "נתניה", "ashkelon": "אשקלון", "beer sheva": "באר שבע",
    "be'er sheva": "באר שבע", "rehovot": "רחובות", "herzliya": "הרצליה",
    "kfar saba": "כפר סבא", "kfar-saba": "כפר סבא", "raanana": "רעננה",
    "modi'in": "מודיעין", "modiin": "מודיעין", "lod": "לוד", "ramla": "רמלה",
}

HEBREW_RE = re.compile(r"[֐-׿]")


def _has_hebrew(s):
    return bool(s and HEBREW_RE.search(s))


def _workplace_word(category):
    c = (category or "").strip()
    if not c:
        return "לעסק"
    if re.search(r"עורך דין|משרד עורכי דין|נוטריון", c):
        return "למשרד"
    if re.search(r'רואה חשבון|רו"ח', c):
        return "למשרד"
    if re.search(r"מרפאה|מרפאת|רופא|וטרינר|קליניקה", c):
        return "למרפאה"
    if re.search(r"מסעדה|פיצ|בית קפה|פאב|בר|דיינר", c):
        return "למסעדה"
    if re.search(r"מספרה|ברבר|סלון", c):
        return "לסלון"
    if re.search(r"חנות|שוק|בוטיק", c):
        return "לחנות"
    if re.search(r"אולם", c):
        return "לאולם"
    if re.search(r"מוסך|גרז'", c):
        return "למוסך"
    if re.search(r"סטודיו", c):
        return "לסטודיו"
    if re.search(r"בית ספר|מוסד|אקדמיה", c):
        return "למוסד"
    return "לעסק"


def _split_credentials(name):
    m = re.match(r"^(.*?)\s*\(([^)]+)\)\s*$", name)
    if m:
        trimmed = re.sub(r"[,，]\s*$", "", m.group(1).strip())
        return trimmed, m.group(2).strip()
    return name.strip(), None


def _translate_credentials(creds):
    return (
        creds
        .replace("Harvard", "הרווארד")
        .replace("MIT", "MIT")
        .replace("Oxford", "אוקספורד")
        .replace("Cambridge", "קיימברידג'")
        .replace("Stanford", "סטנפורד")
        .replace("Yale", "ייל")
    )


def _rating_opener(rating, count):
    if not rating or not count:
        return None
    if rating < 4.5 or count < 10:
        return None
    return f"ראינו את הדירוג המרשים שלכם בגוגל ({rating:.1f}★ עם {count}+ ביקורות)"


def build_lead_email_message_no_site(lead, url):
    """Variant A — for leads with NO website. Mirrors WhatsApp message."""
    workplace = _workplace_word(lead.get("category"))
    trimmed_name, credentials = _split_credentials(lead["name"])
    credentials_he = _translate_credentials(credentials) if credentials else None
    rating_line = _rating_opener(lead.get("google_rating"), lead.get("google_reviews"))

    if credentials_he:
        first = (
            f"שלום, {trimmed_name}. נחשפנו לרקע המקצועי המרשים שלכם "
            f"({credentials_he}) ושמנו לב שאין {workplace} אתר רשמי."
        )
    elif rating_line:
        first = f"שלום, {trimmed_name}. {rating_line} ושמנו לב שאין {workplace} אתר רשמי."
    else:
        first = f"שלום, {trimmed_name}. שמנו לב שאין {workplace} אתר רשמי."

    return (
        f"{first}\n\n"
        f"היום, הצעד הראשון של כל לקוח הוא חיפוש בגוגל – ונוכחות דיגיטלית היא "
        f"הדרך היחידה לוודא שהרושם הראשוני שהם מקבלים תואם את הרמה המקצועית "
        f"שלכם. כדי להראות לכם את הפוטנציאל, בנינו עבורכם סקיצה ראשונית:\n"
        f"{url}\n"
        f"כמובן שניתן לערוך ולשדרג, וזו אינה התוצאה הסופית.\n\n"
        f"אנחנו ב-NovaDigital מציעים כרגע בניית דף נחיתה מקצועי ב-389 ש\"ח בלבד "
        f"(כולל חודש אחסון מתנה). משלמים רק אם מרוצים מהתוצאה.\n\n"
        f"אם זה רלוונטי, נשמח לשלוח פרטים נוספים."
    )


def build_lead_email_message_low_quality(lead, url):
    """Variant B — for leads WITH a low-quality website. User-supplied copy."""
    biz_name    = lead["name"]
    owner_name  = (lead.get("owner_name") or "").strip() or biz_name
    return (
        f"היי {owner_name}, ראיתי את האתר שלכם והיה לי חשוב ליצור קשר.\n\n"
        f"היום, האתר הוא לא רק 'כרטיס ביקור', הוא איש המכירות שעובד עבורכם 24/7. "
        f"כשהאתר איטי או לא מותאם לנייד, לקוחות פוטנציאליים נוטים לעבור למתחרים "
        f"תוך שניות בודדות.\n\n"
        f"שדרוג לאתר מודרני, מהיר ומעוצב יכול להקפיץ משמעותית את כמות הפניות "
        f"ואת האמון שהלקוחות נותנים בכם עוד לפני השיחה הראשונה.\n\n"
        f"צירפתי כאן דוגמה לאתר שבניתי (בסגנון שיכול מאוד להתאים לכם) "
        f"כדי שתוכלו להתרשם מהסטנדרט היום:\n"
        f"{url}\n\n"
        f"אשמח לשלוח לכם כמה נקודות ספציפיות לשיפור שאפשר ליישם אצלכם."
    )


def _pick_variant(lead):
    """Returns ('no_site' | 'low_quality', subject, message_text) for the given lead."""
    has_site = bool((lead.get("website") or "").strip())
    biz_name = lead["name"]
    if has_site:
        return "low_quality", f"שדרוג הנוכחות הדיגיטלית של {biz_name}", build_lead_email_message_low_quality
    return "no_site", f"הצעה לאתר אינטרנט עבור {biz_name}", build_lead_email_message_no_site


def build_lead_email_html(business_name, message_text, url):
    """Wraps the plain-text message in a minimal RTL HTML so Gmail renders cleanly."""
    paragraphs = []
    for para in message_text.split("\n\n"):
        # Linkify the URL inside the paragraph
        safe = para.replace(url, f'<a href="{url}" style="color:#0a66c2;">{url}</a>')
        safe_html = safe.replace("\n", "<br>")
        paragraphs.append(f'<p style="margin:0 0 14px 0;">{safe_html}</p>')
    body = "\n".join(paragraphs)

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head><meta charset="UTF-8"><title>הצעה לבניית אתר עבור {business_name}</title></head>
<body style="margin:0;padding:24px;background:#f5f5f5;font-family:Arial,Helvetica,sans-serif;direction:rtl;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" bgcolor="#ffffff" style="border-radius:8px;padding:32px;font-size:15px;line-height:1.7;color:#222;">
        <tr><td>
{body}
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


# ── Manifest loader ───────────────────────────────────────────────────

def _load_manifest_url_map():
    """Returns {lead_id: full_url} from the v2 manifest CSV."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest not found at {MANIFEST_PATH}")
    url_map = {}
    with MANIFEST_PATH.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                lead_id = int(row["id"])
            except (KeyError, ValueError, TypeError):
                continue
            full_url = (row.get("full_url") or "").strip()
            if full_url:
                url_map[lead_id] = full_url
    return url_map


# ── Lead loader (mirrors WhatsApp campaign filter, plus email-specific) ──

def _load_eligible_leads():
    """
    Pending email candidates: leads with email + not yet emailed + not blacklisted.
    Includes both no-website leads AND has-website-but-low-quality (quality_score < 8) leads.
    Excludes good websites (quality_score >= 8) to avoid spamming professional sites.
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT id, name, phone, email, website, category, city, owner_name,
               google_rating, google_reviews, lead_score, quality_score
        FROM businesses
        WHERE ((website IS NULL OR website = '') OR (quality_score < 8))
          AND email IS NOT NULL AND email != ''
          AND (email_sent IS NULL OR email_sent = 0)
          AND (blacklisted IS NULL OR blacklisted = 0)
        ORDER BY COALESCE(lead_score, 0) DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── SMTP send ─────────────────────────────────────────────────────────

def _send_email(to_address, subject, message_text, html_body):
    """Sends one email and returns the Message-ID we set, for reply matching."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"NovaDigital <{EMAIL_SENDER}>"
    msg["To"]      = to_address
    msg_id = make_msgid(domain=EMAIL_SENDER.split("@")[1] if "@" in EMAIL_SENDER else "novadigital.local")
    msg["Message-ID"] = msg_id
    msg.attach(MIMEText(message_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body,    "html",  "utf-8"))

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as server:
        server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
        server.sendmail(EMAIL_SENDER, to_address, msg.as_string())
    return msg_id


# ── Main entry ────────────────────────────────────────────────────────

def run(dry_run=True, daily_limit=DEFAULT_DAILY_LIMIT, only_lead_id=None):
    """
    Send the WhatsApp-equivalent message via email to leads with an email
    address that haven't been emailed yet. Mirrors the manifest-driven URL
    injection used by the WhatsApp campaign.
    """
    print(f"[Email Campaign] dry_run={dry_run} daily_limit={daily_limit} only_id={only_lead_id}")

    url_map = _load_manifest_url_map()
    print(f"[Email Campaign] manifest entries: {len(url_map)}")

    leads = _load_eligible_leads()
    print(f"[Email Campaign] DB candidates with email + unmessaged: {len(leads)}")

    # Filter to only leads we have a per-lead URL for AND name in Hebrew
    eligible = []
    skipped_no_url = 0
    skipped_no_hebrew = 0
    for lead in leads:
        if only_lead_id is not None and lead["id"] != only_lead_id:
            continue
        if not _has_hebrew(lead["name"]):
            skipped_no_hebrew += 1
            continue
        url = url_map.get(lead["id"])
        if not url:
            skipped_no_url += 1
            continue
        eligible.append((lead, url))

    print(f"[Email Campaign] after filters: {len(eligible)} eligible "
          f"(skipped {skipped_no_url} missing URL, {skipped_no_hebrew} non-Hebrew names)")

    if not eligible:
        print("[Email Campaign] nothing to send.")
        return

    sent = 0
    failed = 0
    consecutive_failures = 0
    variant_counts = {"no_site": 0, "low_quality": 0}

    for i, (lead, url) in enumerate(eligible):
        if sent >= daily_limit:
            print(f"[Email Campaign] reached daily limit {daily_limit}. Stopping.")
            break

        variant_key, subject, builder = _pick_variant(lead)
        message_text = builder(lead, url)
        html_body    = build_lead_email_html(lead["name"], message_text, url)
        variant_counts[variant_key] += 1

        prefix = (
            f"[{i+1}/{len(eligible)}] id={lead['id']} {lead['name']} → "
            f"{lead['email']} [{variant_key}]"
        )

        if dry_run:
            print(f"\n{prefix}")
            print(f"  URL: {url}")
            print(f"  Subject: {subject}")
            print(f"  --- BODY ---\n{message_text}\n  ---")
            sent += 1
            if sent >= 5:
                print(f"\n[Email Campaign] dry_run: showed first 5 of {len(eligible)}. "
                      f"Re-run with daily_limit higher to see more.")
                break
            continue

        try:
            msg_id = _send_email(lead["email"], subject, message_text, html_body)
            mark_sent(lead["id"], "email",
                      message=message_text[:500], status="sent", message_id=msg_id)
            sent += 1
            consecutive_failures = 0
            print(f"{prefix}  ✅ sent  msg_id={msg_id}")
        except smtplib.SMTPAuthenticationError:
            print(f"{prefix}  ❌ SMTP auth failed — check EMAIL_APP_PASSWORD. Aborting.")
            return
        except Exception as e:
            failed += 1
            consecutive_failures += 1
            mark_sent(lead["id"], "email", message=str(e)[:500], status="failed")
            print(f"{prefix}  ❌ {e}")
            if consecutive_failures >= 3:
                print(f"[Email Campaign] 3 consecutive failures — stopping for safety.")
                break

        if i < len(eligible) - 1:
            time.sleep(SEND_DELAY_SECONDS)

    print(f"\n[Email Campaign] DONE. sent={sent} failed={failed}")
    print(f"[Email Campaign] variant breakdown: {variant_counts}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Actually send (default is dry-run)")
    parser.add_argument("--limit", type=int, default=DEFAULT_DAILY_LIMIT)
    parser.add_argument("--only", type=int, default=None, help="Only send to this lead ID (testing)")
    args = parser.parse_args()
    run(dry_run=not args.send, daily_limit=args.limit, only_lead_id=args.only)
