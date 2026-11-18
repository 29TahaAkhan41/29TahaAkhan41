"""CurseForge logosu (400x400) üretir: python3 modpack/tools/logo.py

Ortada Yıldızların Kalbi; çevresindeki halkada paketin sekiz yüzü:
teknoloji, büyü, macera, doğa, görevler, depolama, boyutlar, simya.
Simgeler bu betikte sıfırdan çizilen 16x16 piksel sanatlarıdır.
"""
import math
import os
import random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "yayin", "logo.png")
HEART = os.path.join(ROOT, "overrides/kubejs/assets/kubejs/textures/item/heart_of_the_stars.png")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT2 = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def canvas():
    return Image.new("RGBA", (16, 16), (0, 0, 0, 0))


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


def outline(im, col=(25, 20, 35, 255)):
    """Piksel sanatına koyu dış çizgi ekler."""
    out = im.copy()
    px = im.load()
    for y in range(16):
        for x in range(16):
            if px[x, y][3] == 0 and any(
                    0 <= x + dx < 16 and 0 <= y + dy < 16 and px[x + dx, y + dy][3]
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), col)
    return out


def gear():
    im = canvas()
    base = (165, 170, 185)
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            tooth = 6.6 if math.cos(8 * a) > 0.2 else 5.0
            if 2.0 < r <= tooth:
                im.putpixel((x, y), shade(base, 1.25 - r / 9 + (0.15 if dx + dy < 0 else 0)))
    return outline(im)


def crystal():
    im = canvas()
    for y in range(1, 15):
        w = (y - 1) * 0.75 if y < 6 else (14 - y) * 0.55
        for x in range(16):
            if abs(x - 7.5) <= w:
                left = x < 7.5
                c = (190, 110, 255) if left else (130, 60, 210)
                if abs(x - 7.5) < 1 and y < 8:
                    c = (240, 210, 255)
                im.putpixel((x, y), c + (255,))
    return outline(im)


def sword():
    im = canvas()
    for i in range(3, 13):  # bıçak (çapraz)
        for d in (0, 1):
            x, y = i + d, 15 - i
            if 0 <= x < 16 and 0 <= y < 16:
                im.putpixel((x, y - 1), (215, 235, 245, 255) if d == 0 else (140, 170, 190, 255))
    for x, y in ((2, 10), (3, 11), (4, 12), (5, 13), (6, 12), (1, 9)):  # koruma
        im.putpixel((x, y), (200, 160, 60, 255))
    for x, y in ((2, 13), (1, 14), (3, 12)):  # kabza
        im.putpixel((x, y), (110, 70, 40, 255))
    im.putpixel((0, 15), (230, 190, 70, 255))
    return outline(im)


def sapling():
    im = canvas()
    green, dark = (90, 200, 90), (40, 130, 60)
    for y in range(9, 15):
        im.putpixel((7, y), (120, 80, 45, 255))
        im.putpixel((8, y), (95, 60, 35, 255))
    for cx, cy, r in ((5, 6, 3.2), (10.5, 5, 3.4), (7.5, 2.8, 2.6)):
        for y in range(16):
            for x in range(16):
                if math.hypot(x - cx, y - cy) <= r:
                    im.putpixel((x, y), (green if (x + y) % 3 else dark) + (255,))
    return outline(im)


def book():
    im = canvas()
    for y in range(2, 14):
        for x in range(2, 14):
            c = (175, 60, 50) if x < 12 else (235, 225, 200)
            if x == 2 or y in (2, 13):
                c = (120, 35, 30)
            im.putpixel((x, y), c + (255,))
    for y in range(4, 12):
        im.putpixel((12, y), (250, 245, 230, 255))
        im.putpixel((13, y), (210, 200, 180, 255))
    for x, y in ((6, 6), (7, 5), (8, 6), (7, 7), (6, 8), (8, 8)):  # yıldız amblemi
        im.putpixel((x, y), (255, 215, 90, 255))
    return outline(im)


