"use client";

import { motion } from "motion/react";
import { RevealStagger, staggerItem } from "../Reveal";
import SectionHeader from "../SectionHeader";
import Icon from "../Icon";
import { services } from "@/data/services";

export default function Services() {
  return (
    <section id="services" className="py-20 sm:py-28 relative border-t border-[var(--bg-line)]">
      <div className="relative max-w-7xl mx-auto px-6 sm:px-10">
        <SectionHeader
          num="02"
          label="שירותים"
          title={
            <>
              מה אנחנו <span className="text-[var(--text-muted)]">עושים</span>
            </>
          }
          description="פתרונות דיגיטליים מקצה לקצה שמניבים תוצאות אמיתיות."
        />

        <RevealStagger
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-px bg-[var(--bg-line)] border border-[var(--bg-line)] rounded-xl overflow-hidden"
          stagger={0.06}
        >
          {services.map((service) => (
            <motion.div
              key={service.title}
              variants={staggerItem}
              className="group bg-[var(--bg-base)] hover:bg-[var(--bg-elev)] transition-colors p-6 sm:p-8"
            >
              <div className="mb-5 inline-flex items-center justify-center w-11 h-11 rounded-md border border-[var(--bg-line)] text-white transition-all duration-300 group-hover:border-white group-hover:-translate-y-0.5">
                <Icon name={service.icon} size={22} />
              </div>
              <h3 className="text-lg font-bold text-white mb-3">
                {service.title}
              </h3>
              <p className="text-[var(--text-muted)] text-sm leading-relaxed mb-4">
                {service.description}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {service.features.map((f) => (
                  <span
                    key={f}
                    className="text-[11px] text-[var(--text-muted)] px-2 py-0.5 border border-[var(--bg-line)] rounded"
                  >
                    {f}
                  </span>
                ))}
              </div>
            </motion.div>
          ))}
        </RevealStagger>
      </div>
    </section>
  );
}
