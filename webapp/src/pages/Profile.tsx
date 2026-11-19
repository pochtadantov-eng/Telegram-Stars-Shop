import { useState } from "react";
import type { AppConfig, Me } from "../lib/api";
import { displayName, money } from "../lib/api";
import { Avatar, PageHeader } from "../components/Shell";
import { playClick, playSuccess } from "../lib/sound";
import { haptic } from "../lib/telegram";

type Props = {
  cfg: AppConfig;
  me: Me;
  onBack: () => void;
};

export function Profile({ cfg, me, onBack }: Props) {
  const [copied, setCopied] = useState(false);
  const name = displayName(me);

  async function copy() {
    playClick(720);
    haptic("select");
    try {
      await navigator.clipboard.writeText(me.ref_link);
      setCopied(true);
      playSuccess();
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="page">
      <BrandStrip title={cfg.brand_title} />
      <PageHeader
        title="Профиль"
        subtitle="Ваша статистика и данные"
        onBack={onBack}
        brand={cfg.brand}
      />

      <div className="glass user-chip">
        <Avatar name={name} photo={me.photo_url} />
        <div>
          <strong>{name}</strong>
          <div style={{ fontSize: 12, color: "var(--muted)" }}>Ваш аккаунт</div>
        </div>
      </div>

      <div className="glass card-pad" style={{ marginBottom: 10 }}>
        <div className="stat-grid">
          <div>
            <div className="k">Telegram ID</div>
            <div className="v">{me.id}</div>
          </div>
          <div>
            <div className="k">Сделки</div>
            <div className="v">{me.deals}</div>
          </div>
          <div>
            <div className="k">USDT</div>
            <div className="v">{money(me.usdt)}</div>
          </div>
          <div>
            <div className="k">TON</div>
            <div className="v">{money(me.ton)}</div>
          </div>
          <div>
            <div className="k">Общий оборот</div>
            <div className="v">{money(me.turnover)} ₽</div>
          </div>
          <div>
            <div className="k">Бонусный баланс</div>
            <div className="v">{money(me.bonus_balance)} ₽</div>
          </div>
          <div>
            <div className="k">По реф. ссылке</div>
            <div className="v">{me.ref_count}</div>
          </div>
          <div>
            <div className="k">С рефералов</div>
            <div className="v">{money(me.ref_earned)} ₽</div>
          </div>
        </div>
      </div>

      <div className="glass card-pad">
        <strong>Реферальная ссылка</strong>
        <p style={{ margin: "8px 0 0", fontSize: 12, color: "var(--muted)", lineHeight: 1.45 }}>
          За каждого реферала с 1 успешным обменом — {money(cfg.ref_bonus)} ₽ на бонусный баланс.
        </p>
        <div className="copy-row">
          <input readOnly value={me.ref_link} />
          <button type="button" className="btn-solid" onClick={copy}>
            {copied ? "Скопировано" : "Копировать"}
          </button>
        </div>
      </div>
    </div>
  );
}

function BrandStrip({ title }: { title: string }) {
  return (
    <header className="brand-head">
      <h1>{title}</h1>
      <p>мини-приложение</p>
    </header>
  );
}
