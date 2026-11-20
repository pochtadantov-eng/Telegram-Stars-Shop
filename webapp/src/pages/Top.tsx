import type { AppConfig, LeaderItem, Me } from "../lib/api";
import { displayName, formatCountdown, money } from "../lib/api";
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
  return (
    <div className="page">
      <header className="brand-head">
        <h1>{cfg.brand_title}</h1>
        <p>мини-приложение</p>
      </header>
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
            }}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="glass leader-list">
        {items.length === 0 ? (
          <div className="empty">Пока нет участников за этот период</div>
        ) : (
          items.map((item) => (
            <div className="leader-row" key={item.id}>
              <div className={`place ${item.place <= 3 ? `p${item.place}` : ""}`}>
                {item.place}
              </div>
              <Avatar name={displayName(item)} photo={item.photo_url} />
              <div style={{ fontWeight: 600, fontSize: 13 }}>{displayName(item)}</div>
              <div className="leader-amt">
                <div className="t">{money(item.turnover)} ₽</div>
                {item.prize > 0 ? <div className="p">{money(item.prize)} ₽</div> : null}
              </div>
            </div>
          ))
        )}
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
