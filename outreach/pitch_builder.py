"""
pitch_builder.py — בונה הודעת מכירה אישית ומקצועית לכל עסק.

הודעות מותאמות אישית לפי:
  - אין אתר כלל → למה חייב אתר + מה הם מפסידים
  - יש אתר עם בעיות → פירוט כל בעיה + מספרים + השפעה על העסק
  - CMS ישן (Wix/Weebly) → למה לעבור
  - SEO גרוע → מה זה עושה לדירוג בגוגל
  - אתר ישן (copyright) → מה השתנה מאז
"""

import random
from config import YOUR_NAME, YOUR_PHONE, YOUR_WHATSAPP_URL, PRICE_ILS, PORTFOLIO_LINKS, YOUR_BIO


# ════════════════════════════════════════════════════════════════
#  נתוני הבעיות — מפורטים עם סטטיסטיקות ומספרים
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
        "impact": "עסקים ללא אתר מפסידים בממוצע 30-50 לידים בחודש",
    },
    "no_ssl": {
        "short":  "האתר לא מאובטח (HTTP)",
        "wa_line": "שמתי לב שהאתר שלכם עדיין על HTTP ולא HTTPS",
        "detail": (
            "הדפדפן מציג לכל מבקר אזהרה שהאתר לא מאובטח. "
            "רוב האנשים עוזבים מיד. "
            "בנוסף, גוגל מוריד אתרים ללא SSL בתוצאות החיפוש."
        ),
        "impact": "אתרים ללא SSL מאבדים 40% מהמבקרים בגלל אזהרת הדפדפן",
    },
    "not_mobile": {
        "short":  "לא מותאם לנייד",
        "wa_line": "נכנסתי לאתר שלכם מהנייד וראיתי שהוא לא מותאם",
        "detail": (
            "כיום 72% מהגלישה בישראל היא מהנייד. "
            "באתר שלכם הטקסט קטן והכפתורים צפופים — "
            "לקוח שנכנס מהנייד עוזב תוך שניות."
        ),
        "impact": "אתר שלא מותאם לנייד מפסיד 72% מהמבקרים הפוטנציאליים",
    },
    "no_cta": {
        "short":  "אין כפתורי יצירת קשר",
        "wa_line": "שמתי לב שאין כפתורים ברורים ליצירת קשר",
        "detail": (
            "מבקר שנכנס לאתר לא יודע מה הצעד הבא ויוצא. "
            "אתר בלי כפתור 'התקשר' או 'השאר פרטים' בולט הוא אתר שלא ממיר."
        ),
        "impact": "הוספת כפתורי CTA מעלה את שיעור ההמרה ב-80% בממוצע",
    },
    "no_form": {
        "short":  "אין טופס פנייה",
        "wa_line": "ראיתי שאין טופס יצירת קשר",
        "detail": (
            "חלק גדול מהלקוחות מעדיפים למלא טופס על פני שיחת טלפון. "
            "בלי טופס, אתם מפספסים אותם לחלוטין."
        ),
        "impact": "טופס יצירת קשר אוסף לידים גם כשהעסק סגור — 24/7",
    },
    "no_pixel": {
        "short":  "אין Facebook Pixel",
        "wa_line": "ראיתי שאין Facebook Pixel מותקן",
        "detail": (
            "אם אתם מפרסמים בפייסבוק או אינסטגרם, "
            "אתם לא יכולים לדעת מי המיר ולא יכולים לעשות רימרקטינג. "
            "כסף על פרסום שהולך לאיבוד."
        ),
        "impact": "ללא Pixel, תקציב הפרסום שלכם בפייסבוק יעיל פחות ב-60%",
    },
    "no_analytics": {
        "short":  "אין Google Analytics",
        "wa_line": "אין Google Analytics באתר",
        "detail": (
            "אין לכם מידע על כמה אנשים נכנסים, מאיפה הם מגיעים ואיפה הם עוזבים. "
            "בלי נתונים לא ניתן לשפר."
        ),
        "impact": "בלי Analytics, אי אפשר לדעת אילו ערוצי שיווק עובדים ואילו לא",
    },
    "slow_load": {
        "short":  "טעינה איטית",
        "wa_line": "האתר שלכם לוקח יותר מ-3 שניות להיטען",
        "detail": (
            "יותר מחצי מהמשתמשים עוזבים אתר שלא נטען תוך 3 שניות. "
            "גוגל גם מוריד אתרים איטיים בדירוג."
        ),
        "impact": "כל שנייה נוספת של טעינה מפחיתה את ההמרות ב-7%",
    },
    "wix_site": {
        "short":  "אתר Wix — מוגבל",
        "wa_line": "שמתי לב שהאתר שלכם בנוי על Wix",
        "detail": (
            "Wix הוא פלטפורמה מוגבלת: קשה להתאים אישית, "
            "הטעינה איטית, ה-SEO לא אופטימלי, ולא ניתן לשלוט ב-URL. "
            "אתר מותאם אישית ייראה מקצועי יותר וידורג גבוה יותר בגוגל."
        ),
        "impact": "אתר Custom מדורג 30% יותר גבוה מאתר Wix באותה קטגוריה",
    },
    "old_site": {
        "short":  "אתר ישן",
        "wa_line": "שמתי לב שהאתר שלכם לא עודכן כבר כמה שנים",
        "detail": (
            "אתר ישן נראה לא מקצועי ופוגע באמינות העסק. "
            "גוגל מעדיף אתרים מעודכנים. "
            "סטנדרטים של עיצוב ונגישות השתנו משמעותית."
        ),
        "impact": "אתרים שלא עודכנו 3+ שנים מדורגים 50% פחות בגוגל",
    },
    "bad_seo": {
        "short":  "SEO גרוע",
        "wa_line": "בדקתי את ה-SEO של האתר שלכם ומצאתי בעיות משמעותיות",
        "detail": (
            "חסרים לכם אלמנטים בסיסיים שגוגל דורש: "
            "כותרת עמוד (Title), תיאור (Meta Description), "
            "כותרות H1, ו-sitemap. "
            "בלי אלה, גוגל פשוט לא מדרג אתכם."
        ),
        "impact": "תיקון SEO בסיסי יכול להעלות את הדירוג שלכם בעשרות מקומות",
    },
}


