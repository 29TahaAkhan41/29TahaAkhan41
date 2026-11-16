#!/usr/bin/env python3
"""Pixel Bloom: animated pixel-art cursor pack with an original chibi mascot.

Every cursor is a 32x32 pixel-art frame list, scaled with nearest-neighbour
to 32/64/96/128 px so pixels stay crisp. Reuses the encoders in build.py.

Usage: python3 pixel.py
"""
import os
import shutil
from PIL import Image, ImageDraw, ImageFont

import build

N = 32
SIZES = [32, 64, 96, 128]
NAME = "Pixel Bloom"
OUT = os.path.join(build.DIST, "pixel")

PAL = {
    ".": None,
    "K": (46, 30, 66),       # outline
    "H": (92, 62, 150),      # hair
    "h": (138, 108, 210),    # hair highlight
    "S": (255, 226, 200),    # skin
    "s": (240, 186, 168),    # skin shade
    "E": (70, 96, 214),      # eye
    "W": (255, 255, 255),
    "B": (255, 150, 176),    # blush
    "M": (196, 70, 96),      # mouth
    "D": (244, 120, 184),    # dress
    "d": (206, 82, 146),     # dress shade
    "F": (170, 150, 255),    # flower clip
    "f": (255, 236, 140),    # flower centre
    "Y": (255, 222, 80),     # sparkle
    "y": (255, 246, 190),
    "R": (238, 58, 96),      # red / heart
    "r": (255, 140, 170),
    "P": (124, 92, 220),     # purple accent
    "L": (90, 64, 110),      # shoes
    "G": (150, 150, 165),    # grey
    "T": (240, 200, 140),    # wood
    "O": (70, 70, 80),       # graphite
}

CHIBI = [
    "....KKKKKKKK....",
    "..KKHHHHHHHHKKFF",
    ".KHHHhhHHHHHHKFfF",
    ".KHHhhHHHHHHHHKF.",
    "KHHhHHHHHHHHHHHK",
    "KHHHHKHHHHKHHHHK",
    "KHHKSSSSSSSSKHHK",
    "KHKSSSSSSSSSSKHK",
    "KHKSEESSSSEESKHK",
    "KHKSEWSSSSEWSKHK",
    "KHKSBSSSMSSSBKHK",
    "KHHKSSSSSSSSKHHK",
    ".KHHKKKKKKKKHHK.",
    "..KK.KDWWDK.KK..",
    "....KSKDDKSK....",
    "....KSKDDKSK....",
    "...KDDDDDDDDK...",
    "..KDdDDDDDDdDK..",
    "...KKKKKKKKKK...",
    ".....KLK.KLK....",
    ".....KKK.KKK....",
]
BLINK = {8: "KHKSSSSSSSSSSKHK", 9: "KHKSKKSSSSKKSKHK"}
HAPPY = {8: "KHKSKSSSSSSKSKHK", 9: "KHKKSKSSSSKSKKHK"}

ARROW = [
    "K.........",
    "KK........",
    "KWK.......",
    "KWWK......",
    "KWWWK.....",
    "KWWWWK....",
    "KWWWWWK...",
    "KWWWWWWK..",
    "KWWWWWWWK.",
    "KWWWWKKKKK",
    "KWWKWWK...",
    "KWK.KWWK..",
    "KK...KWWK.",
    "......KK..",
]

HAND = [
    "....KK.......",
    "...KWWK......",
    "...KWWK......",
    "...KWWK......",
    "...KWWKKK....",
    "...KWWKWWKKK.",
    ".KKKWWKWWKWWK",
    "KWWKWWWWWWWWK",
    "KWWKWWWWWWWWK",
    ".KWWWWWWWWWWK",
    ".KWWWWWWWWWWK",
    "..KWWWWWWWWK.",
    "...KWWWWWWK..",
    "...KKKKKKKK..",
]

