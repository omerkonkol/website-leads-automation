"""
reply_monitor.py — Track replies to NovaDigital outreach emails.

Polls the NovaDigital mailbox via IMAP, finds new replies, matches each one
to the original sent email via In-Reply-To header (logged at send time in
outreach_log.message_id), and updates the lead's pipeline status + last_response.

CLI:
    py -m outreach.reply_monitor poll                      # fetch new replies
    py -m outreach.reply_monitor list                      # show stored replies
    py -m outreach.reply_monitor list --unread-only        # only ones I haven't acted on
    py -m outreach.reply_monitor reply <business_id> "<body>"   # send a reply

Reply matching strategy:
    1. Primary: 'In-Reply-To' header → outreach_log.message_id → business_id.
    2. Fallback: sender email matches businesses.email AND lead has email_sent=1.
"""

import argparse
import email
import imaplib
import smtplib
import sys
from datetime import datetime
from email.header import decode_header, make_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import make_msgid, parseaddr

from config import (
    EMAIL_SENDER, EMAIL_APP_PASSWORD,
    SMTP_HOST, SMTP_PORT, IMAP_HOST, IMAP_PORT, YOUR_NAME,
)
from core.database import get_conn, mark_sent

sys.stdout.reconfigure(encoding="utf-8")


# ── IMAP connection ───────────────────────────────────────────────────

def _imap_connect():
    if not EMAIL_SENDER or not EMAIL_APP_PASSWORD:
        raise RuntimeError("EMAIL_SENDER / EMAIL_APP_PASSWORD not configured in .env")
    m = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    m.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
    return m


def _decode(header_val):
    if not header_val:
        return ""
    return str(make_header(decode_header(header_val)))


def _extract_body(msg):
    """Returns the plain-text body of an email.message.Message, fallback to HTML stripped."""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            disp = (part.get("Content-Disposition") or "").lower()
            if ctype == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                try:
                    return payload.decode(charset, errors="replace")
                except LookupError:
                    return payload.decode("utf-8", errors="replace")
        # fallback to first text/html
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True) or b""
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True) or b""
        charset = msg.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except LookupError:
            return payload.decode("utf-8", errors="replace")
    return ""


# ── Reply matching ────────────────────────────────────────────────────

def _match_business(in_reply_to, references, sender_email):
    """
    Returns business_id or None.
    1. Look up Message-ID from In-Reply-To / References in outreach_log.message_id.
    2. Fallback: match sender to businesses.email where email_sent=1.
    """
    candidates = [in_reply_to] + (references.split() if references else [])
    candidates = [c.strip("<> ") for c in candidates if c]

    conn = get_conn()
    try:
        for cand in candidates:
            row = conn.execute(
                "SELECT business_id FROM outreach_log WHERE message_id LIKE ? LIMIT 1",
                (f"%{cand}%",)
            ).fetchone()
            if row:
                return row["business_id"]
        # Fallback: match sender email
        if sender_email:
            row = conn.execute(
                "SELECT id FROM businesses WHERE LOWER(email)=LOWER(?) AND email_sent=1 LIMIT 1",
                (sender_email,)
            ).fetchone()
            if row:
                return row["id"]
    finally:
        conn.close()
    return None


# ── Storage ───────────────────────────────────────────────────────────

def _store_reply(business_id, sender, subject, body, raw_message_id):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    snippet = body[:1000]
    conn = get_conn()
    if business_id is not None:
        conn.execute(
            "UPDATE businesses SET last_response=?, response_date=?, pipeline_stage='replied' WHERE id=?",
            (snippet, now, business_id)
        )
    conn.execute(
        "INSERT INTO outreach_log (business_id, channel, status, message, message_id, sent_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (business_id, "email_reply", "received",
         f"FROM: {sender}\nSUBJECT: {subject}\n\n{snippet}",
         raw_message_id, now)
    )
    conn.commit()
    conn.close()


# ── Main commands ─────────────────────────────────────────────────────

def cmd_poll():
    """Fetch all UNSEEN messages, match to leads, store replies."""
    m = _imap_connect()
    try:
        m.select("INBOX")
        typ, data = m.search(None, "UNSEEN")
        if typ != "OK":
            print(f"[Reply Monitor] IMAP SEARCH failed: {typ}")
            return
        ids = data[0].split()
        print(f"[Reply Monitor] {len(ids)} unread messages.")
        new_matches = 0
        unmatched = 0
        already_logged = _existing_reply_ids()
        for num in ids:
            typ, msg_data = m.fetch(num, "(RFC822)")
            if typ != "OK":
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)

            in_reply_to = (msg.get("In-Reply-To") or "").strip()
            references  = (msg.get("References")  or "").strip()
            from_hdr    = _decode(msg.get("From")  or "")
            subject     = _decode(msg.get("Subject") or "")
            raw_msg_id  = (msg.get("Message-ID") or "").strip()
            _, sender_email = parseaddr(from_hdr)
            body = _extract_body(msg).strip()

            if raw_msg_id and raw_msg_id in already_logged:
                # mark seen and skip
                m.store(num, "+FLAGS", "\\Seen")
                continue

            biz_id = _match_business(in_reply_to, references, sender_email)
            _store_reply(biz_id, from_hdr, subject, body, raw_msg_id)
            if biz_id:
                new_matches += 1
                print(f"  ✅ match  biz_id={biz_id}  from={sender_email}  subj={subject[:60]}")
            else:
                unmatched += 1
                print(f"  ⚠️ no match  from={sender_email}  subj={subject[:60]}")
            m.store(num, "+FLAGS", "\\Seen")

        print(f"[Reply Monitor] DONE. matched={new_matches} unmatched={unmatched}")
    finally:
        m.logout()


