#!/usr/bin/env python3
"""Nebula cursor pack generator.

Draws every cursor procedurally with Pillow and writes:
  dist/windows/<Variant>/*.cur, *.ani + install.inf
  dist/linux/<Variant>/cursors/* + index.theme   (Xcursor format)
  dist/preview.png

Usage: python3 build.py
Requires: Pillow
"""
import math
import os
import shutil
import struct
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(HERE, "dist")

U = 32            # design grid: 32 x 32 units
S = 16            # supersampling: px per unit
CANVAS = U * S    # 512 px working canvas

WIN_SIZES = [32, 48, 64, 96, 128]
X11_SIZES = [24, 32, 48, 64, 96]

VARIANTS = {
    "Nebula Dark": {
        "top": (52, 58, 82), "bottom": (16, 18, 28),
        "outline": (255, 255, 255), "accent": (34, 211, 238),
        "accent2": (168, 85, 247), "danger": (244, 63, 94),
        "glyph": (255, 255, 255),
    },
    "Nebula Light": {
        "top": (255, 255, 255), "bottom": (226, 230, 240),
        "outline": (17, 20, 32), "accent": (8, 145, 178),
        "accent2": (124, 58, 237), "danger": (225, 29, 72),
        "glyph": (255, 255, 255),
    },
}

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# ---------------------------------------------------------------- helpers
def p(pts, dx=0.0, dy=0.0, k=1.0):
    """design units -> canvas px"""
    return [((x * k + dx) * S, (y * k + dy) * S) for x, y in pts]


def new_mask():
    return Image.new("L", (CANVAS, CANVAS), 0)


def poly_mask(pts, dx=0.0, dy=0.0, k=1.0):
    m = new_mask()
    ImageDraw.Draw(m).polygon(p(pts, dx, dy, k), fill=255)
    return m


def dilate(mask, units):
    """round dilation via blur + threshold"""
    r = units * S
    b = mask.filter(ImageFilter.GaussianBlur(r * 0.55))
    return b.point(lambda v: 255 if v > 18 else int(v * 255 / 18))


def union(*ms):
    out = ms[0]
    for m in ms[1:]:
        out = ImageChops.lighter(out, m)
    return out


def subtract(a, b):
    return ImageChops.subtract(a, b)


def solid(color, mask):
    img = Image.new("RGBA", (CANVAS, CANVAS), color + (255,))
    img.putalpha(mask)
    return img


def gradient(top, bottom, mask):
    g = Image.new("RGBA", (1, CANVAS))
    for y in range(CANVAS):
        t = y / (CANVAS - 1)
        g.putpixel((0, y), tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,))
    g = g.resize((CANVAS, CANVAS))
    g.putalpha(mask)
    return g


class Cursor:
    """Layered drawing: body masks get outline + shadow automatically."""

    def __init__(self, theme):
        self.t = theme
        self.layers = []   # (mask, kind, color)

    def body(self, mask, kind="grad", color=None, stroke=1.35):
        self.layers.append((mask, kind, color, stroke))
        return self

    def render(self):
        t = self.t
        out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
        outlines = [dilate(m, s) if s else m for m, _, _, s in self.layers]
        # shadow from union of everything
        sh = union(*outlines).filter(ImageFilter.GaussianBlur(1.1 * S))
        shifted = new_mask()
        shifted.paste(sh, (int(0.6 * S), int(1.1 * S)))
        sh = shifted.point(lambda v: int(v * 0.42))
        out.alpha_composite(solid((0, 0, 0), sh))
        for (m, kind, color, s), o in zip(self.layers, outlines):
            if s:
                out.alpha_composite(solid(t["outline"], o))
            if kind == "grad":
                out.alpha_composite(gradient(t["top"], t["bottom"], m))
            else:
                out.alpha_composite(solid(color, m))
        return out


# ---------------------------------------------------------------- shapes
ARROW = [(0, 0), (0, 18), (4.3, 14.2), (7.4, 21.2), (10.2, 20), (7.2, 13.2), (12.8, 13.2)]


def arrow_mask(dx=3.0, dy=2.0, k=1.0):
    return poly_mask(ARROW, dx, dy, k)


