"""Draws the solar panel's 16x16 textures (run: python3 tools/make_textures.py)."""
from pathlib import Path
from PIL import Image

OUT = Path(__file__).resolve().parent.parent / "content/assets/solartech/textures/block"
FRAME, FRAME_DARK, FRAME_LIGHT = (92, 96, 104), (62, 65, 72), (128, 133, 142)


def top(cell, cell_hi, grid):
    img = Image.new("RGBA", (16, 16), FRAME + (255,))
    px = img.load()
    for y in range(1, 15):
        for x in range(1, 15):
            on_grid = (x - 1) % 5 == 4 or (y - 1) % 5 == 4
            hi = (x - 1) % 5 == 0 and (y - 1) % 5 == 0
            px[x, y] = (grid if on_grid else cell_hi if hi else cell) + (255,)
    for i in range(16):
        px[i, 0] = px[0, i] = FRAME_LIGHT + (255,)
        px[i, 15] = px[15, i] = FRAME_DARK + (255,)
    return img


def side():
    img = Image.new("RGBA", (16, 16), FRAME + (255,))
    px = img.load()
    for x in range(16):
        px[x, 0] = (24, 38, 84, 255)          # the panel's edge
        px[x, 1] = FRAME_LIGHT + (255,)
        px[x, 15] = FRAME_DARK + (255,)
        for y in (5, 10):
            px[x, y] = FRAME_DARK + (255,)
    for y in range(2, 15):
        px[0, y] = FRAME_LIGHT + (255,)
        px[15, y] = FRAME_DARK + (255,)
    for x, y in ((7, 7), (8, 7), (7, 8), (8, 8)):  # the output socket
        px[x, y] = (196, 122, 60, 255)
    return img


def bottom():
    img = Image.new("RGBA", (16, 16), FRAME_DARK + (255,))
    px = img.load()
    for i in range(16):
        px[i, 0] = px[0, i] = px[i, 15] = px[15, i] = FRAME + (255,)
    for y in range(6, 10):
        for x in range(6, 10):
            px[x, y] = (196, 122, 60, 255)
    return img


OUT.mkdir(parents=True, exist_ok=True)
top((24, 38, 84), (40, 60, 120), (150, 160, 175)).save(OUT / "solar_panel_top.png")
top((36, 84, 190), (120, 180, 255), (200, 215, 235)).save(OUT / "solar_panel_top_active.png")
side().save(OUT / "solar_panel_side.png")
bottom().save(OUT / "solar_panel_bottom.png")
