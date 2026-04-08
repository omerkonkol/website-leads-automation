import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "תנאי שימוש | Nova Digital - נובה דיגיטל",
  description: "תנאי השימוש של נובה דיגיטל - Nova Digital",
};

export default function TermsOfService() {
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
          תנאי שימוש
        </h1>
        <p className="text-slate-400 mb-10">עדכון אחרון: אפריל 2026</p>

        <div className="prose prose-invert max-w-none space-y-8 text-slate-300 leading-relaxed">
          <section>
            <h2 className="text-xl font-bold text-white mb-3">1. כללי</h2>
            <p>
              ברוכים הבאים לאתר של Nova Digital — נובה דיגיטל
              (&quot;האתר&quot;). השימוש באתר מהווה הסכמה לתנאי שימוש אלו.
              אם אינך מסכים/ה לתנאים, אנא הימנע/י משימוש באתר.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              2. השירותים שלנו
            </h2>
            <p>
              האתר מספק מידע אודות שירותי בניית אתרים, דפי נחיתה, קידום
              דיגיטלי, אוטומציות, מערכות CRM ושירותים נלווים. התכנים באתר
              מוצגים למטרות מידע ושיווק בלבד ואינם מהווים הצעה מחייבת.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              3. קניין רוחני
            </h2>
            <p>
              כל התכנים באתר — לרבות טקסטים, עיצובים, גרפיקה, לוגואים, קוד
              מקור, וכל חומר אחר — הם רכושה של נובה דיגיטל ומוגנים בזכויות
              יוצרים ובחוקי קניין רוחני. אין להעתיק, לשכפל, להפיץ או להציג
              תכנים מהאתר ללא אישור מראש ובכתב.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              4. הגבלת אחריות
            </h2>
            <p>
              האתר והתכנים בו מסופקים &quot;כמות שהם&quot; (AS IS). אנו עושים
              כמיטב יכולתנו לספק מידע מדויק ועדכני, אולם אין אנו מתחייבים
              לדיוק, שלמות או עדכניות המידע. החברה לא תישא באחריות לכל נזק
              ישיר או עקיף הנובע משימוש באתר או הסתמכות על תכניו.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              5. קישורים לאתרים חיצוניים
            </h2>
            <p>
              האתר עשוי לכלול קישורים לאתרים חיצוניים שאינם בשליטתנו. אנו
              לא אחראים לתכנים, למדיניות הפרטיות או לפרקטיקות של אתרים אלו.
              הגלישה באתרים חיצוניים היא באחריות המשתמש בלבד.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              6. שימוש אסור
            </h2>
            <p>חל איסור על:</p>
            <ul className="list-disc list-inside space-y-2 mt-3">
              <li>שימוש באתר למטרות בלתי חוקיות</li>
              <li>
                ניסיון לחדור למערכות האתר, לשבש את פעולתו או לפגוע בו
              </li>
              <li>העתקת תכנים מהאתר ללא אישור</li>
              <li>התחזות לגורם אחר בעת השימוש באתר</li>
              <li>שימוש בכלים אוטומטיים לסריקת האתר ללא אישור</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              7. תנאי תשלום והתקשרות
            </h2>
            <p>
              המחירים המוצגים באתר הינם להמחשה בלבד ועשויים להשתנות. תנאי
              התקשרות ספציפיים, כולל מחירים סופיים, לוחות זמנים ותנאי תשלום,
              ייקבעו בהסכם נפרד בכתב בין הצדדים. כל המחירים באתר אינם
              כוללים מע&quot;מ, אלא אם צוין אחרת.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              8. ביטול עסקה
            </h2>
            <p>
              ביטול עסקה יתבצע בהתאם להוראות חוק הגנת הצרכן,
              התשמ&quot;א-1981, ותקנות הגנת הצרכן (ביטול עסקה),
              התשע&quot;א-2010. תנאי ביטול ספציפיים יפורטו בהסכם ההתקשרות
              בין הצדדים.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              9. דין חל וסמכות שיפוט
            </h2>
            <p>
              תנאי שימוש אלו כפופים לדיני מדינת ישראל. סמכות השיפוט
              הבלעדית בכל סכסוך הנובע מתנאים אלו תהיה לבתי המשפט
              המוסמכים במחוז תל אביב-יפו.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              10. שינויים בתנאי השימוש
            </h2>
            <p>
              אנו שומרים לעצמנו את הזכות לעדכן תנאי שימוש אלו בכל עת.
              שינויים ייכנסו לתוקף עם פרסומם באתר. מומלץ לעיין בתנאי השימוש
              מעת לעת.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-bold text-white mb-3">
              11. יצירת קשר
            </h2>
            <p>לשאלות בנוגע לתנאי שימוש אלו:</p>
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
