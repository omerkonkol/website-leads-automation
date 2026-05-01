"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import MagneticButton from "../MagneticButton";
import SectionHeader from "../SectionHeader";
import Icon from "../Icon";

const SUPABASE_URL = "https://vinpsfqldlfcgbdajvym.supabase.co";
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpbnBzZnFsZGxmY2diZGFqdnltIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU0Nzc5NjcsImV4cCI6MjA5MTA1Mzk2N30.8wmUv3OoKZItN9Jb9Yf3HGvySJaoSXLxiPIpDK-Hv3w";

type FieldKey = "name" | "phone" | "message";

type FieldProps = {
  id: FieldKey;
  label: string;
  type?: "text" | "tel" | "textarea";
  required?: boolean;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
  dir?: "ltr" | "rtl";
};

function Field({
  id,
  label,
  type = "text",
  required,
  placeholder,
  value,
  onChange,
  dir,
}: FieldProps) {
  const [focused, setFocused] = useState(false);
  const filled = value.length > 0;
  const float = focused || filled;

  return (
    <div className="relative">
      <motion.label
        htmlFor={id}
        className="absolute right-4 pointer-events-none origin-right text-[var(--text-muted)]"
        animate={{
          y: float ? -20 : 14,
          scale: float ? 0.78 : 1,
          color: focused ? "#FFFFFF" : "#A3A3A3",
        }}
        transition={{ duration: 0.18, ease: [0.21, 0.6, 0.35, 1] }}
      >
        {label}
        {required && <span className="text-white mr-1">*</span>}
      </motion.label>
      {type === "textarea" ? (
        <textarea
          id={id}
          rows={4}
          required={required}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={focused ? placeholder : ""}
          className="w-full bg-[var(--bg-base)] border border-[var(--bg-line)] rounded-md px-4 pt-6 pb-3 text-white placeholder-[var(--text-dim)] focus:outline-none focus:border-white transition-colors resize-none"
        />
      ) : (
        <input
          id={id}
          type={type}
          required={required}
          dir={dir}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder={focused ? placeholder : ""}
          className="w-full bg-[var(--bg-base)] border border-[var(--bg-line)] rounded-md px-4 pt-6 pb-3 text-white placeholder-[var(--text-dim)] focus:outline-none focus:border-white transition-colors"
        />
      )}
    </div>
  );
}

export default function Contact() {
  const [formData, setFormData] = useState({ name: "", phone: "", message: "" });
  const [submitted, setSubmitted] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);

    try {
      await fetch(`${SUPABASE_URL}/rest/v1/contact_leads`, {
        method: "POST",
        headers: {
          apikey: SUPABASE_ANON_KEY,
          Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
          "Content-Type": "application/json",
          Prefer: "return=minimal",
        },
        body: JSON.stringify({
          name: formData.name,
          phone: formData.phone,
          message: formData.message || "",
          source: "website",
        }),
      });
    } catch {
      // Don't block WA if Supabase fails
    }

    const text = `שלום, שמי ${formData.name}. ${formData.message || "אשמח לשמוע פרטים נוספים"}`;
    window.open(
      `https://wa.me/972525603365?text=${encodeURIComponent(text)}`,
      "_blank"
    );
    setSaving(false);
    setSubmitted(true);
  };

  return (
    <section id="contact" className="py-20 sm:py-28 relative border-t border-[var(--bg-line)]">
      <div className="relative max-w-3xl mx-auto px-6 sm:px-10">
        <SectionHeader
          num="06"
          label="צור קשר"
          title={
            <>
              בואו <span className="text-[var(--text-muted)]">נדבר</span>
            </>
          }
          description="השאירו פרטים ונחזור אליכם תוך דקות."
          align="start"
        />

        <motion.div
          className="bg-[var(--bg-elev)] border border-[var(--bg-line)] rounded-xl p-6 sm:p-8"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.7 }}
        >
          <AnimatePresence mode="wait">
            {submitted ? (
              <motion.div
                key="success"
                className="text-center py-8"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
              >
                <motion.div
                  className="mb-5 inline-flex items-center justify-center w-14 h-14 rounded-full border border-white text-white"
                  initial={{ scale: 0, rotate: -90 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: "spring", stiffness: 200, damping: 14, delay: 0.1 }}
                >
                  <Icon name="check" size={28} strokeWidth={2} />
                </motion.div>
                <h3 className="text-xl font-bold text-white mb-2">תודה!</h3>
                <p className="text-[var(--text-muted)] text-sm">
                  נפתח לכם חלון וואטסאפ — שלחו לנו הודעה ונחזור אליכם מיד.
                </p>
              </motion.div>
            ) : (
              <motion.form
                key="form"
                onSubmit={handleSubmit}
                className="space-y-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <Field
                  id="name"
                  label="שם מלא"
                  required
                  placeholder="הכנס את שמך"
                  value={formData.name}
                  onChange={(v) => setFormData({ ...formData, name: v })}
                />
                <Field
                  id="phone"
                  label="טלפון"
                  type="tel"
                  required
                  dir="ltr"
                  placeholder="050-000-0000"
                  value={formData.phone}
                  onChange={(v) => setFormData({ ...formData, phone: v })}
                />
                <Field
                  id="message"
                  label="ספרו לנו על העסק שלכם"
                  type="textarea"
                  placeholder="מה העסק שלכם עושה? מה אתם מחפשים?"
                  value={formData.message}
                  onChange={(v) => setFormData({ ...formData, message: v })}
                />
                <MagneticButton
                  type="submit"
                  disabled={saving}
                  className="w-full bg-white text-black hover:bg-[var(--text-muted)] py-3.5 rounded-md text-base font-semibold transition-colors disabled:opacity-60 inline-flex items-center justify-center"
                >
                  <span className="block w-full">
                    {saving ? "שומר..." : "שלחו הודעה בוואטסאפ"}
                  </span>
                </MagneticButton>
              </motion.form>
            )}
          </AnimatePresence>
        </motion.div>

        <div className="mt-8 flex flex-col sm:flex-row gap-4 sm:gap-6 text-sm">
          <a
            href="tel:0525603365"
            className="flex items-center gap-2 text-[var(--text-muted)] hover:text-white transition-colors"
          >
            <Icon name="phone" size={16} />
            052-560-3365
          </a>
          <a
            href="https://wa.me/972525603365"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-[var(--text-muted)] hover:text-white transition-colors"
          >
            <Icon name="whatsapp" size={16} />
            וואטסאפ
          </a>
        </div>
      </div>
    </section>
  );
}