def _existing_reply_ids():
    """Returns set of Message-IDs already logged as email_reply, to avoid duplicates."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT message_id FROM outreach_log WHERE channel='email_reply' AND message_id IS NOT NULL"
    ).fetchall()
    conn.close()
    return {r["message_id"] for r in rows if r["message_id"]}


def cmd_list(unread_only=False):
    """Show replies stored in DB."""
    conn = get_conn()
    where = "WHERE channel='email_reply'"
    if unread_only:
        where += " AND business_id IS NOT NULL AND status='received'"
    rows = conn.execute(f"""
        SELECT ol.id, ol.business_id, ol.message, ol.sent_at, b.name, b.email, b.pipeline_stage
        FROM outreach_log ol
        LEFT JOIN businesses b ON b.id = ol.business_id
        {where}
        ORDER BY ol.sent_at DESC
        LIMIT 50
    """).fetchall()
    conn.close()
    if not rows:
        print("[Reply Monitor] No replies found.")
        return
    print(f"[Reply Monitor] {len(rows)} replies:\n")
    for r in rows:
        biz_label = f"id={r['business_id']} {r['name']}" if r['business_id'] else "[unmatched]"
        print(f"--- log_id={r['id']}  {r['sent_at']}  {biz_label}  stage={r['pipeline_stage']} ---")
        print(r["message"])
        print()


def cmd_reply(business_id, body):
    """Send a reply to a business, threading via In-Reply-To of their last reply."""
    conn = get_conn()
    biz = conn.execute(
        "SELECT id, name, email FROM businesses WHERE id=?", (business_id,)
    ).fetchone()
    if not biz or not biz["email"]:
        print(f"[Reply Monitor] No business id={business_id} or no email.")
        conn.close()
        return

    # Find the last received reply Message-ID for threading
    last_reply = conn.execute("""
        SELECT message_id FROM outreach_log
        WHERE business_id=? AND channel='email_reply' AND message_id IS NOT NULL
        ORDER BY sent_at DESC LIMIT 1
    """, (business_id,)).fetchone()
    in_reply_to = last_reply["message_id"] if last_reply else None

    # Subject from original outreach (re-thread under same subject)
    last_send = conn.execute("""
        SELECT message_id FROM outreach_log
        WHERE business_id=? AND channel='email' AND message_id IS NOT NULL
        ORDER BY sent_at DESC LIMIT 1
    """, (business_id,)).fetchone()
    original_msg_id = last_send["message_id"] if last_send else None
    conn.close()

    msg = MIMEMultipart("alternative")
    msg["From"]    = f"NovaDigital <{EMAIL_SENDER}>"
    msg["To"]      = biz["email"]
    msg["Subject"] = f"Re: שדרוג הנוכחות הדיגיטלית של {biz['name']}"
    msg_id = make_msgid(domain=EMAIL_SENDER.split("@")[1] if "@" in EMAIL_SENDER else "novadigital.local")
    msg["Message-ID"] = msg_id
    if in_reply_to or original_msg_id:
        ref_chain = " ".join(filter(None, [original_msg_id, in_reply_to]))
        msg["In-Reply-To"] = in_reply_to or original_msg_id
        msg["References"]  = ref_chain
    html = body.replace("\n", "<br>")
    msg.attach(MIMEText(body, "plain", "utf-8"))
    msg.attach(MIMEText(
        f'<html dir="rtl"><body style="font-family:Arial;direction:rtl;font-size:15px;line-height:1.7;">{html}</body></html>',
        "html", "utf-8"
    ))

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, biz["email"], msg.as_string())
    except Exception as e:
        print(f"[Reply Monitor] ❌ send failed: {e}")
        return

    # Log the outgoing reply
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    conn.execute(
        "INSERT INTO outreach_log (business_id, channel, status, message, message_id, sent_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (business_id, "email", "sent", body[:500], msg_id, now)
    )
    conn.commit()
    conn.close()
    print(f"[Reply Monitor] ✅ replied to {biz['email']}  msg_id={msg_id}")


# ── Entry point ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="NovaDigital reply monitor")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("poll", help="Fetch unread replies from IMAP, match to leads, store in DB")
    list_p = sub.add_parser("list", help="Show stored replies")
    list_p.add_argument("--unread-only", action="store_true")
    rep = sub.add_parser("reply", help="Send a reply to a lead")
    rep.add_argument("business_id", type=int)
    rep.add_argument("body")
    args = parser.parse_args()

    if args.cmd == "poll":
        cmd_poll()
    elif args.cmd == "list":
        cmd_list(unread_only=args.unread_only)
    elif args.cmd == "reply":
        cmd_reply(args.business_id, args.body)


if __name__ == "__main__":
    main()
