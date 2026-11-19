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

/** Ждём, пока Telegram отдаст initData (на iOS бывает с задержкой). */
export async function waitForInitData(timeoutMs = 4000): Promise<string> {
  const started = Date.now();
  while (Date.now() - started < timeoutMs) {
    const data = tg()?.initData || "";
    if (data) return data;
    await new Promise((r) => setTimeout(r, 100));
  }
  return tg()?.initData || "";
}
