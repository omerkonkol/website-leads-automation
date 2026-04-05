"""
pitch_builder.py — בונה הודעת מכירה אישית ומקצועית לכל עסק.
ללא אימוג'ים. ישירה. אנושית.
"""

import random
from config import YOUR_NAME, YOUR_PHONE, YOUR_WHATSAPP_URL, PRICE_ILS, PORTFOLIO_LINKS, YOUR_BIO


# ════════════════════════════════════════════════════════════════
#  נתוני הבעיות
# ════════════════════════════════════════════════════════════════
ISSUES = {
    "no_website": {
        "short":  "אין אתר",
        "wa_line": "שמתי לב שאין לכם אתר אינטרנט",
        "detail": (
            "בישראל, מעל 85% מהאנשים מחפשים עסק בגוגל לפני שהם מתקשרים. "
            "כשמישהו מחפש שירות שאתם נותנים, הוא לא מוצא אתכם ועובר ישר למתחרה. "
            "כל יום בלי אתר זה לידים שאתם מפסידים."
        ),
    },
    "no_ssl": {
        "short":  "האתר לא מאובטח (HTTP)",
        "wa_line": "שמתי לב שהאתר שלכם עדיין על HTTP ולא HTTPS",
        "detail": (
            "הדפדפן מציג לכל מבקר אזהרה שהאתר לא מאובטח. "
            "רוב האנשים עוזבים מיד. "
            "בנוסף, גוגל מוריד אתרים ללא SSL בתוצאות החיפוש."
        ),
    },
    "not_mobile": {
        "short":  "לא מותאם לנייד",
        "wa_line": "נכנסתי לאתר שלכם מהנייד וראיתי שהוא לא מותאם",
        "detail": (
            "כיום 65% מהגלישה בישראל היא מהנייד. "
            "באתר שלכם הטקסט קטן והכפתורים צפופים — "
            "לקוח שנכנס מהנייד עוזב תוך שניות."
        ),
    },
    "no_cta": {
        "short":  "אין כפתורי יצירת קשר",
        "wa_line": "שמתי לב שאין כפתורים ברורים ליצירת קשר",
        "detail": (
            "מבקר שנכנס לאתר לא יודע מה הצעד הבא ויוצא. "
            "אתר בלי כפתור 'התקשר' או 'השאר פרטים' בולט הוא אתר שלא ממיר."
        ),
    },
    "no_form": {
        "short":  "אין טופס פנייה",
        "wa_line": "ראיתי שאין טופס יצירת קשר",
        "detail": (
            "חלק גדול מהלקוחות מעדיפים למלא טופס על פני שיחת טלפון. "
            "בלי טופס, אתם מפספסים אותם לחלוטין."
        ),
    },
    "no_pixel": {
        "short":  "אין Facebook Pixel",
        "wa_line": "ראיתי שאין Facebook Pixel מותקן",
        "detail": (
            "אם אתם מפרסמים בפייסבוק או אינסטגרם, "
            "אתם לא יכולים לדעת מי המיר ולא יכולים לעשות רימרקטינג. "
            "כסף על פרסום שהולך לאיבוד."
        ),
    },
    "no_analytics": {
        "short":  "אין Google Analytics",
        "wa_line": "אין Google Analytics באתר",
        "detail": (
            "אין לכם מידע על כמה אנשים נכנסים, מאיפה הם מגיעים ואיפה הם עוזבים. "
            "בלי נתונים לא ניתן לשפר."
        ),
    },
    "slow_load": {
        "short":  "טעינה איטית",
        "wa_line": "האתר שלכם לוקח יותר מ-3 שניות להיטען",
        "detail": (
            "יותר מחצי מהמשתמשים עוזבים אתר שלא נטען תוך 3 שניות. "
            "גוגל גם מוריד אתרים איטיים בדירוג."
        ),
    },
}


def detect_issues(biz: dict) -> list[str]:
    if not biz.get("has_website"):
        return ["no_website"]
    found = []
    if not biz.get("has_ssl"):        found.append("no_ssl")
    if not biz.get("is_responsive"):  found.append("not_mobile")
    if not biz.get("has_cta"):        found.append("no_cta")
    if not biz.get("has_form"):       found.append("no_form")
    if not biz.get("has_fb_pixel"):   found.append("no_pixel")
    if not biz.get("has_analytics"):  found.append("no_analytics")
    ms = biz.get("load_time_ms")
    if ms and ms > 3000:              found.append("slow_load")
    return found


# ════════════════════════════════════════════════════════════════
#  הודעת WhatsApp — אישית, ישירה, ללא אימוג'ים
# ════════════════════════════════════════════════════════════════
_OPENERS = [
    "שלום, אני {name_me} — {bio}.",
    "שמי {name_me}, {bio}.",
    "היי, קוראים לי {name_me} — {bio}.",
]