SPARK = [
    ["Y"],
    [".Y.", "YyY", ".Y."],
    ["..Y..", "..Y..", "YYyYY", "..Y..", "..Y.."],
]
HEART = [".KK.KK.", "KrRKRRK", "KRRRRRK", ".KRRRK.", "..KRK..", "...K..."]
QBUBBLE = [
    ".KKKKKKKK.",
    "KWWWWWWWWK",
    "KWWWPPWWWK",
    "KWWPWWPWWK",
    "KWWWWWPWWK",
    "KWWWWPWWWK",
    "KWWWWPWWWK",
    "KWWWWWWWWK",
    "KWWWWPWWWK",
    ".KKKKKKKK.",
    "...KK.....",
    "...K......",
]
DOTS = [
    ".KKKKKKKKKK.",
    "KWWWWWWWWWWK",
    "KWWWWWWWWWWK",
    "KWWWWWWWWWWK",
    "KWWWWWWWWWWK",
    ".KKKKKKKKKK.",
    "..KK........",
    "..K.........",
]
NOSIGN = [
    "..KKKKK..",
    ".KRRRRRK.",
    "KRRRRRRRK",
    "KRWWWWWRK",
    "KRWWWWWRK",
    "KRRRRRRRK",
    "KRRRRRRRK",
    ".KRRRRRK.",
    "..KKKKK..",
]
PIN = [
    "..KKKKK..",
    ".KDDDDDK.",
    "KDDrrrDDK",
    "KDrWWWrDK",
    "KDrWWWrDK",
    "KDDrrrDDK",
    ".KDDDDDK.",
    "..KDDDK..",
    "...KDK...",
    "....K....",
]


# ------------------------------------------------------------------ helpers
def blank():
    return Image.new("RGBA", (N, N), (0, 0, 0, 0))


def stamp(img, grid, x, y, over=None):
    px = img.load()
    for j, row in enumerate(grid):
        for i, c in enumerate(row):
            col = PAL.get(c)
            if col is None:
                continue
            xx, yy = x + i, y + j
            if 0 <= xx < N and 0 <= yy < N:
                px[xx, yy] = col + (255,)
    return img


def chibi(face=None):
    g = list(CHIBI)
    for k, v in (face or {}).items():
        g[k] = v
    return g


def outline_shape(core, fill="W", accent=None):
    """core: set of (x, y). Returns image with fill + 8-way dark outline."""
    img = blank()
    px = img.load()
    for x, y in core:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                xx, yy = x + dx, y + dy
                if 0 <= xx < N and 0 <= yy < N:
                    px[xx, yy] = PAL["K"] + (255,)
    for x, y in core:
        px[x, y] = PAL[fill] + (255,)
    for x, y in accent or ():
        px[x, y] = PAL["D"] + (255,)
    return img


