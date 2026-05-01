"use client";

import { motion } from "motion/react";
import { RevealStagger, staggerItem } from "../Reveal";
import MagneticButton from "../MagneticButton";
import SectionHeader from "../SectionHeader";
import Icon from "../Icon";
import { pricingPlans } from "@/data/pricing";

export default function Pricing() {
  return (
    <section id="pricing" className="py-20 sm:py-28 relative border-t border-[var(--bg-line)]">
      <div className="relative max-w-6xl mx-auto px-6 sm:px-10">
        <SectionHeader
          num="04"
          label="מחירים"
          title={
            <>
              חבילות <span className="text-[var(--text-muted)]">אוטומציה</span>
            </>
          }
          description="בחרו את החבילה שמתאימה לעסק שלכם."
        />

        <RevealStagger
          className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5"
          stagger={0.08}
        >
          {pricingPlans.map((plan) => (
            <motion.div
              key={plan.name}
              variants={staggerItem}
              whileHover={{ y: -4 }}
              transition={{ type: "spring", stiffness: 220, damping: 22 }}
              className={`relative bg-[var(--bg-elev)] rounded-xl p-7 ${
                plan.popular ? "ring-1 ring-white" : "border border-[var(--bg-line)]"
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 right-7 bg-white text-black text-[11px] font-bold px-3 py-1 rounded uppercase tracking-wider">
                  פופולרי
                </div>
              )}

              <div className="mb-6">
                <h3 className="text-sm font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1">
                  {plan.name}
                </h3>
                <p className="text-xs text-[var(--text-dim)] mb-5">{plan.subtitle}</p>
                <div className="flex items-baseline gap-1">
                  <span className="text-4xl font-black text-white">{plan.price}</span>
                  <span className="text-base text-[var(--text-muted)]">₪</span>
                  <span className="text-xs text-[var(--text-dim)] mr-2">{plan.period}</span>
                </div>
              </div>

              <ul className="space-y-2.5 mb-7 pb-7 border-b border-[var(--bg-line)]">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-[var(--text-muted)]">
                    <Icon name="check" size={16} className="text-white flex-shrink-0 mt-0.5" strokeWidth={2} />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>

              <MagneticButton
                href="https://wa.me/972525603365"
                target="_blank"
                rel="noopener noreferrer"
                className={`block text-center py-3 rounded-md font-semibold text-sm transition-colors w-full ${
                  plan.popular
                    ? "bg-white text-black hover:bg-[var(--text-muted)]"
                    : "border border-[var(--bg-line)] text-white hover:bg-[var(--bg-base)]"
                }`}
              >
                <span className="block w-full">התחילו עכשיו</span>
              </MagneticButton>
            </motion.div>
          ))}
        </RevealStagger>

        <motion.div
          className="mt-12"
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.7 }}
        >
          <div className="bg-[var(--bg-elev)] border border-[var(--bg-line)] rounded-xl p-6 sm:p-8 max-w-2xl">
            <div className="text-xs font-bold text-[var(--text-dim)] uppercase tracking-wider mb-2">
              מבצע השקה
            </div>
            <h3 className="text-lg sm:text-xl font-bold text-white mb-2">
              דף נחיתה איכותי מ-299₪ + מע&quot;מ
            </h3>
            <p className="text-[var(--text-muted)] text-sm">
              ל-100 העסקים הראשונים בלבד — כולל תשתית SEO מלאה, עיצוב פרימיום ואופטימיזציה למובייל.
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
