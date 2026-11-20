import type { AppConfig, Me } from "../lib/api";
import { displayName, money } from "../lib/api";
import { Avatar, BrandHead, Tile, TileIcon } from "../components/Shell";
import { Chevron as ChevronIcon } from "../components/Icons";
import { haptic } from "../lib/telegram";

type Props = {
  cfg: AppConfig;
  me: Me;
  weekEndsIn: number;
  onNavigate: (page: string) => void;
};

export function Home({ cfg, me, onNavigate }: Props) {
  const name = displayName(me);

  return (
    <div className="page home-stack">
      <BrandHead title={cfg.brand_title} />

      <div className="grid-2">
        <button
          type="button"
          className="glass mini-stat mini-stat-profile"
          onClick={() => {
            haptic();
            onNavigate("profile");
          }}
        >
          <div className="profile-stat-row">
            <Avatar name={name} photo={me.photo_url || "/icons/profile.png"} size={52} />
            <div className="min-w-0">
              <div className="label">Ваш оборот:</div>
              <div className="value value-lg">{money(me.turnover)} ₽</div>
              <div className="nick-inside trunc">{name}</div>
            </div>
          </div>
        </button>

        <div className="glass mini-stat mini-stat-rates">
          <div className="label">Актуальные курсы</div>
          <div className="rate-lines">
            <div className="rate-line">
              <img className="coin-logo" src="/icons/usdt.svg" alt="USDT" />
              <span>1 USDT = {money(cfg.rates.USDT)} ₽</span>
            </div>
            <div className="rate-line">
              <img className="coin-logo" src="/icons/ton.svg" alt="TON" />
              <span>1 TON = {money(cfg.rates.TON)} ₽</span>
            </div>
          </div>
        </div>
      </div>

      <Tile
        large
        icon={<TileIcon src="/icons/exchange.png" alt="" />}
        title="Создать обмен"
        subtitle="Быстро и безопасно"
        onClick={() => onNavigate("create")}
      />

      <div className="glass ref-note ref-note-lg">
        В профиле — реф. ссылка. За каждого реферала с 1 успешным обменом —{" "}
        {money(cfg.ref_bonus)} ₽ на бонусный баланс.
      </div>

      <Tile
        large
        icon={<TileIcon src="/icons/top.png" alt="" />}
        title="Топ по обмену"
        subtitle="День · неделя · месяц"
        onClick={() => onNavigate("top")}
      />

      <div className="grid-2 square-grid">
        <SquareTile
          icon="/icons/support.png"
          title="Поддержка"
          subtitle="Оператор"
          onClick={() => {
            haptic();
            if (cfg.support_url) window.open(cfg.support_url, "_blank");
            else onNavigate("info");
          }}
        />
        <SquareTile
          icon="/icons/orders.png"
          title="Мои заявки"
          subtitle="Статус"
          onClick={() => {
            haptic();
            onNavigate("orders");
          }}
        />
      </div>
    </div>
  );
}

function SquareTile({
  icon,
  title,
  subtitle,
  onClick,
}: {
  icon: string;
  title: string;
  subtitle: string;
  onClick: () => void;
}) {
  return (
    <button type="button" className="glass square-tile" onClick={onClick}>
      <img className="square-tile-icon" src={icon} alt="" draggable={false} />
      <strong className="square-tile-title">{title}</strong>
      <span className="square-tile-sub">{subtitle}</span>
      <span className="chev square-tile-chev">
        <ChevronIcon />
      </span>
    </button>
  );
}
