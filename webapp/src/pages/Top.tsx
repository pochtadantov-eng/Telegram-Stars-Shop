import type { AppConfig, LeaderItem, Me } from "../lib/api";
import { displayName, formatCountdown, money } from "../lib/api";
import { Avatar, PageHeader } from "../components/Shell";
import { playClick } from "../lib/sound";
import { haptic } from "../lib/telegram";

type Props = {
  cfg: AppConfig;
  me: Me;
  items: LeaderItem[];
  myPlace: number | null;
  myTurnover: number;
  weekEndsIn: number;
  onBack: () => void;
  onOpenInfo: (kind: string) => void;
};

export function Top({
  cfg,
  me,
  items,
  myPlace,
  myTurnover,
  weekEndsIn,
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

      <div className="grid-2" style={{ marginBottom: 10 }}>
        <button
          type="button"
          className="glass tile"
          onClick={() => {
            playClick();
            haptic();
            onOpenInfo("profile");
          }}
        >
          <div className="tile-body">
            <strong>Профиль</strong>
            <span>Ваш аккаунт</span>
          </div>
          <span className="chev">›</span>
        </button>
        <button
          type="button"
          className="glass tile"
          onClick={() => {
            playClick();
            haptic();
            onOpenInfo("orders");
          }}
        >
          <div className="tile-body">
            <strong>Мои заявки</strong>
            <span>Статус обменов</span>
          </div>
          <span className="chev">›</span>
        </button>
      </div>

      <div className="glass tile" style={{ marginBottom: 10 }}>
        <div className="tile-body">
          <strong>Оборот недели 💰</strong>
          <span>До конца: {formatCountdown(weekEndsIn)}</span>
        </div>
      </div>

      <div className="glass leader-list">
        {items.length === 0 ? (
          <div className="empty">Пока нет участников недели</div>
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
                playClick();
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