def double_arrow(angle=0.0, shaft=1.9, head=6.2, length=12.5):
    c = 16
    h = shaft / 2
    pts = [(c, c - length), (c + head, c - length + head), (c + h, c - length + head),
           (c + h, c + length - head), (c + head, c + length - head), (c, c + length),
           (c - head, c + length - head), (c - h, c + length - head),
           (c - h, c - length + head), (c - head, c - length + head)]
    m = poly_mask(pts)
    if angle:
        m = m.rotate(angle, resample=Image.BICUBIC, center=(c * S, c * S))
    return m


def ring(cx, cy, r_out, r_in):
    m = new_mask()
    d = ImageDraw.Draw(m)
    d.ellipse([(cx - r_out) * S, (cy - r_out) * S, (cx + r_out) * S, (cy + r_out) * S], fill=255)
    d.ellipse([(cx - r_in) * S, (cy - r_in) * S, (cx + r_in) * S, (cy + r_in) * S], fill=0)
    return m


def disc(cx, cy, r):
    m = new_mask()
    ImageDraw.Draw(m).ellipse([(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S], fill=255)
    return m


def arc_mask(cx, cy, r, width, start, extent):
    m = new_mask()
    box = [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S]
    ImageDraw.Draw(m).arc(box, start, start + extent, fill=255, width=int(width * S))
    # round caps
    d = ImageDraw.Draw(m)
    rr = r - width / 2
    for a in (start, start + extent):
        x = cx + rr * math.cos(math.radians(a))
        y = cy + rr * math.sin(math.radians(a))
        w = width / 2
        d.ellipse([(x - w) * S, (y - w) * S, (x + w) * S, (y + w) * S], fill=255)
    return m


def rrect(x0, y0, x1, y1, r):
    m = new_mask()
    ImageDraw.Draw(m).rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S, fill=255)
    return m


def text_mask(ch, cx, cy, size):
    m = new_mask()
    f = ImageFont.truetype(FONT_PATH, int(size * S))
    ImageDraw.Draw(m).text((cx * S, cy * S), ch, font=f, fill=255, anchor="mm")
    return m


def hand_mask():
    parts = [
        rrect(10.2, 1.5, 14.6, 17, 2.2),        # index finger
        rrect(14.4, 9.2, 18.6, 18, 2.1),        # middle
        rrect(18.4, 10.4, 22.4, 18.5, 2.0),     # ring
        rrect(22.2, 12.2, 25.8, 19, 1.8),       # little
        rrect(10.2, 13.5, 25.8, 26.5, 4.2),     # palm
        rrect(13.2, 24, 23.2, 29.5, 1.2),       # wrist
    ]
    thumb = rrect(6.8, 13, 11.6, 25.5, 2.3).rotate(38, resample=Image.BICUBIC, center=(11.2 * S, 24.5 * S))
    m = union(*parts, thumb)
    # finger separation grooves
    d = ImageDraw.Draw(m)
    for x, y0, y1 in ((14.5, 11.5, 16.4), (18.5, 12.5, 16.9), (22.3, 14, 17.6)):
        d.line([x * S, y0 * S, x * S, y1 * S], fill=0, width=int(0.55 * S))
    return m


def pen_mask():
    # diagonal pencil from bottom-left tip
    body = [(0, 0), (4, -2.3), (24, -2.3), (24, 2.3), (4, 2.3)]
    m = poly_mask([(x + 4, y + 16) for x, y in body])
    m = m.rotate(45, resample=Image.BICUBIC, center=(4 * S, 16 * S))
    return ImageChops.offset(m, int(-1 * S), int(12 * S))


def person_icon(cx, cy):
    head = disc(cx, cy - 3.1, 2.4)
    torso = new_mask()
    ImageDraw.Draw(torso).pieslice([(cx - 4.6) * S, (cy + 0.2) * S, (cx + 4.6) * S, (cy + 9.4) * S],
                                   180, 360, fill=255)
    return union(head, torso)


def pin_icon(cx, cy):
    m = disc(cx, cy - 2, 4.4)
    ImageDraw.Draw(m).polygon(p([(cx - 3.9, cy), (cx + 3.9, cy), (cx, cy + 6.2)]), fill=255)
    hole = disc(cx, cy - 2, 1.6)
    return m, hole


