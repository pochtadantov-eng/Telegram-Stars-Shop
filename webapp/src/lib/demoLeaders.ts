import type { LeaderItem } from "./api";

export type DemoUser = {
  id: number;
  username: string;
  photo_url: string;
  /** базовый оборот (неделя), дальше масштабируется */
  base: number;
};

/** Пул участников: не все сразу в топе — кто-то выходит/заходит. */
export const DEMO_POOL: DemoUser[] = [
  { id: -1001, username: "voidexx", photo_url: "/avatars/pin01.jpg", base: 14820 },
  { id: -1002, username: "nightswap", photo_url: "/avatars/pin02.jpg", base: 12140 },
  { id: -1003, username: "kryptex_ru", photo_url: "/avatars/pin03.jpg", base: 10360 },
  { id: -1004, username: "m1rror", photo_url: "/avatars/pin04.jpg", base: 8940 },
  { id: -1005, username: "ownflow", photo_url: "/avatars/pin05.jpg", base: 7620 },
  { id: -1006, username: "softcash", photo_url: "/avatars/pin06.jpg", base: 6510 },
  { id: -1007, username: "dexlify", photo_url: "/avatars/pin07.jpg", base: 5480 },
  { id: -1008, username: "lunxiety", photo_url: "/avatars/pin08.jpg", base: 4720 },
  { id: -1009, username: "Trader42kg", photo_url: "/avatars/pin09.jpg", base: 3980 },
  { id: -1010, username: "aruna_wave", photo_url: "/avatars/pin10.jpg", base: 3360 },
  { id: -1011, username: "qx.money", photo_url: "/avatars/pin11.jpg", base: 2890 },
  { id: -1012, username: "neiro_ton", photo_url: "/avatars/pin12.jpg", base: 2410 },
  { id: -1013, username: "paleblue", photo_url: "/avatars/pin13.jpg", base: 1980 },
  { id: -1014, username: "cashkit", photo_url: "/avatars/pin14.jpg", base: 1640 },
  { id: -1015, username: "r0cket_ex", photo_url: "/avatars/pin15.jpg", base: 1320 },
  { id: -1016, username: "flores.iss", photo_url: "/avatars/pin16.jpg", base: 1090 },
  { id: -1017, username: "monxiety", photo_url: "/avatars/pin17.jpg", base: 860 },
  { id: -1018, username: "scarface_op", photo_url: "/avatars/pin18.jpg", base: 720 },
  { id: -1019, username: "rr_dagger", photo_url: "/avatars/pin19.jpg", base: 580 },
  { id: -1020, username: "colosseumx", photo_url: "/avatars/pin20.jpg", base: 450 },
  { id: -1021, username: "pepe_prime", photo_url: "/avatars/pin21.jpg", base: 380 },
  { id: -1022, username: "bentley_gt", photo_url: "/avatars/pin22.jpg", base: 310 },
];

const VISIBLE = 10;

function periodFactor(period: "day" | "week" | "month") {
  return period === "day" ? 0.32 : period === "week" ? 1 : 1.9;
}

function prizeFor(place: number, period: "day" | "week" | "month") {
  const base = place === 1 ? 500 : place === 2 ? 300 : place === 3 ? 150 : 0;
  if (!base) return 0;
  return Math.round(base * (period === "day" ? 0.4 : period === "week" ? 1 : 1.4));
}

function mulberry32(seed: number) {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

/** Снимок «живого» топа: часть пула на экране, суммы чуть гуляют. */
export function liveBoard(
  period: "day" | "week" | "month",
  tick: number,
): LeaderItem[] {
  const rnd = mulberry32(91011 + tick * 97 + (period === "day" ? 3 : period === "week" ? 7 : 13));
  const factor = periodFactor(period);

  // кто сейчас «в игре»: ротируем окно по пулу
  const start = tick % DEMO_POOL.length;
  const activeIds = new Set<number>();
  for (let i = 0; i < VISIBLE + 2; i++) {
    activeIds.add(DEMO_POOL[(start + i * 3) % DEMO_POOL.length].id);
  }
  // иногда выкидываем 1–2 случайных и добавляем других
  const poolCopy = [...DEMO_POOL];
  const active = poolCopy.filter((u) => activeIds.has(u.id));
  while (active.length > VISIBLE) {
    active.splice(Math.floor(rnd() * active.length), 1);
  }
  while (active.length < VISIBLE) {
    const cand = DEMO_POOL[Math.floor(rnd() * DEMO_POOL.length)];
    if (!active.find((a) => a.id === cand.id)) active.push(cand);
  }

  const rows = active.map((u) => {
    const jitter = 0.82 + rnd() * 0.36; // ±18%
    const bump = tick % 5 === 0 && rnd() > 0.7 ? 1.12 + rnd() * 0.2 : 1;
    return {
      place: 0,
      id: u.id,
      username: u.username,
      photo_url: u.photo_url,
      turnover: Math.max(120, Math.round(u.base * factor * jitter * bump)),
      prize: 0,
    } satisfies LeaderItem;
  });

  rows.sort((a, b) => b.turnover - a.turnover);
  return rows.map((r, i) => ({
    ...r,
    place: i + 1,
    prize: prizeFor(i + 1, period),
  }));
}

/** Статичный fallback (для SSR/первого кадра). */
export function leadersForPeriod(period: "day" | "week" | "month"): LeaderItem[] {
  return liveBoard(period, 0);
}
