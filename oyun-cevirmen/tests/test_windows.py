"""Yalnızca Windows'ta çalışır: Windows OCR'ı gerçek bir görüntüyle dener."""
import sys
import threading

import pytest
from PIL import Image, ImageDraw, ImageFont

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows'a özel")


def sample():
    img = Image.new("RGB", (900, 300), (25, 30, 60))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 28)
    d.rectangle((40, 30, 300, 80), fill=(220, 170, 50))
    d.text((60, 38), "New Game", font=f, fill=(20, 20, 20))
    d.text((60, 110), "Load Game", font=f, fill=(255, 255, 255))
    d.text((60, 180), "Press E to open the inventory", font=f, fill=(240, 240, 200))
    return img


def test_windows_ocr_reads_text_in_worker_thread():
    from oyun_cevirmen.screen import WindowsOcr

    out = {}

    def run():  # uygulama OCR'ı arka plan iş parçacığında çalıştırıyor
        try:
            out["blocks"] = WindowsOcr("en").read(sample(), (100, 50))
        except Exception as e:
            out["error"] = e

    t = threading.Thread(target=run)
    t.start()
    t.join(60)
    if "error" in out:
        raise out["error"]
    texts = [b.text for b in out["blocks"]]
    print(texts)
    assert "New Game" in texts
    assert "Load Game" in texts
    assert any("inventory" in t for t in texts)
    ng = next(b for b in out["blocks"] if b.text == "New Game")
    assert 150 <= ng.x <= 175 and 85 <= ng.y <= 100  # ofset eklenmiş ekran koordinatı
