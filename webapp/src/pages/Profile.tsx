import { useState } from "react";
import type { AppConfig, Me } from "../lib/api";
import { displayName, money } from "../lib/api";
import { Avatar, PageHeader } from "../components/Shell";
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
    haptic("select");
    try {
      await navigator.clipboard.writeText(me.ref_link);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="page profile-page">
      <BrandStrip title={cfg.brand_title} />
      <PageHeader
        title="Профиль"
        subtitle="Ваша статистика и данные"
        onBack={onBack}
        brand={cfg.brand}
      />

      <div className="glass user-chip user-chip-lg">
        <Avatar name={name} photo={me.photo_url} size={64} />
        <div>
          <strong className="user-name-lg">{name}</strong>
          <div className="user-sub-lg">Ваш аккаунт</div>
        </div>
      </div>

      <div className="glass card-pad card-pad-lg" style={{ marginBottom: 12 }}>
        <div className="stat-grid stat-grid-lg">
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

      <div className="glass card-pad card-pad-lg">
        <strong className="ref-title">Реферальная ссылка</strong>
        <p className="ref-desc">
          За каждого реферала с 1 успешным обменом — {money(cfg.ref_bonus)} ₽ на бонусный баланс.
        </p>
        <div className="copy-row">
          <input readOnly value={me.ref_link} className="ref-input" />
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
