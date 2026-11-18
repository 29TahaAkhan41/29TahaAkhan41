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

_FONT_CANDIDATES = {
    "win32": [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\segoeui.ttf",
              r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"],
    "darwin": ["/System/Library/Fonts/Supplemental/Arial Bold.ttf",
               "/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"],
    "linux": ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/TTF/DejaVuSans.ttf"],
}


@lru_cache(maxsize=1)
def _font_path() -> str | None:
    key = "win32" if sys.platform == "win32" else "darwin" if sys.platform == "darwin" else "linux"
    for p in _FONT_CANDIDATES[key]:
        if os.path.isfile(p):
            return p
    return None


@lru_cache(maxsize=64)
def _font(size: int) -> ImageFont.ImageFont:
    path = _font_path()
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


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


def text_mask(rgb: np.ndarray, line_height: int) -> np.ndarray:
    """Yazı piksellerini bulur: çevresindeki ortalama renkten belirgin farklı olanlar."""
    r = max(3, line_height)
    local = _smooth(rgb, r)
    dist = np.sqrt(((rgb - local) ** 2).sum(axis=2))
    # Eşik, bölgenin kontrastına göre uyarlanır (soluk yazılar da bulunsun)
    thr = max(28.0, float(np.percentile(dist, 70)) * 1.2)
    mask = dist > thr
    # Kenar yumuşatma piksellerini de kapsamak için maskeyi biraz genişlet
    grow = max(1, line_height // 7)
    m = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(grow * 2 + 1))
    return np.asarray(m) > 0


def inpaint(rgb: np.ndarray, mask: np.ndarray, radius: int) -> np.ndarray:
    """Maskelenmiş pikselleri çevredeki arka planla doldurur (normalize evrişim)."""
    w = (~mask).astype(np.float64)
    out = rgb.copy()
    filled = np.zeros_like(w, dtype=bool)
    r = max(2, radius)
    for _ in range(4):  # büyük yazılarda yarıçapı büyüterek boşlukları kapat
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
    top, bottom = probe.getbbox(original or "Ag")[1::2]
    ratio = max(0.3, (bottom - top) / 100)
    return int(round(glyph_h / ratio))


def fit_text(text: str, box_w: int, box_h: int, line_height: int, original: str = "",
             min_px: int = 9):
    """Metni kutuya sığdıran yazı boyutunu ve satırlarını bulur.

    Başlangıç boyutu, orijinal yazının ekrandaki harf yüksekliğinden hesaplanır; böylece
    çeviri orijinalle aynı büyüklükte görünür. Sığmazsa küçültülür.
    """
    size = max(min_px, _size_for_glyph_height(original.split("\n")[0][:80], line_height))
    while True:
        font = _font(size)
        lines = _wrap(font, text, max(int(box_w * 1.05), 20))
        asc, desc = font.getmetrics()
        lh = asc + desc
        top, bottom = font.getbbox("Ag")[1::2]
        h = lh * (len(lines) - 1) + (bottom - top)
        w = max((font.getlength(l) for l in lines), default=0)
        # Tek satırlık kısa yazılar (buton, menü) biraz taşabilir; uzun metinler sarılır
        max_w = box_w * (1.3 if len(lines) == 1 else 1.1)
        if (h <= box_h * 1.3 and w <= max_w) or size <= min_px:
            return font, lines, int(w), int(lh * (len(lines) - 1) + bottom), lh
        size -= 1


# --- ana işlev -------------------------------------------------------------

def render_block(img: Image.Image, b: TextBlock, offset: tuple[int, int]) -> None:
    """Bloğun çeviri resmini (b.patch) ve ekrandaki yerini (b.px, b.py) hazırlar."""
    ox, oy = offset
    text = b.translated or b.text
    pad = max(2, b.line_height // 4)
    font, lines, tw, th, lh = fit_text(text, b.w, b.h, b.line_height, b.text)

    # Çevrilmiş metin orijinalden büyükse kutu sağa/aşağı genişler
    w = max(b.w, tw) + pad * 2
    h = max(b.h, th) + pad * 2
    x0, y0 = b.x - ox - pad, b.y - oy - pad
    x0 = max(0, min(x0, img.width - 1))
    y0 = max(0, min(y0, img.height - 1))
    x1, y1 = min(img.width, x0 + w), min(img.height, y0 + h)
    crop = np.asarray(img.crop((x0, y0, x1, y1)).convert("RGB"), dtype=np.float64)

    # Yalnızca orijinal yazının bulunduğu dikdörtgende yazı pikseli ara
    mask = np.zeros(crop.shape[:2], bool)
    bx0, by0 = b.x - ox - x0, b.y - oy - y0
    # OCR kutusu harflerin kenarlarını (kontur, gölge) tam kapsamayabilir: biraz genişlet
    m = max(2, b.line_height // 4)
    region = (slice(max(0, by0 - m), max(0, by0) + b.h + m),
              slice(max(0, bx0 - m), max(0, bx0) + b.w + m))
    sub = crop[region]
    if sub.size:
        mask[region] = text_mask(sub, b.line_height)

    clean = inpaint(crop, mask, b.line_height)
    fg, stroke, outlined = text_colors(crop, mask, clean[~mask] if (~mask).any() else clean)
    # Orijinalde kontur varsa ya da arka plan karmaşıksa (doku, resim) kontur çiz
    busy = float(clean.std(axis=(0, 1)).mean()) > 22
    stroke_w = max(1, b.line_height // 12) if outlined else (1 if busy else 0)
    patch = Image.fromarray(np.clip(clean, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(patch)
    top = font.getbbox("Ag")[1]
    ty = max(-top, (patch.height - (th - top)) // 2 - top)
    tx = min(pad, max(0, patch.width - tw))
    for i, line in enumerate(lines):
        draw.text((tx, ty + i * lh), line, font=font, fill=fg,
                  stroke_width=stroke_w, stroke_fill=stroke)
    b.patch = patch
    b.px, b.py = x0 + ox, y0 + oy


def render_all(img: Image.Image, blocks: list[TextBlock], offset: tuple[int, int]) -> None:
    for b in blocks:
        try:
            render_block(img, b, offset)
        except Exception:
            b.patch = None  # çizilemezse düz kutu ile gösterilir
