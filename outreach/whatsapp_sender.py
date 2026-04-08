"""
whatsapp_sender.py — שליחת הודעות WhatsApp דרך WhatsApp Web + Selenium.
מבוסס על הקוד שנכתב לפרויקט החתונה (send_invites.py) ומותאם לפנייה לעסקים.
"""

import sys
import os
import json
import time
import subprocess
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from config import WHATSAPP_PAUSE_BETWEEN, SESSION_DATA_DIR
from database import mark_sent

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


# ════════════════════════════════════════════════════════════════
#  תבנית הודעת ה-WhatsApp לעסקים
# ════════════════════════════════════════════════════════════════
def build_whatsapp_message(business_name: str, main_issue: str, your_name: str, price: int) -> str:
    return (
        f"שלום, אני פונה אליך בנוגע לעסק *{business_name}* 👋\n\n"
        f"שמתי לב ש{main_issue}.\n\n"
        f"אני בונה אתרים מודרניים ומותאמים לנייד במחיר מיוחד של *{price} ₪* בלבד.\n"
        f"תיק העבודות שלי 👇"
    )


# ════════════════════════════════════════════════════════════════
#  פונקציות עזר (זהות לקוד החתונה)
# ════════════════════════════════════════════════════════════════
def normalize_phone(raw: str) -> str:
    phone = str(raw).strip().split(".")[0]
    digits = "".join(c for c in phone if c.isdigit())
    if not digits.startswith("972"):
        digits = "972" + digits.lstrip("0")
    return digits


def paste_text(driver, element, text: str):
    """מדביק טקסט (כולל עברית ואמוג'י) ל-contenteditable דרך JS."""
    driver.execute_script(
        "arguments[0].focus();"
        "document.execCommand('insertText', false, arguments[1]);",
        element, text
    )


def set_clipboard(text: str):
    """שומר טקסט ב-clipboard של Windows."""
    subprocess.run(
        ["powershell", "-Command", f"Set-Clipboard -Value '{text}'"],
        capture_output=True
    )


def get_main_input(wait: WebDriverWait):
    return wait.until(EC.element_to_be_clickable(
        (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
    ))


# ════════════════════════════════════════════════════════════════
#  שליחה לעסק בודד
# ════════════════════════════════════════════════════════════════
def send_to_business(driver, wait: WebDriverWait, business: dict, portfolio_links: list) -> bool:
    """
    שולח הודעת פנייה לעסק אחד.
    מחזיר True אם הצליח.
    """
    from analyzer import build_issue_summary
    from config import YOUR_NAME, PRICE_ILS

    phone = normalize_phone(business["phone"])
    name  = business["name"]
    issue = build_issue_summary({
        "has_website":   business.get("has_website", 0),
        "is_responsive": business.get("is_responsive", 0),
        "has_ssl":       business.get("has_ssl", 0),
        "has_cta":       business.get("has_cta", 0),
        "has_form":      business.get("has_form", 0),
        "issues":        json.loads(business["issues"]) if isinstance(business.get("issues"), str) else business.get("issues", []),
    })

    message = build_whatsapp_message(name, issue, YOUR_NAME, PRICE_ILS)

    try:
        # שלב 1: פתיחת הצ'אט
        driver.get(f"https://web.whatsapp.com/send?phone={phone}")
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        ))
        print(f"    ✅ פתוח צ'אט עם {name}")

        # שלב 2: שליחת הטקסט הראשי
        inp = get_main_input(wait)
        inp.click()
        paste_text(driver, inp, message)
        time.sleep(0.5)
        inp.send_keys(Keys.ENTER)
        print(f"    ✅ נשלחה הודעה טקסטואלית")

        # שלב 3: שליחת לינקים לתיק עבודות (כל אחד בנפרד)
        for link in portfolio_links:
            time.sleep(1)
            set_clipboard(link)
            inp = get_main_input(wait)
            inp.click()
            inp.send_keys(Keys.CONTROL + "v")
            time.sleep(0.8)
            inp.send_keys(Keys.ENTER)
        print(f"    ✅ נשלחו {len(portfolio_links)} לינקים לתיק עבודות")

        return True

    except Exception as e:
        print(f"    ❌ נכשל עבור {name} ({phone}): {e}")
        return False


# ════════════════════════════════════════════════════════════════
#  הפעלה ראשית
# ════════════════════════════════════════════════════════════════
def run_whatsapp_campaign(businesses: list, portfolio_links: list):
    """
    מריץ קמפיין WhatsApp לרשימת עסקים.
    businesses: רשימת dict מה-DB (מ-get_pending_outreach).
    """
    if not businesses:
        print("[WhatsApp] אין עסקים לשליחה.")
        return

    # ── ניקוי נהגים קיימים ──
    subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe"], capture_output=True)

    lockfile = Path(SESSION_DATA_DIR) / "lockfile"
    if lockfile.exists():
        try:
            lockfile.unlink()
        except PermissionError:
            print("[WhatsApp] ❌ lockfile נעול. סגור את Chrome ונסה שוב.")
            return

    # ── הפעלת Chrome ──
    opts = Options()
    opts.add_argument("--start-maximized")
    opts.add_argument(f"user-data-dir={os.path.abspath(SESSION_DATA_DIR)}")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    wait = WebDriverWait(driver, 35)

    print("[WhatsApp] פותח WhatsApp Web...")
    driver.get("https://web.whatsapp.com")
    input(">>> סרוק את קוד ה-QR (אם נדרש) ואז לחץ ENTER...")

    success = 0
    failed  = 0

    for i, biz in enumerate(businesses):
        print(f"\n[{i+1}/{len(businesses)}] {biz['name']} | {biz['phone']}")
        ok = send_to_business(driver, wait, biz, portfolio_links)

        if ok:
            mark_sent(biz["id"], "whatsapp", message=f"קמפיין שיווק אתרים", status="sent")
            success += 1
        else:
            mark_sent(biz["id"], "whatsapp", message="", status="failed")
            failed += 1
            # נסיון התאוששות
            try:
                driver.get("https://web.whatsapp.com")
                time.sleep(3)
            except Exception:
                pass

        if i < len(businesses) - 1:
            print(f"    ⏳ ממתין {WHATSAPP_PAUSE_BETWEEN} שניות...")
            time.sleep(WHATSAPP_PAUSE_BETWEEN)

    print(f"\n{'='*50}")
    print(f"[WhatsApp] סיכום:")
    print(f"  ✅ נשלחו בהצלחה: {success}")
    print(f"  ❌ נכשלו:         {failed}")
    print("="*50)
    driver.quit()
