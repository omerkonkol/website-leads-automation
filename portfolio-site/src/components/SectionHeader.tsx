"use client";

import { motion } from "motion/react";
import { type ReactNode } from "react";

type SectionHeaderProps = {
  num: string;
  label: string;
  title: ReactNode;
  description?: string;
  align?: "start" | "center";
};

export default function SectionHeader({
  num,
  label,
  title,
  description,
  align = "start",
}: SectionHeaderProps) {
  const alignClass = align === "center" ? "text-center mx-auto" : "text-start";

  return (
    <div className={`max-w-2xl mb-14 sm:mb-20 ${alignClass}`}>
      <motion.div
        className="section-num mb-5 flex items-center gap-3"
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.6 }}
        transition={{ duration: 0.5 }}
      >
        <span className="section-num">
          <strong>{num}</strong>
          <span className="mx-2 text-[var(--text-dim)]">/</span>
          <span className="text-[var(--text-primary)]">{label}</span>
        </span>
        <span className="h-px flex-1 bg-[var(--bg-line)]" />
      </motion.div>
      <motion.h2
        className="h-display text-3xl sm:text-4xl md:text-5xl text-white"
        initial={{ opacity: 0, y: 18 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.7, delay: 0.05, ease: [0.21, 0.6, 0.35, 1] }}
      >
        {title}
      </motion.h2>
      {description && (
        <motion.p
          className="text-[var(--text-muted)] text-lg leading-relaxed mt-5 max-w-xl"
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.7, delay: 0.15 }}
        >
          {description}
        </motion.p>
      )}
    </div>
  );
}
