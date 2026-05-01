"use client";

import { motion, useReducedMotion } from "motion/react";
import { useRef, useState } from "react";
import SectionHeader from "../SectionHeader";
import Icon from "../Icon";
import { testimonials } from "@/data/testimonials";

export default function Testimonials() {
  const reduce = useReducedMotion();
  const [index, setIndex] = useState(0);
  const trackRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const goNext = () => setIndex((i) => Math.min(testimonials.length - 1, i + 1));
  const goPrev = () => setIndex((i) => Math.max(0, i - 1));

  const cardWidth = 340;
  const gap = 16;
  const offset = -(index * (cardWidth + gap));

  return (
    <section className="py-20 sm:py-28 relative overflow-hidden border-t border-[var(--bg-line)]">
      <div className="relative max-w-7xl mx-auto px-6 sm:px-10">
        <SectionHeader
          num="05"
          label="לקוחות מספרים"
          title={
            <>
              מה <span className="text-[var(--text-muted)]">אומרים עלינו</span>
            </>
          }
          description="לקוחות מרוצים שגדלו איתנו."
        />

        <div className="relative" ref={containerRef}>
          <div className="md:hidden">
            <div className="snap-x-cards flex gap-4 overflow-x-auto pb-4 -mx-6 px-6">
              {testimonials.map((t) => (
                <TestimonialCard key={t.author} t={t} />
              ))}
            </div>
            <p className="text-xs text-[var(--text-dim)] text-center mt-2">
              גררו את הכרטיסיות לצדדים
            </p>
          </div>

          <div className="hidden md:block">
            <motion.div
              ref={trackRef}
              className="flex gap-4 will-change-transform"
              animate={{ x: reduce ? 0 : offset }}
              transition={{ type: "spring", stiffness: 90, damping: 22 }}
              drag={reduce ? false : "x"}
              dragConstraints={{
                left: -((testimonials.length - 1) * (cardWidth + gap)),
                right: 0,
              }}
              dragElastic={0.1}
              onDragEnd={(_, info) => {
                if (info.offset.x < -80 && index < testimonials.length - 1) goNext();
                else if (info.offset.x > 80 && index > 0) goPrev();
              }}
            >
              {testimonials.map((t) => (
                <TestimonialCard key={t.author} t={t} />
              ))}
            </motion.div>
          </div>

          <div className="hidden md:flex items-center gap-3 mt-8">
            <button
              onClick={goPrev}
              disabled={index === 0}
              className="w-10 h-10 rounded-md border border-[var(--bg-line)] hover:border-white hover:bg-[var(--bg-elev)] disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center justify-center text-white"
              aria-label="הקודם"
            >
              <Icon name="arrow-left" size={16} />
            </button>
            <button
              onClick={goNext}
              disabled={index === testimonials.length - 1}
              className="w-10 h-10 rounded-md border border-[var(--bg-line)] hover:border-white hover:bg-[var(--bg-elev)] disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center justify-center text-white"
              aria-label="הבא"
            >
              <Icon name="arrow-right" size={16} />
            </button>
            <div className="text-xs text-[var(--text-dim)] mr-3 tracking-wider">
              <span className="text-white font-bold">{String(index + 1).padStart(2, "0")}</span>
              <span className="mx-2">/</span>
              <span>{String(testimonials.length).padStart(2, "0")}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TestimonialCard({ t }: { t: (typeof testimonials)[number] }) {
  return (
    <div className="shrink-0 w-[300px] md:w-[340px] bg-[var(--bg-elev)] border border-[var(--bg-line)] rounded-xl p-6">
      <div className="text-white/40 mb-4">
        <Icon name="quote" size={24} />
      </div>
      <p className="text-white text-sm leading-relaxed mb-5">
        &ldquo;{t.quote}&rdquo;
      </p>
      <div className="border-t border-[var(--bg-line)] pt-4">
        <div className="text-white text-sm font-bold">{t.author}</div>
        <div className="text-[var(--text-dim)] text-xs mt-0.5">{t.role}</div>
      </div>
    </div>
  );
}
