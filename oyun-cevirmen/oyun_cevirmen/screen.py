"""Ekran görüntüsü alma ve OCR (görüntüdeki yazıyı okuma)."""
from __future__ import annotations

import os
import sys
from concurrent.futures import ThreadPoolExecutor
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
    patch: object = None  # oyunun görünümüne uydurulmuş çeviri resmi (render.py)
    px: int = 0
    py: int = 0


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
    "windows": "Windows OCR (en hızlı, önerilen)",
    "tesseract": "Tesseract",
    "easyocr": "EasyOCR (yavaş, GPU ister)",
}
DEFAULT_OCR = "windows" if sys.platform == "win32" else "tesseract"


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
            # Dil dosyaları exe'nin yanındaki tessdata klasöründeyse onu kullan
            tessdata = os.path.join(os.path.dirname(tesseract_path), "tessdata")
            if os.path.isdir(tessdata):
                os.environ["TESSDATA_PREFIX"] = tessdata
        # Tesseract'ın kendi iç paralelliği (OpenMP), iki tarama aynı anda çalışınca
        # işlemciyi kilitliyor: tek taramayı saniyelerden dakikalara çıkarabiliyordu.
        os.environ["OMP_THREAD_LIMIT"] = "1"
        self.pt = pytesseract
        self.scale = None  # None: görüntü boyutuna göre otomatik
        self.lang = TESS_LANGS.get(source_lang, "eng")
        self.cjk = source_lang in CJK
        self.min_conf = min_conf

    def _pass(self, variant, extra, psm):
        try:
            return self.pt.image_to_data(variant, lang=self.lang, config=psm + extra,
                                         output_type=self.pt.Output.DICT)
        except self.pt.TesseractError:
            if not extra:
                raise
            # Eski Tesseract (<5.3) bu ayarı bilmez
            return self.pt.image_to_data(variant, lang=self.lang, config=psm,
                                         output_type=self.pt.Output.DICT)

    def read(self, img, offset):
        # Küçük bölgeler (diyalog kutusu vb.) büyütülürse daha iyi okunur; tüm ekranı
        # büyütmek ise çok yavaşlatır.
        scale = self.scale or (2.0 if img.height <= 1100 else 1.5 if img.height <= 1440 else 1.0)
        gray = _prepare(img, scale)
        words: list[dict] = []
        psm = "--psm 6" if self.cjk else "--psm 11"
        # Oyunlarda yazı hem açık hem koyu, arkaplan da renkli olabilir: iki geçiş yap
        # (aynı anda). 2. geçiş: ters görüntü + yerel (Sauvola) eşikleme -> renkli butonlar.
        variants = ((gray, ""), (ImageOps.invert(gray), " -c thresholding_method=2"))
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda v: self._pass(v[0], v[1], psm), variants))
        for data in results:
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


# Kaynak dil kodu -> Windows OCR dil etiketinin başı
WIN_LANGS = {
    "en": "en", "ja": "ja", "zh-CN": "zh-Hans", "ko": "ko", "ru": "ru", "de": "de",
    "fr": "fr", "es": "es", "it": "it", "pt": "pt", "pl": "pl",
}
LANG_NAMES_TR = {
    "en": "İngilizce", "ja": "Japonca", "zh-CN": "Çince", "ko": "Korece", "ru": "Rusça",
    "de": "Almanca", "fr": "Fransızca", "es": "İspanyolca", "it": "İtalyanca",
    "pt": "Portekizce", "pl": "Lehçe",
}


