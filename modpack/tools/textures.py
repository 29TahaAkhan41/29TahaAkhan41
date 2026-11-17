"""Özel eşyaların 16x16 dokularını üretir: python3 modpack/tools/textures.py"""
import math
import os
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "overrides", "kubejs", "assets", "kubejs", "textures", "item")


def shade(c, f):
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (255,)


def orb(name, base, glow):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 7.5)
            if d <= 6.2:
                light = 1.25 - (math.hypot(x - 5.5, y - 5.5) / 9)
                im.putpixel((x, y), shade(base, light))
            elif d <= 7.2:
                im.putpixel((x, y), shade(base, 0.45))
    for p in [(5, 5), (6, 5), (5, 6)]:
        im.putpixel(p, glow + (255,))
    return im


def star(name, base, glow, size=7.0):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            dx, dy = x - 7.5, y - 7.5
            ang = math.atan2(dy, dx)
            r = math.hypot(dx, dy)
            lim = size * (0.45 + 0.55 * abs(math.cos(2.5 * ang)) ** 3)
            if r <= lim:
                im.putpixel((x, y), shade(base, 1.3 - r / (size * 1.4)))
    for p in [(7, 7), (8, 7), (7, 8), (8, 8)]:
        im.putpixel(p, glow + (255,))
    return im


def heart(name, base, glow):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            u, v = (x - 7.5) / 6.5, -(y - 7.0) / 6.5
            if (u * u + v * v - 1) ** 3 - u * u * v ** 3 <= 0:
                im.putpixel((x, y), shade(base, 1.2 - (y / 22)))
    for p in [(4, 4), (4, 5)]:
        im.putpixel(p, (255, 220, 235, 255))
    for p in [(7, 5), (8, 5), (7, 6), (8, 6), (5, 7), (6, 7), (9, 7), (10, 7), (7, 8), (8, 8), (7, 9), (8, 9)]:
        im.putpixel(p, glow + (255,))
    for p in [(7, 7), (8, 7)]:
        im.putpixel(p, (255, 255, 255, 255))
    return im


def ring(name, base, gem):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 8.5)
            if 4.0 <= d <= 6.0:
                im.putpixel((x, y), shade(base, 1.2 - (y / 30)))
    for x in range(6, 10):
        for y in range(1, 4):
            im.putpixel((x, y), gem + (255,))
    im.putpixel((6, 1), (255, 255, 255, 255))
    return im


def medal(name, base, ribbon):
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y in range(0, 7):
        for x in range(4, 12):
            if abs(x - 7.5) >= (y * 0.4):
                im.putpixel((x, y), ribbon + (255,) if (x + y) % 3 else shade(ribbon, 0.7))
    for y in range(16):
        for x in range(16):
            d = math.hypot(x - 7.5, y - 10.5)
            if d <= 4.6:
                im.putpixel((x, y), shade(base, 1.25 - d / 9))
            elif d <= 5.4:
                im.putpixel((x, y), shade(base, 0.55))
    for p in [(7, 9), (8, 9), (7, 10), (8, 10), (7, 11), (8, 11), (6, 10), (9, 10), (7, 8), (8, 12)]:
        im.putpixel(p, (255, 255, 230, 255))
    return im


ITEMS = {
    "stellar_essence": orb("stellar_essence", (70, 110, 230), (220, 235, 255)),
    "cosmic_core": orb("cosmic_core", (120, 50, 170), (255, 200, 255)),
    "creative_catalyst": star("creative_catalyst", (220, 60, 220), (255, 255, 255)),
    "flight_ring": ring("flight_ring", (230, 190, 60), (110, 230, 255)),
    "heart_of_the_stars": heart("heart_of_the_stars", (200, 40, 120), (255, 230, 120)),
    "completion_medal": medal("completion_medal", (240, 190, 40), (90, 60, 200)),
}

os.makedirs(OUT, exist_ok=True)
for name, img in ITEMS.items():
    img.save(os.path.join(OUT, name + ".png"))
print("dokular yazıldı:", ", ".join(ITEMS))
