#!/usr/bin/env python3
"""Figura avatarı: Neon zırh (klasik / Steve kolları), çok katmanlı 3D zırh + parlayan (emissive) kısımlar.

Girdi : neon_skin.png (64x64, klasik model)
Çıktı : neon_zirh.bbmodel, neon_ekstra.png, neon_skin_e.png, neon_ekstra_e.png, preview.png

Figura, adı "_e" ile biten dokuyu aynı adlı dokunun emissive (karanlıkta parlayan) katmanı olarak kullanır.
Koordinatlar Blockbench/Figura düzeninde: ayaklar y=0, karakter KUZEYE (-Z) bakar, karakterin sağı +X.
"""
import base64, io, json, math, os, uuid
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SKIN = Image.open(os.path.join(HERE, "neon_skin.png")).convert("RGBA")
EXTRA = Image.new("RGBA", (64, 64), (0, 0, 0, 0)); EX = EXTRA.load()
EXTRA_E = Image.new("RGBA", (64, 64), (0, 0, 0, 0)); EXE = EXTRA_E.load()

# ---------------------------------------------------------------- neon gradyanı (skin ile aynı)
STOPS = [(255, 150, 40), (255, 70, 60), (245, 50, 150), (170, 40, 210), (70, 20, 120)]
DARK = (26, 12, 40)


def grad(gx, gy):
    t = max(0, min(1, 0.6 * gx / 15 + 0.4 * gy / 31))
    s = t * (len(STOPS) - 1); i = min(int(s), len(STOPS) - 2); f = s - i
    return tuple(int(STOPS[i][k] * (1 - f) + STOPS[i + 1][k] * f) for k in range(3))


def mix(a, b, f):
    return tuple(int(a[k] * (1 - f) + b[k] * f) for k in range(3))


def bright(c, f):
    return mix(c, (255, 255, 255), f)


def world_grad(X, Y):
    """Model koordinatından gradyan rengi (önden bakınca ekran x = 8 - X, y = 32 - Y)."""
    return grad(8 - X, 32 - Y)


