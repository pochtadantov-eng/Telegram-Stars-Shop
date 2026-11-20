import type { LeaderItem } from "./api";

export type DemoUser = {
  id: number;
  username: string;
  photo_url: string;
  /** как часто торгует: 0.05…0.55 (шанс сделки за тик) */
  activity: number;
  /** типичный размер одной сделки, ₽ */
  ticketMin: number;
  ticketMax: number;
};

/** Пул трейдеров с разным стилем: кто-то редко/крупно, кто-то часто/мелко. */
export const DEMO_POOL: DemoUser[] = [
  { id: -1001, username: "voidexx", photo_url: "/avatars/pin01.jpg", activity: 0.22, ticketMin: 4200, ticketMax: 9800 },
  { id: -1002, username: "nightswap", photo_url: "/avatars/pin02.jpg", activity: 0.28, ticketMin: 2800, ticketMax: 7400 },
  { id: -1003, username: "kryptex_ru", photo_url: "/avatars/pin03.jpg", activity: 0.18, ticketMin: 5100, ticketMax: 11200 },
  { id: -1004, username: "m1rror", photo_url: "/avatars/pin04.jpg", activity: 0.35, ticketMin: 900, ticketMax: 3200 },
  { id: -1005, username: "ownflow", photo_url: "/avatars/pin05.jpg", activity: 0.14, ticketMin: 6800, ticketMax: 15400 },
  { id: -1006, username: "softcash", photo_url: "/avatars/pin06.jpg", activity: 0.31, ticketMin: 1100, ticketMax: 4100 },
  { id: -1007, username: "dexlify", photo_url: "/avatars/pin07.jpg", activity: 0.24, ticketMin: 1600, ticketMax: 5200 },
  { id: -1008, username: "lunxiety", photo_url: "/avatars/pin08.jpg", activity: 0.12, ticketMin: 7400, ticketMax: 16800 },
  { id: -1009, username: "Trader42kg", photo_url: "/avatars/pin09.jpg", activity: 0.4, ticketMin: 600, ticketMax: 2400 },
  { id: -1010, username: "aruna_wave", photo_url: "/avatars/pin10.jpg", activity: 0.2, ticketMin: 2100, ticketMax: 5900 },
  { id: -1011, username: "qx.money", photo_url: "/avatars/pin11.jpg", activity: 0.16, ticketMin: 3200, ticketMax: 8700 },
  { id: -1012, username: "neiro_ton", photo_url: "/avatars/pin12.jpg", activity: 0.33, ticketMin: 700, ticketMax: 2800 },
  { id: -1013, username: "paleblue", photo_url: "/avatars/pin13.jpg", activity: 0.1, ticketMin: 4500, ticketMax: 12000 },
  { id: -1014, username: "cashkit", photo_url: "/avatars/pin14.jpg", activity: 0.26, ticketMin: 950, ticketMax: 3600 },
  { id: -1015, username: "r0cket_ex", photo_url: "/avatars/pin15.jpg", activity: 0.19, ticketMin: 1400, ticketMax: 4800 },
  { id: -1016, username: "flores.iss", photo_url: "/avatars/pin16.jpg", activity: 0.08, ticketMin: 8200, ticketMax: 18400 },
  { id: -1017, username: "monxiety", photo_url: "/avatars/pin17.jpg", activity: 0.37, ticketMin: 500, ticketMax: 2100 },
  { id: -1018, username: "scarface_op", photo_url: "/avatars/pin18.jpg", activity: 0.15, ticketMin: 2600, ticketMax: 7100 },
  { id: -1019, username: "rr_dagger", photo_url: "/avatars/pin19.jpg", activity: 0.29, ticketMin: 800, ticketMax: 3000 },
  { id: -1020, username: "colosseumx", photo_url: "/avatars/pin20.jpg", activity: 0.11, ticketMin: 3900, ticketMax: 9500 },
  { id: -1021, username: "pepe_prime", photo_url: "/avatars/pin21.jpg", activity: 0.42, ticketMin: 400, ticketMax: 1800 },
  { id: -1022, username: "bentley_gt", photo_url: "/avatars/pin22.jpg", activity: 0.07, ticketMin: 9000, ticketMax: 21000 },
];

type TraderState = {
  user: DemoUser;
  turnover: number;
  trades: number;
  /** тики без сделки — «молчит» */
  quiet: number;
};

type Market = {
  period: "day" | "week" | "month";
  traders: TraderState[];
  /** id последних, кто только что продал (для подсветки) */
  lastDealIds: number[];
};

const VISIBLE = 12;

