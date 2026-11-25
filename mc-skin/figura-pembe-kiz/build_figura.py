#!/usr/bin/env python3
"""Figura avatarı üretir: pembe skinli kız, çok katmanlı 3D model.

Girdi : skin.png (64x64, slim) — bu klasörde
Çıktı : pembe_kiz.bbmodel  (Blockbench modeli, Figura doğrudan okur)
        ekstra.png         (ek 3D parçaların dokusu)
        preview.png        (kontrol için 3D önizleme)

Koordinatlar Blockbench/Figura düzeninde: 1 birim = 1 piksel, ayaklar y=0,
karakter KUZEYE (-Z) bakar, karakterin sağı +X.
"""
import base64, io, json, math, os, random, uuid
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(5)

SKIN = Image.open(os.path.join(HERE, "skin.png")).convert("RGBA")
EXTRA = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
EX = EXTRA.load()

# ---------------------------------------------------------------- palet (skin'den alındı)
HAIR = (232, 220, 218); HAIR_D = (214, 199, 200); HAIR_DD = (204, 190, 192)
HAIR_L = (240, 228, 225); HAIR_LL = (252, 242, 242)
PINK = (245, 208, 217); PINK_L = (250, 215, 221); PINK_M = (240, 201, 211)
PINK_D = (207, 145, 149); PINK_DD = (194, 134, 140)
WHITE = (255, 250, 250); LACE = (240, 228, 225)


