"""Çeviriyi oyunun görünümüne uydurarak çizer.

Her metin bloğu için ekran görüntüsünden o bölgeyi alır, orijinal yazının
piksellerini bulup çevresindeki arka planla doldurur (geçişli renkler ve dokular
korunur) ve Türkçe metni oyunun kendi yazı renginde çizer. Sonuç, orijinalin tam
üstüne konan küçük bir resimdir.
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .screen import TextBlock

# Yazı tipi seçenekleri: anahtar -> (Windows, macOS, Linux adayları)
FONT_STYLES = {
    "sans-bold": "Kalın (okunaklı)",
    "sans": "Normal",
    "serif": "Tırnaklı / klasik (fantastik ve RPG oyunları)",
    "serif-bold": "Tırnaklı kalın",
}
_FONT_CANDIDATES = {
    "sans-bold": {
        "win32": [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"],
        "darwin": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf"],
        "linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    },
    "sans": {
        "win32": [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"],
        "darwin": ["/System/Library/Fonts/Supplemental/Arial.ttf"],
        "linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    },
    "serif": {
        "win32": [r"C:\Windows\Fonts\georgia.ttf", r"C:\Windows\Fonts\times.ttf"],
        "darwin": ["/System/Library/Fonts/Supplemental/Georgia.ttf"],
        "linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"],
    },
    "serif-bold": {
        "win32": [r"C:\Windows\Fonts\georgiab.ttf", r"C:\Windows\Fonts\timesbd.ttf"],
        "darwin": ["/System/Library/Fonts/Supplemental/Georgia Bold.ttf"],
        "linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
    },
}
font_style = "sans-bold"  # arayüzden değiştirilir


@lru_cache(maxsize=8)
def _font_path(style: str) -> str | None:
    key = "win32" if sys.platform == "win32" else "darwin" if sys.platform == "darwin" else "linux"
    for st in (style, "sans-bold", "sans"):
        for p in _FONT_CANDIDATES.get(st, {}).get(key, []):
            if os.path.isfile(p):
                return p
    return None


@lru_cache(maxsize=256)
def _font_for(style: str, size: int) -> ImageFont.ImageFont:
    path = _font_path(style)
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def _font(size: int) -> ImageFont.ImageFont:
    return _font_for(font_style, size)


# --- görüntü işleme yardımcıları -----------------------------------------

def _box_blur(a: np.ndarray, r: int) -> np.ndarray:
    """Hızlı kutu bulanıklaştırma (2 eksende, kenarlar tekrar edilerek)."""
    if r <= 0:
        return a
    out = a
    for axis in (0, 1):
        pad = [(0, 0)] * out.ndim
        pad[axis] = (r + 1, r)
        p = np.pad(out, pad, mode="edge")
        c = np.cumsum(p, axis=axis, dtype=np.float64)
        n = out.shape[axis]
        hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(c, np.arange(0, n), axis=axis)
        out = (hi - lo) / (2 * r + 1)
    return out


def _smooth(a: np.ndarray, r: int) -> np.ndarray:
    # Üç kez kutu bulanıklaştırma ≈ Gauss bulanıklaştırma
    for _ in range(3):
        a = _box_blur(a, max(1, r // 2))
    return a


def _dilate(mask: np.ndarray, r: int) -> np.ndarray:
    if r <= 0:
        return mask
    m = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(r * 2 + 1))
    return np.asarray(m) > 0


def text_mask(rgb: np.ndarray, line_height: int, return_strong: bool = False):
    """Yazı piksellerini bulur: çevresindeki ortalama renkten belirgin farklı olanlar.

    İki eşik kullanır: belirgin yazı pikselleri ve bunların hemen yakınındaki soluk
    pikseller (parlama/glow, gölge, kenar yumuşatma). Böylece silinen yazının etrafında
    hale kalmaz.
    """
    r = max(3, line_height)
    local = _smooth(rgb, r)
    dist = np.sqrt(((rgb - local) ** 2).sum(axis=2))
    # Eşik, bölgenin kontrastına göre uyarlanır (soluk yazılar da bulunsun)
    thr = max(28.0, float(np.percentile(dist, 70)) * 1.2)
    strong = dist > thr
    # Bölgeyi baştan sona kesen düz çizgiler yazı değil, buton/kutu kenarıdır: silinirse
    # yerine kenarın öbür yanındaki renk taşar.
    h, w = strong.shape
    if w > 8:
        strong[strong.mean(axis=1) > 0.8, :] = False
    if h > 8:
        strong[:, strong.mean(axis=0) > 0.8] = False
    weak = dist > max(10.0, thr * 0.3)
    mask = strong | (weak & _dilate(strong, max(2, line_height // 2)))
    # Kenar yumuşatma piksellerini de kapsamak için maskeyi biraz genişlet
    mask = _dilate(mask, max(1, line_height // 7))
    return (mask, strong) if return_strong else mask


def inpaint(rgb: np.ndarray, mask: np.ndarray, radius: int) -> np.ndarray:
    """Maskelenmiş pikselleri çevredeki arka planla doldurur (normalize evrişim)."""
    w = (~mask).astype(np.float64)
    out = rgb.copy()
    filled = np.zeros_like(w, dtype=bool)
    r = max(2, radius // 3)  # önce en yakın piksellerden doldur
    for _ in range(6):  # büyük yazılarda yarıçapı büyüterek boşlukları kapat
        num = _smooth(rgb * w[..., None], r)
        den = _smooth(w, r)[..., None]
        bg = num / np.maximum(den, 1e-6)
        take = mask & ~filled & (den[..., 0] > 0.05)
        out[take] = bg[take]
        filled |= take
        if filled[mask].all():
            break
        r *= 2
    rest = mask & ~filled
    if rest.any():
        out[rest] = rgb[~mask].mean(axis=0) if (~mask).any() else rgb.mean(axis=(0, 1))
    # Doldurulan alan pürüzsüz kalırsa grenli/dokulu arka planda dikdörtgen gibi seçilir:
    # çevredeki ince dokuyu (gürültü, gren) doldurulan piksellere geri ekle.
    unmasked = ~mask
    if mask.any() and unmasked.sum() > 50:
        residual = (rgb - _box_blur(rgb, 2))[unmasked]
        # Yalnızca sıradan gren: kenar/geçiş pikselleri (buton kenarı vb.) benek yapmasın
        norms = np.linalg.norm(residual, axis=1)
        residual = residual[norms <= np.percentile(norms, 75)]
        rng = np.random.default_rng(mask.shape[0] * 7919 + mask.shape[1])  # her karede aynı
        out[mask] += residual[rng.integers(0, len(residual), int(mask.sum()))]
    return out


def _luminance(c) -> float:
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


def text_colors(rgb: np.ndarray, mask: np.ndarray, bg: np.ndarray):
    """Orijinal yazının rengini ve (varsa) kontur rengini tahmin eder.

    Döner: (yazı rengi, kontur rengi, orijinalde kontur var mı)
    """
    bg_mean = bg.reshape(-1, 3).mean(axis=0)
    has_outline = False
    stroke = None
    if mask.any():
        px = rgb[mask]
        d = np.sqrt(((px - bg_mean) ** 2).sum(axis=1))
        # Yalnızca arka plandan en belirgin ayrışan pikseller (maskenin geri kalanı yazının
        # çevresindeki kenar yumuşatma / arka plan pikselleridir)
        core = px[d >= 0.6 * np.percentile(d, 98)]
        fg = np.median(core, axis=0)
        # Konturlu yazı: yazı pikselleri iki gruba ayrılır (ör. sarı dolgu + siyah kenar)
        lum = px @ np.array([0.299, 0.587, 0.114])
        far_from_bg = np.sqrt(((px - bg_mean) ** 2).sum(axis=1)) > 60
        other = px[(np.abs(lum - _luminance(fg)) > 110) & far_from_bg]
        if len(other) > 0.12 * len(px):
            has_outline = True
            stroke = tuple(int(v) for v in np.median(other, axis=0))
    else:
        fg = np.array([255, 255, 255] if _luminance(bg_mean) < 128 else [0, 0, 0], float)
    # Yazı ile arka plan arasında yeterli kontrast yoksa siyah/beyaz kullan
    if not has_outline and abs(_luminance(fg) - _luminance(bg_mean)) < 60:
        fg = np.array([255, 255, 255] if _luminance(bg_mean) < 128 else [15, 15, 15], float)
    if stroke is None:
        stroke = (0, 0, 0) if _luminance(fg) > 128 else (255, 255, 255)
    return tuple(int(v) for v in fg), stroke, has_outline


# --- metin yerleşimi --------------------------------------------------------

def _wrap(font, text: str, width: int) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = f"{cur} {word}".strip()
            if cur and font.getlength(trial) > width:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        lines.append(cur)
    return lines


def _size_for_glyph_height(original: str, glyph_h: int) -> int:
    """Orijinal metnin harfleri glyph_h piksel yükseklikte olacak yazı boyutu."""
    probe = _font(100)
    letters = [c for c in original if c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        original = "HEXAMN"  # BÜYÜK HARF: büyük harf yüksekliği ("Q" kuyruğu yanıltmasın)
    top, bottom = probe.getbbox(original or "Ag")[1::2]
    ratio = max(0.3, (bottom - top) / 100)
    return int(round(glyph_h / ratio))


def fit_text(text: str, box_w: int, box_h: int, line_height: int, original: str = "",
             min_px: int = 9, no_wrap: bool = False, max_w: float | None = None):
    """Metni kutuya sığdıran yazı boyutunu ve satırlarını bulur.

    Başlangıç boyutu, orijinal yazının ekrandaki harf yüksekliğinden hesaplanır; böylece
    çeviri orijinalle aynı büyüklükte görünür. Sığmazsa küçültülür. no_wrap: menü ve
    buton gibi tek satırlık yazılar bölünmez; en fazla %25 küçültülür, gerekirse taşar.
    """
    start = max(min_px, _size_for_glyph_height(original.split("\n")[0][:80], line_height))
    size = start
    while True:
        font = _font(size)
        lines = [text.replace("\n", " ")] if no_wrap else \
            _wrap(font, text, max(int(box_w * 1.05), 20))
        asc, desc = font.getmetrics()
        lh = asc + desc
        top, bottom = font.getbbox("Ag")[1::2]
        h = lh * (len(lines) - 1) + (bottom - top)
        w = max((font.getlength(l) for l in lines), default=0)
        if no_wrap:
            # Yanlardaki boş yere kadar taşabilir; ancak gerekirse %35'e kadar küçülür
            limit = max_w if max_w is not None else box_w * 1.35
            ok = w <= limit or size <= max(min_px, int(start * 0.65))
        else:
            ok = (h <= box_h * 1.3 and w <= box_w * 1.1) or size <= min_px
        if ok:
            return font, lines, int(w), int(lh * (len(lines) - 1) + bottom), lh
        size -= 1


# --- ana işlev -------------------------------------------------------------

def _measure_glyphs(img, x, y, w, h, line_height):
    """Kutudaki belirgin yazı piksellerinin yüksekliğini ve dikey ortasını bulur."""
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(img.width, x + w), min(img.height, y + h)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return None
    rgb = np.asarray(img.crop((x0, y0, x1, y1)).convert("RGB"), dtype=np.float64)
    local = _smooth(rgb, max(3, line_height))
    dist = np.sqrt(((rgb - local) ** 2).sum(axis=2))
    thr = max(28.0, float(np.percentile(dist, 70)) * 1.2)
    # Yalnızca yazının çekirdeği (parlama ve gölge daha soluktur, ölçüme girmesin)
    counts = (dist > thr * 1.6).sum(axis=1)
    on = counts > max(2, counts.max() * 0.08)
    # Yazı, kesintisiz bir satır grubudur; boşlukla ayrılmış ışık parçacıkları, gölge
    # vb. ayrı gruplar oluşturur. En çok yazı pikseli içeren grubu seç.
    groups, start, gap = [], None, 0
    for i, v in enumerate(on):
        if v:
            if start is None:
                start = i
            gap, end = 0, i
        elif start is not None:
            gap += 1
            if gap > 2:
                groups.append((start, end))
                start, gap = None, 0
    if start is not None:
        groups.append((start, end))
    if not groups:
        return None
    r0, r1 = max(groups, key=lambda g: counts[g[0]:g[1] + 1].sum())
    if r1 - r0 < 2:
        return None
    rows = np.array([r0, r1])
    gh = int(r1 - r0 + 1)
    if gh < line_height * 0.4:  # ölçüm şüpheli: OCR değerini kullan
        return None
    return min(gh, line_height), y0 + (rows[0] + rows[-1]) / 2


def render_block(img: Image.Image, b: TextBlock, offset: tuple[int, int]) -> None:
    """Bloğun çeviri resmini (b.patch) ve ekrandaki yerini (b.px, b.py) hazırlar."""
    ox, oy = offset
    text = b.translated or b.text
    # Tek satırlık kısa yazı (menü, buton, başlık) mı, yoksa paragraf mı?
    label = b.h < b.line_height * 1.6 and len(b.text) <= 40
    bx, by = b.x - ox, b.y - oy  # görüntü koordinatlarında orijinal kutu
    glyph_h, glyph_cy = b.line_height, by + b.h / 2
    if label:
        # Parlama/gölge OCR kutusunu şişirir: harf yüksekliğini ve dikey ortayı gerçek
        # yazı piksellerinden ölç (yoksa çeviri olduğundan büyük ve kaymış çıkar)
        measured = _measure_glyphs(img, bx, by, b.w, b.h, b.line_height)
        if measured:
            glyph_h, glyph_cy = measured
    font, lines, tw, th, lh = fit_text(text, b.w, b.h, glyph_h, b.text, no_wrap=label,
                                       max_w=getattr(b, "room_w", None))

    g = max(3, glyph_h // 2)   # parlama/gölge payı: orijinalin bu kadar dışı da temizlenir
    feather = max(2, glyph_h // 5)  # kenarda ekrana yumuşak geçiş
    m = g + feather
    align = getattr(b, "align", "center") if label else "left"
    if label and align == "center":
        # Orijinalin merkezine hizala (ortalanmış menülerde kayma olmasın)
        cx = bx + b.w / 2
        half = max(b.w, tw) / 2 + m
        x0, x1 = int(cx - half), int(cx + half)
    elif label and align == "right":
        x0, x1 = bx + b.w - max(b.w, tw) - m, bx + b.w + m
    else:
        x0, x1 = bx - m, bx + max(b.w, tw) + m
    y0, y1 = by - m, by + max(b.h, th) + m
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(img.width, x1), min(img.height, y1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        b.patch = None
        return
    crop = np.asarray(img.crop((x0, y0, x1, y1)).convert("RGB"), dtype=np.float64)

    # Yazı piksellerini yalnızca orijinal kutu (+ parlama payı) içinde ara
    mask = np.zeros(crop.shape[:2], bool)
    ry0, rx0 = max(0, by - g - y0), max(0, bx - g - x0)
    ry1, rx1 = by + b.h + g - y0, bx + b.w + g - x0
    region = (slice(ry0, max(ry0, ry1)), slice(rx0, max(rx0, rx1)))
    sub = crop[region]
    strong = np.zeros(crop.shape[:2], bool)
    if sub.size:
        mask[region], strong[region] = text_mask(sub, b.line_height, return_strong=True)
    # Resim komşu bir yazının üstüne taşıyorsa o yazıyı da temizle (yoksa iki çeviri
    # resminin kesiştiği yerde eski yazının parçası / parlaması görünür)
    for o in getattr(b, "neighbors", ()):
        oy0, ox0 = max(0, o.y - oy - g - y0), max(0, o.x - ox - g - x0)
        oy1, ox1 = min(mask.shape[0], o.y - oy + o.h + g - y0), min(mask.shape[1], o.x - ox + o.w + g - x0)
        if oy1 - oy0 > 2 and ox1 - ox0 > 2:
            nreg = (slice(oy0, oy1), slice(ox0, ox1))
            mask[nreg] |= text_mask(crop[nreg], o.line_height)

    clean = inpaint(crop, mask, b.line_height)
    fg, stroke, outlined = text_colors(crop, mask, clean[~mask] if (~mask).any() else clean)

    # Kenarlarda orijinal ekrana yumuşak geçiş: kutunun sınırı seçilmesin
    hh, ww = crop.shape[:2]
    ey = np.minimum(np.arange(hh), np.arange(hh)[::-1])[:, None]
    ex = np.minimum(np.arange(ww), np.arange(ww)[::-1])[None, :]
    alpha = np.clip(np.minimum(ey, ex) / feather, 0, 1)[..., None]
    clean = clean * alpha + crop * (1 - alpha)

    # Orijinal yazı parlıyor muydu (glow)? Yazının hemen çevresi, arka plana göre
    # yazı rengine doğru açılmışsa evet: çeviriye de benzer parlama verilir.
    glow = 0.0
    if strong.any():
        ring = _dilate(strong, max(2, glyph_h // 4)) & ~_dilate(strong, 1)
        if ring.any():
            bgc = clean[ring]
            contrast = np.linalg.norm(np.array(fg, float) - bgc.mean(axis=0)) or 1.0
            lift = ((crop[ring] - bgc) * (np.array(fg, float) - bgc.mean(axis=0))).sum(axis=1)
            glow = float(np.clip(np.median(lift) / contrast ** 2, 0, 1))

    # Orijinalde kontur varsa ya da arka plan karmaşıksa (doku, resim) kontur çiz
    # (karmaşıklık yalnızca yazının hemen arkasında ölçülür: butonun dışı sayılmaz)
    behind = clean[region] if clean[region].size else clean
    busy = float(behind.reshape(-1, 3).std(axis=0).mean()) > 22
    stroke_w = max(1, b.line_height // 12) if outlined else (1 if busy else 0)
    patch = Image.fromarray(np.clip(clean, 0, 255).astype(np.uint8))
    top = font.getbbox("Ag")[1]
    # Dikeyde: orijinal yazının ortasına
    ty = int(glyph_cy - y0 - (th - top) / 2 - top)
    def line_x(line):
        if align == "center":
            return (ww - font.getlength(line)) / 2
        if align == "right":
            return bx + b.w - x0 - font.getlength(line)
        return bx - x0
    positions = [(int(line_x(l)), ty + i * lh) for i, l in enumerate(lines)]
    if glow > 0.03:  # ölçümde parlamasız yazılar 0.0, parlayanlar 0.05-0.07 çıktı
        layer = Image.new("L", patch.size, 0)
        dl = ImageDraw.Draw(layer)
        for (tx, tyy), line in zip(positions, lines):
            dl.text((tx, tyy), line, font=font, fill=255, stroke_width=max(1, glyph_h // 10))
        layer = layer.filter(ImageFilter.GaussianBlur(max(2, glyph_h / 5)))
        strength = min(1.0, glow * 7)
        layer = layer.point(lambda v: int(v * strength))
        patch = Image.composite(Image.new("RGB", patch.size, fg), patch, layer)
    draw = ImageDraw.Draw(patch)
    for (tx, tyy), line in zip(positions, lines):
        draw.text((tx, tyy), line, font=font, fill=fg, stroke_width=stroke_w, stroke_fill=stroke)
    b.patch = patch
    b.px, b.py = x0 + ox, y0 + oy


def _free_width(b: TextBlock, blocks: list[TextBlock], screen_w: int, ox: int) -> float:
    """Yazının, aynı hizadaki komşularına çarpmadan ortalanarak kaplayabileceği genişlik."""
    cx = b.x + b.w / 2
    left, right = ox, ox + screen_w
    for o in blocks:
        if o is b:
            continue
        # Dikeyde çakışıyorsa (aynı satırda/sekme çubuğunda) komşudur
        if o.y < b.y + b.h and b.y < o.y + o.h:
            if o.x + o.w <= b.x:
                left = max(left, o.x + o.w)
            elif o.x >= b.x + b.w:
                right = min(right, o.x)
    gap = max(4, b.line_height // 2)
    half = min(cx - left, right - cx) - gap
    return max(b.w, 2 * half)


def _alignment(b: TextBlock, blocks: list[TextBlock]) -> str:
    """Alt alta duran komşu yazılara bakarak hizalamayı tahmin eder: left/center/right."""
    votes = {"left": 0, "center": 0, "right": 0}
    tol = max(4, b.line_height * 0.5)
    for o in blocks:
        if o is b or not (o.x < b.x + b.w and b.x < o.x + o.w):
            continue  # yatayda çakışmıyorsa aynı sütunda değil
        if abs((o.y + o.h / 2) - (b.y + b.h / 2)) > b.line_height * 8:
            continue
        if abs(o.x - b.x) < tol:
            votes["left"] += 1
        if abs((o.x + o.w / 2) - (b.x + b.w / 2)) < tol:
            votes["center"] += 1
        if abs((o.x + o.w) - (b.x + b.w)) < tol:
            votes["right"] += 1
    best = max(votes, key=votes.get)
    return best if votes[best] else "center"


def render_all(img: Image.Image, blocks: list[TextBlock], offset: tuple[int, int]) -> None:
    for b in blocks:
        b.room_w = _free_width(b, blocks, img.width, offset[0])
        b.align = _alignment(b, blocks)
        # Yakındaki diğer yazılar (resimler kesişebilir)
        b.neighbors = [o for o in blocks if o is not b
                       and o.x < b.x + b.w + b.line_height * 2 and b.x < o.x + o.w + b.line_height * 2
                       and o.y < b.y + b.h + b.line_height * 2 and b.y < o.y + o.h + b.line_height * 2]
    for b in blocks:
        try:
            render_block(img, b, offset)
        except Exception:
            b.patch = None  # çizilemezse düz kutu ile gösterilir
