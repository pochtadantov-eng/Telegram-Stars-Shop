import type { AppConfig, Order } from "../lib/api";
import { METHOD_LABELS, STATUS_LABELS, money } from "../lib/api";
import { PageHeader } from "../components/Shell";

type Props = {
  cfg: AppConfig;
  orders: Order[];
  onBack: () => void;
};

export function Orders({ cfg, orders, onBack }: Props) {
  return (
    <div className="page">
      <header className="brand-head">
        <h1>{cfg.brand_title}</h1>
        <p>мини-приложение</p>
      </header>
      <PageHeader
        title="Мои заявки"
        subtitle="Статус обменов"
        onBack={onBack}
        brand={cfg.brand}
      />

      {orders.length === 0 ? (
        <div className="glass empty">Заявок пока нет — создайте первый обмен</div>
      ) : (
        orders.map((o) => (
          <div key={o.id} className="glass order-item">
            <div className="top">
              <span>
                #{o.id} · {o.amount} {o.asset}
              </span>
              <span className={`badge ${o.status}`}>{STATUS_LABELS[o.status] || o.status}</span>
            </div>
            <div style={{ marginTop: 6, fontSize: 13, color: "var(--muted)" }}>
              {METHOD_LABELS[o.method] || o.method} → {money(o.payout)} ₽
            </div>
            <div style={{ marginTop: 4, fontSize: 12, color: "var(--muted)" }}>
              {new Date(o.created_at * 1000).toLocaleString("ru-RU")}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
