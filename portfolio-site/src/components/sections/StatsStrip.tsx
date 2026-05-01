"use client";

import { motion } from "motion/react";
import { RevealStagger, staggerItem } from "../Reveal";
import CountUp from "../CountUp";
import { stats } from "@/data/stats";

export default function StatsStrip() {
  return (
    <section className="py-12 sm:py-16 relative border-t border-[var(--bg-line)]">
      <div className="max-w-7xl mx-auto px-6 sm:px-10">
        <RevealStagger
          className="grid grid-cols-2 sm:grid-cols-4 gap-px bg-[var(--bg-line)] border border-[var(--bg-line)] rounded-xl overflow-hidden"
          stagger={0.06}
        >
          {stats.map((s) => (
            <motion.div
              key={s.label}
              variants={staggerItem}
              className="bg-[var(--bg-base)] py-8 px-6"
            >
              <div className="text-3xl sm:text-4xl font-black text-white mb-1">
                <CountUp to={s.value} prefix={s.prefix} suffix={s.suffix} />
              </div>
              <div className="text-xs text-[var(--text-dim)] uppercase tracking-wider">
                {s.label}
              </div>
            </motion.div>
          ))}
        </RevealStagger>
      </div>
    </section>
  );
}
