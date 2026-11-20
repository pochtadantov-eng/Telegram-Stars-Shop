import type { AppConfig, Me } from "../lib/api";
import { displayName, money } from "../lib/api";
import { Avatar, BrandHead, Tile, TileIcon } from "../components/Shell";
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
          className="glass mini-stat mini-stat-short profile-stat"
          onClick={() => {
            haptic();
            onNavigate("profile");
          }}
        >
          <div className="profile-stat-row">
            <Avatar name={name} photo={me.photo_url || "/icons/profile.png"} size={44} />
            <div className="min-w-0">
              <div className="label">Профиль</div>
              <div className="value trunc">{name}</div>
              <div className="rates">
                <span>Оборот {money(me.turnover)} ₽</span>
              </div>
            </div>
          </div>
        </button>
        <div className="glass mini-stat mini-stat-short">
          <div className="label">Актуальные курсы</div>
          <div className="rates rates-lg">
            <span>1 USDT = {money(cfg.rates.USDT)} ₽</span>
            <span>1 TON = {money(cfg.rates.TON)} ₽</span>
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

      <div className="grid-2">
        <Tile
          compact
          icon={<TileIcon src="/icons/support.png" alt="" />}
          title="Поддержка"
          subtitle="Оператор"
          onClick={() => {
            if (cfg.support_url) window.open(cfg.support_url, "_blank");
            else onNavigate("info");
          }}
        />
        <Tile
          compact
          icon={<TileIcon src="/icons/orders.png" alt="" />}
          title="Мои заявки"
          subtitle="Статус"
          onClick={() => onNavigate("orders")}
        />
      </div>
    </div>
  );
}