def chest():
    im = canvas()
    for y in range(3, 14):
        for x in range(1, 15):
            c = (160, 105, 50) if (y + x // 4) % 5 else (125, 80, 40)
            if y == 7:
                c = (95, 60, 30)
            im.putpixel((x, y), c + (255,))
    for x, y in ((7, 6), (8, 6), (7, 7), (8, 7), (7, 8), (8, 8)):
        im.putpixel((x, y), (215, 215, 225, 255))
    return outline(im)


def portal():
    im = canvas()
    for y in range(1, 15):
        for x in range(3, 13):
            if x in (3, 12) or y in (1, 14):
                im.putpixel((x, y), (35, 25, 55, 255))
            else:
                t = math.sin(x * 1.3 + y * 0.8)
                im.putpixel((x, y), (int(150 + 60 * t), 60, int(220 + 30 * t), 255))
    for x, y in ((6, 5), (9, 9), (7, 11)):
        im.putpixel((x, y), (255, 220, 255, 255))
    return outline(im)


def potion():
    im = canvas()
    for y in range(1, 4):
        for x in range(7, 9):
            im.putpixel((x, y), (150, 100, 60, 255))
    for y in range(4, 7):
        for x in range(6, 10):
            im.putpixel((x, y), (200, 225, 240, 255))
    for y in range(7, 15):
        for x in range(16):
            if math.hypot(x - 7.5, y - 10.5) <= 4.6:
                c = (80, 220, 150) if y > 8 else (200, 225, 240)
                if x < 6 and y < 11:
                    c = (200, 255, 220)
                im.putpixel((x, y), c + (255,))
    return outline(im)


def star_points(cx, cy, r_out, r_in, n=4, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = r_out if i % 2 == 0 else r_in
        a = rot + i * math.pi / n
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def main():
    S = 4  # süper örnekleme
    W = 400 * S
    random.seed(11)
    img = Image.new("RGBA", (W, W))
    d = ImageDraw.Draw(img)
    for y in range(W):  # gece gökyüzü
        t = y / W
        d.line([(0, y), (W, y)], fill=(int(10 + 28 * t), int(8 + 14 * t), int(34 + 48 * t), 255))
    for _ in range(220):
        x, y = random.randrange(W), random.randrange(W)
        b = random.randint(110, 255)
        r = random.choice([1, 1, 2, 3]) * S / 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=(b, b, 255, 255))

    cx, cy, ring = W // 2, int(W * 0.38), int(W * 0.27)

    glow = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse([cx - ring * 1.15, cy - ring * 1.15, cx + ring * 1.15, cy + ring * 1.15], fill=(120, 70, 210, 90))
    g.ellipse([cx - ring * 0.55, cy - ring * 0.55, cx + ring * 0.55, cy + ring * 0.55], fill=(255, 120, 200, 110))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(40 * S)))
    d = ImageDraw.Draw(img)

    # Halka ve sekiz kollu yıldız çizgileri
    gold = (240, 200, 90, 255)
    d.ellipse([cx - ring, cy - ring, cx + ring, cy + ring], outline=gold, width=3 * S)
    d.ellipse([cx - ring + 10 * S, cy - ring + 10 * S, cx + ring - 10 * S, cy + ring - 10 * S],
              outline=(240, 200, 90, 120), width=1 * S)
    pts = [(cx + ring * math.cos(-math.pi / 2 + i * math.pi / 4), cy + ring * math.sin(-math.pi / 2 + i * math.pi / 4))
           for i in range(8)]
    for i in range(8):  # yıldız poligonu (8/3)
        d.line([pts[i], pts[(i + 3) % 8]], fill=(170, 190, 255, 110), width=2 * S)

    # Ortada Yıldızların Kalbi
    heart = Image.open(HEART).resize((112 * S, 112 * S), Image.NEAREST)
    img.alpha_composite(heart, (cx - 56 * S, cy - 54 * S))

    # Sekiz simge (madalyon içinde)
    icons = [gear(), crystal(), sword(), sapling(), book(), chest(), portal(), potion()]
    order = [0, 4, 1, 5, 2, 6, 3, 7]  # dört ana yüz eksenlerde, diğerleri çaprazlarda
    for slot, idx in enumerate(order):
        px, py = pts[slot]
        main_axis = slot % 2 == 0
        rad = (33 if main_axis else 27) * S
        d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=(28, 20, 48, 255), outline=gold, width=3 * S)
        size = (46 if main_axis else 36) * S
        ic = icons[idx].resize((size, size), Image.NEAREST)
        img.alpha_composite(ic, (int(px - size / 2), int(py - size / 2)))

    # Köşelerde küçük parıltılar
    for sx, sy, r in ((0.12, 0.10, 12), (0.88, 0.12, 9), (0.10, 0.66, 8), (0.90, 0.62, 11)):
        d.polygon(star_points(W * sx, W * sy, r * S, r * S * 0.28), fill=(255, 240, 200, 255))

    # Başlık
    f = ImageFont.truetype(FONT, 58 * S)
    title = "Star Path"
    bw = d.textbbox((0, 0), title, font=f)[2]
    tx, ty = (W - bw) // 2, int(W * 0.735)
    d.text((tx + 4 * S, ty + 4 * S), title, font=f, fill=(0, 0, 0, 200))
    d.text((tx, ty), title, font=f, fill=(255, 214, 90, 255), stroke_width=2 * S, stroke_fill=(110, 60, 20, 255))
    f2 = ImageFont.truetype(FONT2, 14 * S)
    sub = "TECH  ·  MAGIC  ·  ADVENTURE  ·  1.21.1"
    sw = d.textbbox((0, 0), sub, font=f2)[2]
    d.text(((W - sw) // 2, int(W * 0.895)), sub, font=f2, fill=(205, 215, 255, 255))

    img.resize((400, 400), Image.LANCZOS).convert("RGB").save(OUT)
    print("logo:", OUT)


if __name__ == "__main__":
    main()
