"use client";

import { motion, useReducedMotion } from "motion/react";
import MagneticButton from "../MagneticButton";
import Icon from "../Icon";

const line1 = ["נכסים", "דיגיטליים"];
const line2 = ["שמניבים"];
const line3 = ["תוצאות."];

export default function Hero() {
  const reduce = useReducedMotion();

  const wordVariants = {
    hidden: { opacity: 0, y: reduce ? 0 : 40 },
    show: { opacity: 1, y: 0 },
  };

  return (
    <section className="relative min-h-screen flex flex-col justify-center overflow-hidden pt-28 pb-20">
      <div className="relative max-w-7xl mx-auto px-6 sm:px-10 w-full">
        <motion.div
          className="section-num mb-6 sm:mb-10 flex items-center gap-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <strong>00</strong>
          <span className="text-[var(--text-dim)]">/</span>
          <span className="text-white">נובה דיגיטל — סטודיו דיגיטלי</span>
        </motion.div>

        <motion.h1
          className="h-display text-4xl sm:text-5xl md:text-6xl lg:text-7xl text-white"
          initial="hidden"
          animate="show"
          variants={{
            show: {
              transition: { staggerChildren: 0.08, delayChildren: 0.25 },
            },
          }}
        >
          <span className="block">
            {line1.map((w) => (
              <motion.span
                key={w}
                variants={wordVariants}
                transition={{ duration: 0.7, ease: [0.21, 0.6, 0.35, 1] }}
                className="inline-block ml-3"
              >
                {w}
              </motion.span>
            ))}
          </span>
          <span className="block text-[var(--text-muted)]">
            {line2.map((w) => (
              <motion.span
                key={w}
                variants={wordVariants}
                transition={{ duration: 0.7, ease: [0.21, 0.6, 0.35, 1] }}
                className="inline-block ml-3"
              >
                {w}
              </motion.span>
            ))}
          </span>
          <span className="block">
            {line3.map((w) => (
              <motion.span
                key={w}
                variants={wordVariants}
                transition={{ duration: 0.7, ease: [0.21, 0.6, 0.35, 1] }}
                className="inline-block ml-3"
              >
                {w}
              </motion.span>
            ))}
          </span>
        </motion.h1>

        <motion.p
          className="text-[var(--text-muted)] text-lg sm:text-xl mt-10 max-w-xl leading-relaxed"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.95, ease: [0.21, 0.6, 0.35, 1] }}
        >
          אנחנו בונים אתרים, דפי נחיתה ומערכות אוטומציה עם הטכנולוגיות
          המתקדמות ביותר — כדי שהעסק שלך יצמח.
        </motion.p>

        <motion.div
          className="mt-12 flex flex-col sm:flex-row items-start gap-4"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 1.1 }}
        >
          <MagneticButton
            href="https://wa.me/972525603365"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white text-black px-8 py-4 rounded-md text-base font-semibold hover:bg-[var(--text-muted)] transition-colors inline-flex items-center justify-center"
          >
            <span>שיחת ייעוץ חינם</span>
          </MagneticButton>
          <MagneticButton
            href="#portfolio"
            className="border border-[var(--bg-line)] text-white px-8 py-4 rounded-md text-base font-medium hover:bg-[var(--bg-elev)] transition-colors inline-flex items-center justify-center"
          >
            <span>צפו בעבודות</span>
          </MagneticButton>
        </motion.div>
      </div>

      <motion.div
        className="absolute bottom-10 right-10 hidden md:flex items-center gap-3 text-xs text-[var(--text-dim)] tracking-widest uppercase"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1, y: [0, -6, 0] }}
        transition={{
          opacity: { duration: 0.6, delay: 1.6 },
          y: { duration: 2, repeat: Infinity, ease: "easeInOut" },
        }}
      >
        <span>גלול למטה</span>
        <Icon name="arrow-down" size={16} />
      </motion.div>
    </section>
  );
}
