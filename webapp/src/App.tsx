import { useCallback, useEffect, useState } from "react";
import {
  api,
  type AppConfig,
  type LeaderItem,
  type Me,
  type Order,
} from "./lib/api";
import { initTelegram, tg, waitForInitData } from "./lib/telegram";
import { Home } from "./pages/Home";
import { Profile } from "./pages/Profile";
import { Top, type Period } from "./pages/Top";
import { Orders } from "./pages/Orders";
import { CreateExchange } from "./pages/CreateExchange";

type Page = "home" | "profile" | "top" | "orders" | "create" | "info";

export default function App() {
  const [page, setPage] = useState<Page>("home");
  const [cfg, setCfg] = useState<AppConfig | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [leaders, setLeaders] = useState<LeaderItem[]>([]);
  const [weekEndsIn, setWeekEndsIn] = useState(0);
  const [myPlace, setMyPlace] = useState<number | null>(null);
  const [myWeekTurnover, setMyWeekTurnover] = useState(0);
  const [period, setPeriod] = useState<Period>("week");
  const [infoText, setInfoText] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const [c, m, r] = await Promise.all([api.config(), api.me(), api.rates()]);
    setCfg(c);
    setMe(m);
    setWeekEndsIn(r.week_ends_in);
  }, []);

  const loadTop = useCallback(async (p: Period) => {
    const res = await api.leaderboard(p);
    setLeaders(res.items);
    setMyPlace(res.me.place);
    setMyWeekTurnover(res.me.turnover);
    setWeekEndsIn(res.week_ends_in);
    setPeriod(p);
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      initTelegram();
      const initData = await waitForInitData();
      if (!initData && !import.meta.env.DEV) {
        if (!cancelled) {
          setError(
            "Нет данных Telegram. Откройте Mini App кнопкой из бота @CryptoTradesi_bot",
          );
          setLoading(false);
        }
        return;
      }
      try {
        await refresh();
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Ошибка загрузки");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refresh]);

  useEffect(() => {
    const id = setInterval(() => {
      setWeekEndsIn((s) => Math.max(0, s - 1));
      setMe((m) =>
        m && m.cooldown_left > 0 ? { ...m, cooldown_left: m.cooldown_left - 1 } : m,
      );
    }, 1000);
    return () => clearInterval(id);
  }, []);

  async function go(next: Page) {
    setError("");
    if (next === "orders" && me) {
      const res = await api.orders();
      setOrders(res.orders);
    }
    if (next === "top") {
      await loadTop(period);
    }
    if (next === "profile" || next === "create") {
      await refresh();
    }
    if (next === "info") {
      setInfoText(cfg?.support_url ? `Поддержка: ${cfg.support_url}` : "Поддержка");
    }
    setPage(next);
  }

  async function createOrder(payload: Record<string, unknown>) {
    await api.createOrder(payload);
    await refresh();
    const res = await api.orders();
    setOrders(res.orders);
    setPage("orders");
  }

  function openInfo(kind: string) {
    if (kind === "profile") {
      void go("profile");
      return;
    }
    if (kind === "orders") {
      void go("orders");
      return;
    }
    if (!cfg) return;
    if (kind === "support" && cfg.support_url) {
      window.open(cfg.support_url, "_blank");
      return;
    }
    const map: Record<string, string> = {
      info: `Обмен ${cfg.brand}: продайте USDT (TRC20/TON) или TON и получите рубли на СБП/карту.`,
      security: "Мы не храним seed-фразы. Перевод крипты — только по инструкции оператора.",
      support: `Поддержка: ${cfg.support_url}`,
      history: "История доступна в разделе «Мои заявки».",
      faq: `Минимум: ${cfg.min_usdt} USDT / ${cfg.min_ton} TON. Кулдаун между заявками — ${Math.round(cfg.order_cooldown_sec / 60)} мин.`,
    };
    setInfoText(map[kind] || "");
    setPage("info");
  }

  if (loading || !cfg || !me) {
    return (
      <div className="app-shell" data-brand={cfg?.brand || "SwiftEx"}>
        <div className="loading">{error || "Загрузка…"}</div>
      </div>
    );
  }

  return (
    <div className="app-shell" data-brand={cfg.brand}>
      {error && page === "home" ? <div className="error-banner">{error}</div> : null}

      {page === "home" && (
        <Home
          cfg={cfg}
          me={me}
          weekEndsIn={weekEndsIn}
          onNavigate={(p) => void go(p as Page)}
        />
      )}
      {page === "profile" && (
        <Profile cfg={cfg} me={me} onBack={() => setPage("home")} />
      )}
      {page === "top" && (
        <Top
          cfg={cfg}
          me={me}
          items={leaders}
          myPlace={myPlace}
          myTurnover={myWeekTurnover}
          weekEndsIn={weekEndsIn}
          period={period}
          onPeriod={(p) => void loadTop(p)}
          onBack={() => setPage("home")}
          onOpenInfo={openInfo}
        />
      )}
      {page === "orders" && (
        <Orders cfg={cfg} orders={orders} onBack={() => setPage("home")} />
      )}
      {page === "create" && (
        <CreateExchange
          cfg={cfg}
          me={me}
          onBack={() => setPage("home")}
          onSubmit={createOrder}
        />
      )}
      {page === "info" && (
        <div className="page">
          <header className="brand-head">
            <h1>{cfg.brand_title}</h1>
            <p>мини-приложение</p>
          </header>
          <div className="glass card-pad" style={{ lineHeight: 1.5 }}>
            {infoText}
          </div>
          <button
            type="button"
            className="btn-primary"
            style={{ width: "100%", marginTop: 14 }}
            onClick={() => setPage("home")}
          >
            Назад
          </button>
          {tg()?.initData ? null : (
            <div className="hint">Dev-режим: откройте через Telegram для полной авторизации</div>
          )}
        </div>
      )}
    </div>
  );
}