# ---------------------------------------------------------------- cursor set
def build_set(t):
    """returns dict name -> (frames:list[Image], hotspot(units), delay_jiffies)"""
    C = lambda: Cursor(t)
    res = {}

    res["pointer"] = ([C().body(arrow_mask()).render()], (3, 2), 0)

    # help: arrow + ? badge
    img = C().body(arrow_mask(2, 1, 0.92)).body(disc(23, 22.5, 6.2), "solid", t["accent"]) \
        .body(text_mask("?", 23, 22.8, 9), "solid", t["glyph"], stroke=0).render()
    res["help"] = ([img], (2, 1), 0)

    # working in background: arrow + spinning arc
    frames = []
    for i in range(18):
        a = i * 20
        frames.append(C().body(arrow_mask(2, 1, 0.92))
                      .body(disc(23.5, 23, 6.4), "solid", t["bottom"])
                      .body(arc_mask(23.5, 23, 5.3, 2.1, a - 90, 250), "solid", t["accent"], stroke=0)
                      .render())
    res["working"] = (frames, (2, 1), 3)

    # busy: big ring with gradient comet
    frames = []
    for i in range(18):
        a = i * 20
        cur = C().body(ring(16, 16, 11.5, 6.6))
        img = cur.render()
        arc1 = arc_mask(16, 16, 10.9, 3.6, a - 90, 140)
        arc2 = arc_mask(16, 16, 10.9, 3.6, a + 90, 140)
        img.alpha_composite(solid(t["accent"], arc1))
        img.alpha_composite(solid(t["accent2"], arc2))
        frames.append(img)
    res["busy"] = (frames, (16, 16), 3)

    # precision
    m = new_mask()
    d = ImageDraw.Draw(m)
    w = 1.0
    for x0, y0, x1, y1 in ((16 - w, 3, 16 + w, 12.5), (16 - w, 19.5, 16 + w, 29),
                           (3, 16 - w, 12.5, 16 + w), (19.5, 16 - w, 29, 16 + w)):
        d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=w * S, fill=255)
    res["precision"] = ([C().body(m).body(disc(16, 16, 1.2), "solid", t["accent"], stroke=0.9).render()],
                        (16, 16), 0)

    # text select (I-beam)
    m = new_mask()
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([15.2 * S, 6.5 * S, 16.8 * S, 25.5 * S], radius=0.6 * S, fill=255)
    d.rounded_rectangle([11.5 * S, 5 * S, 20.5 * S, 7 * S], radius=1 * S, fill=255)
    d.rounded_rectangle([11.5 * S, 25 * S, 20.5 * S, 27 * S], radius=1 * S, fill=255)
    res["text"] = ([C().body(m).render()], (16, 16), 0)

    # handwriting (pen)
    pm = pen_mask()
    tip = new_mask()
    ImageDraw.Draw(tip).polygon(p([(3, 29), (4.2, 23), (9, 27.8)]), fill=255)
    tip = ImageChops.multiply(tip, pm)
    res["handwriting"] = ([C().body(pm).body(tip, "solid", t["accent"], stroke=0).render()], (3, 29), 0)

    # unavailable
    slash = new_mask()
    ImageDraw.Draw(slash).line([8.5 * S, 8.5 * S, 23.5 * S, 23.5 * S], fill=255, width=int(3.2 * S))
    slash = ImageChops.multiply(slash, disc(16, 16, 10))
    res["unavailable"] = ([C().body(union(ring(16, 16, 11.5, 8), slash), "solid", t["danger"]).render()],
                          (16, 16), 0)

    # resize
    res["vert"] = ([C().body(double_arrow(0)).render()], (16, 16), 0)
    res["horz"] = ([C().body(double_arrow(90)).render()], (16, 16), 0)
    res["dgn1"] = ([C().body(double_arrow(45, length=11.5)).render()], (16, 16), 0)    # NW-SE
    res["dgn2"] = ([C().body(double_arrow(-45, length=11.5)).render()], (16, 16), 0)   # NE-SW
    res["move"] = ([C().body(union(double_arrow(0, head=5), double_arrow(90, head=5)))
                    .body(disc(16, 16, 2), "solid", t["accent"], stroke=0).render()], (16, 16), 0)

    # alternate select (up arrow)
    up = [(16, 2), (25, 13), (19.3, 13), (19.3, 29), (12.7, 29), (12.7, 13), (7, 13)]
    res["alternate"] = ([C().body(poly_mask(up)).render()], (16, 2), 0)

    # link (hand)
    res["link"] = ([C().body(hand_mask()).render()], (12.4, 1.5), 0)

    # location select
    pin, hole = pin_icon(23.5, 21)
    img = C().body(arrow_mask(2, 1, 0.92)).body(subtract(pin, hole), "solid", t["accent"]).render()
    res["pin"] = ([img], (2, 1), 0)

    # person select
    img = C().body(arrow_mask(2, 1, 0.92)).body(disc(23.5, 23, 7), "solid", t["accent2"]) \
        .body(ImageChops.multiply(person_icon(23.5, 22.4), disc(23.5, 23, 6.3)),
              "solid", t["glyph"], stroke=0).render()
    res["person"] = ([img], (2, 1), 0)
    return res


