"""Windows'ta uçtan uca deneme (CI'da çalışır, sonucu ekran görüntüsü olarak kaydeder).

Sahte bir "oyun" penceresi açar, uygulamanın ekranı okumasını ve çeviriyi oyunun
üstüne çizmesini sağlar, sonra ekran görüntüsü alır. Çeviri motoru sahtedir
(internet ve API anahtarı gerekmez).
"""
import json
import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageDraw, ImageFont, ImageTk  # noqa: E402

from oyun_cevirmen import gui, overlay, screen  # noqa: E402
from oyun_cevirmen.translator import Backend  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "e2e")
OUT.mkdir(parents=True, exist_ok=True)

SOZ = {"New Game": "Yeni Oyun", "Load Game": "Oyun Yükle", "Settings": "Ayarlar",
       "Health: 85/100": "Can: 85/100"}


class Fake(Backend):
    name = "fake"

    def translate_batch(self, texts, s, t):
        return [SOZ.get(x, "Yaşlı demirci sana bakıp şöyle der: Bana üç demir külçe getir, "
                           "sana bir kahramana yaraşır bir kılıç döveyim."
                if "blacksmith" in x.lower() else "[TR] " + x) for x in texts]


gui.make_backend = lambda *a, **k: Fake()


def game_image(w=1000, h=600):
    import numpy as np

    yy, xx = np.mgrid[0:h, 0:w]
    arr = np.stack([40 + xx / w * 120, 30 + yy / h * 60, 90 + np.sin(xx / 40) * 25], -1)
    img = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(r"C:\Windows\Fonts\georgiab.ttf", 30)
    s = ImageFont.truetype(r"C:\Windows\Fonts\georgia.ttf", 21)
    for i in range(240):
        d.line((70, 70 + i * 0.25, 340, 70 + i * 0.25), fill=(230, 150 - i // 3, 40))
    d.text((95, 78), "New Game", font=f, fill=(40, 20, 10))
    d.text((90, 150), "Load Game", font=f, fill=(250, 230, 160), stroke_width=2,
           stroke_fill=(0, 0, 0))
    d.text((90, 210), "Settings", font=f, fill=(180, 220, 255))
    d.rectangle((330, 400, 980, 570), fill=(20, 15, 30), outline=(200, 170, 90), width=3)
    for i, line in enumerate(("The old blacksmith looks at you and says:",
                              "Bring me three iron ingots and I will forge",
                              "you a sword worthy of a hero.")):
        d.text((350, 420 + i * 30), line, font=s, fill=(240, 235, 200))
    d.text((780, 20), "Health: 85/100", font=s, fill=(255, 90, 90))
    return img


def grab(path, box):
    with screen._mss() as sct:
        g = sct.grab({"left": box[0], "top": box[1], "width": box[2], "height": box[3]})
        Image.frombytes("RGB", g.size, g.rgb).save(path)


# Katmanın ekran görüntüsünden gizlenmesi (WDA_EXCLUDEFROMCAPTURE) çalışıyor mu?
_probe_root = tk.Tk()
_probe = tk.Toplevel(_probe_root)
_probe.geometry("50x50+0+0")
_probe.update()
CAPTURE_EXCLUSION_WORKS = overlay.exclude_from_capture(_probe)
_probe_root.destroy()
# Test görüntüsünde çeviri görünsün diye gizlemeyi kapat (uygulama o zaman çekimden
# önce katmanı kısa süre gizleyen yedek yolu kullanır)
overlay.exclude_from_capture = lambda win: False

results = {"ekran_goruntusunden_gizleme_calisiyor": CAPTURE_EXCLUSION_WORKS}
for spec in sys.argv[2:] or ["windows", "tesseract"]:
    # "windows@2" = Windows OCR, görüntü 2 kat büyütülerek
    engine, _, sc = spec.partition("@")
    screen.WindowsOcr.scale = float(sc) if sc else None
    app = gui.App()
    app.s.region = None
    app.s.ocr_engine = engine
    app.var_ocr.set(screen.OCR_ENGINES[engine])
    game = tk.Toplevel(app.root)
    game.overrideredirect(True)
    game.geometry("1000x600+0+0")
    photo = ImageTk.PhotoImage(game_image())
    tk.Label(game, image=photo, bd=0).pack()

    def finish(spec=spec, app=app):
        grab(OUT / f"sonuc-{spec.replace('@', '-x')}.png", (0, 0, 1000, 600))
        results[spec] = {
            "durum": app.lbl_status.cget("text"),
            "katman": len(app.overlay.windows),
            "metinler": app.log.get("1.0", "end").strip().splitlines(),
            "konumlar": [w.winfo_geometry() for w in app.overlay.windows],
        }
        app.quit()

    app.root.after(800, app.root.iconify)  # uygulama penceresi oyunu kapatmasın
    app.root.after(2000, app.translate_screen)
    app.root.after(9000, finish)
    app.run()
    game_image().save(OUT / "oyun.png")

(OUT / "sonuc.json").write_text(json.dumps(results, ensure_ascii=False, indent=2),
                                encoding="utf-8")
print(json.dumps(results, ensure_ascii=False, indent=2))
