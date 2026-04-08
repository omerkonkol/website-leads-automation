import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "הצהרת נגישות | Nova Digital - נובה דיגיטל",
  description: "הצהרת הנגישות של נובה דיגיטל - Nova Digital",
};

export default function AccessibilityStatement() {
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
          הצהרת נגישות
        </h1>
        <p className="text-slate-400 mb-10">עדכון אחרון: אפריל 2026</p>

        <div className="prose prose-invert max-w-none space-y-8 text-slate-300 leading-relaxed">
          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              1. מחויבות לנגישות
            </h2>
            <p>
              Nova Digital — נובה דיגיטל מחויבת להנגשת האתר לאנשים עם
              מוגבלויות, בהתאם לחוק שוויון זכויות לאנשים עם מוגבלות,
              התשנ&quot;ח-1998, ולתקנות שוויון זכויות לאנשים עם מוגבלות
              (התאמות נגישות לשירות), התשע&quot;ג-2013.
            </p>
            <p className="mt-3">
              אנו שואפים לעמוד בדרישות תקן הנגישות הישראלי (ת&quot;י
              5568) המבוסס על הנחיות WCAG 2.0 ברמה AA.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              2. התאמות נגישות שבוצעו באתר
            </h2>
            <ul className="list-disc list-inside space-y-2">
              <li>
                <strong>מבנה סמנטי:</strong> שימוש בתגיות HTML סמנטיות
                (כותרות, רשימות, ניווט) לזיהוי נכון על ידי קוראי מסך
              </li>
              <li>
                <strong>ניגודיות צבעים:</strong> שמירה על ניגודיות מספקת
                בין טקסט לרקע
              </li>
              <li>
                <strong>תגיות ARIA:</strong> שימוש בתגיות aria-label
                לאלמנטים אינטראקטיביים
              </li>
              <li>
                <strong>ניווט מקלדת:</strong> האתר ניתן לניווט באמצעות
                מקלדת בלבד
              </li>
              <li>
                <strong>טקסט חלופי:</strong> תמונות באתר כוללות תיאור טקסטי
                חלופי (alt text)
              </li>
              <li>
                <strong>התאמה למובייל:</strong> האתר מותאם לתצוגה במגוון
                מכשירים וגדלי מסך
              </li>
              <li>
                <strong>RTL:</strong> תמיכה מלאה בכיוון טקסט מימין לשמאל
                בעברית
              </li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              3. טכנולוגיות תומכות
            </h2>
            <p>האתר תומך בדפדפנים ובטכנולוגיות הנגישות הבאות:</p>
            <ul className="list-disc list-inside space-y-2 mt-3">
              <li>Google Chrome (גרסה אחרונה)</li>
              <li>Mozilla Firefox (גרסה אחרונה)</li>
              <li>Microsoft Edge (גרסה אחרונה)</li>
              <li>Safari (גרסה אחרונה)</li>
              <li>קוראי מסך: NVDA, JAWS, VoiceOver</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              4. מגבלות ידועות
            </h2>
            <p>
              למרות מאמצינו, ייתכנו חלקים באתר שטרם הונגשו במלואם. אנו
              עובדים באופן שוטף לשיפור הנגישות ולטיפול בנושאים אלו. אם
              נתקלתם בבעיית נגישות, נשמח לשמוע ולטפל בכך בהקדם.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              5. פנייה בנושא נגישות
            </h2>
            <p>
              אם נתקלתם בבעיה בנגישות האתר, או אם יש לכם הצעות לשיפור,
              אנא פנו אלינו:
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
            <p className="mt-4">
              אנו מתחייבים לטפל בכל פנייה בנושא נגישות תוך 14 ימי עסקים.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              6. נציב נגישות
            </h2>
            <p>
              לפניות בנושא נגישות ניתן לפנות לנציב הנגישות שלנו בטלפון
              052-560-3365 או באמצעות וואטסאפ.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              7. מידע נוסף
            </h2>
            <p>
              למידע נוסף על זכויות אנשים עם מוגבלויות ונגישות אתרי אינטרנט
              בישראל, ניתן לפנות ל:
            </p>
            <ul className="list-disc list-inside space-y-2 mt-3">
              <li>
                נציבות שוויון זכויות לאנשים עם מוגבלות — משרד המשפטים
              </li>
              <li>מוקד טלפוני *6763</li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
