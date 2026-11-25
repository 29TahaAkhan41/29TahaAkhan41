#!/usr/bin/env python3
"""Minecraft Java Edition skin: sade, günlük giyimli genç kız (SLIM / Alex modeli).

Çıktılar (bu dosyanın yanına yazılır):
  skin.png      64x64 RGBA skin
  preview.png   3D'ye katlanmış ön / yan / arka görünüm, 10x (üst sıra: 1.+2. katman, alt sıra: sadece 1. katman)
  skin_x8.png   düz doku 8x, UV bölgeleri çizgili

Çalıştırma:  python3 make_skin.py
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
random.seed(1207)  # gürültü her çalıştırmada aynı olsun


# --------------------------------------------------------------------------- renkler
def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(a[k] + (b[k] - a[k]) * t) for k in range(3))


WHITE, BLACK = (255, 255, 255), (0, 0, 0)

SKIN, SKIN_D = hexc("F2D2B8"), hexc("E0B89C")
HAIR, HAIR_D, HAIR_L = hexc("6B4630"), hexc("4A2F20"), hexc("8C6145")
TEE = hexc("F5F1EA")
CARD, CARD_D = hexc("E8A8B8"), hexc("C9879A")
JEAN, JEAN_D = hexc("6F8FB8"), hexc("50709A")
SHOE, SOLE = hexc("F7F7F7"), hexc("C8C8C8")

EYE_TOP = hexc("3E2618")      # koyu kahve
EYE_BOT = hexc("C98A3A")      # bal rengi
BROW = HAIR_L
BLUSH = mix(SKIN, hexc("EE9AA8"), 0.35)   # çok soluk pembe
MOUTH = mix(SKIN, hexc("C9707E"), 0.55)   # soluk gül
TEE_SHADOW = mix(TEE, hexc("B8A894"), 0.35)
CUFF = mix(JEAN, WHITE, 0.2)  # bir ton açık mavi

# 3 tonlu rampalar: (açık, ana, koyu)
R_SKIN = (mix(SKIN, WHITE, 0.25), SKIN, SKIN_D)
R_HAIR = (mix(HAIR, HAIR_L, 0.45), HAIR, HAIR_D)
R_TEE = (mix(TEE, WHITE, 0.5), TEE, mix(TEE, hexc("CFC4B4"), 0.35))
R_CARD = (mix(CARD, WHITE, 0.16), CARD, mix(CARD, CARD_D, 0.55))
R_JEAN = (mix(JEAN, WHITE, 0.1), JEAN, mix(JEAN, JEAN_D, 0.6))
R_SHOE = (SHOE, SHOE, mix(SHOE, SOLE, 0.3))

# Işık sol üstten (önden bakınca). Karakterin sağ yüzü ekranın solunda -> daha aydınlık.
FACE_BIAS = {"top": -0.30, "right": -0.08, "front": 0.0, "left": 0.12, "back": 0.15, "bottom": 0.45}


def tone(ramp, face, i, j, w, h):
    """Yüzey içi konuma göre rampadan ton seç: üst açık, alt koyu, ön yüzde sol daha aydınlık."""
    v = (j + 0.5) / h * 0.85 + FACE_BIAS[face]
    if face == "front":
        v += ((i + 0.5) / w - 0.5) * 0.25
    return ramp[0] if v < 0.30 else ramp[2] if v > 0.78 else ramp[1]


def jitter(c, n):
    d = random.randint(-n, n)
    return tuple(max(0, min(255, x + d)) for x in c)


# --------------------------------------------------------------------------- UV düzeni
img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
PX = img.load()


def put(x, y, rgb):
    PX[x, y] = tuple(rgb) + (255,)


def faces(u, v, w, h, d):
    """Kutu açınımı: {yüz: (x, y, genişlik, yükseklik)}"""
    return {
        "top": (u + d, v, w, d),
        "bottom": (u + d + w, v, w, d),
        "right": (u, v + d, d, h),
        "front": (u + d, v + d, w, h),
        "left": (u + d + w, v + d, d, h),
        "back": (u + 2 * d + w, v + d, w, h),
    }


#        parça         (u, v, w, h, d) 1. katman   2. katman (u, v)
PARTS = {
    "head":      ((0, 0, 8, 8, 8),   (32, 0)),
    "body":      ((16, 16, 8, 12, 4), (16, 32)),
    "right_arm": ((40, 16, 3, 12, 4), (40, 32)),   # slim: 3 px
    "left_arm":  ((32, 48, 3, 12, 4), (48, 48)),
    "right_leg": ((0, 16, 4, 12, 4),  (0, 32)),
    "left_leg":  ((16, 48, 4, 12, 4), (0, 48)),
}
SIDES = ("right", "front", "left", "back")


def F1(part):
    u, v, w, h, d = PARTS[part][0]
    return faces(u, v, w, h, d)


def F2(part):
    (_, _, w, h, d), (ou, ov) = PARTS[part]
    return faces(ou, ov, w, h, d)


def fill(rect, fn):
    """rect içindeki her (i, j) için fn(i, j, w, h) -> rgb ya da None (None = boş bırak)."""
    x, y, w, h = rect
    for j in range(h):
        for i in range(w):
            c = fn(i, j, w, h)
            if c is not None:
                put(x + i, y + j, c)


def ramp_fn(ramp, face, y0=0, rows=None, noise=0):
    """Yalnızca [y0, y0+rows) satırlarını, o bölgeye göre yerel gölgeyle boyar."""
    def fn(i, j, w, h):
        n = rows if rows is not None else h
        if not (y0 <= j < y0 + n):
            return None
        c = tone(ramp, face, i, j - y0, w, n)
        return jitter(c, noise) if noise else c
    return fn


def knit(c, i):
    """Hırka örgü dokusu: tek sütunlar çok hafif koyu (dikey örgü çizgisi)."""
    return mix(c, BLACK, 0.035) if i % 2 else c


# =========================================================================== KAFA
def head_front_face_base(rect):
    x, y, w, h = rect
    fill(rect, ramp_fn(R_SKIN, "front"))
    # kâkül: alın 2 piksel, ortadan hafif ayrık
    for i in range(8):
        put(x + i, y, tone(R_HAIR, "front", i, 0, 8, 8))
        if i != 4:
            put(x + i, y + 1, tone(R_HAIR, "front", i, 1, 8, 8))
    put(x + 0, y + 2, HAIR)  # şakaklar, yan saçla birleşir
    put(x + 7, y + 2, HAIR_D)
    # ince kaşlar
    for i in (1, 2, 5, 6):
        put(x + i, y + 3, BROW)
    # 2x2 gözler: üst koyu kahve, alt bal, iç üst köşede beyaz parıltı
    for ex, inner in ((1, 2), (5, 5)):
        for i in (ex, ex + 1):
            put(x + i, y + 4, WHITE if i == inner else EYE_TOP)
            put(x + i, y + 5, EYE_BOT)
    # allık: gözlerin hemen altında 1'er piksel
    put(x + 1, y + 6, BLUSH)
    put(x + 6, y + 6, BLUSH)
    # tek piksel soluk gül ağız
    put(x + 4, y + 6, MOUTH)


def head_base():
    F = F1("head")
    fill(F["top"], ramp_fn(R_HAIR, "top"))
    for k in ("right", "left", "back"):
        fill(F[k], ramp_fn(R_HAIR, k))
    head_front_face_base(F["front"])
    fill(F["bottom"], ramp_fn(R_SKIN, "bottom"))


def head_overlay():
    F = F2("head")
    # üst: tam kabarık saç
    fill(F["top"], ramp_fn(R_HAIR, "top"))
    # yanlar: üst 4 satır dolu; altta kulak boşluğu, önünde sarkan tutam, arkada uzun saç
    def side(face, front_cols, back_cols):
        def fn(i, j, w, h):
            if j < 4 or i in front_cols or i in back_cols:
                return tone(R_HAIR, face, i, j, w, h)
            return None
        return fn
    fill(F["right"], side("right", front_cols=(6, 7), back_cols=(0, 1, 2)))   # sağ yüz: i=7 öne bakar
    fill(F["left"], side("left", front_cols=(0, 1), back_cols=(5, 6, 7)))     # sol yüz: i=0 öne bakar
    # arka: omuz hizasına kadar tam saç
    fill(F["back"], ramp_fn(R_HAIR, "back"))
    # ön: kâkül uçları 1 piksel öne çıkar
    x, y, _, _ = F["front"]
    for i in range(8):
        put(x + i, y, tone(R_HAIR, "front", i, 0, 8, 8))
        if i != 4:
            put(x + i, y + 1, tone(R_HAIR, "front", i, 1, 8, 8))
    put(x + 0, y + 2, HAIR)
    put(x + 7, y + 2, HAIR_D)
    # tel ışıltıları (3 adet, sol üst ışığa yakın yerlerde)
    put(F["top"][0] + 2, F["top"][1] + 5, HAIR_L)
    put(F["right"][0] + 5, F["right"][1] + 1, HAIR_L)
    put(x + 2, y + 0, HAIR_L)


# =========================================================================== GÖVDE
def body_base():
    F = F1("body")
    for k in ("top", "right", "front", "left", "back", "bottom"):
        fill(F[k], ramp_fn(R_TEE, k))
    x, y, _, _ = F["front"]
    put(x + 3, y, TEE_SHADOW)   # yaka gölgesi
    put(x + 4, y, TEE_SHADOW)


def cardigan_fn(face, open_cols=()):
    def fn(i, j, w, h):
        if i in open_cols:
            return None
        if j == h - 1:  # alt kenarda koyu ribana (tüm yüzlerde aynı satır)
            return mix(CARD_D, BLACK, 0.05) if i % 2 else CARD_D
        return knit(tone(R_CARD, face, i, j, w, h - 1), i)
    return fn


def body_overlay():
    F = F2("body")
    fill(F["front"], cardigan_fn("front", open_cols=(3, 4)))   # önü açık: tişört görünür
    for k in ("right", "left", "back"):
        fill(F[k], cardigan_fn(k))
    # omuzlar (üst yüz): ön kenarda (j=3) açıklık devam eder
    fill(F["top"], lambda i, j, w, h: None if (j == 3 and i in (3, 4)) else knit(tone(R_CARD, "top", i, j, w, h), i))


# =========================================================================== KOLLAR (slim)
def arm_base(part):
    F = F1(part)
    for k in SIDES:
        fill(F[k], ramp_fn(R_TEE, k, 0, 3))      # tişört kolu: omuzdan 3 px
        fill(F[k], ramp_fn(R_SKIN, k, 3, 9))     # kol + el
    fill(F["top"], ramp_fn(R_TEE, "top"))
    fill(F["bottom"], ramp_fn(R_SKIN, "bottom"))


def arm_overlay(part):
    F = F2(part)
    for k in SIDES:
        def fn(i, j, w, h, k=k):
            if j < 9:
                return knit(tone(R_CARD, k, i, j, w, 9), i)
            if j == 9:
                return CARD_D           # bilekte ribana
            return None                 # el (2 px) şeffaf
        fill(F[k], fn)
    fill(F["top"], lambda i, j, w, h: knit(tone(R_CARD, "top", i, j, w, h), i))


# =========================================================================== BACAKLAR
def leg_base(part):
    F = F1(part)
    for k in SIDES:
        def fn(i, j, w, h, k=k):
            if j < 10:
                c = jitter(tone(R_JEAN, k, i, j, w, 10), 4)
                if k == "front" and j in (5, 6):
                    c = mix(c, WHITE, 0.07)          # dizde çok hafif açık ton
                if (k == "right" and i == 1) or (k == "left" and i == 2):
                    c = jitter(JEAN_D, 2)            # yan dikiş
                return c
            if j == 10:
                return tone(R_SHOE, k, i, 0, w, 1)
            return SOLE
        fill(F[k], fn)
    fill(F["top"], ramp_fn(R_JEAN, "top", noise=3))
    fill(F["bottom"], lambda i, j, w, h: SOLE)


def leg_overlay(part):
    F = F2(part)
    for k in SIDES:
        fill(F[k], lambda i, j, w, h: CUFF if j == 9 else None)   # paça kıvrımı
    x, y, w, _ = F["front"]
    for i in range(w):
        put(x + i, y + 10, SHOE)                                  # ayakkabı burnu


# =========================================================================== ÇİZİM
head_base(); body_base()
for p in ("right_arm", "left_arm"):
    arm_base(p)
for p in ("right_leg", "left_leg"):
    leg_base(p)

head_overlay(); body_overlay()
for p in ("right_arm", "left_arm"):
    arm_overlay(p)
for p in ("right_leg", "left_leg"):
    leg_overlay(p)

img.save(os.path.join(OUT, "skin.png"))

# =========================================================================== KONTROLLER
assert img.size == (64, 64), img.size
assert img.mode == "RGBA", img.mode
for part in PARTS:
    for name, (x, y, w, h) in F1(part).items():
        for i in range(x, x + w):
            for j in range(y, y + h):
                assert PX[i, j][3] == 255, f"1. katman boşluk: {part}.{name} ({i},{j})"
for i in range(64):
    for j in range(64):
        assert PX[i, j][3] in (0, 255), f"yarı saydam piksel ({i},{j})"
for i in (54, 55):
    for j in range(20, 32):
        assert PX[i, j][3] == 0, f"slim sağ kol kullanılmayan sütun dolu ({i},{j})"
for i in (46, 47):
    for j in range(52, 64):
        assert PX[i, j][3] == 0, f"slim sol kol kullanılmayan sütun dolu ({i},{j})"
# 2. katman bölgeleri dışındaki boş alanlar da boş kalmalı
used = set()
for part in PARTS:
    for F in (F1(part), F2(part)):
        for x, y, w, h in F.values():
            used |= {(i, j) for i in range(x, x + w) for j in range(y, y + h)}
for i in range(64):
    for j in range(64):
        if (i, j) not in used:
            assert PX[i, j][3] == 0, f"UV dışı piksel dolu ({i},{j})"
print("assert'ler geçti: 64x64 RGBA, 1. katman tam dolu, alfa yalnızca 0/255, slim sütunları boş")


# =========================================================================== ÖNİZLEME (3D)
#            parça        (x, y, z, w, h, d) model uzayı (y aşağı, z izleyiciye doğru), 2. katman şişirme
GEO = {
    "head":      ((4, 0, -4, 8, 8, 8), 0.5),
    "body":      ((4, 8, -2, 8, 12, 4), 0.25),
    "right_arm": ((1, 8, -2, 3, 12, 4), 0.25),   # karakterin sağı = ekranın solu
    "left_arm":  ((12, 8, -2, 3, 12, 4), 0.25),
    "right_leg": ((4, 20, -2, 4, 12, 4), 0.25),
    "left_leg":  ((8, 20, -2, 4, 12, 4), 0.25),
}
NORMALS = {"front": (0, 0, 1), "back": (0, 0, -1), "right": (-1, 0, 0),
           "left": (1, 0, 0), "top": (0, -1, 0), "bottom": (0, 1, 0)}
SHADE = {"front": 1.0, "back": 0.82, "right": 0.9, "left": 0.9, "top": 1.05, "bottom": 0.7}


def quads(with_overlay):
    for part, ((x, y, z, w, h, d), inf) in GEO.items():
        layers = [(F1(part), 0.0)] + ([(F2(part), inf)] if with_overlay else [])
        for F, e in layers:
            x0, y0, z0, x1, y1, z1 = x - e, y - e, z - e, x + w + e, y + h + e, z + d + e
            L = lambda a, b, t: a + (b - a) * t
            corner = {
                "front":  lambda u, v: (L(x0, x1, u), L(y0, y1, v), z1),
                "back":   lambda u, v: (L(x1, x0, u), L(y0, y1, v), z0),
                "right":  lambda u, v: (x0, L(y0, y1, v), L(z0, z1, u)),
                "left":   lambda u, v: (x1, L(y0, y1, v), L(z1, z0, u)),
                "top":    lambda u, v: (L(x0, x1, u), y0, L(z0, z1, v)),
                "bottom": lambda u, v: (L(x0, x1, u), y1, L(z1, z0, v)),
            }
            for name, fn in corner.items():
                fx, fy, fw, fh = F[name]
                for i in range(fw):
                    for j in range(fh):
                        c = PX[fx + i, fy + j]
                        if c[3] == 0:
                            continue
                        pts = [fn(i / fw, j / fh), fn((i + 1) / fw, j / fh),
                               fn((i + 1) / fw, (j + 1) / fh), fn(i / fw, (j + 1) / fh)]
                        yield name, pts, c[:3], e


def render(view, with_overlay, sc=10, size=(220, 360)):
    """Ortografik görünüm. view: 'front' | 'right' (karakterin sağ yanı) | 'back'."""
    def tr(p):
        x, y, z = p[0] - 8, p[1] - 16, p[2]
        if view == "front":
            return x, y, z
        if view == "back":
            return -x, y, -z
        return z, y, -x          # sağ yan: kamera -x yönünde, yüz ekranın sağında
    items = []
    for name, pts, c, e in quads(with_overlay):
        n = NORMALS[name]
        if tr((n[0] + 8, n[1] + 16, n[2]))[2] <= 0.01:
            continue
        P = [tr(p) for p in pts]
        col = tuple(min(255, round(v * SHADE[name])) for v in c)
        items.append((sum(q[2] for q in P) / 4 + e * 0.01,
                      [(size[0] / 2 + q[0] * sc, size[1] / 2 + q[1] * sc) for q in P], col))
    im = Image.new("RGB", size, (58, 60, 72))
    dr = ImageDraw.Draw(im)
    for _, poly, col in sorted(items, key=lambda t: t[0]):
        dr.polygon(poly, fill=col)
    return im


def font(sz):
    """Türkçe harfleri (Ö, ğ) gösterebilen bir yazı tipi; yoksa Pillow'un varsayılanı."""
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "DejaVuSans.ttf", "Arial.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(path, sz)
        except OSError:
            continue
    return ImageFont.load_default()


