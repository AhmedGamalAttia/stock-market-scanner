"use client";

import type { ExitRow, Hold, SignalWithStock } from "@/lib/types";
import { isHalal } from "@/lib/utils";
import { ExitCard } from "./exit-card";
import { HiddenBanner, useHalalOnly } from "./halal-context";
import { OpportunitiesGrid } from "./opportunities-grid";
import { PositionCard } from "./position-card";

type Props = {
  buys: SignalWithStock[];
  holds: Hold[];
  exits: ExitRow[];
  /** خريطة الرمز → الحالة الشرعية (للمراكز والخروجات اللى مش بتحمل الحالة جواها) */
  statusBySymbol: Record<string, string | null>;
};

export function TodayBoard({ buys, holds, exits, statusBySymbol }: Props) {
  const { halalOnly } = useHalalOnly();

  const keep = (symbol: string, embedded?: string | null) =>
    !halalOnly || isHalal(embedded ?? statusBySymbol[symbol] ?? null);

  const visBuys = buys.filter((s) => keep(s.symbol, s.stock?.sharia_status));
  const visHolds = holds.filter((h) => keep(h.symbol));
  const visExits = exits.filter((e) => keep(e.symbol));

  const hiddenBuys = buys.length - visBuys.length;
  const hiddenHolds = holds.length - visHolds.length;
  const hiddenExits = exits.length - visExits.length;

  const urgent = visHolds.filter((h) => h.pending_exit);
  const calm = visHolds.filter((h) => !h.pending_exit);

  return (
    <>
      {(visExits.length > 0 || hiddenExits > 0) && (
        <Section
          emoji="🔴"
          title={`اخرج (${visExits.length})`}
          hint="المراكز دى اتقفلت بقواعد الاستراتيجية فى جلسة اليوم. لو داخل فيها، اخرج على الافتتاح."
          hidden={hiddenExits}
        >
          {visExits.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {visExits.map((e) => (
                <ExitCard key={e.id} e={e} />
              ))}
            </div>
          )}
        </Section>
      )}

      {urgent.length > 0 && (
        <Section
          emoji="⚠️"
          title={`اخرج بكرة على الافتتاح (${urgent.length})`}
          hint="الاتجاه انقلب على إقفال اليوم. الاستراتيجية بتبيع على افتتاح الجلسة الجاية."
        >
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {urgent.map((h) => (
              <PositionCard key={h.id} h={h} />
            ))}
          </div>
        </Section>
      )}

      <Section
        emoji="🟢"
        title={`ادخل (${visBuys.length})`}
        hint="إشارات جديدة على إقفال اليوم. الدخول على افتتاح الجلسة الجاية بسعر الدخول أو أقل، والوقف من أول لحظة."
        hidden={hiddenBuys}
      >
        {visBuys.length === 0 ? (
          <div className="panel p-8 text-center">
            <div className="font-semibold mb-1">مفيش إشارات دخول متوافقة النهاردة</div>
            <p className="text-muted text-sm max-w-lg mx-auto leading-relaxed">
              ده طبيعى — الاستراتيجية بتدخل لما الاتجاه ينقلب لصاعد بس، وده بيحصل كام مرة فى الشهر على كل
              الأسهم. الانتظار جزء من الخطة.
            </p>
          </div>
        ) : (
          <OpportunitiesGrid signals={visBuys} />
        )}
      </Section>

      <Section
        emoji="🔵"
        title={`استمر (${calm.length})`}
        hint="مراكز مفتوحة حسب الاستراتيجية. لو داخل فيها: سيبها شغالة، والتزم بالوقف المكتوب على كل كارت."
        hidden={hiddenHolds}
      >
        {calm.length === 0 ? (
          <div className="panel p-6 text-center text-muted text-sm">مفيش مراكز مفتوحة متوافقة حالياً.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {calm.map((h) => (
              <PositionCard key={h.id} h={h} />
            ))}
          </div>
        )}
      </Section>
    </>
  );
}

function Section({
  emoji,
  title,
  hint,
  hidden = 0,
  children,
}: {
  emoji: string;
  title: string;
  hint: string;
  hidden?: number;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-xl font-bold">
          {emoji} {title}
        </h2>
        <p className="text-xs text-muted mt-0.5">{hint}</p>
        {hidden > 0 && (
          <div className="mt-1">
            <HiddenBanner count={hidden} />
          </div>
        )}
      </div>
      {children}
    </section>
  );
}
