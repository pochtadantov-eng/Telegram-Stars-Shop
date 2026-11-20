import { useMemo, useState, type ReactNode } from "react";
import type { AppConfig, Me } from "../lib/api";
import { METHOD_LABELS, money } from "../lib/api";
import { PageHeader } from "../components/Shell";
import { BankIcon, CardIcon, PersonIcon, PhoneIcon } from "../components/Icons";
import { haptic } from "../lib/telegram";

type Props = {
  cfg: AppConfig;
  me: Me;
  onBack: () => void;
  onSubmit: (payload: Record<string, unknown>) => Promise<void>;
};

type AssetChoice = {
  id: string;
  asset: "USDT" | "TON";
  method: string;
  label: string;
  logo: string;
};

const ASSET_CHOICES: AssetChoice[] = [
  { id: "ton", asset: "TON", method: "ton", label: "TON", logo: "/icons/ton.svg" },
  {
    id: "usdt-trc20",
    asset: "USDT",
    method: "trc20",
    label: "USDT (TRC20)",
    logo: "/icons/usdt-trc20.svg",
  },
  {
    id: "usdt-ton",
    asset: "USDT",
    method: "ton",
    label: "USDT (TON)",
    logo: "/icons/usdt-ton.svg",
  },
];

function choiceFrom(asset: "USDT" | "TON", method: string): AssetChoice {
  return (
    ASSET_CHOICES.find((c) => c.asset === asset && c.method === method) ||
    ASSET_CHOICES.find((c) => c.asset === asset) ||
    ASSET_CHOICES[1]
  );
}

