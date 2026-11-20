import { tg } from "./telegram";

export type AppConfig = {
  brand: string;
  brand_title: string;
  rates: { USDT: number; TON: number };
  min_usdt: number;
  min_ton: number;
  ref_bonus: number;
  delay_compensation: number;
  order_cooldown_sec: number;
  order_sla_sec: number;
  support_url: string;
  weekly_prizes: number[];
  methods: Record<string, string[]>;
  assets: string[];
  payout_label: string;
  totals: { done_orders: number; users: number };
  bot_username: string;
  terms: string;
};

export type Me = {
  id: number;
  username?: string;
  first_name?: string;
  photo_url?: string;
  deals: number;
  usdt: number;
  ton: number;
  turnover: number;
  bonus_balance: number;
  ref_count: number;
  ref_earned: number;
  week_turnover: number;
  week_place: number | null;
  ref_link: string;
  cooldown_left: number;
};

export type Order = {
  id: number;
  asset: string;
  method: string;
  amount: number;
  rate: number;
  payout: number;
  bonus_used: number;
  status: string;
  created_at: number;
  phone: string;
  bank: string;
};

export type LeaderItem = {
  place: number;
  id: number;
  username?: string;
  first_name?: string;
  photo_url?: string;
  turnover: number;
  prize: number;
};

function headers(): HeadersInit {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const initData = tg()?.initData;
  if (initData) {
    // Официальный способ — не ломает спецсимволы initData в HTTP-заголовках
    h.Authorization = `tma ${initData}`;
  } else if (import.meta.env.DEV) {
    h["X-Dev-User"] = "1001";
  }
  return h;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { ...init, headers: { ...headers(), ...init?.headers } });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  config: () => req<AppConfig>("/api/config"),
  me: () => req<Me>("/api/me"),
  rates: () => req<{ rates: AppConfig["rates"]; week_ends_in: number }>("/api/rates"),
  leaderboard: (period: "day" | "week" | "month" = "week") =>
    req<{
      items: LeaderItem[];
      me: { place: number | null; turnover: number };
      week_ends_in: number;
      period: string;
      prizes: number[];
    }>(`/api/leaderboard?period=${period}`),
  orders: () => req<{ orders: Order[] }>("/api/orders"),
  createOrder: (body: Record<string, unknown>) =>
    req<{ order: Order }>("/api/orders", { method: "POST", body: JSON.stringify(body) }),
};

export function money(v: number) {
  return v.toLocaleString("ru-RU", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function formatCountdown(sec: number) {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  return `${h}ч ${m}м`;
}

export function displayName(u: { username?: string; first_name?: string; id?: number }) {
  if (u.username) return `@${u.username}`;
  return u.first_name || (u.id ? String(u.id) : "user");
}

export const METHOD_LABELS: Record<string, string> = {
  cryptobot: "Crypto Bot чеком",
  trc20: "TRC20",
  ton: "TON",
  xrocket: "xRocket чеком",
};

export const STATUS_LABELS: Record<string, string> = {
  pending: "Ожидает оператора",
  accepted: "В работе",
  done: "Успешно",
  rejected: "Отклонено",
  cancelled: "Отменено",
};
