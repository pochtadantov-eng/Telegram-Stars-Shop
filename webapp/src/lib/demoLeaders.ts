import type { LeaderItem } from "./api";

/**
 * Демо-топ: ники в стиле Telegram, аватарки — смесь
 * TG-букв (как дефолт в Telegram) + нормальные фото-профили.
 * Сортировка по обороту ↓, суммы пока небольшие.
 */
export const DEMO_LEADERS: LeaderItem[] = [
  {
    place: 1,
    id: -1001,
    username: "voidexx",
    photo_url: "/avatars/a1.jpg",
    turnover: 12840,
    prize: 500,
  },
  {
    place: 2,
    id: -1002,
    username: "nightswap",
    photo_url: "/avatars/tg1.svg",
    turnover: 9760,
    prize: 300,
  },
  {
    place: 3,
    id: -1003,
    username: "kryptex_ru",
    photo_url: "/avatars/a3.jpg",
    turnover: 8120,
    prize: 150,
  },
  {
    place: 4,
    id: -1004,
    username: "m1rror",
    photo_url: "/avatars/tg2.svg",
    turnover: 6540,
    prize: 0,
  },
  {
    place: 5,
    id: -1005,
    username: "ownflow",
    photo_url: "/avatars/a4.jpg",
    turnover: 5210,
    prize: 0,
  },
  {
    place: 6,
    id: -1006,
    username: "softcash",
    photo_url: "/avatars/a5.jpg",
    turnover: 4180,
    prize: 0,
  },
  {
    place: 7,
    id: -1007,
    username: "dexlify",
    photo_url: "/avatars/tg3.svg",
    turnover: 3490,
    prize: 0,
  },
  {
    place: 8,
    id: -1008,
    username: "lunxiety",
    photo_url: "/avatars/a7.jpg",
    turnover: 2760,
    prize: 0,
  },
  {
    place: 9,
    id: -1009,
    username: "Trader42kg",
    photo_url: "/avatars/tg4.svg",
    turnover: 2140,
    prize: 0,
  },
  {
    place: 10,
    id: -1010,
    username: "aruna_wave",
    photo_url: "/avatars/a9.jpg",
    turnover: 1680,
    prize: 0,
  },
  {
    place: 11,
    id: -1011,
    username: "qx.money",
    photo_url: "/avatars/tg5.svg",
    turnover: 1290,
    prize: 0,
  },
  {
    place: 12,
    id: -1012,
    username: "neiro_ton",
    photo_url: "/avatars/a10.jpg",
    turnover: 980,
    prize: 0,
  },
  {
    place: 13,
    id: -1013,
    username: "paleblue",
    photo_url: "/avatars/tg6.svg",
    turnover: 720,
    prize: 0,
  },
  {
    place: 14,
    id: -1014,
    username: "cashkit",
    photo_url: "/avatars/a11.jpg",
    turnover: 510,
    prize: 0,
  },
  {
    place: 15,
    id: -1015,
    username: "r0cket_ex",
    photo_url: "/avatars/tg7.svg",
    turnover: 340,
    prize: 0,
  },
];

export function leadersForPeriod(period: "day" | "week" | "month"): LeaderItem[] {
  const factor = period === "day" ? 0.35 : period === "week" ? 1 : 1.85;
  return DEMO_LEADERS.map((row, i) => ({
    ...row,
    place: i + 1,
    turnover: Math.round(row.turnover * factor),
    prize:
      row.prize > 0
        ? Math.round(row.prize * (period === "day" ? 0.4 : period === "week" ? 1 : 1.4))
        : 0,
  }));
}
