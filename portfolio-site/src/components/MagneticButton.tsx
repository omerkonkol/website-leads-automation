"use client";

import {
  motion,
  useMotionValue,
  useSpring,
  useReducedMotion,
} from "motion/react";
import {
  type ReactNode,
  type PointerEvent,
  type CSSProperties,
  type Ref,
  useRef,
} from "react";

type MagneticButtonProps = {
  children: ReactNode;
  className?: string;
  href?: string;
  target?: string;
  rel?: string;
  type?: "button" | "submit";
  disabled?: boolean;
  onClick?: () => void;
  strength?: number;
  ariaLabel?: string;
  style?: CSSProperties;
};

export default function MagneticButton({
  children,
  className,
  href,
  target,
  rel,
  type = "button",
  disabled,
  onClick,
  strength = 0.3,
  ariaLabel,
  style,
}: MagneticButtonProps) {
  const reduce = useReducedMotion();
  const anchorRef = useRef<HTMLAnchorElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const spring = { stiffness: 220, damping: 18, mass: 0.5 };
  const springX = useSpring(x, spring);
  const springY = useSpring(y, spring);

  const onMove = (e: PointerEvent<HTMLElement>) => {
    if (reduce) return;
    const el = anchorRef.current ?? buttonRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    x.set((e.clientX - cx) * strength);
    y.set((e.clientY - cy) * strength);
  };

  const onLeave = () => {
    x.set(0);
    y.set(0);
  };

  const inner = (
    <motion.span
      style={{ x: springX, y: springY, display: "inline-flex" }}
      className="will-change-transform"
    >
      {children}
    </motion.span>
  );

  if (href) {
    return (
      <a
        ref={anchorRef as Ref<HTMLAnchorElement>}
        href={href}
        target={target}
        rel={rel}
        aria-label={ariaLabel}
        onPointerMove={onMove}
        onPointerLeave={onLeave}
        className={className}
        style={style}
      >
        {inner}
      </a>
    );
  }

  return (
    <button
      ref={buttonRef as Ref<HTMLButtonElement>}
      type={type}
      disabled={disabled}
      onClick={onClick}
      aria-label={ariaLabel}
      onPointerMove={onMove}
      onPointerLeave={onLeave}
      className={className}
      style={style}
    >
      {inner}
    </button>
  );
}
