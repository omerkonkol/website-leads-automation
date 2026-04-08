import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "מדיניות פרטיות | Nova Digital - נובה דיגיטל",
  description: "מדיניות הפרטיות של נובה דיגיטל - Nova Digital",
};

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-slate-dark pt-24 pb-16">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <a
          href="/"
          className="inline-flex items-center gap-2 text-brand-cyan hover:text-white transition-colors text-sm mb-8"
        >
          &larr; חזרה לעמוד הראשי
        </a>

        <h1 className="text-3xl sm:text-4xl font-black text-white mb-2">
          מדיניות פרטיות
        </h1>
        <p className="text-slate-400 mb-10">עדכון אחרון: אפריל 2026</p>

        <div className="prose prose-invert max-w-none space-y-8 text-slate-300 leading-relaxed">
          <section>
            <h2 className="text-xl font-bold text-white mb-3">1. כללי</h2>
            <p>
              Nova Digital — נובה דיגיטל (&quot;החברה&quot;, &quot;אנחנו&quot;) מכבדת את
              פרטיות המשתמשים באתר שלה. מדיניות פרטיות זו מתארת את האופן שבו
              אנו אוספים, משתמשים ומגנים על המידע האישי שלך, בהתאם לחוק הגנת
              הפרטיות, התשמ&quot;א-1981, ותקנותיו.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              2. איזה מידע אנחנו אוספים?
            </h2>
            <p>אנו עשויים לאסוף את סוגי המידע הבאים:</p>
            <ul className="list-disc list-inside space-y-2 mt-3">
              <li>
                <strong>מידע שנמסר באופן יזום:</strong> שם מלא, מספר טלפון,
                כתובת דוא&quot;ל, ופרטים נוספים שתמסרו בטפסי יצירת קשר.
              </li>
              <li>
                <strong>מידע טכני:</strong> כתובת IP, סוג דפדפן, מערכת הפעלה,
                דפים שנצפו, זמן שהייה, ומקור ההגעה לאתר.
              </li>
              <li>
                <strong>עוגיות (Cookies):</strong> קבצי מידע קטנים הנשמרים
                בדפדפן שלך לצרכי שיפור חוויית המשתמש וניתוח סטטיסטי.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              3. כיצד אנו משתמשים במידע?
            </h2>
            <ul className="list-disc list-inside space-y-2">
              <li>מענה לפניות ובקשות שנשלחו דרך האתר</li>
              <li>שיפור השירותים והתכנים שלנו</li>
              <li>ניתוח סטטיסטי ומעקב אחר ביצועי האתר</li>
              <li>יצירת קשר עם לקוחות פוטנציאליים שהשאירו פרטים</li>
              <li>
                עמידה בדרישות חוקיות ורגולטוריות בהתאם לדין הישראלי
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              4. שיתוף מידע עם צדדים שלישיים
            </h2>
            <p>
              אנו לא מוכרים, משכירים או מעבירים מידע אישי לצדדים שלישיים,
              למעט במקרים הבאים:
            </p>
            <ul className="list-disc list-inside space-y-2 mt-3">
              <li>כאשר נדרש לפי חוק או צו בית משפט</li>
              <li>
                לספקי שירות הפועלים מטעמנו (כגון שירותי אחסון, אנליטיקס) —
                בכפוף להתחייבותם לשמירה על סודיות
              </li>
              <li>בהסכמתך המפורשת</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              5. עוגיות (Cookies)
            </h2>
            <p>האתר שלנו משתמש בעוגיות לצרכים הבאים:</p>
            <ul className="list-disc list-inside space-y-2 mt-3">
              <li>
                <strong>עוגיות הכרחיות:</strong> נדרשות לפעולה תקינה של האתר
              </li>
              <li>
                <strong>עוגיות אנליטיות:</strong> מסייעות לנו להבין כיצד
                מבקרים משתמשים באתר
              </li>
              <li>
                <strong>עוגיות שיווקיות:</strong> משמשות למעקב אחר
                אפקטיביות קמפיינים
              </li>
            </ul>
            <p className="mt-3">
              ניתן לנהל את העדפות העוגיות דרך הגדרות הדפדפן שלך. חסימת
              עוגיות מסוימות עלולה לפגוע בחוויית השימוש באתר.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              6. אבטחת מידע
            </h2>
            <p>
              אנו נוקטים באמצעי אבטחה סבירים ומקובלים כדי להגן על המידע
              האישי שלך מפני גישה בלתי מורשית, שימוש לרעה, או חשיפה. עם
              זאת, אין באפשרותנו להבטיח הגנה מוחלטת על מידע המועבר
              באינטרנט.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              7. זכויותיך
            </h2>
            <p>
              בהתאם לחוק הגנת הפרטיות, התשמ&quot;א-1981, הינך זכאי/ת:
            </p>
            <ul className="list-disc list-inside space-y-2 mt-3">
              <li>לעיין במידע האישי שנאסף אודותיך</li>
              <li>לבקש תיקון או מחיקה של מידע שגוי</li>
              <li>להתנגד לשימוש במידע שלך לצרכי דיוור ישיר</li>
              <li>לבקש העברת המידע שלך (ניידות מידע)</li>
            </ul>
            <p className="mt-3">
              לצורך מימוש זכויותיך, ניתן לפנות אלינו בפרטי הקשר המפורטים
              בסעיף 9.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              8. שינויים במדיניות
            </h2>
            <p>
              אנו שומרים לעצמנו את הזכות לעדכן מדיניות פרטיות זו מעת לעת.
              שינויים מהותיים יפורסמו באתר. המשך שימוש באתר לאחר עדכון
              המדיניות מהווה הסכמה למדיניות המעודכנת.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">9. יצירת קשר</h2>
            <p>
              לשאלות או בקשות בנוגע למדיניות פרטיות זו, ניתן לפנות אלינו:
            </p>
            <ul className="list-none space-y-2 mt-3">
              <li>
                טלפון:{" "}
                <a
                  href="tel:0525603365"
                  className="text-brand-cyan hover:underline"
                  dir="ltr"
                >
                  052-560-3365
                </a>
              </li>
              <li>
                וואטסאפ:{" "}
                <a
                  href="https://wa.me/972525603365"
                  className="text-brand-cyan hover:underline"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  לחצו כאן
                </a>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
