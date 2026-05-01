import { type ReactElement, type SVGProps } from "react";

export type IconName =
  | "globe"
  | "bot"
  | "chart"
  | "rocket"
  | "card"
  | "analytics"
  | "chat"
  | "palette"
  | "gear"
  | "launch"
  | "check"
  | "arrow-up-right"
  | "arrow-down"
  | "arrow-left"
  | "arrow-right"
  | "phone"
  | "whatsapp"
  | "quote"
  | "menu"
  | "close";

type IconProps = SVGProps<SVGSVGElement> & {
  name: IconName;
  size?: number;
};

const paths: Record<IconName, ReactElement> = {
  globe: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18" />
      <path d="M12 3a13.5 13.5 0 010 18M12 3a13.5 13.5 0 000 18" />
    </>
  ),
  bot: (
    <>
      <rect x="4" y="7" width="16" height="12" rx="2.5" />
      <path d="M12 3v4" />
      <circle cx="12" cy="3" r="0.6" fill="currentColor" />
      <circle cx="9" cy="13" r="1.1" fill="currentColor" />
      <circle cx="15" cy="13" r="1.1" fill="currentColor" />
      <path d="M2 13h2M20 13h2" />
    </>
  ),
  chart: (
    <>
      <path d="M4 20V8M10 20V4M16 20v-9M22 20H2" />
    </>
  ),
  rocket: (
    <>
      <path d="M14 6.5C14 11 10 15 10 15s-4-1-4-5 4-7.5 4-7.5 4 3.5 4 4z" />
      <path d="M10 15l-2 2-3-1 1-3 2-2" />
      <path d="M14 11l3 1-1 3-3-2" />
      <circle cx="10" cy="8" r="1" fill="currentColor" />
    </>
  ),
  card: (
    <>
      <rect x="3" y="6" width="18" height="13" rx="2" />
      <path d="M3 10h18" />
      <path d="M7 15h3" />
    </>
  ),
  analytics: (
    <>
      <path d="M3 17l5-5 4 4 8-9" />
      <path d="M14 7h7v7" />
    </>
  ),
  chat: (
    <>
      <path d="M21 12a8 8 0 01-12.5 6.6L3 20l1.4-5.5A8 8 0 1121 12z" />
      <circle cx="9" cy="12" r="0.8" fill="currentColor" />
      <circle cx="13" cy="12" r="0.8" fill="currentColor" />
      <circle cx="17" cy="12" r="0.8" fill="currentColor" />
    </>
  ),
  palette: (
    <>
      <path d="M12 3a9 9 0 109 9c0-1.5-1.2-2-2.5-2H17a2 2 0 010-4h.5C18.8 6 20 5.5 20 4c0-.6-.5-1-1-1z" />
      <circle cx="7.5" cy="11" r="1" fill="currentColor" />
      <circle cx="9" cy="7" r="1" fill="currentColor" />
      <circle cx="13" cy="6" r="1" fill="currentColor" />
      <circle cx="16.5" cy="9" r="1" fill="currentColor" />
    </>
  ),
  gear: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 2v3M12 19v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M2 12h3M19 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" />
    </>
  ),
  launch: (
    <>
      <path d="M5 19l3-3M9 15l-3-1-1 3 4 1 1 4 3-1-1-3" />
      <path d="M14 13c4-2 7-7 7-11-4 0-9 3-11 7" />
      <circle cx="15" cy="9" r="1.5" />
    </>
  ),
  check: (
    <>
      <path d="M5 13l4 4L19 7" />
    </>
  ),
  "arrow-up-right": (
    <>
      <path d="M7 17L17 7M9 7h8v8" />
    </>
  ),
  "arrow-down": (
    <>
      <path d="M19 14l-7 7m0 0l-7-7m7 7V3" />
    </>
  ),
  "arrow-left": (
    <>
      <path d="M15 19l-7-7 7-7" />
    </>
  ),
  "arrow-right": (
    <>
      <path d="M9 5l7 7-7 7" />
    </>
  ),
  phone: (
    <>
      <path d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
    </>
  ),
  whatsapp: (
    <g fill="currentColor" stroke="none">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z" />
      <path d="M12 0C5.373 0 0 5.373 0 12c0 2.625.846 5.059 2.284 7.034L.789 23.492a.5.5 0 00.612.638l4.648-1.408A11.953 11.953 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-2.387 0-4.592-.8-6.363-2.147l-.178-.14-3.693 1.12 1.178-3.534-.154-.184A9.96 9.96 0 012 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10z" />
    </g>
  ),
  quote: (
    <g fill="currentColor" stroke="none">
      <path d="M9.983 3v7.391c0 5.704-3.731 9.57-8.983 10.609l-.995-2.151c2.432-.917 3.995-3.638 3.995-5.849h-4v-10h9.983zm14.017 0v7.391c0 5.704-3.748 9.571-9 10.609l-.996-2.151c2.433-.917 3.996-3.638 3.996-5.849h-3.983v-10h9.983z" />
    </g>
  ),
  menu: (
    <>
      <path d="M4 6h16M4 12h16M4 18h16" />
    </>
  ),
  close: (
    <>
      <path d="M6 18L18 6M6 6l12 12" />
    </>
  ),
};

export default function Icon({ name, size = 24, strokeWidth = 1.6, ...rest }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden
      {...rest}
    >
      {paths[name]}
    </svg>
  );
}
