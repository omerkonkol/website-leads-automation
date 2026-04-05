"""
email_sender.py — שליחת מיילים HTML מעוצבים לעסקים.
משתמש ב-Gmail SMTP עם App Password.
"""

import sys
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    EMAIL_SENDER, EMAIL_APP_PASSWORD, EMAIL_PAUSE_BETWEEN,
    PORTFOLIO_LINKS, YOUR_NAME, YOUR_PHONE, YOUR_WHATSAPP_URL, PRICE_ILS
)
from database import mark_sent

sys.stdout.reconfigure(encoding="utf-8")


# ════════════════════════════════════════════════════════════════
#  תבנית HTML למייל
# ════════════════════════════════════════════════════════════════
def build_html_email(business_name: str, main_issue: str, portfolio: list) -> str:
    portfolio_html = "\n".join(
        f'<li><a href="{link}" style="color:#4F46E5;text-decoration:none;">{link}</a></li>'
        for link in portfolio
    )
    return f"""<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>הצעה לבניית אתר</title>
</head>
<body style="margin:0;padding:0;background:#F3F4F6;font-family:Arial,Helvetica,sans-serif;direction:rtl;">
  <table width="100%" cellpadding="0" cellspacing="0" bgcolor="#F3F4F6">
    <tr>
      <td align="center" style="padding:40px 20px;">
        <table width="600" cellpadding="0" cellspacing="0" bgcolor="#FFFFFF"
               style="border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.1);">

          <!-- Header -->
          <tr>
            <td align="center" bgcolor="#4F46E5" style="padding:36px 40px;">
              <h1 style="margin:0;color:#FFFFFF;font-size:26px;font-weight:bold;">
                🌐 שדרוג הנוכחות הדיגיטלית שלך
              </h1>
              <p style="margin:10px 0 0;color:#C7D2FE;font-size:15px;">
                הצעה מיוחדת עבור {business_name}
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 40px;color:#374151;">
              <p style="font-size:16px;line-height:1.7;margin-top:0;">
                שלום לצוות <strong>{business_name}</strong> 👋
              </p>
              <p style="font-size:15px;line-height:1.7;">
                שמתי לב ש<strong style="color:#EF4444;">{main_issue}</strong> —
                ובעולם הדיגיטלי של היום, זה עלול לעלות ללקוחות פוטנציאליים.
              </p>

              <!-- Problem box -->
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:#FEF2F2;border-right:4px solid #EF4444;border-radius:8px;margin:20px 0;">
                <tr>
                  <td style="padding:16px 20px;color:#991B1B;font-size:14px;">
                    <strong>הבעיה שזיהיתי:</strong> {main_issue}
                  </td>
                </tr>
              </table>

              <p style="font-size:15px;line-height:1.7;">
                אני מתמחה בבניית אתרים מודרניים, מהירים ומותאמים לנייד —
                בדגש על <strong>המרת מבקרים ללקוחות</strong>.
              </p>

              <!-- Portfolio -->
              <h3 style="color:#1F2937;font-size:17px;margin-bottom:8px;">
                🎨 דוגמאות מתיק העבודות שלי:
              </h3>
              <ul style="padding-right:20px;line-height:2;font-size:14px;">
                {portfolio_html}
              </ul>

              <!-- Price box -->
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:#F0FDF4;border:2px solid #22C55E;border-radius:12px;margin:24px 0;">
                <tr>
                  <td align="center" style="padding:24px;">
                    <p style="margin:0;font-size:14px;color:#166534;">מחיר הקמה מיוחד</p>
                    <p style="margin:8px 0;font-size:42px;font-weight:bold;color:#15803D;">
                      {PRICE_ILS} ₪
                    </p>
                    <p style="margin:0;font-size:13px;color:#166534;">
                      כולל עיצוב, פיתוח, התאמה לנייד ו-SSL
                    </p>
                  </td>
                </tr>
              </table>

              <!-- CTA Buttons -->
              <table width="100%" cellpadding="0" cellspacing="0" style="margin:28px 0;">
                <tr>
                  <td align="center" style="padding:6px;">
                    <a href="{YOUR_WHATSAPP_URL}"
                       style="display:inline-block;background:#25D366;color:#FFFFFF;
                              text-decoration:none;padding:16px 36px;border-radius:50px;
                              font-size:16px;font-weight:bold;letter-spacing:0.5px;">
                      💬 שלח לי הודעה ב-WhatsApp
                    </a>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding:6px;">
                    <a href="tel:{YOUR_PHONE}"
                       style="display:inline-block;background:#4F46E5;color:#FFFFFF;
                              text-decoration:none;padding:14px 36px;border-radius:50px;
                              font-size:15px;font-weight:bold;">
                      📞 התקשר עכשיו: {YOUR_PHONE}
                    </a>
                  </td>
                </tr>
              </table>

              <p style="font-size:14px;color:#6B7280;line-height:1.7;">
                אשמח לשמוע עליך יותר ולהתאים פתרון שמתאים בדיוק לצרכי העסק.
                ניתן גם לתאם שיחה קצרה ללא התחייבות.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td bgcolor="#F9FAFB" style="padding:20px 40px;border-top:1px solid #E5E7EB;">
              <p style="margin:0;font-size:13px;color:#9CA3AF;text-align:center;">
                {YOUR_NAME} | {YOUR_PHONE}<br>
                <a href="mailto:{EMAIL_SENDER}" style="color:#9CA3AF;">{EMAIL_SENDER}</a>
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def build_plain_text(business_name: str, main_issue: str, portfolio: list) -> str:
    links = "\n".join(f"  - {l}" for l in portfolio)
    return (
        f"שלום לצוות {business_name},\n\n"
        f"שמתי לב ש{main_issue}.\n\n"
        f"אני מתמחה בבניית אתרים מודרניים במחיר של {PRICE_ILS} ₪.\n\n"
        f"תיק עבודות:\n{links}\n\n"
        f"לפרטים: {YOUR_PHONE} | {YOUR_WHATSAPP_URL}\n\n"
        f"בברכה,\n{YOUR_NAME}"
    )


# ════════════════════════════════════════════════════════════════
#  שליחת מייל בודד
# ════════════════════════════════════════════════════════════════
def send_email(to_address: str, business_name: str, main_issue: str) -> bool:
    """שולח מייל HTML לעסק אחד. מחזיר True אם הצליח."""
    if not to_address or "@" not in to_address:
        print(f"    [Email] כתובת לא תקינה: {to_address}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"💡 שדרוג האתר של {business_name} — הצעה ב-{PRICE_ILS} ₪"
    msg["From"]    = f"{YOUR_NAME} <{EMAIL_SENDER}>"
    msg["To"]      = to_address

    plain_body = build_plain_text(business_name, main_issue, PORTFOLIO_LINKS)
    html_body  = build_html_email(business_name, main_issue, PORTFOLIO_LINKS)

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body,  "html",  "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, to_address, msg.as_string())
        return True
    except smtplib.SMTPAuthenticationError:
        print("    [Email] ❌ שגיאת אימות — בדוק EMAIL_APP_PASSWORD ב-config.py")
        return False
    except Exception as e:
        print(f"    [Email] ❌ שגיאה: {e}")
        return False


# ════════════════════════════════════════════════════════════════
#  הפעלה ראשית
# ════════════════════════════════════════════════════════════════
def run_email_campaign(businesses: list):
    """מריץ קמפיין מייל לרשימת עסקים."""
    from analyzer import build_issue_summary
    import json

    if not businesses:
        print("[Email] אין עסקים לשליחה.")
        return

    has_email = [b for b in businesses if b.get("email")]
    no_email  = len(businesses) - len(has_email)
    print(f"[Email] {len(has_email)} עסקים עם מייל | {no_email} ללא מייל")

    success = 0
    failed  = 0

    for i, biz in enumerate(has_email):
        issue = build_issue_summary({
            "has_website":   biz.get("has_website", 0),
            "is_responsive": biz.get("is_responsive", 0),
            "has_ssl":       biz.get("has_ssl", 0),
            "has_cta":       biz.get("has_cta", 0),
            "issues":        json.loads(biz["issues"]) if isinstance(biz.get("issues"), str) else biz.get("issues", []),
        })
        print(f"\n[{i+1}/{len(has_email)}] {biz['name']} → {biz['email']}")

        ok = send_email(biz["email"], biz["name"], issue)
        if ok:
            mark_sent(biz["id"], "email", status="sent")
            print(f"    ✅ נשלח בהצלחה")
            success += 1
        else:
            mark_sent(biz["id"], "email", status="failed")
            failed += 1

        if i < len(has_email) - 1:
            print(f"    ⏳ ממתין {EMAIL_PAUSE_BETWEEN} שניות...")
            time.sleep(EMAIL_PAUSE_BETWEEN)

    print(f"\n{'='*50}")
    print(f"[Email] סיכום:")
    print(f"  ✅ נשלחו: {success}")
    print(f"  ❌ נכשלו: {failed}")
    print("="*50)