function mulberry32(seed: number) {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

function periodScale(period: "day" | "week" | "month") {
  // стартовый оборот периода: день меньше, месяц больше
  return period === "day" ? 1 : period === "week" ? 2.6 : 6.2;
}

function prizeFor(place: number, period: "day" | "week" | "month") {
  const base = place === 1 ? 500 : place === 2 ? 300 : place === 3 ? 150 : 0;
  if (!base) return 0;
  return Math.round(base * (period === "day" ? 0.4 : period === "week" ? 1 : 1.4));
}

function randTicket(u: DemoUser, rnd: () => number) {
  const span = u.ticketMax - u.ticketMin;
  return Math.round(u.ticketMin + rnd() * span);
}

/** Стартовая история: у каждого разное число сделок и сумм. */
function seedMarket(period: "day" | "week" | "month"): Market {
  const dayKey = Math.floor(Date.now() / 86_400_000);
  const rnd = mulberry32(dayKey * 7919 + (period === "day" ? 11 : period === "week" ? 29 : 47));
  const scale = periodScale(period);

  const traders: TraderState[] = DEMO_POOL.map((user) => {
    // 0…N сделок уже «за период» — у всех по-разному
    const maxTrades =
      period === "day"
        ? 1 + Math.floor(rnd() * 5) // 1–5
        : period === "week"
          ? 3 + Math.floor(rnd() * 10)
          : 8 + Math.floor(rnd() * 22);

    // неактивные: часть людей почти не торговала
    const idle = rnd() < 0.18;
    const trades = idle ? Math.floor(rnd() * 2) : Math.max(1, Math.floor(maxTrades * (0.35 + rnd() * 0.65)));

    let turnover = 0;
    for (let i = 0; i < trades; i++) {
      turnover += Math.round(randTicket(user, rnd) * (0.85 + rnd() * 0.3));
    }
    turnover = Math.round(turnover * (0.55 + scale * 0.18));

    return {
      user,
      turnover,
      trades,
      quiet: Math.floor(rnd() * 8),
    };
  });

  return { period, traders, lastDealIds: [] };
}

let market: Market | null = null;

function ensure(period: "day" | "week" | "month"): Market {
  if (!market || market.period !== period) {
    market = seedMarket(period);
  }
  return market;
}

function toBoard(m: Market): LeaderItem[] {
  const sorted = [...m.traders].sort((a, b) => b.turnover - a.turnover);
  return sorted.slice(0, VISIBLE).map((t, i) => ({
    place: i + 1,
    id: t.user.id,
    username: t.user.username,
    photo_url: t.user.photo_url,
    turnover: t.turnover,
    prize: prizeFor(i + 1, m.period),
  }));
}

export type MarketTickResult = {
  board: LeaderItem[];
  /** кто получил сделку на этом тике */
  dealtIds: number[];
};

/**
 * Один шаг «рынка»:
 * — чаще всего 0 сделок (никто не двигается)
 * — иногда 1 сделка у случайного активного
 * — редко 2 сделки
 * Суммы только растут; места меняются только если кого-то обогнали.
 */
export function tickMarket(period: "day" | "week" | "month"): MarketTickResult {
  const m = ensure(period);
  m.lastDealIds = [];

  const rnd = mulberry32((Date.now() ^ (m.traders[0]?.turnover ?? 1)) >>> 0);

  // сколько сделок на тик: 55% — 0, 35% — 1, 10% — 2
  const roll = rnd();
  const dealCount = roll < 0.55 ? 0 : roll < 0.9 ? 1 : 2;

  const candidates = m.traders
    .map((t, i) => {
      // чем дольше молчит — тем выше шанс «проснуться», но activity режет
      const hunger = Math.min(1, t.quiet / 12);
      const weight = t.user.activity * (0.45 + hunger);
      return { i, weight };
    })
    .filter((c) => c.weight > 0.02);

  const picked = new Set<number>();
  for (let d = 0; d < dealCount && candidates.length; d++) {
    const total = candidates.reduce((s, c) => s + (picked.has(c.i) ? 0 : c.weight), 0);
    if (total <= 0) break;
    let x = rnd() * total;
    let chosen = -1;
    for (const c of candidates) {
      if (picked.has(c.i)) continue;
      x -= c.weight;
      if (x <= 0) {
        chosen = c.i;
        break;
      }
    }
    if (chosen < 0) continue;
    picked.add(chosen);

    const t = m.traders[chosen];
    const amount = randTicket(t.user, rnd);
    t.turnover += amount;
    t.trades += 1;
    t.quiet = 0;
    m.lastDealIds.push(t.user.id);
  }

  // все без сделки — quiet++
  for (let i = 0; i < m.traders.length; i++) {
    if (!picked.has(i)) m.traders[i].quiet += 1;
  }

  return { board: toBoard(m), dealtIds: m.lastDealIds };
}

export function leadersForPeriod(period: "day" | "week" | "month"): LeaderItem[] {
  return toBoard(ensure(period));
}

export function resetMarket(period: "day" | "week" | "month"): LeaderItem[] {
  market = seedMarket(period);
  return toBoard(market);
}

/** Следующая пауза до тика, мс — неровный ритм, не метроном. */
export function nextTickDelay(): number {
  // 18–42 сек
  return 18_000 + Math.floor(Math.random() * 24_000);
}
