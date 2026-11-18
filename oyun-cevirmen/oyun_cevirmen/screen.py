"""Ekran görüntüsü alma ve OCR (görüntüdeki yazıyı okuma)."""
from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageOps


@dataclass
class TextBlock:
    """Ekranda bulunan bir metin bloğu (ekran koordinatlarında)."""

    x: int
    y: int
    w: int
    h: int
    text: str
    line_height: int
    translated: str = ""
    bg: str = "#101418"
    fg: str = "#ffffff"


@dataclass
class Region:
    left: int
    top: int
    width: int
    height: int


def _mss():
    import mss

    return getattr(mss, "MSS", None) and mss.MSS() or mss.mss()


def monitors() -> list[Region]:
    with _mss() as sct:
        return [Region(m["left"], m["top"], m["width"], m["height"]) for m in sct.monitors[1:]]


def capture(region: Region) -> Image.Image:
    with _mss() as sct:
        shot = sct.grab(
            {"left": region.left, "top": region.top, "width": region.width, "height": region.height}
        )
        return Image.frombytes("RGB", shot.size, shot.rgb)


def image_signature(img: Image.Image) -> bytes:
    """Ekran değişti mi diye hızlı karşılaştırma için küçük bir parmak izi."""
    return img.convert("L").resize((64, 36)).point(lambda p: p // 16 * 16).tobytes()


def signature_changed(a: bytes | None, b: bytes, tolerance: float = 0.02) -> bool:
    if a is None or len(a) != len(b):
        return True
    diff = sum(1 for x, y in zip(a, b) if x != y)
    return diff / len(b) > tolerance


def apply_colors(img: Image.Image, blocks: list[TextBlock], offset: tuple[int, int]) -> None:
    """Her bloğun arkaplan rengini, kutunun kenarındaki piksellerden tahmin eder.

    Böylece çeviri, oyunun kendi butonu/kutusuyla aynı renkte görünür.
    """
    ox, oy = offset
    rgb = img.convert("RGB")
    for b in blocks:
        x0, y0 = max(0, b.x - ox - 3), max(0, b.y - oy - 3)
        x1, y1 = min(rgb.width - 1, b.x - ox + b.w + 3), min(rgb.height - 1, b.y - oy + b.h + 3)
        if x1 <= x0 or y1 <= y0:
            continue
        pts = []
        step = max(1, (x1 - x0) // 40)
        for x in range(x0, x1, step):
            pts += [rgb.getpixel((x, y0)), rgb.getpixel((x, y1))]
        step = max(1, (y1 - y0) // 10)
        for y in range(y0, y1, step):
            pts += [rgb.getpixel((x0, y)), rgb.getpixel((x1, y))]
        # Kenar piksellerinin medyanı (yazı kenara taşsa bile sağlam)
        r, g, bl = (sorted(c[i] for c in pts)[len(pts) // 2] for i in range(3))
        b.bg = f"#{r:02x}{g:02x}{bl:02x}"
        lum = 0.299 * r + 0.587 * g + 0.114 * bl
        b.fg = "#111111" if lum > 140 else "#ffffff"


# --- OCR motorları --------------------------------------------------------

# Kaynak dil kodu -> Tesseract dil kodu
TESS_LANGS = {
    "auto": "eng", "en": "eng", "ja": "jpn", "zh-CN": "chi_sim", "ko": "kor", "ru": "rus",
    "de": "deu", "fr": "fra", "es": "spa", "it": "ita", "pt": "por", "pl": "pol",
}
# Kaynak dil kodu -> EasyOCR dil listesi
EASY_LANGS = {
    "auto": ["en"], "en": ["en"], "ja": ["ja", "en"], "zh-CN": ["ch_sim", "en"],
    "ko": ["ko", "en"], "ru": ["ru", "en"], "de": ["de", "en"], "fr": ["fr", "en"],
    "es": ["es", "en"], "it": ["it", "en"], "pt": ["pt", "en"], "pl": ["pl", "en"],
}
CJK = {"ja", "zh-CN", "ko"}

OCR_ENGINES = {
    "tesseract": "Tesseract (hızlı, kurulum gerekir)",
    "easyocr": "EasyOCR (oyun ekranlarında daha iyi, yavaş/GPU)",
}


def _prepare(img: Image.Image, scale: float) -> Image.Image:
    """Gri tona çevir ve küçük oyun yazıları için büyüt."""
    gray = img.convert("L")
    if scale != 1:
        gray = gray.resize((int(gray.width * scale), int(gray.height * scale)), Image.LANCZOS)
    return gray


class OcrEngine:
    def read(self, img: Image.Image, offset: tuple[int, int]) -> list[TextBlock]:
        raise NotImplementedError


class TesseractOcr(OcrEngine):
    def __init__(self, source_lang: str = "en", tesseract_path: str = "", min_conf: int = 55):
        import pytesseract

        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.pt = pytesseract
        self.lang = TESS_LANGS.get(source_lang, "eng")
        self.cjk = source_lang in CJK
        self.min_conf = min_conf

    def read(self, img, offset):
        scale = 2.0 if img.height < 1600 else 1.0
        gray = _prepare(img, scale)
        words: list[dict] = []
        psm = "--psm 6" if self.cjk else "--psm 11"
        # Oyunlarda yazı hem açık hem koyu, arkaplan da renkli olabilir: iki geçiş yap.
        # 2. geçiş: ters çevrilmiş görüntü + yerel (Sauvola) eşikleme -> renkli butonlar.
        for variant, extra in ((gray, ""), (ImageOps.invert(gray), " -c thresholding_method=2")):
            try:
                data = self.pt.image_to_data(variant, lang=self.lang, config=psm + extra,
                                             output_type=self.pt.Output.DICT)
            except self.pt.TesseractError:
                if not extra:
                    raise
                # Eski Tesseract (<5.3) bu ayarı bilmez
                data = self.pt.image_to_data(variant, lang=self.lang, config=psm,
                                             output_type=self.pt.Output.DICT)
            for i, txt in enumerate(data["text"]):
                txt = txt.strip()
                try:
                    conf = float(data["conf"][i])
                except ValueError:
                    conf = -1
                if txt and conf >= self.min_conf and any(c.isalnum() for c in txt):
                    words.append({
                        "x": data["left"][i] / scale, "y": data["top"][i] / scale,
                        "w": data["width"][i] / scale, "h": data["height"][i] / scale,
                        "text": txt, "conf": conf,
                    })
        words = _dedupe_words(words)
        return group_words(words, offset, joiner="" if self.cjk else " ")


class EasyOcr(OcrEngine):
    _readers: dict[tuple, object] = {}

    def __init__(self, source_lang: str = "en", gpu: bool = True, min_conf: float = 0.35):
        import easyocr

        langs = tuple(EASY_LANGS.get(source_lang, ["en"]))
        if langs not in self._readers:
            self._readers[langs] = easyocr.Reader(list(langs), gpu=gpu, verbose=False)
        self.reader = self._readers[langs]
        self.cjk = source_lang in CJK
        self.min_conf = min_conf

    def read(self, img, offset):
        import numpy as np

        results = self.reader.readtext(np.array(img), paragraph=False)
        words = []
        for box, txt, conf in results:
            if conf < self.min_conf or not txt.strip():
                continue
            xs = [p[0] for p in box]
            ys = [p[1] for p in box]
            words.append({"x": min(xs), "y": min(ys), "w": max(xs) - min(xs),
                          "h": max(ys) - min(ys), "text": txt.strip(), "conf": conf})
        return group_words(words, offset, joiner="" if self.cjk else " ")


def make_ocr(engine: str, source_lang: str, tesseract_path: str = "") -> OcrEngine:
    if engine == "easyocr":
        return EasyOcr(source_lang)
    return TesseractOcr(source_lang, tesseract_path)


# --- Kelimeleri satırlara, satırları bloklara toplama ---------------------

def _dedupe_words(words: list[dict]) -> list[dict]:
    """Normal ve ters çevrilmiş geçişte bulunan aynı kelimelerden iyisini tut."""
    words = sorted(words, key=lambda w: -w["conf"])
    kept: list[dict] = []
    for w in words:
        if not any(_overlap(w, k) > 0.5 for k in kept):
            kept.append(w)
    return kept


def _overlap(a: dict, b: dict) -> float:
    ix = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    iy = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    inter = ix * iy
    smaller = min(a["w"] * a["h"], b["w"] * b["h"]) or 1
    return inter / smaller


def group_words(words: list[dict], offset: tuple[int, int], joiner: str = " ") -> list[TextBlock]:
    """Kelimeleri satırlara, birbirine yakın satırları paragraf bloklarına toplar.

    Arayüz öğeleri (butonlar, menüler) genelde ayrı kalır; diyalog kutularındaki
    çok satırlı yazılar tek blok olarak çevrilir (daha doğru çeviri için).
    """
    if not words:
        return []
    words = sorted(words, key=lambda w: (w["y"] + w["h"] / 2, w["x"]))

    # 1) Satırlar: önce dikeyde aynı hizadaki kelimeleri topla, sonra soldan sağa
    #    sırala ve aralarında büyük boşluk olan yerlerden böl (ayrı butonlar vb.)
    rows: list[list[dict]] = []
    for w in words:
        cy = w["y"] + w["h"] / 2
        for row in rows:
            rcy = sum(r["y"] + r["h"] / 2 for r in row) / len(row)
            rh = sum(r["h"] for r in row) / len(row)
            if abs(cy - rcy) < max(rh, w["h"]) * 0.45:
                row.append(w)
                break
        else:
            rows.append([w])

    lines: list[list[dict]] = []
    for row in rows:
        row.sort(key=lambda w: w["x"])
        cur = [row[0]]
        for w in row[1:]:
            last = cur[-1]
            h = max(sum(c["h"] for c in cur) / len(cur), w["h"])
            if w["x"] - (last["x"] + last["w"]) > h * 2.0:
                lines.append(cur)
                cur = [w]
            else:
                cur.append(w)
        lines.append(cur)

    def bbox(items):
        x0 = min(i["x"] for i in items)
        y0 = min(i["y"] for i in items)
        x1 = max(i["x"] + i["w"] for i in items)
        y1 = max(i["y"] + i["h"] for i in items)
        return x0, y0, x1, y1

    line_objs = []
    for line in lines:
        x0, y0, x1, y1 = bbox(line)
        line_objs.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "h": y1 - y0,
                          "text": joiner.join(w["text"] for w in line)})
    line_objs.sort(key=lambda l: (l["y0"], l["x0"]))

    # 2) Bloklar: alt alta, sola hizalı/üst üste binen, aralığı küçük satırlar
    blocks: list[list[dict]] = []
    for ln in line_objs:
        for blk in blocks:
            last = blk[-1]
            vgap = ln["y0"] - last["y1"]
            similar_size = 0.7 < ln["h"] / max(last["h"], 1) < 1.4
            h_overlap = min(ln["x1"], last["x1"]) - max(ln["x0"], last["x0"])
            if -last["h"] * 0.3 <= vgap < last["h"] * 0.9 and similar_size and h_overlap > 0 \
                    and abs(ln["x0"] - last["x0"]) < last["h"] * 3:
                blk.append(ln)
                break
        else:
            blocks.append([ln])

    ox, oy = offset
    out = []
    for blk in blocks:
        x0 = min(l["x0"] for l in blk)
        y0 = min(l["y0"] for l in blk)
        x1 = max(l["x1"] for l in blk)
        y1 = max(l["y1"] for l in blk)
        text = joiner.join(l["text"] for l in blk)
        if len(text.strip()) < 2:
            continue
        out.append(TextBlock(int(x0 + ox), int(y0 + oy), int(x1 - x0), int(y1 - y0), text,
                             int(sum(l["h"] for l in blk) / len(blk))))
    return out