class WindowsOcr(OcrEngine):
    """Windows 10/11'in yerleşik yazı tanıma motoru: çok hızlı, ekran yazısında başarılı."""

    scale: float | None = None  # None: görüntü boyutuna göre otomatik

    def __init__(self, source_lang: str = "en"):
        from winrt.windows.media.ocr import OcrEngine as WinOcrEngine

        self._Engine = WinOcrEngine
        self.cjk = source_lang in CJK
        self.engine = None
        if source_lang == "auto":
            self.engine = WinOcrEngine.try_create_from_user_profile_languages()
        else:
            prefix = WIN_LANGS.get(source_lang, source_lang).lower()
            for lang in WinOcrEngine.available_recognizer_languages:
                tag = lang.language_tag.lower()
                if tag == prefix or tag.startswith(prefix + "-"):
                    self.engine = WinOcrEngine.try_create_from_language(lang)
                    break
        if self.engine is None:
            name = LANG_NAMES_TR.get(source_lang, source_lang)
            raise RuntimeError(
                f"Windows'ta {name} yazı tanıma paketi yüklü değil. Windows Ayarlar > Saat ve dil "
                f"> Dil ve bölge'den {name} dilini ekleyin ya da OCR motorunu Tesseract yapın.")
        self.max_dim = int(WinOcrEngine.max_image_dimension)

    def read(self, img, offset):
        import asyncio

        from winrt.windows.graphics.imaging import BitmapPixelFormat, SoftwareBitmap
        from winrt.windows.storage.streams import DataWriter

        # Küçük bölgelerde küçük yazılar için büyüt; motorun boyut sınırını aşma
        # Windows'taki denemede 2 kat büyütme hem daha doğru hem de yeterince hızlıydı
        # (1000x600 alan: 0,2-0,4 sn)
        scale = self.scale or (2.0 if img.height <= 1440 else 1.0)
        if max(img.width, img.height) * scale > self.max_dim:
            scale = self.max_dim / max(img.width, img.height)
        work = img.convert("RGB")
        if scale != 1:
            work = work.resize((int(work.width * scale), int(work.height * scale)), Image.LANCZOS)
        data = work.convert("RGBA").tobytes("raw", "BGRA")
        writer = DataWriter()
        writer.write_bytes(data)
        bitmap = SoftwareBitmap.create_copy_from_buffer(
            writer.detach_buffer(), BitmapPixelFormat.BGRA8, work.width, work.height)

        async def recognize():
            return await self.engine.recognize_async(bitmap)

        result = asyncio.run(recognize())
        words = []
        for line in result.lines:
            for w in line.words:
                r = w.bounding_rect
                if w.text.strip():
                    words.append({"x": r.x / scale, "y": r.y / scale, "w": r.width / scale,
                                  "h": r.height / scale, "text": w.text.strip(), "conf": 100})
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
    if engine == "windows":
        if sys.platform != "win32":
            return TesseractOcr(source_lang, tesseract_path)
        return WindowsOcr(source_lang)
    if engine == "easyocr":
        return EasyOcr(source_lang)
    return TesseractOcr(source_lang, tesseract_path)


# --- Kelimeleri satırlara, satırları bloklara toplama ---------------------

def looks_like_text(text: str) -> bool:
    """OCR'ın dokudan/simgelerden uydurduğu anlamsız okumaları eler.

    Bunlar çevirmene gönderilince saçma "çeviriler" ortaya çıkıyordu.
    """
    chars = [c for c in text if not c.isspace()]
    letters = [c for c in chars if c.isalpha()]
    if len(letters) < 2:
        return False
    if len(letters) / len(chars) < 0.5:  # çoğu simge/noktalama: |[=~_ gibi
        return False
    # Tek "kelime" ve içinde hiç sesli harf yoksa (Latin alfabesi) büyük olasılıkla çöp
    latin = [c for c in letters if c.isascii()]
    if len(latin) == len(letters) and " " not in text.strip() and len(letters) > 3 \
            and not any(c in "aeiouyAEIOUY" for c in letters):
        return False
    return True


def _dedupe_words(words: list[dict]) -> list[dict]:
    """Normal ve ters çevrilmiş geçişte bulunan aynı kelimelerden iyisini tut."""
    words = sorted(words, key=lambda w: -w["conf"])
    kept: list[dict] = []
    for w in words:
        if not any(_overlap(w, k) > 0.5 or _same_word(w, k) for k in kept):
            kept.append(w)
    return kept


def _same_word(a: dict, b: dict) -> bool:
    """Aynı kelime, iki taramada biraz kaymış kutularla bulunmuş mu? (ör. ince "I")"""
    if a["text"].lower() != b["text"].lower():
        return False
    h = max(a["h"], b["h"], 1)
    return (abs((a["x"] + a["w"] / 2) - (b["x"] + b["w"] / 2)) < h * 0.6
            and abs((a["y"] + a["h"] / 2) - (b["y"] + b["h"] / 2)) < h * 0.6)


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
        text = " ".join(joiner.join(l["text"] for l in blk).split())
        if not looks_like_text(text):
            continue
        out.append(TextBlock(int(x0 + ox), int(y0 + oy), int(x1 - x0), int(y1 - y0), text,
                             int(sum(l["h"] for l in blk) / len(blk))))
    return out
