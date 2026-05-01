"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useState } from "react";
import Icon from "./Icon";

export default function WhatsAppFloat() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 2500);
    return () => clearTimeout(t);
  }, []);

  return (
    <AnimatePresence>
      {visible && (
        <motion.a
          href="https://wa.me/972525603365"
          target="_blank"
          rel="noopener noreferrer"
          aria-label="WhatsApp"
          className="fixed bottom-6 left-6 z-50 hover:brightness-110 text-white w-12 h-12 rounded-full flex items-center justify-center shadow-lg"
          style={{ background: "#25D366" }}
          initial={{ opacity: 0, scale: 0, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0 }}
          whileHover={{ scale: 1.08 }}
          whileTap={{ scale: 0.95 }}
          transition={{ type: "spring", stiffness: 220, damping: 18 }}
        >
          <span
            className="absolute inset-0 rounded-full animate-ping opacity-50"
            style={{ background: "#25D366" }}
          />
          <Icon name="whatsapp" size={24} className="relative" />
        </motion.a>
      )}
    </AnimatePresence>
  );
}