# ---------------------------------------------------------------- encoders
def downscale(img, size):
    return img.convert("RGBa").resize((size, size), Image.LANCZOS).convert("RGBA")


def dib(img):
    w, h = img.size
    px = img.tobytes("raw", "BGRA")
    rows = [px[y * w * 4:(y + 1) * w * 4] for y in range(h)]
    xor = b"".join(reversed(rows))
    stride = ((w + 31) // 32) * 4
    alpha = img.getchannel("A")
    and_rows = []
    for y in range(h - 1, -1, -1):
        bits = bytearray(stride)
        for x in range(w):
            if alpha.getpixel((x, y)) == 0:
                bits[x // 8] |= 0x80 >> (x % 8)
        and_rows.append(bytes(bits))
    hdr = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0, len(xor) + stride * h, 0, 0, 0, 0)
    return hdr + xor + b"".join(and_rows)


def cur_bytes(master, hot, sizes):
    entries, blobs = [], []
    off = 6 + 16 * len(sizes)
    for s in sizes:
        im = downscale(master, s)
        if s >= 64:   # PNG-compressed entries (Windows Vista+) keep files small
            import io
            buf = io.BytesIO()
            im.save(buf, "PNG", optimize=True)
            data = buf.getvalue()
        else:
            data = dib(im)
        hx = min(s - 1, round(hot[0] * s / U))
        hy = min(s - 1, round(hot[1] * s / U))
        entries.append(struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, hx, hy, len(data), off))
        blobs.append(data)
        off += len(data)
    return struct.pack("<HHH", 0, 2, len(sizes)) + b"".join(entries) + b"".join(blobs)


def chunk(cid, data):
    pad = b"\0" if len(data) % 2 else b""
    return cid + struct.pack("<I", len(data)) + data + pad


def ani_bytes(frames, hot, sizes, rate, title):
    icons = b"".join(chunk(b"icon", cur_bytes(f, hot, sizes)) for f in frames)
    anih = struct.pack("<9I", 36, len(frames), len(frames), 0, 0, 0, 0, rate, 1)
    info = b"LIST" + struct.pack("<I", 4 + len(chunk(b"INAM", title.encode() + b"\0"))) + b"INFO" + \
        chunk(b"INAM", title.encode() + b"\0")
    body = b"ACON" + info + chunk(b"anih", anih) + b"LIST" + struct.pack("<I", 4 + len(icons)) + b"fram" + icons
    return b"RIFF" + struct.pack("<I", len(body)) + body


def xcursor_bytes(frames, hot, sizes, rate):
    images = []
    delay_ms = max(1, round(rate * 1000 / 60)) if len(frames) > 1 else 0
    for s in sizes:
        for f in frames:
            im = downscale(f, s)
            # Xcursor wants premultiplied ARGB
            pm = im.convert("RGBa").tobytes("raw", "BGRa")
            hx = min(s - 1, round(hot[0] * s / U))
            hy = min(s - 1, round(hot[1] * s / U))
            hdr = struct.pack("<9I", 36, 0xFFFD0002, s, 1, s, s, hx, hy, delay_ms)
            images.append((s, hdr + pm))
    ntoc = len(images)
    pos = 16 + 12 * ntoc
    toc, data = b"", b""
    for s, blob in images:
        toc += struct.pack("<III", 0xFFFD0002, s, pos)
        data += blob
        pos += len(blob)
    return b"Xcur" + struct.pack("<III", 16, 0x10000, ntoc) + toc + data


