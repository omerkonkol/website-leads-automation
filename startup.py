import os, shutil

DATA_DIR = os.getenv("DATA_DIR", "/data")
DB_PATH  = os.getenv("DB_PATH", "leads.db")

if DB_PATH.startswith("/data") and not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(DB_PATH) and os.path.exists("leads.db"):
    shutil.copy("leads.db", DB_PATH)
    print(f"[startup] DB initialized at {DB_PATH}")
else:
    print(f"[startup] DB ready: {DB_PATH}")