def spark_at(img, x, y, phase):
    """phase 0..5 -> small, mid, big, mid, small, none ; x,y = centre"""
    lvl = [0, 1, 2, 1, 0, None][phase % 6]
    if lvl is None:
        return img
    g = SPARK[lvl]
    return stamp(img, g, x - len(g[0]) // 2, y - len(g) // 2)


# ------------------------------------------------------------------ cursors
BOB = [0, 0, 0, -1, -1, -1, 0, 0]
CX, CY = 15, 11  # chibi position beside the arrow


def base_frames(n=8, blink_at=6, extra=None, face=None, with_arrow=True, sparks=True):
    frames = []
    for i in range(n):
        img = blank()
        if sparks:
            spark_at(img, 29, 13, i)
            spark_at(img, 12, 27, i + 3)
        f = BLINK if i == blink_at else face
        stamp(img, chibi(f), CX, CY + BOB[i % len(BOB)])
        if extra:
            extra(img, i)
        if with_arrow:
            stamp(img, ARROW, 0, 0)
        frames.append(img)
    return frames


def make_all():
    res = {}
    res["pointer"] = (base_frames(), (0, 0), 8)

    def help_extra(img, i):
        stamp(img, QBUBBLE, 21, [0, 0, 1, 1][i % 4] - 0)
    res["help"] = (base_frames(extra=help_extra, sparks=False), (0, 0), 8)

    def work_extra(img, i):
        stamp(img, DOTS, 19, 1)
        for k in range(min(i % 4, 3)):
            stamp(img, ["PP", "PP"], 21 + k * 3, 3)
    res["working"] = (base_frames(extra=work_extra, sparks=False), (0, 0), 10)

    # busy: chibi hops in the centre, sparkles orbit
    hop = [0, -1, -3, -4, -3, -1, 0, 0]
    corners = [(3, 3), (28, 3), (28, 28), (3, 28)]
    frames = []
    for i in range(8):
        img = blank()
        w = [10, 8, 6, 6, 6, 8, 10, 10][i]
        ImageDraw.Draw(img).line([16 - w // 2, 30, 16 + w // 2 - 1, 30], fill=(0, 0, 0, 70))
        for k, (x, y) in enumerate(corners):
            spark_at(img, x, y, i + k * 2 + (0 if i % 2 else 1))
        stamp(img, chibi(HAPPY if hop[i] < -2 else None), 8, 9 + hop[i])
        frames.append(img)
    res["busy"] = (frames, (16, 16), 8)

    # precision crosshair
    core = {(16, y) for y in range(5, 14)} | {(16, y) for y in range(19, 28)} | \
           {(x, 16) for x in range(5, 14)} | {(x, 16) for x in range(19, 28)}
    frames = []
    for i in range(6):
        img = outline_shape(core)
        img.putpixel((16, 16), PAL["D"] + (255,))
        spark_at(img, 25, 7, i)
        frames.append(img)
    res["precision"] = (frames, (16, 16), 10)

    # text I-beam
    core = {(16, y) for y in range(7, 26)} | {(x, 6) for x in range(13, 20) if x != 16} | \
           {(x, 26) for x in range(13, 20) if x != 16} | {(16, 6), (16, 26)}
    res["text"] = ([outline_shape(core)], (16, 16), 0)

    # handwriting: pencil drawn on a diagonal, tip at bottom-left
    frames = []
    for i in range(6):
        img = blank()
        px = img.load()
        for x in range(N):
            for y in range(N):
                a = (x - 2) + (29 - y)      # along the pencil
                q = (x - 2) - (29 - y)      # across
                if a < 0 or a > 36 or abs(q) > 3 or abs(q) > a:
                    continue
                if abs(q) == 3 or a == 36 or abs(q) == a:
                    c = "K"
                elif a < 3:
                    c = "O"
                elif a < 7:
                    c = "T"
                elif a < 28:
                    c = "F" if q < 0 else ("P" if q > 0 else "h")
                elif a < 31:
                    c = "G"
                else:
                    c = "r"
                px[x, y] = PAL[c] + (255,)
        spark_at(img, 6, 22, i)
        frames.append(img)
    res["handwriting"] = (frames, (2, 29), 10)

    # unavailable: chibi shakes its head next to a no-sign
    frames = []
    for i in range(8):
        img = blank()
        stamp(img, chibi(BLINK if i in (2, 6) else None), 6 + [0, 1, 0, -1][i % 4], 4)
        stamp(img, NOSIGN, 21, 21)
        frames.append(img)
    res["unavailable"] = (frames, (16, 16), 8)

    # resize arrows
    def vcore():
        c = set()
        for k in range(5):
            for j in range(-k, k + 1):
                c.add((16 + j, 3 + k))
                c.add((16 + j, 29 - k))
        c |= {(16, y) for y in range(8, 25)}
        return c
    v = vcore()
    h = {(y, x) for x, y in v}
    res["vert"] = ([outline_shape(v)], (16, 16), 0)
    res["horz"] = ([outline_shape(h)], (16, 16), 0)

    def dcore():
        c = {(i, i) for i in range(8, 25)}
        for x in range(4, 29):
            for y in range(4, 29):
                if x + y <= 15:
                    c.add((x, y))
                if x + y >= 49:
                    c.add((x, y))
        return c
    d1 = dcore()
    d2 = {(32 - x, y) for x, y in d1}
    res["dgn1"] = ([outline_shape(d1)], (16, 16), 0)
    res["dgn2"] = ([outline_shape(d2)], (16, 16), 0)

    mv = set()
    for k in range(4):
        for j in range(-k, k + 1):
            mv |= {(16 + j, 3 + k), (16 + j, 29 - k), (3 + k, 16 + j), (29 - k, 16 + j)}
    mv |= {(16, y) for y in range(7, 26)} | {(x, 16) for x in range(7, 26)}
    img = outline_shape(mv)
    stamp(img, [".D.", "DDD", ".D."], 15, 15)
    res["move"] = ([img], (16, 16), 0)

    up = set()
    for k in range(7):
        for j in range(-k, k + 1):
            up.add((16 + j, 2 + k))
    up |= {(x, y) for x in range(15, 18) for y in range(9, 29)}
    res["alternate"] = ([outline_shape(up)], (16, 2), 0)

    # link: pointing hand + chibi sending hearts
    def link_frames():
        out = []
        for i in range(8):
            img = blank()
            stamp(img, chibi(HAPPY), CX + 1, CY + 1 + BOB[i])
            hy = 12 - i * 2
            if i < 6:
                stamp(img, HEART, 24, hy)
            stamp(img, HAND, 0, 0)
            out.append(img)
        return out
    res["link"] = (link_frames(), (4, 0), 8)

    frames = []
    for i in range(8):
        img = blank()
        stamp(img, chibi(), CX, CY + BOB[i])
        stamp(img, PIN, 23, [0, -1, -2, -2, -1, 0, 0, 0][i] + 1)
        stamp(img, ARROW, 0, 0)
        frames.append(img)
    res["pin"] = (frames, (0, 0), 8)

    def person_extra(img, i):
        if i < 6:
            stamp(img, HEART, 25, 10 - i)
    res["person"] = (base_frames(extra=person_extra, face=HAPPY, blink_at=-1, sparks=False), (0, 0), 8)
    return res


# ------------------------------------------------------------------ output
def nearest(img, size):
    return img.resize((size, size), Image.NEAREST)


def preview(cset, path_png, path_gif):
    order = build.WIN_ORDER
    scale, cell = 3, 120
    cols = 6
    rows = (len(order) + cols - 1) // cols
    W, H = cols * cell, rows * (cell + 18) + 10
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    nframes = 24
    gif = []
    for f in range(nframes):
        im = Image.new("RGBA", (W, H), (44, 46, 58, 255))
        d = ImageDraw.Draw(im)
        for k, name in enumerate(order):
            frames = cset[name][0]
            fr = frames[f % len(frames)]
            x = (k % cols) * cell + (cell - N * scale) // 2
            y = (k // cols) * (cell + 18) + 10
            im.alpha_composite(nearest(fr, N * scale), (x, y))
            d.text(((k % cols) * cell + cell // 2, y + N * scale + 10), name, font=font,
                   fill=(220, 222, 235), anchor="mm")
        gif.append(im.convert("RGB"))
    gif[0].save(path_png)
    gif[0].save(path_gif, save_all=True, append_images=gif[1:], duration=133, loop=0)


def main():
    build.downscale = nearest          # crisp pixels for every encoder
    build.WIN_SIZES = SIZES
    build.X11_SIZES = [32, 64, 96]
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    cset = make_all()
    folder = NAME.replace(" ", "")
    build.write_windows(NAME, cset, os.path.join(OUT, "windows", folder))
    build.write_linux(NAME, cset, os.path.join(OUT, "linux", folder))
    preview(cset, os.path.join(OUT, "preview.png"), os.path.join(OUT, "preview.gif"))
    print("done ->", OUT)


if __name__ == "__main__":
    main()
