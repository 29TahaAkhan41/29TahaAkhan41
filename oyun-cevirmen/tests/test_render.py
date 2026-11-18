import numpy as np
from PIL import Image, ImageDraw

from oyun_cevirmen.render import fit_text, inpaint, render_block, text_colors, text_mask
from oyun_cevirmen.screen import TextBlock, looks_like_text


def gradient(w, h):
    xx = np.tile(np.linspace(40, 200, w), (h, 1))
    return np.stack([xx, xx * 0.5, 255 - xx], -1)


def test_inpaint_removes_text_and_keeps_gradient():
    bg = gradient(200, 40)
    img = Image.fromarray(bg.astype(np.uint8))
    ImageDraw.Draw(img).text((10, 10), "Hello World", fill=(255, 255, 255),
                             font_size=20)
    rgb = np.asarray(img, float)
    mask = text_mask(rgb, 20)
    assert 0.05 < mask.mean() < 0.6
    clean = inpaint(rgb, mask, 20)
    # Yazı silindikten sonra sonuç, yazısız geçişli arka plana çok yakın olmalı
    assert np.abs(clean - bg).mean() < 6


def test_text_color_is_detected():
    img = Image.new("RGB", (160, 40), (20, 20, 60))
    ImageDraw.Draw(img).text((8, 8), "Quest", fill=(250, 210, 60), font_size=22)
    rgb = np.asarray(img, float)
    mask = text_mask(rgb, 18)
    clean = inpaint(rgb, mask, 18)
    fg, stroke, outlined = text_colors(rgb, mask, clean[~mask])
    assert abs(fg[0] - 250) < 30 and abs(fg[1] - 210) < 30 and fg[2] < 110
    assert not outlined


def test_fit_text_wraps_and_shrinks():
    font, lines, w, h, lh = fit_text("Çok uzun bir Türkçe cümle burada duruyor", 150, 40, 14,
                                     "A long English sentence")
    assert len(lines) >= 2 and w <= 150 * 1.1 + 1


def test_render_block_makes_patch_at_position():
    img = Image.new("RGB", (400, 100), (30, 30, 30))
    ImageDraw.Draw(img).text((50, 30), "Start", fill=(255, 255, 255), font_size=24)
    b = TextBlock(50 + 100, 30 + 200, 60, 20, "Start", 18, translated="Başla")
    render_block(img, b, (100, 200))
    assert b.patch is not None and b.patch.width >= 60
    assert 140 <= b.px <= 150 and 220 <= b.py <= 230


def test_looks_like_text():
    assert looks_like_text("New Game")
    assert looks_like_text("HP")
    assert looks_like_text("Görev tamamlandı")
    assert not looks_like_text("|[=~_")
    assert not looks_like_text("x")
    assert not looks_like_text("Wrrkxzt")  # sesli harfsiz uydurma okuma
