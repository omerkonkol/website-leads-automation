import Image from "next/image";

export default function Footer() {
  return (
    <footer className="border-t border-[var(--bg-line)] py-10 mt-10">
      <div className="max-w-7xl mx-auto px-6 sm:px-10">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
          <div className="flex items-center gap-2">
            <Image
              src="/nova-icon.png"
              alt="Nova Digital"
              width={26}
              height={26}
              className="rounded"
              style={{ width: 26, height: 26 }}
            />
            <span className="text-sm font-bold text-white">Nova Digital</span>
          </div>

          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-[var(--text-dim)]">
            <a href="/privacy" className="hover:text-white transition-colors">מדיניות פרטיות</a>
            <a href="/terms" className="hover:text-white transition-colors">תנאי שימוש</a>
            <a href="/accessibility" className="hover:text-white transition-colors">הצהרת נגישות</a>
            <span className="opacity-60">
              &copy; {new Date().getFullYear()} Nova Digital
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
