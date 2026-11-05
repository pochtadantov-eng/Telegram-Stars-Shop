"""Генерация баннеров в тёмно-фиолетовом стиле (как «UNDO PROMPTS» на видео)."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 640
ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# имя -> (метка, глиф: star|ton|user|gift|chat)
SCREENS = {
    "home": ("01 / HOME", "star"),
    "stars": ("02 / STARS", "star"),
    "ton": ("03 / TON", "ton"),
    "profile": ("04 / PROFILE", "user"),
    "invite": ("05 / INVITE", "gift"),
    "support": ("06 / SUPPORT", "chat"),
    "order": ("07 / ORDER", "star"),
}


def _star(cx, cy, r, rot=-math.pi / 2, inner=0.45):
    pts = []
    for i in range(10):
        a = rot + i * math.pi / 5
        rr = r if i % 2 == 0 else r * inner
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def _glyph(d: ImageDraw.ImageDraw, kind: str, cx: int, cy: int, r: int, col):
    if kind == "star":
        d.polygon(_star(cx, cy, r), fill=col)
    elif kind == "ton":  # ромб-«алмаз» TON
        d.polygon([(cx - r, cy - r * .6), (cx + r, cy - r * .6), (cx, cy + r)], fill=col)
        d.polygon([(cx, cy - r * .35), (cx + r * .55, cy - r * .35), (cx, cy + r * .55)], fill=(18, 10, 34))
        d.polygon([(cx, cy - r * .35), (cx - r * .55, cy - r * .35), (cx, cy + r * .55)], fill=(18, 10, 34))
    elif kind == "user":
        d.ellipse([cx - r * .4, cy - r * .9, cx + r * .4, cy - r * .1], fill=col)
        d.pieslice([cx - r * .8, cy + r * .0, cx + r * .8, cy + r * 1.6], 180, 360, fill=col)
    elif kind == "gift":
        d.rectangle([cx - r * .8, cy - r * .2, cx + r * .8, cy + r * .9], fill=col)
        d.rectangle([cx - r * .9, cy - r * .55, cx + r * .9, cy - r * .2], fill=col)
        d.rectangle([cx - r * .1, cy - r * .55, cx + r * .1, cy + r * .9], fill=(18, 10, 34))
        d.ellipse([cx - r * .6, cy - r * 1.0, cx, cy - r * .55], outline=col, width=12)
        d.ellipse([cx, cy - r * 1.0, cx + r * .6, cy - r * .55], outline=col, width=12)
    elif kind == "chat":
        d.rounded_rectangle([cx - r, cy - r * .7, cx + r, cy + r * .5], r * .3, fill=col)
        d.polygon([(cx - r * .5, cy + r * .4), (cx - r * .5, cy + r * .95), (cx), (cy + r * .4)], fill=col)


def make(name: str, brand: str, path: str):
    label, glyph = SCREENS[name]
    rnd = random.Random(name)
    img = Image.new("RGB", (W, H), (14, 9, 26))
    px = ImageDraw.Draw(img)
    for y in range(H):  # вертикальный градиент
        t = y / H
        px.line([(0, y), (W, y)], fill=(int(16 + 22 * t), int(9 + 4 * t), int(30 + 26 * t)))

    # мягкое свечение справа
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([760, 40, 1260, 600], fill=(120, 60, 220))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.blend(img, Image.composite(glow, img, glow.convert("L")), 0.55)

    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(70):  # звёздная пыль
        x, y, s = rnd.randint(0, W), rnd.randint(0, H), rnd.choice([2, 2, 3, 5])
        d.polygon(_star(x, y, s * 2), fill=(255, 255, 255, rnd.randint(40, 150)))
    for x in range(0, W, 64):  # тонкая сетка
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 6))
    for y in range(0, H, 64):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 6))

    # крупный глиф справа
    gcol = (255, 200, 60) if glyph == "star" else (80, 170, 255) if glyph == "ton" else (190, 140, 255)
    for i, a in ((260, 40), (215, 70)):
        d.ellipse([990 - i, 320 - i, 990 + i, 320 + i], outline=(*gcol, a), width=2)
    _glyph(d, glyph, 990, 320, 180, gcol)

    # вертикальный водяной знак как «UNDO PROMPTS» сбоку
    wm = Image.new("RGBA", (H, 90), (0, 0, 0, 0))
    ImageDraw.Draw(wm).text((0, 0), brand.upper(), font=ImageFont.truetype(FONT, 64), fill=(255, 255, 255, 22))
    img.paste(wm.rotate(-90, expand=True), (W - 90, 0), wm.rotate(-90, expand=True))

    # заголовок
    words = brand.upper().split()
    big = ImageFont.truetype(FONT, 150 if len(words[0]) <= 6 else 118)
    d.text((70, 150), words[0], font=big, fill=(255, 255, 255, 255))
    if len(words) > 1:
        d.text((76, 318), " ".join(words[1:]), font=ImageFont.truetype(FONT, 54), fill=(180, 110, 255, 255))
    d.text((76, 400), label, font=ImageFont.truetype(MONO, 30), fill=(255, 255, 255, 120))
    d.rounded_rectangle([70, 470, 330, 476], 3, fill=(180, 110, 255, 255))

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.convert("RGB").save(path, "JPEG", quality=88)


def path(name: str) -> str:
    """Свой GIF/MP4-баннер (assets/<имя>.gif|mp4) приоритетнее сгенерированной картинки."""
    for ext in ("gif", "mp4", "jpg"):
        p = os.path.join(ASSETS, f"{name}.{ext}")
        if os.path.exists(p):
            return p
    return os.path.join(ASSETS, f"{name}.jpg")


def is_animation(name: str) -> bool:
    return path(name).endswith((".gif", ".mp4"))


def ensure(brand: str, force: bool = False):
    for n in SCREENS:
        if force or not os.path.exists(path(n)):
            make(n, brand, os.path.join(ASSETS, f"{n}.jpg"))


if __name__ == "__main__":
    ensure(os.getenv("BRAND", "STARS SHOP"), force=True)
