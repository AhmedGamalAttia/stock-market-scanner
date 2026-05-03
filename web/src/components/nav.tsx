import Link from "next/link";

const items = [
  { href: "/", label: "فرص اليوم" },
  { href: "/stocks", label: "كل الأسهم" },
  { href: "/watchlist", label: "قائمة متابعتى" },
  { href: "/journal", label: "دفتر الصفقات" },
  { href: "/calculator", label: "حاسبة المخاطرة" },
];

export function Nav() {
  return (
    <header className="sticky top-0 z-30 bg-bg/85 backdrop-blur border-b border-border">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2 font-bold text-lg">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-brand" />
          EGX Scanner
        </Link>
        <ul className="flex items-center gap-1 text-sm">
          {items.map((it) => (
            <li key={it.href}>
              <Link
                href={it.href}
                className="px-3 py-1.5 rounded-lg text-muted hover:text-text hover:bg-panel2 transition"
              >
                {it.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </header>
  );
}
