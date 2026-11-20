import { useEffect, useRef, useState } from "react";
import type { AppConfig, LeaderItem, Me } from "../lib/api";
import { displayName, formatCountdown, money } from "../lib/api";
import { leadersForPeriod, nextTickDelay, resetMarket, tickMarket } from "../lib/demoLeaders";
import { Avatar, PageHeader } from "../components/Shell";
import { haptic } from "../lib/telegram";

export type Period = "day" | "week" | "month";

type Props = {
  cfg: AppConfig;
  me: Me;
  items: LeaderItem[];
  myPlace: number | null;
  myTurnover: number;
  weekEndsIn: number;
  period: Period;
  onPeriod: (p: Period) => void;
  onBack: () => void;
  onOpenInfo: (kind: string) => void;
};

const PERIODS: { id: Period; label: string }[] = [
  { id: "day", label: "День" },
  { id: "week", label: "Неделя" },
  { id: "month", label: "Месяц" },
];

const CROWN: Record<number, string> = {
  1: "/icons/crown-1.svg",
  2: "/icons/crown-2.svg",
  3: "/icons/crown-3.svg",
};

export function Top({
  cfg,
  items,
  myPlace,
  myTurnover,
  weekEndsIn,
  period,
  onPeriod,
  onBack,
  onOpenInfo,
}: Props) {
  const useDemo = items.length === 0;
  const [board, setBoard] = useState<LeaderItem[]>(() =>
    useDemo ? leadersForPeriod(period) : items,
  );
  const [flashIds, setFlashIds] = useState<number[]>([]);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!useDemo) {
      setBoard(items);
      return;
    }
    setBoard(leadersForPeriod(period));
  }, [useDemo, items, period]);

  useEffect(() => {
    if (!useDemo) return;

    const schedule = () => {
      timerRef.current = window.setTimeout(() => {
        const { board: next, dealtIds } = tickMarket(period);
        setBoard(next);
        if (dealtIds.length) {
          setFlashIds(dealtIds);
          window.setTimeout(() => setFlashIds([]), 1600);
        }
        schedule();
      }, nextTickDelay());
    };

    schedule();
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current);
    };
  }, [useDemo, period]);

  return (
    <div className="page">
      <PageHeader
        title="Топ по обмену"
        subtitle={`До конца: ${formatCountdown(weekEndsIn)}`}
        onBack={onBack}
        brand={cfg.brand}
      />

      <div className="period-tabs">
        {PERIODS.map((p) => (
          <button
            key={p.id}
            type="button"
            className={`period-tab ${period === p.id ? "active" : ""}`}
            onClick={() => {
              haptic("select");
              onPeriod(p.id);
              if (useDemo) {
                setBoard(resetMarket(p.id));
                setFlashIds([]);
              }
            }}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="glass leader-list">
        {board.map((item) => {
          const flashed = flashIds.includes(item.id);
          return (
            <div
              className={`leader-row ${item.place <= 3 ? `top-${item.place}` : ""} ${
                flashed ? "leader-deal" : ""
              }`}
              key={item.id}
            >
              <div className={`place ${item.place <= 3 ? `p${item.place}` : ""}`}>
                {CROWN[item.place] ? (
                  <img className="place-crown" src={CROWN[item.place]} alt={`${item.place}`} />
                ) : (
                  item.place
                )}
              </div>
              <Avatar name={displayName(item)} photo={item.photo_url} size={40} />
              <div className="leader-name">
                <div className="leader-nick">{displayName(item)}</div>
                {item.place <= 3 ? (
                  <div className="leader-rank-label">
                    {item.place === 1 ? "Топ 1" : item.place === 2 ? "Топ 2" : "Топ 3"}
                  </div>
                ) : null}
              </div>
              <div className="leader-amt">
                <div className={`t ${flashed ? "amt-bump" : ""}`}>{money(item.turnover)} ₽</div>
                {item.prize > 0 ? <div className="p">приз {money(item.prize)} ₽</div> : null}
              </div>
            </div>
          );
        })}
      </div>

      <div className="glass me-bar">
        Вы на <b>{myPlace ?? "—"} месте</b> · оборот <b>{money(myTurnover)} ₽</b>
      </div>

      <div className="glass guarantee">
        <strong>🚀 Мы ценим ваше время!</strong>
        Вашу заявку обработают в течение ближайших 15 минут. Если вдруг задержимся — подарим
        вам {money(cfg.delay_compensation)} ₽ к обмену в качестве компенсации.
      </div>

      <div className="glass" style={{ marginTop: 12, padding: "10px 14px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 700 }}>
          <span>Полезная информация</span>
          <span>▾</span>
        </div>
        <div className="info-icons">
          {[
            ["ℹ️", "info"],
            ["🛡️", "security"],
            ["🎧", "support"],
            ["📄", "history"],
            ["❓", "faq"],
          ].map(([icon, kind]) => (
            <button
              key={kind}
              type="button"
              onClick={() => {
                haptic();
                onOpenInfo(kind);
              }}
            >
              {icon}
            </button>
          ))}
        </div>
      </div>

      <div className="footer-meta">
        {cfg.totals.done_orders} успешных обменов · {cfg.totals.users} пользователей
      </div>
    </div>
  );
}
