let audio: HTMLAudioElement | null = null;
let unlocked = false;

function getAudio() {
  if (!audio) {
    audio = new Audio("/sounds/click.mp3");
    audio.preload = "auto";
    audio.volume = 0.55;
  }
  return audio;
}

/** Разблокировка звука после первого жеста (iOS/Telegram). */
export function unlockSound() {
  if (unlocked) return;
  try {
    const a = getAudio();
    a.currentTime = 0;
    const p = a.play();
    if (p && typeof p.then === "function") {
      p.then(() => {
        a.pause();
        a.currentTime = 0;
        unlocked = true;
      }).catch(() => {
        /* wait for next gesture */
      });
    } else {
      unlocked = true;
    }
  } catch {
    /* noop */
  }
}

/** Клик из присланного mp3 */
export function playClick(_pitch = 640) {
  try {
    unlockSound();
    const a = getAudio();
    a.pause();
    a.currentTime = 0;
    void a.play().catch(() => {
      /* autoplay */
    });
  } catch {
    /* noop */
  }
}

export function playSuccess() {
  playClick();
  setTimeout(() => playClick(), 90);
}
