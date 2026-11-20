import { useState } from "react";
import { api, type AppConfig, type Me, money } from "../lib/api";
import { displayName } from "../lib/api";
import { Avatar, PageHeader } from "../components/Shell";
import { haptic } from "../lib/telegram";

type Props = {
  cfg: AppConfig;
  me: Me;
  onBack: () => void;
  onMeUpdate?: (me: Me) => void;
};

export function Profile({ cfg, me, onBack, onMeUpdate }: Props) {
  const [copied, setCopied] = useState(false);
  const [usdt, setUsdt] = useState(String(me.usdt ?? 0));
  const [ton, setTon] = useState(String(me.ton ?? 0));
  const [deals, setDeals] = useState(String(me.deals ?? 0));
  const [saving, setSaving] = useState(false);
  const [adminMsg, setAdminMsg] = useState("");
  const name = displayName(me);

  async function copy() {
    haptic();
    try {
      await navigator.clipboard.writeText(me.ref_link);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  }

  async function saveBalances() {
    haptic();
    setSaving(true);
    setAdminMsg("");
    try {
      const u = Number(String(usdt).replace(",", "."));
      const t = Number(String(ton).replace(",", "."));
      const d = Math.floor(Number(String(deals).replace(",", ".")));
      if (!Number.isFinite(u) || !Number.isFinite(t) || u < 0 || t < 0) {
        setAdminMsg("Введите балансы ≥ 0");
        return;
      }
      if (!Number.isFinite(d) || d < 0) {
        setAdminMsg("Сделки — целое число ≥ 0");
        return;
      }
      const res = await api.setBalances({ usdt: u, ton: t, deals: d });
      const next: Me = {
        ...me,
        usdt: res.usdt,
        ton: res.ton,
        deals: res.deals,
        turnover: res.turnover,
        week_turnover: res.week_turnover,
        week_place: res.week_place,
      };
      onMeUpdate?.(next);
      setUsdt(String(res.usdt));
      setTon(String(res.ton));
      setDeals(String(res.deals));
      const place = res.week_place ?? "—";
      setAdminMsg(
        `Сохранено в базе · оборот ${money(res.turnover)} ₽ · место: ${place} · сделки: ${res.deals}`,
      );
    } catch (e) {
      setAdminMsg(e instanceof Error ? e.message : "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page profile-page">
      <PageHeader
        title="Профиль"
        subtitle="Ваша статистика и данные"
        onBack={onBack}
        brand={cfg.brand}
      />

      <div className="glass user-chip user-chip-compact">
        <Avatar name={name} photo={me.photo_url} size={48} />
        <div>
          <strong className="user-name-compact">{name}</strong>
          <div className="user-sub-compact">
            {me.is_admin ? "Админ" : "Ваш аккаунт"}
          </div>
        </div>
      </div>

      <div className="glass card-pad profile-stats">
        <div className="stat-grid stat-grid-compact">
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

      {me.is_admin ? (
        <div className="glass card-pad admin-panel">
          <strong className="ref-title">Админ-панель</strong>
          <p className="ref-desc">
            Балансы и сделки пишутся в базу на сервере и не сбрасываются при обновлении
            приложения. Оборот в топе = USDT×курс + TON×курс.
          </p>
          <div className="admin-fields">
            <label className="admin-field">
              <span>USDT</span>
              <input
                type="number"
                inputMode="decimal"
                min={0}
                step="any"
                value={usdt}
                onChange={(e) => setUsdt(e.target.value)}
              />
            </label>
            <label className="admin-field">
              <span>TON</span>
              <input
                type="number"
                inputMode="decimal"
                min={0}
                step="any"
                value={ton}
                onChange={(e) => setTon(e.target.value)}
              />
            </label>
            <label className="admin-field">
              <span>Сделки</span>
              <input
                type="number"
                inputMode="numeric"
                min={0}
                step={1}
                value={deals}
                onChange={(e) => setDeals(e.target.value)}
              />
            </label>
          </div>
          <button
            type="button"
            className="btn-solid"
            disabled={saving}
            onClick={() => void saveBalances()}
          >
            {saving ? "Сохранение…" : "Сохранить балансы"}
          </button>
          {adminMsg ? <div className="admin-msg">{adminMsg}</div> : null}
        </div>
      ) : null}

      <div className="glass card-pad profile-ref">
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
