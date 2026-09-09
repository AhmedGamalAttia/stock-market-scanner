"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

/**
 * فلتر التوافق الشرعى العام — مصدر واحد للحقيقة عبر كل الصفحات.
 * الافتراضى: "حلال فقط" (المتوافق الصافى). المستخدم يقدر يظهر الباقى بزر واحد،
 * والاختيار بيتحفظ فى المتصفح فيفضل ثابت بين الجلسات.
 */

const KEY = "egx:halalOnly";

type Ctx = {
  halalOnly: boolean;
  setHalalOnly: (v: boolean) => void;
  toggle: () => void;
  /** true بعد ما نقرأ التخزين المحلى — لتجنّب وميض قيمة خاطئة */
  ready: boolean;
};

const HalalCtx = createContext<Ctx>({
  halalOnly: true,
  setHalalOnly: () => {},
  toggle: () => {},
  ready: false,
});

export function HalalProvider({ children }: { children: React.ReactNode }) {
  const [halalOnly, setState] = useState(true);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      if (localStorage.getItem(KEY) === "false") setState(false);
    } catch {
      /* التخزين المحلى مش متاح — نكمّل بالافتراضى */
    }
    setReady(true);
  }, []);

  const setHalalOnly = useCallback((v: boolean) => {
    setState(v);
    try {
      localStorage.setItem(KEY, String(v));
    } catch {
      /* تجاهل */
    }
  }, []);

  const toggle = useCallback(() => setHalalOnly(!halalOnly), [halalOnly, setHalalOnly]);

  return (
    <HalalCtx.Provider value={{ halalOnly, setHalalOnly, toggle, ready }}>
      {children}
    </HalalCtx.Provider>
  );
}

export function useHalalOnly(): Ctx {
  return useContext(HalalCtx);
}

/** زر التبديل — يوضع فى شريط التنقل */
export function HalalToggle() {
  const { halalOnly, toggle } = useHalalOnly();
  return (
    <button
      onClick={toggle}
      aria-pressed={halalOnly}
      title={
        halalOnly
          ? "بتشوف الأسهم المتوافقة مع الشريعة فقط — اضغط لإظهار الكل"
          : "بتشوف كل الأسهم — اضغط للاقتصار على المتوافق شرعياً"
      }
      className={`shrink-0 flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border transition ${
        halalOnly
          ? "bg-success/15 text-success border-success/40"
          : "bg-panel2 text-muted border-border hover:text-text"
      }`}
    >
      <span>{halalOnly ? "⭐" : "◉"}</span>
      <span className="whitespace-nowrap">{halalOnly ? "حلال فقط" : "كل الأسهم"}</span>
    </button>
  );
}

/** تنبيه صغير بعدد العناصر المخفية غير المتوافقة، مع رابط "إظهار" يفكّ الفلتر عالمياً */
export function HiddenBanner({ count }: { count: number }) {
  const { halalOnly, setHalalOnly } = useHalalOnly();
  if (!halalOnly || count <= 0) return null;
  return (
    <div className="text-xs text-muted flex items-center gap-2 px-1">
      <span>🔒 مخفى {count} غير متوافق شرعياً</span>
      <button onClick={() => setHalalOnly(false)} className="text-brand hover:underline">
        إظهار
      </button>
    </div>
  );
}