export function CreateExchange({ cfg, me, onBack, onSubmit }: Props) {
  const [asset, setAsset] = useState<"USDT" | "TON">("USDT");
  const [amount, setAmount] = useState("");
  const [bonus, setBonus] = useState("");
  const [method, setMethod] = useState("trc20");
  const [pickerOpen, setPickerOpen] = useState(false);
  const [phone, setPhone] = useState("");
  const [bank, setBank] = useState("");
  const [fullName, setFullName] = useState("");
  const [card, setCard] = useState("");
  const [wantPdf, setWantPdf] = useState(true);
  const [accept, setAccept] = useState(false);
  const [termsOpen, setTermsOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const methods = cfg.methods[asset] || [];
  // Тот же курс, что на главной (cfg.rates), без «сырого» market
  const rate = cfg.rates[asset];
  const rateUsdt = cfg.rates.USDT;
  const rateTon = cfg.rates.TON;
  const min = asset === "USDT" ? cfg.min_usdt : cfg.min_ton;
  const amountNum = parseFloat(amount.replace(",", ".")) || 0;
  const selected = choiceFrom(asset, method);
  const knownChoice = ASSET_CHOICES.find((c) => c.asset === asset && c.method === method);
  const pillLabel = knownChoice
    ? knownChoice.label
    : asset === "TON"
      ? "TON"
      : method === "cryptobot"
        ? "USDT (Crypto Bot)"
        : method === "xrocket"
          ? "USDT (xRocket)"
          : selected.label;
  const pillLogo = knownChoice
    ? knownChoice.logo
    : asset === "TON"
      ? "/icons/ton.svg"
      : "/icons/usdt.svg";

  const bonusNum = Math.min(
    parseFloat(bonus.replace(",", ".")) || 0,
    me.bonus_balance,
  );
  const payout = amountNum > 0 ? amountNum * rate + bonusNum : 0;

  const canSubmit = useMemo(() => {
    return (
      amountNum >= min &&
      phone.trim().length >= 10 &&
      bank.trim().length >= 2 &&
      accept &&
      me.cooldown_left <= 0 &&
      !busy
    );
  }, [amountNum, min, phone, bank, accept, me.cooldown_left, busy]);

  function applyChoice(choice: AssetChoice) {
    haptic("select");
    setAsset(choice.asset);
    setMethod(choice.method);
    setPickerOpen(false);
  }

  async function submit() {
    if (!canSubmit) {
      if (amountNum < min) setError(`Укажите сумму от ${min} ${asset}`);
      else if (!accept) setError("Примите условия обмена");
      else if (me.cooldown_left > 0)
        setError(`Следующую заявку можно создать через ${Math.ceil(me.cooldown_left / 60)} мин.`);
      else setError("Заполните телефон и банк");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await onSubmit({
        asset,
        method,
        amount: amountNum,
        bonus_used: bonusNum,
        phone: phone.trim(),
        bank: bank.trim(),
        full_name: fullName.trim() || null,
        card_number: card.trim() || null,
        want_pdf: wantPdf,
        accept_terms: true,
      });
      haptic();
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Ошибка";
      if (msg.startsWith("cooldown:")) {
        setError("Подождите перед следующей заявкой");
      } else {
        setError(msg);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page create-page">
      <PageHeader
        title="Создать обмен"
        subtitle="Заполните данные заявки"
        onBack={onBack}
        brand={cfg.brand}
      />

      <div className="rate-bar rate-bar-soft">
        <div className="marquee">
          <div className="marquee-track">
            {[0, 1].map((i) => (
              <span className="marquee-chunk" key={i}>
                <img src="/icons/usdt.svg" alt="" />
                <span>1 USD = {money(rateUsdt)} ₽</span>
                <span className="marquee-gap" />
                <img src="/icons/usdt.svg" alt="" />
                <span>1 USDT = {money(rateUsdt)} ₽</span>
                <span className="marquee-gap" />
                <img src="/icons/ton.svg" alt="" />
                <span>1 TON = {money(rateTon)} ₽</span>
                <span className="marquee-sep">·</span>
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className={`glass exchange-card give ${pickerOpen ? "picker-open" : ""}`}>
        <div className="row-top">
          <span>Вы отдаёте</span>
          <span>
            Минимум от {min} {asset}
          </span>
        </div>
        <div className="give-row">
          <input
            className="amount-input"
            inputMode="decimal"
            placeholder="0"
            value={amount}
            onChange={(e) => setAmount(e.target.value.replace(/[^\d.,]/g, ""))}
          />
          <div className="asset-picker-wrap">
            <button
              type="button"
              className="asset-pill"
              onClick={() => {
                haptic("select");
                setPickerOpen((v) => !v);
              }}
            >
              <span>{pillLabel}</span>
              <img src={pillLogo} alt="" className="asset-pill-logo" />
              <span className="asset-pill-caret">{pickerOpen ? "▴" : "▾"}</span>
            </button>
            {pickerOpen ? (
              <div className="asset-menu" role="listbox">
                {ASSET_CHOICES.map((c) => {
                  const active = asset === c.asset && method === c.method;
                  return (
                    <button
                      key={c.id}
                      type="button"
                      className={`asset-menu-item ${active ? "active" : ""}`}
                      onClick={() => applyChoice(c)}
                    >
                      <img src={c.logo} alt="" />
                      <span>{c.label}</span>
                      {active ? <em>✓</em> : null}
                    </button>
                  );
                })}
              </div>
            ) : null}
          </div>
        </div>
      </div>

      <div className="exchange-gap" aria-hidden />

      <div className="glass exchange-card get get-soft">
        <div className="row-top">
          <span>Вы получаете</span>
          <span>{cfg.payout_label}</span>
        </div>
        <div style={{ fontSize: 36, fontWeight: 800 }}>{money(payout)} ₽</div>
        <div style={{ marginTop: 6, fontSize: 12, opacity: 0.9 }}>Курс {money(rate)}</div>
      </div>

      <div className="section-label" style={{ display: "flex", justifyContent: "space-between" }}>
        <span>Добавить бонусы</span>
        <span style={{ color: "var(--muted)", fontWeight: 500 }}>
          доступно {money(me.bonus_balance)} ₽
        </span>
      </div>
      <div className="glass card-pad">
        <div className="bonus-tools">
          <div className="field-box" style={{ flex: 1, margin: 0 }}>
            <input
              inputMode="decimal"
              placeholder="000"
              value={bonus}
              onChange={(e) => setBonus(e.target.value.replace(/[^\d.,]/g, ""))}
            />
            <span>₽</span>
          </div>
          <button
            type="button"
            className="mini-round"
            onClick={() => {
              setBonus(String(me.bonus_balance / 2));
            }}
          >
            ½
          </button>
          <button
            type="button"
            className="mini-round"
            onClick={() => {
              setBonus(String(me.bonus_balance));
            }}
          >
            Всё
          </button>
        </div>
        <div style={{ marginTop: 8, fontSize: 12, color: "var(--muted)" }}>
          К выплате с бонусом: {money(payout)} ₽
        </div>
      </div>

      <div className="section-label">Как переведёте {asset}</div>
      <div className="chips">
        {methods.map((m) => (
          <button
            key={m}
            type="button"
            className={`chip ${method === m ? "active" : ""}`}
            onClick={() => {
              haptic("select");
              setMethod(m);
            }}
          >
            {method === m ? "✓ " : ""}
            {METHOD_LABELS[m] || m}
          </button>
        ))}
      </div>

      <div className="section-label" style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <span className="tile-icon" style={{ width: 34, height: 34, fontSize: 14 }}>
          <CardIcon />
        </span>
        <div>
          <div>Реквизиты получателя</div>
          <div style={{ fontSize: 12, color: "var(--muted)", fontWeight: 500 }}>
            Укажите данные для перевода
          </div>
        </div>
      </div>

      <div className="glass card-pad">
        <Field
          label="Телефон"
          hint="обязательно"
          icon={<PhoneIcon />}
          placeholder="79001234567"
          value={phone}
          onChange={setPhone}
        />
        <Field
          label="Банк"
          hint="обязательно"
          icon={<BankIcon />}
          placeholder="Название банка"
          value={bank}
          onChange={setBank}
        />
        <Field
          label="ФИО"
          hint="необязательно"
          icon={<PersonIcon />}
          placeholder="ФИО получателя"
          value={fullName}
          onChange={setFullName}
        />
        <Field
          label="Номер карты"
          hint="необязательно"
          icon={<CardIcon />}
          placeholder="0000 0000 0000 0000"
          value={card}
          onChange={setCard}
        />

        <div className="toggle-row">
          <div>
            <strong>PDF-чек выплаты</strong>
            <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
              Оператор пришлёт чек перевода файлом
            </div>
          </div>
          <button
            type="button"
            className={`toggle ${wantPdf ? "on" : ""}`}
            aria-label="PDF чек"
            onClick={() => {
              haptic("select");
              setWantPdf((v) => !v);
            }}
          >
            <i />
          </button>
        </div>

        <div style={{ marginTop: 8 }}>
          <div className="k" style={{ color: "var(--muted)", fontSize: 12 }}>
            Курс обмена
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, marginTop: 4 }}>
            1 {asset} = {money(rate)} ₽
          </div>
        </div>
      </div>

      <button
        type="button"
        className="glass tile"
        style={{ marginTop: 10 }}
        onClick={() => {
          setTermsOpen((v) => !v);
        }}
      >
        <div className="tile-body">
          <strong>Условия обмена</strong>
        </div>
        <span>{termsOpen ? "▴" : "▾"}</span>
      </button>
      {termsOpen ? (
        <div className="glass card-pad" style={{ marginTop: 8, fontSize: 13, color: "var(--muted)" }}>
          {cfg.terms}
        </div>
      ) : null}

      <button
        type="button"
        className="check-row"
        onClick={() => {
          haptic("select");
          setAccept((v) => !v);
        }}
      >
        <span className={`check ${accept ? "on" : ""}`}>{accept ? "✓" : ""}</span>
        Принимаю условия обмена
      </button>

      {error ? <div className="error-banner">{error}</div> : null}

      <button type="button" className="btn-primary" style={{ width: "100%" }} onClick={submit} disabled={busy}>
        {amountNum < min ? "Укажите сумму обмена" : busy ? "Создаём…" : "Создать заявку"}
      </button>
      <div className="hint">
        Следующую заявку можно создать через {Math.round(cfg.order_cooldown_sec / 60)} минут.
      </div>

      {pickerOpen ? (
        <button
          type="button"
          className="asset-menu-backdrop"
          aria-label="Закрыть"
          onClick={() => setPickerOpen(false)}
        />
      ) : null}
    </div>
  );
}

function Field({
  label,
  hint,
  icon,
  placeholder,
  value,
  onChange,
}: {
  label: string;
  hint: string;
  icon: ReactNode;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="field">
      <label>
        <span>{label}</span>
        <em>{hint}</em>
      </label>
      <div className="field-box">
        <span className="ico">{icon}</span>
        <input
          placeholder={placeholder}
          value={value}
          onChange={(e) => onChange(e.target.value)}
        />
      </div>
    </div>
  );
}