def build_whatsapp_pitch(biz: dict) -> str:
    biz_name = biz.get("name", "")
    issues   = detect_issues(biz)
    ms       = biz.get("load_time_ms")
    opener   = random.choice(_OPENERS).format(name_me=YOUR_NAME, bio=YOUR_BIO)

    if "no_website" in issues:
        return (
            f"שלום,\n\n"
            f"{opener}\n\n"
            f"חיפשתי את {biz_name} באינטרנט ושמתי לב שאין לכם אתר.\n\n"
            f"בישראל מעל 85% מהאנשים מחפשים עסק בגוגל לפני שמתקשרים — "
            f"כלומר, כשמישהו מחפש {_category_hint(biz)} באזור שלכם, הוא לא מוצא אתכם ועובר ישר למתחרה. "
            f"מדובר בלקוחות שכבר רוצים לשלם, אבל לא יכולים למצוא אתכם.\n\n"
            f"אתר טוב עובד בשבילכם 24/7 — גם כשאתם ישנים. "
            f"הוא מציג את העסק, מאפשר ליצור קשר, ובונה אמינות מול לקוחות חדשים שעוד לא מכירים אתכם.\n\n"
            f"הכנתי לכם דוגמה לאתר שאוכל לבנות עבורכם:\n"
            f"{{DEMO_URL}}\n\n"
            f"כמובן שאפשר להתייעץ על כל דבר שתרצו להוסיף או לשנות. "
            f"אם זה מעניין אתכם נשמח אם תפנו אלינו.\n\n"
            f"{YOUR_NAME} | {YOUR_PHONE}"
        )

    top  = ISSUES[issues[0]]
    rest = issues[1:]

    body = (
        f"שלום,\n\n"
        f"{opener}\n\n"
        f"נכנסתי לאתר של {biz_name} ו{top['wa_line']}.\n"
        f"{top['detail']}\n\n"
        f"אתר שעובד טוב הוא הדבר הכי אפקטיבי שיש לעסק היום — "
        f"הוא זה שגורם ללקוח חדש שעוד לא מכיר אתכם לבחור דווקא בכם ולא במתחרה.\n"
    )

    if len(rest) == 1:
        body += f"\nמצאתי גם בעיה נוספת: {ISSUES[rest[0]]['short']}.\n"
    elif len(rest) >= 2:
        body += f"\nמצאתי עוד {len(rest)} נקודות נוספות שפוגעות בביצועי האתר.\n"

    body += (
        f"\nהכנתי לכם דוגמה לאתר משודרג:\n"
        f"{{DEMO_URL}}\n\n"
        f"כמובן שאפשר להתייעץ על כל דבר שתרצו להוסיף או לשנות. "
        f"אם זה מעניין אתכם נשמח אם תפנו אלינו.\n\n"
        f"{YOUR_NAME} | {YOUR_PHONE}"
    )
    return body


def _category_hint(biz: dict) -> str:
    """מחזיר תיאור קצר של הקטגוריה לשם הכנסה להודעה."""
    cat = (biz.get("category") or biz.get("search_query") or "").strip()
    if not cat:
        return "שירות"
    # קחו את 2-3 המילים הראשונות
    words = cat.split()
    return " ".join(words[:2]) if len(words) > 2 else cat


# ════════════════════════════════════════════════════════════════
#  פנייה מלאה — למייל / לעיון לפני שיחה
# ════════════════════════════════════════════════════════════════
def build_full_pitch(biz: dict) -> str:
    biz_name = biz.get("name", "")
    website  = biz.get("website", "")
    issues   = detect_issues(biz)
    ms       = biz.get("load_time_ms")

    lines = [
        f"שלום לצוות {biz_name},",
        "",
        f"שמי {YOUR_NAME}, {YOUR_BIO}.",
        "",
    ]

    if "no_website" in issues:
        lines += [
            f"חיפשתי את {biz_name} באינטרנט ושמתי לב שאין לכם אתר.",
            "",
            "מה המשמעות המעשית:",
            f"  - {ISSUES['no_website']['detail']}",
            "  - עסקים מתחרים עם אתר מקבלים את הלקוחות שיכולים היו לפנות אליכם.",
            "  - כשמישהו ממליץ עליכם ואנשים הולכים לחפש — הם לא מוצאים כלום.",
            "",
        ]
    else:
        lines += [
            f"נכנסתי לאתר שלכם ({website}) ובדקתי אותו לעומק.",
            f"מצאתי {len(issues)} בעיות שפוגעות בביצועים שלו:",
            "",
        ]
        for i, key in enumerate(issues, 1):
            issue = ISSUES.get(key)
            if not issue:
                continue
            if key == "slow_load" and ms:
                detail = f"האתר נטען ב-{ms/1000:.1f} שניות. {issue['detail']}"
            else:
                detail = issue["detail"]
            lines += [
                f"{i}. {issue['short']}",
                f"   {detail}",
                "",
            ]

    lines += [
        "-" * 48,
        "",
        "מה אני מציע:",
        "",
        "אבנה לכם אתר חדש שיכלול:",
        "  - עיצוב מותאם אישית לעסק",
        "  - מותאם לנייד",
        "  - HTTPS מאובטח",
        "  - כפתורי WhatsApp וטופס יצירת קשר",
        "  - Google Analytics ו-Facebook Pixel",
        "  - SEO בסיסי",
        "  - טעינה מהירה",
        "",
        "הכנתי לכם דוגמה לאתר שאוכל לבנות עבורכם:",
        "  {DEMO_URL}",
        "",
        "כמובן שאפשר להתייעץ על כל דבר שתרצו להוסיף או לשנות.",
        "אם זה מעניין אתכם נשמח אם תפנו אלינו.",
        "",
    ]

    if PORTFOLIO_LINKS:
        lines += ["דוגמאות נוספות מתיק העבודות:"]
        for link in PORTFOLIO_LINKS:
            lines.append(f"  {link}")
        lines.append("")

    lines += [
        "-" * 48,
        "",
        f"{YOUR_NAME}",
        f"{YOUR_PHONE}",
        f"{YOUR_WHATSAPP_URL}",
    ]

    return "\n".join(lines)


def build_sales_summary(biz: dict) -> str:
    issues = detect_issues(biz)
    if not issues:
        return "אתר תקין — שיפור כללי"
    return " | ".join(ISSUES[k]["short"] for k in issues[:4])