views = [("front", "Ön"), ("right", "Yan (sağ)"), ("back", "Arka")]
CW, CH, TOP, LEFT = 220, 360, 34, 150
pv = Image.new("RGB", (LEFT + CW * 3, TOP + CH * 2), (40, 42, 52))
d = ImageDraw.Draw(pv)
for c, (v, label) in enumerate(views):
    d.text((LEFT + c * CW + CW // 2, TOP // 2), label, fill=(235, 235, 240), font=font(18), anchor="mm")
    for r, ov in enumerate((True, False)):
        pv.paste(render(v, ov), (LEFT + c * CW, TOP + r * CH))
for r, label in enumerate(("1. + 2. katman", "Sadece 1. katman")):
    d.text((LEFT // 2, TOP + r * CH + CH // 2), label, fill=(235, 235, 240), font=font(15), anchor="mm")
pv.save(os.path.join(OUT, "preview.png"))


# =========================================================================== DÜZ DOKU x8
S = 8
flat = Image.new("RGBA", (64 * S, 64 * S))
fd = ImageDraw.Draw(flat)
for i in range(64):
    for j in range(64):
        fd.rectangle([i * S, j * S, i * S + S - 1, j * S + S - 1],
                     fill=(205, 205, 210, 255) if (i + j) % 2 else (235, 235, 238, 255))
flat.alpha_composite(img.resize((64 * S, 64 * S), Image.NEAREST))
fd = ImageDraw.Draw(flat)
for part in PARTS:
    for F, col in ((F1(part), (0, 170, 255, 255)), (F2(part), (255, 60, 160, 255))):
        for x, y, w, h in F.values():
            fd.rectangle([x * S, y * S, (x + w) * S - 1, (y + h) * S - 1], outline=col, width=1)
for part, ((u, v, *_), (ou, ov)) in PARTS.items():
    fd.text((u * S + 2, v * S + 1), part, fill=(0, 110, 200, 255), font=font(9))
    fd.text((ou * S + 2, ov * S + 1), part + " 2", fill=(200, 30, 120, 255), font=font(9))
flat.save(os.path.join(OUT, "skin_x8.png"))
print("yazıldı: skin.png, preview.png, skin_x8.png")