def box_faces(u, v, w, h, d):
    """Kutu açınımı (Minecraft skin düzeni) -> {yüz: (x, y, w, h)}"""
    return {"top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d), "right": (u, v + d, d, h),
            "front": (u + d, v + d, w, h), "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h)}


def paint(rect, fn):
    x, y, w, h = rect
    for j in range(h):
        for i in range(w):
            c = fn(i, j, w, h)
            if c is not None:
                EX[x + i, y + j] = tuple(c) + (255,)


def hair_c(i, j, h, seed=0):
    """Yumuşak dikey saç telleri, üst açık alt koyu."""
    base = (HAIR, HAIR_L, HAIR, HAIR_D, HAIR, HAIR_LL if (i + seed) % 7 == 2 else HAIR)[(i * 5 + seed) % 6]
    if j >= h - 2:
        base = HAIR_D if base != HAIR_DD else HAIR_DD
    return base


# ================================================================ EKSTRA DOKU
# Her parça: (u, v) doku köşesi ve (w, h, d) texel boyutu
TEX = {
    "hair_shell": ((0, 0), (8, 8, 8)),
    "long_hair":  ((0, 16), (9, 14, 2)),
    "skirt1":     ((24, 16), (8, 3, 4)),
    "skirt2":     ((24, 24), (8, 2, 4)),
    "strand":     ((48, 16), (1, 8, 2)),
    "bow_knot":   ((56, 16), (2, 2, 1)),
    "bow_tail":   ((56, 20), (1, 3, 1)),
    "bow_loop":   ((48, 28), (3, 3, 1)),
    "collar":     ((0, 32), (5, 1, 1)),
    "bowtie":     ((0, 36), (3, 2, 1)),
    "clip":       ((0, 40), (2, 1, 1)),
    "cuff":       ((16, 32), (3, 1, 4)),
    "puff":       ((32, 32), (3, 3, 4)),
    "sock":       ((48, 32), (4, 1, 4)),
}


def F(name):
    (u, v), (w, h, d) = TEX[name]
    return box_faces(u, v, w, h, d)


# --- saç kabuğu (kafanın üstünde 3. katman)
f = F("hair_shell")
paint(f["top"], lambda i, j, w, h: HAIR_D if i == 3 else hair_c(i, 0, 8, j))
paint(f["back"], lambda i, j, w, h: hair_c(i, j, 99))
paint(f["right"], lambda i, j, w, h: hair_c(i, j, 99, 1) if (j < 4 or i in (0, 1, 2, 7)) else None)  # i=7 öne bakar
paint(f["left"], lambda i, j, w, h: hair_c(i, j, 99, 2) if (j < 4 or i in (0, 5, 6, 7)) else None)   # i=0 öne bakar
paint(f["front"], lambda i, j, w, h: hair_c(i, j, 99, 3) if (j == 0 or (j == 1 and i not in (3, 4)) or (i in (0, 7) and j < 4)) else None)

# --- sırta inen uzun saç (ucu kırık kırık)
f = F("long_hair")
ends = [12, 14, 13, 14, 12, 14, 13, 14, 12]
paint(f["back"], lambda i, j, w, h: hair_c(i, j, ends[i], 4) if j < ends[i] else None)
paint(f["front"], lambda i, j, w, h: HAIR_DD if j < ends[w - 1 - i] else None)
paint(f["right"], lambda i, j, w, h: hair_c(i, j, 12, 5) if j < 12 + i else None)
paint(f["left"], lambda i, j, w, h: hair_c(i, j, 12, 6) if j < 13 - i else None)
paint(f["top"], lambda i, j, w, h: HAIR)
paint(f["bottom"], lambda i, j, w, h: HAIR_D)

# --- yüz kenarından sarkan tutamlar
f = F("strand")
for k in ("front", "back", "right", "left"):
    paint(f[k], lambda i, j, w, h: (HAIR_L if j < 2 else HAIR if j < 6 else HAIR_D) if j < 7 or (i + j) % 2 else None)
paint(f["top"], lambda i, j, w, h: HAIR)
paint(f["bottom"], lambda i, j, w, h: HAIR_D)

# --- etek: üst kat pileli, alt kat dantelli
f = F("skirt1")
for k in ("front", "back", "right", "left"):
    paint(f[k], lambda i, j, w, h: PINK_L if j == 1 else (PINK_D if i % 2 == 0 else PINK_DD))
paint(f["top"], lambda i, j, w, h: PINK_D)
paint(f["bottom"], lambda i, j, w, h: PINK_DD)
f = F("skirt2")
for k in ("front", "back", "right", "left"):
    paint(f[k], lambda i, j, w, h: (PINK_DD if i % 2 else PINK_D) if j == 0 else (WHITE if i % 2 == 0 else LACE))
paint(f["top"], lambda i, j, w, h: PINK_DD)
paint(f["bottom"], lambda i, j, w, h: LACE)

# --- arka fiyonk
for name, main, edge in (("bow_loop", PINK_M, PINK_D), ("bow_knot", PINK_D, PINK_DD), ("bow_tail", PINK_D, PINK_DD)):
    for k, r in F(name).items():
        paint(r, lambda i, j, w, h, m=main, e=edge: e if (i in (0, w - 1) or j in (0, h - 1)) and w > 2 and h > 2 else m)
# --- yaka, kurdele, toka
for k, r in F("collar").items():
    paint(r, lambda i, j, w, h: WHITE if i % 2 == 0 else LACE)
for k, r in F("bowtie").items():
    paint(r, lambda i, j, w, h: PINK_DD if i == w // 2 else PINK_D)
for k, r in F("clip").items():
    paint(r, lambda i, j, w, h: PINK_D if i == 0 else PINK_L)
# --- manşet fırfırı, omuz kabarıklığı, çorap fırfırı
for k in ("front", "back", "right", "left"):
    paint(F("cuff")[k], lambda i, j, w, h: WHITE if i % 2 == 0 else PINK_L)
    paint(F("puff")[k], lambda i, j, w, h: PINK_L if j == 0 else PINK if j == 1 else PINK_M)
    paint(F("sock")[k], lambda i, j, w, h: WHITE if i % 2 == 0 else LACE)
paint(F("puff")["top"], lambda i, j, w, h: PINK_L)

EXTRA.save(os.path.join(HERE, "ekstra.png"))


# ================================================================ MODEL (küpler)
def uid():
    return str(uuid.uuid4())


def box_uv(u, v, w, h, d):
    """Blockbench box-UV yerleşimi (Minecraft skin ile aynı)."""
    return {
        "north": [u + d, v + d, u + d + w, v + d + h],
        "east":  [u, v + d, u + d, v + d + h],
        "south": [u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h],
        "west":  [u + d + w, v + d, u + 2 * d + w, v + d + h],
        "up":    [u + d + w, v + d, u + d, v],
        "down":  [u + d + 2 * w, v, u + d + w, v + d],
    }


GROUPS = {}   # grup adı -> {"origin":..., "children": [küp]}
ELEMENTS = []


def cube(group, name, frm, to, uv, dims, tex, inflate=0.0, skip=()):
    uvs = box_uv(*uv, *dims)
    faces = {k: ({"uv": v, "texture": tex} if k not in skip else {"uv": [0, 0, 0, 0], "texture": None})
             for k, v in uvs.items()}
    el = {"name": name, "type": "cube", "box_uv": False, "rescale": False, "locked": False,
          "from": list(frm), "to": list(to), "autouv": 0, "color": 0, "inflate": inflate,
          "origin": GROUPS[group]["origin"], "faces": faces, "uuid": uid()}
    ELEMENTS.append(el)
    GROUPS[group]["children"].append(el)


def group(name, origin):
    GROUPS[name] = {"origin": list(origin), "children": []}


S, X = 0, 1  # doku indeksleri: 0 = skin.png, 1 = ekstra.png

# Figura anahtar kelimeli gruplar: vanilla animasyonları bu isimlere bağlanır
group("Head", (0, 24, 0)); group("Body", (0, 24, 0))
group("RightArm", (5, 22, 0)); group("LeftArm", (-5, 22, 0))
group("RightLeg", (1.9, 12, 0)); group("LeftLeg", (-1.9, 12, 0))

# --- 1. ve 2. katman (normal skin)
cube("Head", "kafa", (-4, 24, -4), (4, 32, 4), (0, 0), (8, 8, 8), S)
cube("Head", "kafa_2", (-4, 24, -4), (4, 32, 4), (32, 0), (8, 8, 8), S, 0.5)
cube("Body", "govde", (-4, 12, -2), (4, 24, 2), (16, 16), (8, 12, 4), S)
cube("Body", "govde_2", (-4, 12, -2), (4, 24, 2), (16, 32), (8, 12, 4), S, 0.25)
cube("RightArm", "sag_kol", (4, 12, -2), (7, 24, 2), (40, 16), (3, 12, 4), S)
cube("RightArm", "sag_kol_2", (4, 12, -2), (7, 24, 2), (40, 32), (3, 12, 4), S, 0.25)
cube("LeftArm", "sol_kol", (-7, 12, -2), (-4, 24, 2), (32, 48), (3, 12, 4), S)
cube("LeftArm", "sol_kol_2", (-7, 12, -2), (-4, 24, 2), (48, 48), (3, 12, 4), S, 0.25)
cube("RightLeg", "sag_bacak", (0, 0, -2), (4, 12, 2), (0, 16), (4, 12, 4), S)
cube("RightLeg", "sag_bacak_2", (0, 0, -2), (4, 12, 2), (0, 32), (4, 12, 4), S, 0.25)
cube("LeftLeg", "sol_bacak", (-4, 0, -2), (0, 12, 2), (16, 48), (4, 12, 4), S)
cube("LeftLeg", "sol_bacak_2", (-4, 0, -2), (0, 12, 2), (0, 48), (4, 12, 4), S, 0.25)

# --- ek 3D katmanlar
T = lambda n: (TEX[n][0], TEX[n][1])
cube("Head", "sac_hacim", (-4, 24, -4), (4, 32, 4), *T("hair_shell"), X, 1.0, skip=("down",))
cube("Head", "tutam_sag", (4.3, 19, -4.4), (5.3, 27, -2.4), *T("strand"), X, skip=("down",))
cube("Head", "tutam_sol", (-5.3, 19, -4.4), (-4.3, 27, -2.4), *T("strand"), X, skip=("down",))
cube("Head", "toka", (2, 30.2, -5.2), (4, 31.2, -4.2), *T("clip"), X)
cube("Head", "fiyonk_dugum", (-1, 26, 4.8), (1, 28, 5.8), *T("bow_knot"), X)
cube("Head", "fiyonk_sag", (1, 25.5, 4.9), (4, 28.5, 5.7), *T("bow_loop"), X)
cube("Head", "fiyonk_sol", (-4, 25.5, 4.9), (-1, 28.5, 5.7), *T("bow_loop"), X)
cube("Head", "fiyonk_kurdele", (-0.5, 23, 5.0), (0.5, 26, 5.6), *T("bow_tail"), X)
cube("Body", "uzun_sac", (-4.5, 10, 2.4), (4.5, 24, 4.2), *T("long_hair"), X, skip=("up", "down"))
cube("Body", "yaka", (-2.5, 23, -2.75), (2.5, 24, -2.25), *T("collar"), X)
cube("Body", "kurdele", (-1.5, 21, -2.9), (1.5, 22.6, -2.4), *T("bowtie"), X)
cube("Body", "etek_ust", (-4.6, 10.6, -2.6), (4.6, 13.6, 2.6), *T("skirt1"), X, skip=("down",))
cube("Body", "etek_alt", (-5.0, 9.8, -3.0), (5.0, 11.4, 3.0), *T("skirt2"), X, skip=("up", "down"))
for g, (x0, x1) in (("RightArm", (4, 7)), ("LeftArm", (-7, -4))):
    k = "sag" if g == "RightArm" else "sol"
    cube(g, f"mansete_{k}", (x0, 14, -2), (x1, 15, 2), *T("cuff"), X, 0.55, skip=("up", "down"))
    cube(g, f"omuz_{k}", (x0, 21, -2), (x1, 24, 2), *T("puff"), X, 0.5, skip=("down",))
for g, (x0, x1) in (("RightLeg", (0, 4)), ("LeftLeg", (-4, 0))):
    k = "sag" if g == "RightLeg" else "sol"
    cube(g, f"corap_{k}", (x0, 6, -2), (x1, 7, 2), *T("sock"), X, 0.45, skip=("up", "down"))


# ================================================================ .bbmodel yaz
def png_b64(im):
    buf = io.BytesIO(); im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


textures = []
for i, (fname, im) in enumerate((("skin.png", SKIN), ("ekstra.png", EXTRA))):
    textures.append({"path": "", "name": fname, "folder": "", "namespace": "", "id": str(i),
                     "width": 64, "height": 64, "uv_width": 64, "uv_height": 64,
                     "particle": False, "render_mode": "default", "render_sides": "auto",
                     "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
                     "visible": True, "internal": True, "saved": True, "uuid": uid(),
                     "relative_path": fname, "source": png_b64(im)})

outliner = [{"name": n, "origin": g["origin"], "color": 0, "uuid": uid(), "export": True,
             "mirror_uv": False, "isOpen": True, "locked": False, "visibility": True, "autouv": 0,
             "children": [c["uuid"] for c in g["children"]]} for n, g in GROUPS.items()]

bb = {"meta": {"format_version": "4.5", "model_format": "free", "box_uv": False},
      "name": "pembe_kiz", "model_identifier": "", "visible_box": [1, 1, 0],
      "variable_placeholders": "", "variable_placeholder_buttons": [], "timeline_setups": [],
      "unhandled_root_fields": {}, "resolution": {"width": 64, "height": 64},
      "elements": ELEMENTS, "outliner": outliner, "textures": textures}
with open(os.path.join(HERE, "pembe_kiz.bbmodel"), "w") as fp:
    json.dump(bb, fp, indent=1)

# ================================================================ kontroller
for im in (SKIN, EXTRA):
    assert im.size == (64, 64) and im.mode == "RGBA"
    assert all(im.getpixel((i, j))[3] in (0, 255) for i in range(64) for j in range(64)), "yarı saydam piksel"
for el in ELEMENTS:
    for k, fc in el["faces"].items():
        if fc["texture"] is None:
            continue
        a, b, c, d = fc["uv"]
        assert 0 <= min(a, c) and max(a, c) <= 64 and 0 <= min(b, d) and max(b, d) <= 64, (el["name"], k)
print(f"{len(ELEMENTS)} küp, {len(GROUPS)} grup yazıldı -> pembe_kiz.bbmodel")


# ================================================================ önizleme (Blockbench yüz yönleriyle)
TEXIMG = [SKIN.load(), EX]


def face_quads(el, only_vanilla):
    if only_vanilla and el["faces"]["north"].get("texture") == X:
        return
    e = el["inflate"]
    x0, y0, z0 = (c - e for c in el["from"])
    x1, y1, z1 = (c + e for c in el["to"])
    L = lambda a, b, t: a + (b - a) * t
    geo = {  # (s, t) -> nokta ; s = uv yatay ilerleme, t = uv dikey ilerleme
        "north": lambda s, t: (L(x1, x0, s), L(y1, y0, t), z0),
        "south": lambda s, t: (L(x0, x1, s), L(y1, y0, t), z1),
        "east":  lambda s, t: (x1, L(y1, y0, t), L(z1, z0, s)),
        "west":  lambda s, t: (x0, L(y1, y0, t), L(z0, z1, s)),
        "up":    lambda s, t: (L(x0, x1, s), y1, L(z0, z1, t)),
        "down":  lambda s, t: (L(x0, x1, s), y0, L(z1, z0, t)),
    }
    normal = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
    for k, fc in el["faces"].items():
        if fc["texture"] is None:
            continue
        a, b, c, d = fc["uv"]
        nu, nv = abs(c - a), abs(d - b)
        tex = TEXIMG[fc["texture"]]
        for p in range(nu):
            for q in range(nv):
                tx = math.floor(a + (p + 0.5) / nu * (c - a)); ty = math.floor(b + (q + 0.5) / nv * (d - b))
                col = tex[tx, ty]
                if col[3] == 0:
                    continue
                g = geo[k]
                yield k, normal[k], [g(p / nu, q / nv), g((p + 1) / nu, q / nv), g((p + 1) / nu, (q + 1) / nv), g(p / nu, (q + 1) / nv)], col[:3]


def render(yaw, only_vanilla=False, size=(260, 400), sc=10, pitch=-10):
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    def tr(p):  # kamera kuzeyde, güneye bakıyor: ekran x = -X, ekran y = -Y, kameraya doğru = -Z
        x, y, z = -p[0], -(p[1] - 16), -p[2]
        x, z = x * cy + z * sy, -x * sy + z * cy
        y, z = y * cp - z * sp, y * sp + z * cp
        return x, y, z
    light = {"north": 1.0, "south": 0.8, "east": 0.9, "west": 0.86, "up": 1.06, "down": 0.65}
    items = []
    for el in ELEMENTS:
        for k, n, pts, col in face_quads(el, only_vanilla):
            nz = tr(n)[2] - tr((0, 0, 0))[2]
            if nz <= 0.01:
                continue
            P = [tr(p) for p in pts]
            items.append((sum(q[2] for q in P) / 4, [(size[0] / 2 + q[0] * sc, size[1] / 2 + q[1] * sc) for q in P],
                          tuple(min(255, round(v * light[k])) for v in col)))
    im = Image.new("RGB", size, (62, 58, 72)); dr = ImageDraw.Draw(im)
    for _, poly, col in sorted(items, key=lambda t: t[0]):
        dr.polygon(poly, fill=col)
    return im


def font(sz):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", sz)
    except OSError:
        return ImageFont.load_default()


views = [(-30, "Ön (3/4)"), (0, "Ön"), (90, "Yan"), (180, "Arka"), (150, "Arka (3/4)")]
pv = Image.new("RGB", (150 + 260 * len(views), 30 + 400 * 2), (40, 40, 50)); d = ImageDraw.Draw(pv)
for c, (yaw, label) in enumerate(views):
    d.text((150 + c * 260 + 130, 15), label, fill=(235, 235, 240), font=font(16), anchor="mm")
    pv.paste(render(yaw), (150 + c * 260, 30))
    pv.paste(render(yaw, only_vanilla=True), (150 + c * 260, 430))
d.text((75, 230), "Figura\n(çok katmanlı)", fill=(235, 235, 240), font=font(15), anchor="mm", align="center")
d.text((75, 630), "Normal skin\n(2 katman)", fill=(235, 235, 240), font=font(15), anchor="mm", align="center")
pv.save(os.path.join(HERE, "preview.png"))
print("preview.png yazıldı")
