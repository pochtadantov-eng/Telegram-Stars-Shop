import type { AppConfig, Me } from "../lib/api";
import { formatCountdown, money } from "../lib/api";
import { BrandHead, Tile } from "../components/Shell";
import { ListIcon, SwapIcon, TrophyIcon, UserIcon, WalletIcon } from "../components/Icons";
import { playClick } from "../lib/sound";
import { haptic } from "../lib/telegram";

type Props = {
  cfg: AppConfig;
  me: Me;
  weekEndsIn: number;
  onNavigate: (page: string) => void;
};

export function Home({ cfg, me, weekEndsIn, onNavigate }: Props) {
  return (
    <div className="page home-stack">
      <BrandHead title={cfg.brand_title} />

      <div className="grid-2">
        <button
          type="button"
          className="glass mini-stat"
          onClick={() => {
            playClick();
            haptic();
            onNavigate("profile");
          }}
        >
          <div className="label">Ваш оборот</div>
          <div className="value">{money(me.turnover)} ₽</div>
        </button>
        <div className="glass mini-stat">
          <div className="label">Актуальные курсы</div>
          <div className="rates">
            <span>1 USDT = {money(cfg.rates.USDT)} ₽</span>
            <span>1 TON = {money(cfg.rates.TON)} ₽</span>
          </div>
        </div>
      </div>

      <Tile
        icon={<SwapIcon />}
        title="Создать обмен"
        subtitle="Быстро и безопасно"
        onClick={() => onNavigate("create")}
      />

      <div className="glass ref-note">
        В разделе «Профиль» можно получить реф. ссылку. За каждого реферала с 1 успешным
        обменом — {money(cfg.ref_bonus)} ₽ на бонусный баланс.
      </div>

      <Tile
        icon={<TrophyIcon />}
        title="Топ по обмену"
        subtitle="Лучшие курсы и обмены"
        onClick={() => onNavigate("top")}
      />

      <div className="grid-2">
        <Tile
          icon={<UserIcon />}
          title="Профиль"
          subtitle="Ваш аккаунт"
          onClick={() => onNavigate("profile")}
        />
        <Tile
          icon={<ListIcon />}
          title="Мои заявки"
          subtitle="Статус обменов"
          onClick={() => onNavigate("orders")}
        />
      </div>

      <Tile
        icon={<WalletIcon />}
        title="Оборот недели 💰"
        subtitle={`До конца: ${formatCountdown(weekEndsIn)}`}
        onClick={() => onNavigate("top")}
      />
    </div>
  );
}