def detect_issues(biz: dict) -> list[str]:
    """מזהה את כל הבעיות בעסק — מפורט."""
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

    # בדיקות חדשות
    cms = biz.get("cms_platform") or ""
    if cms == "wix":
        found.append("wix_site")

    copyright_year = biz.get("copyright_year")
    if copyright_year and copyright_year < 2022:
        found.append("old_site")

    seo_score = biz.get("seo_score")
    if seo_score is not None and seo_score < 50:
        found.append("bad_seo")

    return found


def _category_hint(biz: dict) -> str:
    cat = (biz.get("category") or biz.get("search_query") or "").strip()
    if not cat:
        return "שירות"
    words = cat.split()
    return " ".join(words[:2]) if len(words) > 2 else cat


# ════════════════════════════════════════════════════════════════
#  הודעת WhatsApp — אישית, ישירה, מפורטת
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
    )

    # הוסף מידע ספציפי
    if "slow_load" in issues and ms:
        body += f"(האתר שלכם נטען ב-{ms/1000:.1f} שניות — הרבה מעל הממוצע.)\n\n"

    body += (
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


# ════════════════════════════════════════════════════════════════
#  פנייה מלאה — למייל / לעיון לפני שיחה — סופר מפורטת
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
            "למה אתר הוא הכרחי לעסק שלכם:",
            "",
            "  1. נוכחות בגוגל:",
            f"     85% מהישראלים מחפשים '{_category_hint(biz)}' בגוגל לפני שמתקשרים.",
            f"     בלי אתר — אתם פשוט לא קיימים בשבילם. הם עוברים למתחרה.",
            "",
            "  2. אמינות:",
            "     לקוח שמקבל המלצה עליכם הולך מיד לחפש אתכם באינטרנט.",
            "     אם הוא לא מוצא אתר — הוא מפקפק באמינות שלכם.",
            "",
            "  3. עבודה 24/7:",
            "     אתר טוב אוסף לידים גם בשעה 23:00 כשאתם ישנים.",
            "     טופס יצירת קשר + WhatsApp = לקוחות שפונים אליכם אוטומטית.",
            "",
            "  4. יתרון על מתחרים:",
            "     המתחרים שלכם כבר יש להם אתר. כל יום בלי אתר — לקוחות שעוברים אליהם.",
            "",
        ]
    else:
        lines += [
            f"נכנסתי לאתר שלכם ({website}) ובדקתי אותו לעומק.",
            f"מצאתי {len(issues)} בעיות שפוגעות בביצועים ובהכנסות שלכם:",
            "",
        ]
        for i, key in enumerate(issues, 1):
            issue = ISSUES.get(key)
            if not issue:
                continue
            if key == "slow_load" and ms:
                detail = f"האתר נטען ב-{ms/1000:.1f} שניות. {issue['detail']}"
            elif key == "old_site" and biz.get("copyright_year"):
                years_old = 2026 - biz["copyright_year"]
                detail = f"האתר לא עודכן {years_old} שנים (מאז {biz['copyright_year']}). {issue['detail']}"
            elif key == "bad_seo":
                seo_details = []
                if not biz.get("has_title_tag"):  seo_details.append("Title Tag")
                if not biz.get("has_meta_desc"):  seo_details.append("Meta Description")
                if not biz.get("has_h1"):         seo_details.append("H1")
                if not biz.get("has_sitemap"):    seo_details.append("Sitemap")
                detail = f"חסרים: {', '.join(seo_details)}. {issue['detail']}"
            else:
                detail = issue["detail"]

            lines += [
                f"  {i}. {issue['short']}",
                f"     {detail}",
                f"     📊 השפעה: {issue.get('impact', '')}",
                "",
            ]

    lines += [
        "-" * 48,
        "",
        "מה אני מציע:",
        "",
        "אבנה לכם אתר חדש ומקצועי שיכלול:",
        "  ✅ עיצוב מותאם אישית לעסק שלכם",
        "  ✅ מותאם לנייד (72% מהגלישה בישראל)",
        "  ✅ HTTPS מאובטח (נדרש לדירוג בגוגל)",
        "  ✅ כפתורי WhatsApp + התקשר + השאר פרטים",
        "  ✅ טופס יצירת קשר (אוסף לידים 24/7)",
        "  ✅ Google Analytics + Facebook Pixel",
        "  ✅ SEO מלא (Title, Description, H1, Sitemap)",
        "  ✅ טעינה מהירה (מתחת ל-2 שניות)",
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
    return " | ".join(ISSUES[k]["short"] for k in issues[:4] if k in ISSUES)


# ════════════════════════════════════════════════════════════════
#  Score explanation — הסבר מפורט של הציון לדשבורד
# ════════════════════════════════════════════════════════════════
def build_score_explanation(biz: dict, score: int, breakdown: dict) -> str:
    """
    מייצר הסבר מפורט ומקצועי של הציון — לתצוגה בדשבורד.
    כולל: למה הציון כזה, מה הבעיות, ולמה כדאי לפנות.
    """
    name = biz.get("name", "")
    issues = detect_issues(biz)

    lines = [f"📊 ניתוח מפורט — {name}", ""]

    # ציון כללי
    if score >= 70:
        lines.append(f"🔥 ציון: {score}/100 — ליד חם מאוד! עסק שממש צריך אתר/שדרוג.")
    elif score >= 45:
        lines.append(f"⚡ ציון: {score}/100 — ליד טוב, כדאי לפנות.")
    else:
        lines.append(f"❄️ ציון: {score}/100 — ליד קר, עדיפות נמוכה.")
    lines.append("")

    # פירוט הבעיות
    if not biz.get("has_website"):
        lines += [
            "🚫 אין אתר אינטרנט כלל!",
            f"   זו ההזדמנות הטובה ביותר — {name} לא נמצא בגוגל.",
            "   כל לקוח שמחפש את השירות שלו עובר למתחרה.",
            "",
        ]
    else:
        lines.append("🌐 יש אתר — בעיות שנמצאו:")
        for key in issues:
            issue = ISSUES.get(key)
            if not issue:
                continue
            lines.append(f"   ❌ {issue['short']}: {issue.get('impact', '')}")
        lines.append("")

    # CMS
    cms = biz.get("cms_platform")
    if cms:
        if cms == "wix":
            lines.append(f"🔧 CMS: Wix — פלטפורמה מוגבלת, קשה לקידום SEO")
        elif cms == "wordpress":
            lines.append(f"🔧 CMS: WordPress — ניתן לשפר ולהתאים")
        elif cms == "custom":
            lines.append(f"🔧 CMS: אתר מותאם אישית")

    # SEO
    seo = biz.get("seo_score")
    if seo is not None:
        if seo < 25:
            lines.append(f"📈 SEO: {seo}/100 — גרוע מאוד, כמעט בלתי נראה בגוגל")
        elif seo < 50:
            lines.append(f"📈 SEO: {seo}/100 — חלש, מפסידים הרבה תנועה אורגנית")
        elif seo < 75:
            lines.append(f"📈 SEO: {seo}/100 — בינוני, יש מקום לשיפור")
        else:
            lines.append(f"📈 SEO: {seo}/100 — סביר")

    # Copyright year
    cy = biz.get("copyright_year")
    if cy and cy < 2022:
        lines.append(f"📅 אתר ישן: copyright {cy} ({2026-cy} שנים)")

    # Google Reviews
    reviews = biz.get("google_reviews") or 0
    rating = biz.get("google_rating") or 0
    if reviews > 0:
        lines.append(f"⭐ Google: {reviews} ביקורות, דירוג {rating}")
        if reviews > 20 and not biz.get("has_website"):
            lines.append(f"   💡 עסק פופולרי בלי אתר — הזדמנות מצוינת!")

    lines.append("")

    # פירוט הניקוד
    lines.append("📋 פירוט הניקוד:")
    for reason, pts in sorted(breakdown.items(), key=lambda x: -x[1]):
        sign = "+" if pts > 0 else ""
        lines.append(f"   {sign}{pts}  {reason}")

    return "\n".join(lines)
