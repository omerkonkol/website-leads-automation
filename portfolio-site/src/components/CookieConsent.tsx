"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";

export default function CookieConsent() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem("cookie_consent")) {
      const t = setTimeout(() => setShow(true), 1500);
      return () => clearTimeout(t);
    }
  }, []);

  const accept = () => {
    localStorage.setItem("cookie_consent", "accepted");
    setShow(false);
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          className="fixed bottom-0 left-0 right-0 z-50 p-4"
          initial={{ y: 80, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 80, opacity: 0 }}
          transition={{ duration: 0.4, ease: [0.21, 0.6, 0.35, 1] }}
        >
          <div className="max-w-3xl mx-auto bg-[var(--bg-elev)] border border-[var(--bg-line)] rounded-xl p-5 flex flex-col sm:flex-row items-center gap-4 shadow-2xl">
            <p className="text-sm text-[var(--text-muted)] flex-1 text-center sm:text-right">
              אתר זה משתמש בעוגיות (cookies) לצורך שיפור חוויית המשתמש וניתוח תנועה באתר.
              למידע נוסף ראו את{" "}
              <a href="/privacy" className="text-white hover:underline">
                מדיניות הפרטיות
              </a>{" "}
              שלנו.
            </p>
            <div className="flex gap-2">
              <button
                onClick={accept}
                className="bg-white text-black hover:bg-[var(--text-muted)] px-5 py-2 rounded-md text-sm font-semibold transition-colors"
              >
                מאשר
              </button>
              <button
                onClick={accept}
                className="border border-[var(--bg-line)] text-white px-5 py-2 rounded-md text-sm transition-colors hover:bg-[var(--bg-base)]"
              >
                סגור
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