def box_faces(u, v, w, h, d):
    return {"top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d), "right": (u, v + d, d, h),
            "front": (u + d, v + d, w, h), "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h)}


# ================================================================ EKSTRA DOKU
TEX = {   # ad: ((u, v), (w, h, d))
    "horn_base": ((0, 0), (2, 2, 2)),
    "horn_tip":  ((8, 0), (1, 3, 1)),
    "visor":     ((12, 0), (7, 1, 1)),
    "crest":     ((28, 0), (1, 2, 6)),
    "pauldron":  ((0, 8), (5, 3, 6)),
    "pauldron2": ((22, 8), (2, 2, 5)),
    "core":      ((36, 8), (3, 4, 1)),
    "core_frame": ((44, 8), (5, 6, 1)),
    "fin_c":     ((0, 20), (1, 8, 2)),
    "fin_s":     ((6, 20), (1, 5, 1)),
    "belt":      ((10, 20), (8, 1, 4)),
    "gauntlet":  ((34, 20), (4, 5, 4)),
    "knee":      ((50, 20), (3, 3, 1)),
    "boot":      ((0, 32), (4, 3, 4)),
}


def paint_armor(name, at, rows=("top",), edges=False):
    """Koyu zırh plakası. rows: yan yüzlerde parlayan şerit ('top' üst kenar, 'bottom' alt kenar).
    edges=True ise tüm kenarlar parlar (çerçeve gibi). at = parçanın dünya konumu (X, Y)."""
    (u, v), (w, h, d) = TEX[name]
    g = world_grad(*at)
    for k, (x, y, fw, fh) in box_faces(u, v, w, h, d).items():
        side = k in ("front", "back", "right", "left")
        for i in range(fw):
            for j in range(fh):
                if edges:
                    glow = (i in (0, fw - 1) or j in (0, fh - 1)) and fw > 1 and fh > 1
                else:
                    glow = side and (("top" in rows and j == 0) or ("bottom" in rows and j == fh - 1))
                c = bright(g, 0.3) if glow else mix(DARK, g, 0.14 + 0.08 * (j / max(1, fh - 1)))
                EX[x + i, y + j] = c + (255,)
                if glow:
                    EXE[x + i, y + j] = c + (255,)


def paint_crystal(name, at):
    """Tamamı parlayan enerji kristali."""
    (u, v), (w, h, d) = TEX[name]
    g = world_grad(*at)
    for k, (x, y, fw, fh) in box_faces(u, v, w, h, d).items():
        for i in range(fw):
            for j in range(fh):
                c = bright(g, 0.55 if (i + j) % 3 == 0 else 0.25)
                EX[x + i, y + j] = c + (255,); EXE[x + i, y + j] = c + (255,)


paint_armor("horn_base", (4.5, 32), rows=("top",))
paint_crystal("horn_tip", (5, 35))
paint_crystal("visor", (0, 27.5))
paint_armor("crest", (0, 33), rows=("top",))
paint_armor("pauldron", (6, 23), rows=("bottom",))
paint_armor("pauldron2", (8, 21), rows=("bottom",))
paint_crystal("core", (0, 18.5))
paint_armor("core_frame", (0, 18.5), edges=True)
paint_crystal("fin_c", (0, 18))
paint_crystal("fin_s", (2, 18))
paint_armor("belt", (0, 12.5), rows=())
paint_armor("gauntlet", (6, 14), rows=("top", "bottom"))
paint_armor("knee", (2, 7.5), rows=("top",))
paint_armor("boot", (2, 1.5), rows=("top",))
# kemer tokası: ön yüz ortası parlak
(u, v), (w, h, d) = TEX["belt"]
bx, by = u + d, v + d
for i in (3, 4):
    c = bright(world_grad(0, 12.5), 0.5); EX[bx + i, by] = c + (255,); EXE[bx + i, by] = c + (255,)

# ---------------------------------------------------------------- skin'in emissive katmanı
SKIN_E = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
sp, sep = SKIN.load(), SKIN_E.load()
for i in range(64):
    for j in range(64):
        r, g_, b, a = sp[i, j]
        if a and max(r, g_, b) >= 150:   # parlak neon pikseller (çatlaklar, çekirdek, gözler)
            sep[i, j] = (r, g_, b, 255)

EXTRA.save(os.path.join(HERE, "neon_ekstra.png"))
EXTRA_E.save(os.path.join(HERE, "neon_ekstra_e.png"))
SKIN_E.save(os.path.join(HERE, "neon_skin_e.png"))


# ================================================================ MODEL
def uid():
    return str(uuid.uuid4())


def box_uv(u, v, w, h, d):
    return {"north": [u + d, v + d, u + d + w, v + d + h], "east": [u, v + d, u + d, v + d + h],
            "south": [u + 2 * d + w, v + d, u + 2 * d + 2 * w, v + d + h], "west": [u + d + w, v + d, u + 2 * d + w, v + d + h],
            "up": [u + d + w, v + d, u + d, v], "down": [u + d + 2 * w, v, u + d + w, v + d]}


GROUPS, ELEMENTS = {}, []


def group(name, origin):
    GROUPS[name] = {"origin": list(origin), "children": []}


def cube(grp, name, frm, to, uv, dims, tex, inflate=0.0, skip=()):
    faces = {k: ({"uv": v, "texture": tex} if k not in skip else {"uv": [0, 0, 0, 0], "texture": None})
             for k, v in box_uv(*uv, *dims).items()}
    el = {"name": name, "type": "cube", "box_uv": False, "rescale": False, "locked": False, "from": list(frm),
          "to": list(to), "autouv": 0, "color": 0, "inflate": inflate, "origin": GROUPS[grp]["origin"],
          "faces": faces, "uuid": uid()}
    ELEMENTS.append(el); GROUPS[grp]["children"].append(el)


S, X = 0, 1
group("Head", (0, 24, 0)); group("Body", (0, 24, 0))
group("RightArm", (5, 22, 0)); group("LeftArm", (-5, 22, 0))
group("RightLeg", (1.9, 12, 0)); group("LeftLeg", (-1.9, 12, 0))

# 1. ve 2. katman (klasik kollar: 4 px)
cube("Head", "kafa", (-4, 24, -4), (4, 32, 4), (0, 0), (8, 8, 8), S)
cube("Head", "kafa_2", (-4, 24, -4), (4, 32, 4), (32, 0), (8, 8, 8), S, 0.5)
cube("Body", "govde", (-4, 12, -2), (4, 24, 2), (16, 16), (8, 12, 4), S)
cube("Body", "govde_2", (-4, 12, -2), (4, 24, 2), (16, 32), (8, 12, 4), S, 0.25)
cube("RightArm", "sag_kol", (4, 12, -2), (8, 24, 2), (40, 16), (4, 12, 4), S)
cube("RightArm", "sag_kol_2", (4, 12, -2), (8, 24, 2), (40, 32), (4, 12, 4), S, 0.25)
cube("LeftArm", "sol_kol", (-8, 12, -2), (-4, 24, 2), (32, 48), (4, 12, 4), S)
cube("LeftArm", "sol_kol_2", (-8, 12, -2), (-4, 24, 2), (48, 48), (4, 12, 4), S, 0.25)
cube("RightLeg", "sag_bacak", (0, 0, -2), (4, 12, 2), (0, 16), (4, 12, 4), S)
cube("RightLeg", "sag_bacak_2", (0, 0, -2), (4, 12, 2), (0, 32), (4, 12, 4), S, 0.25)
cube("LeftLeg", "sol_bacak", (-4, 0, -2), (0, 12, 2), (16, 48), (4, 12, 4), S)
cube("LeftLeg", "sol_bacak_2", (-4, 0, -2), (0, 12, 2), (0, 48), (4, 12, 4), S, 0.25)

T = lambda n: (TEX[n][0], TEX[n][1])
# --- kask: boynuzlar, ibik, parlayan vizör
for sgn, k in ((1, "sag"), (-1, "sol")):
    xs = sorted((sgn * 3.2, sgn * 5.2))
    cube("Head", f"boynuz_{k}", (xs[0], 31.2, -1), (xs[1], 33.2, 1), *T("horn_base"), X)
    xt = sorted((sgn * 4.4, sgn * 5.4))
    cube("Head", f"boynuz_uc_{k}", (xt[0], 33.2, -0.5), (xt[1], 36.2, 0.5), *T("horn_tip"), X)
cube("Head", "ibik", (-0.5, 32.4, -3), (0.5, 34.4, 3), *T("crest"), X)
cube("Head", "vizor", (-3.5, 27, -4.9), (3.5, 28, -4.45), *T("visor"), X)
# --- gövde: enerji çekirdeği + çerçeve, sırtta kristal yüzgeçler, kemer
cube("Body", "cekirdek_cerceve", (-2.5, 15.5, -2.85), (2.5, 21.5, -2.35), *T("core_frame"), X)
cube("Body", "cekirdek", (-1.5, 16.5, -3.3), (1.5, 20.5, -2.5), *T("core"), X)
cube("Body", "yuzgec_orta", (-0.5, 14, 2.3), (0.5, 22, 4.3), *T("fin_c"), X)
cube("Body", "yuzgec_sag", (1.5, 15.5, 2.3), (2.5, 20.5, 3.6), *T("fin_s"), X)
cube("Body", "yuzgec_sol", (-2.5, 15.5, 2.3), (-1.5, 20.5, 3.6), *T("fin_s"), X)
cube("Body", "kemer", (-4, 12, -2), (4, 13.2, 2), *T("belt"), X, 0.5, skip=("up", "down"))
# --- kollar: iki katlı omuzluk + eldiven
for grp, sgn, k in (("RightArm", 1, "sag"), ("LeftArm", -1, "sol")):
    a = sorted((sgn * 3.6, sgn * 8.9)); cube(grp, f"omuzluk_{k}", (a[0], 21.6, -2.9), (a[1], 24.7, 2.9), *T("pauldron"), X)
    b = sorted((sgn * 7.2, sgn * 9.3)); cube(grp, f"omuzluk2_{k}", (b[0], 19.8, -2.6), (b[1], 21.8, 2.6), *T("pauldron2"), X)
    c = sorted((sgn * 4, sgn * 8)); cube(grp, f"eldiven_{k}", (c[0], 12, -2), (c[1], 17, 2), *T("gauntlet"), X, 0.5, skip=("down",))
# --- bacaklar: dizlik + çizme zırhı
for grp, sgn, k in (("RightLeg", 1, "sag"), ("LeftLeg", -1, "sol")):
    a = sorted((sgn * 0.3, sgn * 3.7)); cube(grp, f"dizlik_{k}", (a[0], 6, -2.9), (a[1], 9, -2.3), *T("knee"), X)
    b = sorted((0, sgn * 4)); cube(grp, f"cizme_{k}", (b[0], 0, -2), (b[1], 3, 2), *T("boot"), X, 0.4, skip=("up",))


# ================================================================ .bbmodel
def png_b64(im):
    buf = io.BytesIO(); im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


TEXLIST = [("neon_skin.png", SKIN), ("neon_ekstra.png", EXTRA), ("neon_skin_e.png", SKIN_E), ("neon_ekstra_e.png", EXTRA_E)]
textures = [{"path": "", "name": n, "folder": "", "namespace": "", "id": str(i), "width": 64, "height": 64,
             "uv_width": 64, "uv_height": 64, "particle": False, "render_mode": "default", "render_sides": "auto",
             "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False,
             "visible": True, "internal": True, "saved": True, "uuid": uid(), "relative_path": n, "source": png_b64(im)}
            for i, (n, im) in enumerate(TEXLIST)]
outliner = [{"name": n, "origin": g["origin"], "color": 0, "uuid": uid(), "export": True, "mirror_uv": False,
             "isOpen": True, "locked": False, "visibility": True, "autouv": 0,
             "children": [c["uuid"] for c in g["children"]]} for n, g in GROUPS.items()]
bb = {"meta": {"format_version": "4.5", "model_format": "free", "box_uv": False}, "name": "neon_zirh",
      "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "", "variable_placeholder_buttons": [],
      "timeline_setups": [], "unhandled_root_fields": {}, "resolution": {"width": 64, "height": 64},
      "elements": ELEMENTS, "outliner": outliner, "textures": textures}
with open(os.path.join(HERE, "neon_zirh.bbmodel"), "w") as fp:
    json.dump(bb, fp, indent=1)

# ---------------------------------------------------------------- kontroller
for n, im in TEXLIST:
    assert im.size == (64, 64) and im.mode == "RGBA", n
    assert all(im.getpixel((i, j))[3] in (0, 255) for i in range(64) for j in range(64)), n
for el in ELEMENTS:
    for k, fc in el["faces"].items():
        if fc["texture"] is not None:
            a, b, c, d = fc["uv"]
            assert 0 <= min(a, c) and max(a, c) <= 64 and 0 <= min(b, d) and max(b, d) <= 64, (el["name"], k)
print(f"{len(ELEMENTS)} küp, {len(GROUPS)} grup -> neon_zirh.bbmodel")


# ================================================================ önizleme
PIX = {S: SKIN.load(), X: EX}
EPIX = {S: SKIN_E.load(), X: EXE}
NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}


