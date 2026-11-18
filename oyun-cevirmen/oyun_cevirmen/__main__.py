"""Kullanım:
    python -m oyun_cevirmen                      -> arayüzü açar
    python -m oyun_cevirmen dosya en_us.json     -> dil dosyasını komut satırından çevirir
    python -m oyun_cevirmen dosya lang/ -o lang_tr --kaynak en --motor google
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def cli(argv: list[str]) -> int:
    from . import file_translator as ft
    from .translator import BACKENDS, SOURCE_LANGUAGES, Translator, make_backend

    p = argparse.ArgumentParser(prog="oyun_cevirmen dosya",
                                description="Oyun dil dosyalarını Türkçeye çevirir.")
    p.add_argument("girdi", type=Path, help="Dosya veya klasör")
    p.add_argument("-o", "--cikti", type=Path, help="Çıktı dosyası/klasörü")
    p.add_argument("--kaynak", default="auto", choices=list(SOURCE_LANGUAGES))
    p.add_argument("--motor", default="google", choices=list(BACKENDS))
    p.add_argument("--anahtar", default="", help="Gemini/Groq/DeepL API anahtarı")
    p.add_argument("--model", default="", help="Yapay zekâ modeli (boşsa varsayılan)")
    a = p.parse_args(argv)

    tr = Translator(make_backend(a.motor, a.anahtar, a.model), source=a.kaynak, target="tr")
    if a.girdi.is_dir():
        out = a.cikti or Path(str(a.girdi).rstrip("/\\") + "_tr")
        for path, res in ft.translate_folder(a.girdi, out, tr,
                                             lambda n, i, t: n and print(f"[{i + 1}/{t}] {n}")):
            print(f"  {path.name}: {res if isinstance(res, str) else f'{res} metin'}")
        print(f"Bitti → {out}")
    else:
        out = a.cikti or ft.default_output_path(a.girdi)
        n = ft.translate_file(a.girdi, out, tr,
                              lambda d, t: print(f"\r{d}/{t} metin", end="", flush=True))
        print(f"\n{n} metin çevrildi → {out}")
    return 0


def ocr_self_test(out_path: str) -> int:
    """Paketlenmiş .exe'de OCR motorlarının çalıştığını doğrular (CI kullanır)."""
    import json
    import traceback

    from PIL import Image, ImageDraw, ImageFont

    from .gui import find_tesseract
    from .screen import TesseractOcr, WindowsOcr

    img = Image.new("RGB", (700, 200), (25, 30, 60))
    font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 30)
    ImageDraw.Draw(img).text((40, 60), "Start New Game", font=font, fill=(255, 255, 255))
    report = {}
    for name, make in (("windows", lambda: WindowsOcr("en")),
                       ("tesseract", lambda: TesseractOcr("en", find_tesseract()))):
        try:
            report[name] = [b.text for b in make().read(img, (0, 0))]
        except Exception:
            report[name] = "HATA: " + traceback.format_exc()
    Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = all(isinstance(v, list) and "Start New Game" in v for v in report.values())
    return 0 if ok else 1


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--ocr-test":
        sys.exit(ocr_self_test(sys.argv[2]))
    if len(sys.argv) > 1 and sys.argv[1] in ("dosya", "file"):
        sys.exit(cli(sys.argv[2:]))
    from .gui import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