# ---------------------------------------------------------------- packaging
WIN_ORDER = ["pointer", "help", "working", "busy", "precision", "text", "handwriting", "unavailable",
             "vert", "horz", "dgn1", "dgn2", "move", "alternate", "link", "pin", "person"]

X11_NAMES = {
    "pointer": ["left_ptr", "default", "arrow", "top_left_arrow"],
    "help": ["help", "question_arrow", "whats_this", "left_ptr_help", "5c6cd98b3f3ebcb1f9c7f1c204630408",
             "d9ce0ab605698f320427677b458ad60b"],
    "working": ["progress", "left_ptr_watch", "half-busy", "08e8e1c95fe2fc01f976f1e063a24ccd",
                "3ecb610c1bf2410f44200f48c40d3599"],
    "busy": ["wait", "watch"],
    "precision": ["crosshair", "cross", "tcross", "cross_reverse", "diamond_cross"],
    "text": ["text", "xterm", "ibeam", "vertical-text"],
    "handwriting": ["pencil", "draft"],
    "unavailable": ["not-allowed", "no-drop", "crossed_circle", "circle", "forbidden",
                    "03b6e0fcb3499374a867c041f52298f0"],
    "vert": ["ns-resize", "n-resize", "s-resize", "row-resize", "sb_v_double_arrow", "v_double_arrow",
             "size_ver", "top_side", "bottom_side", "split_v", "00008160000006810000408080010102"],
    "horz": ["ew-resize", "e-resize", "w-resize", "col-resize", "sb_h_double_arrow", "h_double_arrow",
             "size_hor", "left_side", "right_side", "split_h", "028006030e0e7ebffc7f7070c0600140"],
    "dgn1": ["nwse-resize", "nw-resize", "se-resize", "size_fdiag", "bd_double_arrow",
             "top_left_corner", "bottom_right_corner", "c7088f0f3e6c8088236ef8e1e3e70000"],
    "dgn2": ["nesw-resize", "ne-resize", "sw-resize", "size_bdiag", "fd_double_arrow",
             "top_right_corner", "bottom_left_corner", "fcf1c3c7cd4491d801f1e1c78f100000"],
    "move": ["move", "fleur", "size_all", "all-scroll", "grabbing", "4498f0e0c1937ffe01fd06f973665830",
             "9081237383d90e509aa00f00170e968f"],
    "alternate": ["up_arrow", "center_ptr", "sb_up_arrow"],
    "link": ["pointer", "hand", "hand1", "hand2", "pointing_hand", "e29285e634086352946a0e7090d73106",
             "9d800788f1b08800ae810202380a0822"],
    "pin": ["context-menu", "alias", "copy", "dnd-link", "dnd-copy"],
    "person": ["cell"],
}