def face_quads(el, only_vanilla):
    if only_vanilla and el["faces"]["north"].get("texture") == X:
        return
    e = el["inflate"]
    x0, y0, z0 = (c - e for c in el["from"]); x1, y1, z1 = (c + e for c in el["to"])
    L = lambda a, b, t: a + (b - a) * t
    geo = {"north": lambda s, t: (L(x1, x0, s), L(y1, y0, t), z0), "south": lambda s, t: (L(x0, x1, s), L(y1, y0, t), z1),
           "east": lambda s, t: (x1, L(y1, y0, t), L(z1, z0, s)), "west": lambda s, t: (x0, L(y1, y0, t), L(z0, z1, s)),
           "up": lambda s, t: (L(x0, x1, s), y1, L(z0, z1, t)), "down": lambda s, t: (L(x0, x1, s), y0, L(z1, z0, t))}
    for k, fc in el["faces"].items():
        if fc["texture"] is None:
            continue
        a, b, c, d = fc["uv"]; nu, nv = abs(c - a), abs(d - b)
        for p in range(nu):
            for q in range(nv):
                tx = math.floor(a + (p + .5) / nu * (c - a)); ty = math.floor(b + (q + .5) / nv * (d - b))
                col = PIX[fc["texture"]][tx, ty]
                if col[3] == 0:
                    continue
                glow = EPIX[fc["texture"]][tx, ty][3] > 0
                g = geo[k]
                yield k, [g(p / nu, q / nv), g((p + 1) / nu, q / nv), g((p + 1) / nu, (q + 1) / nv), g(p / nu, (q + 1) / nv)], col[:3], glow


