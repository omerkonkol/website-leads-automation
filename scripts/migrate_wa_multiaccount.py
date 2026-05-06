"""
DB migration: add wa_accounts + wa_messages tables, account_phone on outreach_log.

Idempotent: safe to run multiple times.

Run:
    py scripts/migrate_wa_multiaccount.py
"""
import sqlite3
from pathlib import Path

DB = Path("e:/system/leads.db")

DDL_WA_ACCOUNTS = """
CREATE TABLE IF NOT EXISTS wa_accounts (
    phone               TEXT PRIMARY KEY,
    label               TEXT,
    status              TEXT DEFAULT 'pending',
    daily_limit         INTEGER DEFAULT 20,
    daily_sent          INTEGER DEFAULT 0,
    daily_reset_date    TEXT DEFAULT (date('now')),
    last_sent_at        TEXT,
    ban_reason          TEXT,
    branding_set        INTEGER DEFAULT 0,
    created_at          TEXT DEFAULT (datetime('now'))
)
"""

DDL_WA_MESSAGES = """
CREATE TABLE IF NOT EXISTS wa_messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    account_phone   TEXT NOT NULL,
    lead_id         INTEGER,
    peer_phone      TEXT NOT NULL,
    direction       TEXT NOT NULL CHECK (direction IN ('in','out')),
    status          TEXT DEFAULT 'sent',
    body            TEXT,
    media_path      TEXT,
    raw_id          TEXT,
    sent_at         TEXT DEFAULT (datetime('now')),
    delivered_at    TEXT,
    read_at         TEXT,
    replied_to_id   INTEGER REFERENCES wa_messages(id)
)
"""

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_wa_messages_thread ON wa_messages(account_phone, peer_phone, sent_at)",
    "CREATE INDEX IF NOT EXISTS idx_wa_messages_lead   ON wa_messages(lead_id, sent_at)",
    "CREATE INDEX IF NOT EXISTS idx_wa_messages_unread ON wa_messages(direction, read_at)",
]


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute(DDL_WA_ACCOUNTS)
    cur.execute(DDL_WA_MESSAGES)
    for stmt in INDEXES:
        cur.execute(stmt)

    # Add account_phone to outreach_log if missing
    cols = {r[1] for r in cur.execute("PRAGMA table_info(outreach_log)").fetchall()}
    if "account_phone" not in cols:
        cur.execute("ALTER TABLE outreach_log ADD COLUMN account_phone TEXT")
        print("Added account_phone column to outreach_log")

    # Seed the existing primary account
    primary_phone = "+972525603365"
    cur.execute(
        """INSERT OR IGNORE INTO wa_accounts (phone, label, status, daily_limit, branding_set)
           VALUES (?, 'primary', 'pending', 20, 1)""",
        (primary_phone,),
    )

    # Backfill: every outreach_log row from today gets primary account
    cur.execute(
        """UPDATE outreach_log
              SET account_phone = ?
            WHERE channel='whatsapp' AND account_phone IS NULL""",
        (primary_phone,),
    )
    print(f"Backfilled {cur.rowcount} outreach_log rows with account_phone={primary_phone}")

    # Backfill wa_messages from outreach_log (so the inbox UI shows the 17 already sent)
    # Each successful 'sent' row → wa_messages with direction='out'
    cur.execute(
        """SELECT business_id, message, sent_at, status FROM outreach_log
            WHERE channel='whatsapp' AND status='sent'
              AND business_id NOT IN (SELECT lead_id FROM wa_messages WHERE direction='out')"""
    )
    sent_rows = cur.fetchall()
    if sent_rows:
        for biz_id, msg, sent_at, status in sent_rows:
            phone_row = cur.execute(
                "SELECT phone FROM businesses WHERE id=?", (biz_id,)
            ).fetchone()
            if not phone_row:
                continue
            peer = phone_row[0]
            cur.execute(
                """INSERT INTO wa_messages (account_phone, lead_id, peer_phone, direction, status, body, sent_at)
                   VALUES (?, ?, ?, 'out', 'sent', ?, ?)""",
                (primary_phone, biz_id, peer, msg, sent_at),
            )
        print(f"Backfilled {len(sent_rows)} outbound messages into wa_messages")

    con.commit()

    # Report
    print("\n--- Schema status ---")
    accounts = cur.execute("SELECT phone, label, status, daily_limit, branding_set FROM wa_accounts").fetchall()
    print(f"wa_accounts ({len(accounts)} rows):")
    for a in accounts:
        print(f"  phone={a[0]} label={a[1]} status={a[2]} limit={a[3]} branding={a[4]}")
    msg_count = cur.execute("SELECT COUNT(*) FROM wa_messages").fetchone()[0]
    print(f"wa_messages: {msg_count} rows")

    con.close()


if __name__ == "__main__":
    main()
