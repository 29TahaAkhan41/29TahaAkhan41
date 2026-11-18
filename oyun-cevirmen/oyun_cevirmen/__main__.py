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


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] in ("dosya", "file"):
        sys.exit(cli(sys.argv[2:]))
    from .gui import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