def write_windows(variant, cset, out):
    os.makedirs(out, exist_ok=True)
    files = {}
    for name in WIN_ORDER:
        frames, hot, rate = cset[name]
        if len(frames) > 1:
            fn = f"{name}.ani"
            data = ani_bytes(frames, hot, WIN_SIZES, rate, f"{variant} {name}")
        else:
            fn = f"{name}.cur"
            data = cur_bytes(frames[0], hot, WIN_SIZES)
        with open(os.path.join(out, fn), "wb") as fh:
            fh.write(data)
        files[name] = fn

    folder = variant.replace(" ", "")
    scheme = ",".join(f"%10%\\%CUR_DIR%\\%{n}%" for n in WIN_ORDER)
    reg_vals = ["Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", "NWPen", "No", "SizeNS",
                "SizeWE", "SizeNWSE", "SizeNESW", "SizeAll", "UpArrow", "Hand", "Pin", "Person"]
    lines = [
        "; " + variant + " cursor scheme - right-click > Install",
        "[Version]", 'signature="$CHICAGO$"', "",
        "[DefaultInstall]", "CopyFiles = Scheme.Cur", "AddReg    = Scheme.Reg, Wreg", "",
        "[DestinationDirs]", 'Scheme.Cur = 10,"%CUR_DIR%"', "",
        "[Scheme.Reg]",
        f'HKCU,"Control Panel\\Cursors\\Schemes","%SCHEME_NAME%",,"{scheme}"', "",
        "[Wreg]",
        'HKCU,"Control Panel\\Cursors",,0x00020000,"%SCHEME_NAME%"',
    ]
    lines += [f'HKCU,"Control Panel\\Cursors",{v},0x00020000,"%10%\\%CUR_DIR%\\%{n}%"'
              for v, n in zip(reg_vals, WIN_ORDER)]
    lines += ['HKLM,"Software\\Microsoft\\Windows\\CurrentVersion\\Runonce\\Setup\\","",,'
              '"rundll32.exe shell32.dll,Control_RunDLL main.cpl @0"', "",
              "[Scheme.Cur]"] + [files[n] for n in WIN_ORDER] + ["", "[Strings]",
              f'CUR_DIR = "Cursors\\{folder}"', f'SCHEME_NAME = "{variant}"']
    lines += [f'{n} = "{files[n]}"' for n in WIN_ORDER]
    with open(os.path.join(out, "install.inf"), "w", newline="\r\n") as fh:
        fh.write("\n".join(lines) + "\n")


def write_linux(variant, cset, out):
    cdir = os.path.join(out, "cursors")
    os.makedirs(cdir, exist_ok=True)
    for name, aliases in X11_NAMES.items():
        frames, hot, rate = cset[name]
        primary = aliases[0]
        with open(os.path.join(cdir, primary), "wb") as fh:
            fh.write(xcursor_bytes(frames, hot, X11_SIZES, rate))
        for a in aliases[1:]:
            link = os.path.join(cdir, a)
            if os.path.lexists(link):
                os.remove(link)
            os.symlink(primary, link)
    with open(os.path.join(out, "index.theme"), "w") as fh:
        fh.write(f"[Icon Theme]\nName={variant}\nComment={variant} cursor theme\nInherits=Adwaita\n")


def write_preview(sets, path):
    order = WIN_ORDER
    cell, pad = 96, 24
    labels_h = 26
    w = pad * 2 + cell * len(order)
    h = pad + (cell + labels_h + pad) * len(sets) + 30
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bgs = [(236, 239, 245), (30, 33, 44)]
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    title_font = ImageFont.truetype(FONT_PATH, 15)
    y = pad
    d = ImageDraw.Draw(img)
    for i, (variant, cset) in enumerate(sets.items()):
        bg = bgs[i % 2]
        fg = (30, 33, 44) if i % 2 == 0 else (230, 233, 240)
        d.rounded_rectangle([8, y - 16, w - 8, y + cell + labels_h + 6], 14, fill=bg + (255,))
        d.text((pad, y - 12), variant, font=title_font, fill=fg)
        for j, name in enumerate(order):
            frames = cset[name][0]
            f = frames[len(frames) // 3]
            ci = downscale(f, 64)
            x = pad + j * cell + (cell - 64) // 2
            img.alpha_composite(ci, (x, y + 14))
            d.text((pad + j * cell + cell // 2, y + cell + 6), name, font=font, fill=fg, anchor="mm")
        y += cell + labels_h + pad + 6
    bg = Image.new("RGBA", img.size, (250, 250, 252, 255))
    bg.alpha_composite(img)
    bg.convert("RGB").save(path)


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    sets = {}
    for variant, theme in VARIANTS.items():
        print("rendering", variant)
        cset = build_set(theme)
        sets[variant] = cset
        folder = variant.replace(" ", "")
        write_windows(variant, cset, os.path.join(DIST, "windows", folder))
        write_linux(variant, cset, os.path.join(DIST, "linux", folder))
    write_preview(sets, os.path.join(DIST, "preview.png"))
    print("done ->", DIST)


if __name__ == "__main__":
    main()
