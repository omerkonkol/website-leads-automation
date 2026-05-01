"use client";

import { motion } from "motion/react";
import { RevealStagger, staggerItem } from "../Reveal";
import SectionHeader from "../SectionHeader";
import Icon from "../Icon";
import { processSteps } from "@/data/process";

export default function Process() {
  return (
    <section id="process" className="py-20 sm:py-28 relative border-t border-[var(--bg-line)]">
      <div className="relative max-w-5xl mx-auto px-6 sm:px-10">
        <SectionHeader
          num="03"
          label="תהליך עבודה"
          title={
            <>
              איך זה <span className="text-[var(--text-muted)]">עובד</span>
            </>
          }
          description="תהליך מסודר ושקוף מהרגע הראשון."
        />

        <RevealStagger className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-10 sm:gap-y-14" stagger={0.08}>
          {processSteps.map((step) => (
            <motion.div
              key={step.step}
              variants={staggerItem}
              className="flex gap-5 group"
            >
              <div className="text-xs font-bold text-[var(--text-dim)] tracking-widest pt-1.5 shrink-0">
                {step.step}
              </div>
              <div className="border-t border-[var(--bg-line)] pt-4 flex-1 group-hover:border-white/40 transition-colors">
                <div className="mb-4 text-white">
                  <Icon name={step.icon} size={22} />
                </div>
                <h3 className="text-lg font-bold text-white mb-2">
                  {step.title}
                </h3>
                <p className="text-[var(--text-muted)] text-sm leading-relaxed">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </RevealStagger>
      </div>
    </section>
  );
}