def render(yaw, only_vanilla=False, night=False, size=(280, 420), sc=10, pitch=-10):
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, spn = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    def tr(p):
        x, y, z = -p[0], -(p[1] - 17), -p[2]
        x, z = x * cy + z * sy, -x * sy + z * cy
        return x, y * cp - z * spn, y * spn + z * cp
    light = {"north": 1.0, "south": 0.8, "east": 0.9, "west": 0.86, "up": 1.06, "down": 0.65}
    items = []
    for el in ELEMENTS:
        for k, pts, col, glow in face_quads(el, only_vanilla):
            if tr(NORMAL[k])[2] - tr((0, 0, 0))[2] <= 0.01:
                continue
            P = [tr(p) for p in pts]
            f = 1.0 if (night and glow) else (0.22 if night else light[k])
            items.append((sum(q[2] for q in P) / 4, [(size[0] / 2 + q[0] * sc, size[1] / 2 + q[1] * sc) for q in P],
                          tuple(min(255, round(v * f)) for v in col)))
    im = Image.new("RGB", size, (8, 6, 14) if night else (232, 230, 238)); dr = ImageDraw.Draw(im)
    for _, poly, col in sorted(items, key=lambda t: t[0]):
        dr.polygon(poly, fill=col)
    return im


def font(sz):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", sz)
    except OSError:
        return ImageFont.load_default()


views = [(-30, "Ön (3/4)"), (0, "Ön"), (90, "Yan"), (180, "Arka"), (150, "Arka (3/4)")]
rows = [("Figura", {}), ("Figura\nkaranlıkta", {"night": True}), ("Normal skin\n(2 katman)", {"only_vanilla": True})]
pv = Image.new("RGB", (150 + 280 * len(views), 30 + 420 * len(rows)), (40, 40, 50)); d = ImageDraw.Draw(pv)
for c, (yaw, label) in enumerate(views):
    d.text((150 + c * 280 + 140, 15), label, fill=(235, 235, 240), font=font(16), anchor="mm")
    for r, (_, kw) in enumerate(rows):
        pv.paste(render(yaw, **kw), (150 + c * 280, 30 + r * 420))
for r, (label, _) in enumerate(rows):
    d.text((75, 30 + r * 420 + 210), label, fill=(235, 235, 240), font=font(15), anchor="mm", align="center")
pv.save(os.path.join(HERE, "preview.png"))
print("preview.png yazıldı")
