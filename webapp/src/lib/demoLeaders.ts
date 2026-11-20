import type { LeaderItem } from "./api";

/** Демо-топ, пока в боте мало реальных обменов. Сортировка по обороту ↓ */
export const DEMO_LEADERS: LeaderItem[] = [
  {
    place: 1,
    id: -1001,
    username: "artem_fx",
    first_name: "Артём",
    photo_url: "/avatars/u1.jpg",
    turnover: 12840,
    prize: 500,
  },
  {
    place: 2,
    id: -1002,
    username: "nika.trade",
    first_name: "Ника",
    photo_url: "/avatars/u2.jpg",
    turnover: 9760,
    prize: 300,
  },
  {
    place: 3,
    id: -1003,
    username: "maxim_k",
    first_name: "Максим",
    photo_url: "/avatars/u3.jpg",
    turnover: 8120,
    prize: 150,
  },
  {
    place: 4,
    id: -1004,
    username: "olya_swap",
    first_name: "Оля",
    photo_url: "/avatars/u4.jpg",
    turnover: 6540,
    prize: 0,
  },
  {
    place: 5,
    id: -1005,
    username: "denis88",
    first_name: "Денис",
    photo_url: "/avatars/u5.jpg",
    turnover: 5210,
    prize: 0,
  },
  {
    place: 6,
    id: -1006,
    username: "katya.m",
    first_name: "Катя",
    photo_url: "/avatars/u6.jpg",
    turnover: 4180,
    prize: 0,
  },
  {
    place: 7,
    id: -1007,
    username: "ivan_crypto",
    first_name: "Иван",
    photo_url: "/avatars/u7.jpg",
    turnover: 3490,
    prize: 0,
  },
  {
    place: 8,
    id: -1008,
    username: "sasha_r",
    first_name: "Саша",
    photo_url: "/avatars/u8.jpg",
    turnover: 2760,
    prize: 0,
  },
  {
    place: 9,
    id: -1009,
    username: "pavel.n",
    first_name: "Павел",
    photo_url: "/avatars/u9.jpg",
    turnover: 2140,
    prize: 0,
  },
  {
    place: 10,
    id: -1010,
    username: "marina_v",
    first_name: "Марина",
    photo_url: "/avatars/u10.jpg",
    turnover: 1680,
    prize: 0,
  },
  {
    place: 11,
    id: -1011,
    username: "kirill.ex",
    first_name: "Кирилл",
    photo_url: "/avatars/u11.jpg",
    turnover: 1290,
    prize: 0,
  },
  {
    place: 12,
    id: -1012,
    username: "lena_soft",
    first_name: "Лена",
    photo_url: "/avatars/u12.jpg",
    turnover: 980,
    prize: 0,
  },
  {
    place: 13,
    id: -1013,
    username: "roma_ton",
    first_name: "Рома",
    photo_url: "/avatars/u13.jpg",
    turnover: 720,
    prize: 0,
  },
  {
    place: 14,
    id: -1014,
    username: "anya.k",
    first_name: "Аня",
    photo_url: "/avatars/u14.jpg",
    turnover: 510,
    prize: 0,
  },
  {
    place: 15,
    id: -1015,
    username: "timur_b",
    first_name: "Тимур",
    photo_url: "/avatars/u15.jpg",
    turnover: 340,
    prize: 0,
  },
];

export function leadersForPeriod(period: "day" | "week" | "month"): LeaderItem[] {
  // Небольшие суммы «пока что»: день меньше, месяц чуть больше
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
