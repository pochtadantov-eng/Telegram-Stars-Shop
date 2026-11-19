export function tg(): TelegramWebApp | null {
  return window.Telegram?.WebApp ?? null;
}

export function initTelegram() {
  const app = tg();
  if (!app) return;
  app.ready();
  app.expand();
  try {
    app.setHeaderColor?.("#06102a");
    app.setBackgroundColor?.("#06102a");
  } catch {
    /* older clients */
  }
}

export function haptic(kind: "tap" | "select" = "tap") {
  const h = tg()?.HapticFeedback;
  if (!h) return;
  try {
    if (kind === "select") h.selectionChanged();
    else h.impactOccurred("soft");
  } catch {
    /* noop */
  }
}
