"""Dokulari, modelleri, dil dosyalarini, tarifleri ve loot tablolarini uretir.
Kullanim: python3 tools/gen_resources.py src/main/resources   (Pillow gerekir)"""
import json, os, shutil, sys
from PIL import Image, ImageDraw
R = sys.argv[1]
M = "teknikmod"
for d in (f"assets/{M}", f"data/{M}", "data/minecraft", "data/c"):
    shutil.rmtree(os.path.join(R, d), ignore_errors=True)
def w(path, obj):
    p = os.path.join(R, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: json.dump(obj, f, indent=2, ensure_ascii=False); f.write("\n")
def save(img, name):
    p = os.path.join(R, f"assets/{M}/textures/{name}.png"); os.makedirs(os.path.dirname(p), exist_ok=True); img.save(p)

# kademe: onek, LED rengi, EN/TR ad oneki, yukseltme malzemesi
TIERS = [("", (200, 210, 226), "", "", None),
         ("advanced_", (255, 200, 50), "Advanced ", "Gelişmiş ", "#c:ingots/gold"),
         ("elite_", (50, 225, 235), "Elite ", "Elit ", "#c:gems/diamond"),
         ("creative_", (224, 72, 255), "Creative ", "Yaratıcı ", False)]   # False: tarifi yok

# --- palet: koyu, mat metal ---
EDGE, DEEP, GLASS = (27, 29, 35), (20, 22, 27), (16, 18, 24)
def lerp(a, b, t): return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
def dim(c, f): return tuple(round(v * f) for v in c)
def px(img, x, y, c): img.putpixel((x, y), tuple(c) + (255,))
def rect(img, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): px(img, x, y, c)
def casing(accent=None):
    """Duz, hafif gecisli govde plakasi: koyu dis cizgi, ustte isik, altta golge."""
    img = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16): px(img, x, y, lerp((72, 77, 90), (52, 56, 67), y / 15))
    for i in range(16):
        for (x, y) in ((i, 0), (i, 15), (0, i), (15, i)): px(img, x, y, EDGE)
    for i in range(1, 15):
        px(img, i, 1, (108, 114, 131)); px(img, 1, i, (90, 96, 111))
        px(img, i, 14, (38, 41, 49)); px(img, 14, i, (44, 47, 56))
    return img
def led(img, x0, x1, y, accent):
    """Isikli serit: parlak cizgi + altinda soluk yansima."""
    for x in range(x0, x1 + 1): px(img, x, y, accent); px(img, x, y + 1, lerp(dim(accent, .45), (52, 56, 67), .35))
    px(img, x0, y, lerp(accent, (255, 255, 255), .6))
def vents(img, y0, n, x0=4, x1=11):
    for k in range(n):
        y = y0 + 2 * k
        for x in range(x0, x1 + 1): px(img, x, y, DEEP)
        for x in range(x0, x1 + 1): px(img, x, y + 1, (86, 92, 107))

B = f"{M}:block/"
blocks, en, tr = [], {}, {}
def shaped(name, pattern, key, count=1):
    w(f"data/{M}/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": "redstone", "pattern": pattern,
        "key": {k: ({"tag": v[1:]} if v.startswith("#") else {"item": v}) for k, v in key.items()},
        "result": {"id": f"{M}:{name}", "count": count}})
I, C, G, RS = "#c:ingots/iron", "#c:ingots/copper", "#c:ingots/gold", "#c:dusts/redstone"
SOLAR_CELLS = [((70, 110, 190), (20, 36, 84)), ((70, 150, 235), (16, 50, 120)), ((90, 225, 245), (8, 70, 130)), ((236, 150, 255), (70, 16, 120))]

for ti, (pre, accent, en_pre, tr_pre, upgrade) in enumerate(TIERS):
    side, top = pre + "machine_side", pre + "machine_top"
    img = casing(); vents(img, 4, 2); led(img, 3, 12, 10, accent); save(img, "block/" + side)
    # ust: fan izgarasi + kose isiklari
    img = casing(); rect(img, 4, 4, 11, 11, EDGE); rect(img, 5, 5, 10, 10, DEEP)
    for y in range(5, 11):
        for x in range(5, 11):
            if (x + y) % 2 == 0: px(img, x, y, (48, 52, 62))
    rect(img, 7, 7, 8, 8, (96, 102, 118))
    for (x, y) in ((3, 3), (12, 3), (3, 12), (12, 12)): px(img, x, y, accent)
    save(img, "block/" + top)
    # komur jeneratoru on yuz: durum ekrani + camli yanma odasi
    for lit in (False, True):
        img = casing()
        rect(img, 3, 3, 12, 4, GLASS)
        px(img, 4, 3, accent); px(img, 5, 3, accent); px(img, 4, 4, dim(accent, .5)); px(img, 5, 4, dim(accent, .5))
        for x in (8, 10): px(img, x, 3, accent if lit else dim(accent, .3))
        px(img, 11, 4, (255, 90, 60) if not lit else (90, 240, 120))
        rect(img, 3, 6, 12, 13, EDGE); rect(img, 4, 7, 11, 12, GLASS)
        if lit:
            for y in range(7, 13):
                for x in range(4, 12): px(img, x, y, lerp((96, 30, 12), (255, 150, 30), (y - 7) / 5))
            for (x, h) in ((5, 2), (6, 4), (7, 3), (8, 5), (9, 3), (10, 2)):   # alev dilleri
                for k in range(h): px(img, x, 12 - k, lerp((255, 236, 130), (255, 170, 40), k / max(1, h - 1)))
        else:
            for x in range(5, 11): px(img, x, 12, (46, 30, 26))
            px(img, 6, 12, (120, 52, 24)); px(img, 9, 12, (96, 40, 20)); px(img, 7, 11, (40, 30, 28))
        px(img, 4, 7, (70, 76, 92)); px(img, 5, 7, (44, 48, 58))                 # cam yansimasi
        save(img, f"block/{pre}coal_generator_front" + ("_on" if lit else ""))
    # gunes paneli: 2x2 cam hucre, capraz gecis ve parlama
    hi, lo = SOLAR_CELLS[ti]
    img = Image.new("RGBA", (16, 16)); rect(img, 0, 0, 15, 15, (18, 21, 30))
    frame = lerp(accent, (150, 158, 174), .35)
    for i in range(16):
        for (x, y) in ((i, 0), (i, 15), (0, i), (15, i)): px(img, x, y, frame)
    for (cx, cy) in ((1, 1), (9, 1), (1, 9), (9, 9)):
        for y in range(6):
            for x in range(6):
                c = lerp(hi, lo, min(1, (x + y) / 8))
                if x + y == 3: c = lerp(c, (255, 255, 255), .28)             # capraz parlama
                if y == 3: c = lerp(c, (200, 215, 240), .12)                  # iletken cizgi
                px(img, cx + x, cy + y, c)
    save(img, f"block/{pre}solar_panel_top")
    img = casing(); rect(img, 0, 0, 15, 0, lerp(hi, lo, .4)); rect(img, 0, 1, 15, 1, frame)
    rect(img, 1, 2, 14, 5, (56, 60, 72)); led(img, 3, 12, 3, accent); rect(img, 0, 2, 0, 5, EDGE); rect(img, 15, 2, 15, 5, EDGE)
    save(img, f"block/{pre}solar_panel_side")
    # batarya yan: dikey sarj gostergesi
    img = casing(); rect(img, 5, 2, 10, 13, EDGE); rect(img, 6, 3, 9, 12, GLASS)
    for k, y in enumerate((10, 7, 4)):
        c = accent if k < 2 else dim(accent, .35)
        rect(img, 6, y, 9, y + 1, c); px(img, 6, y, lerp(c, (255, 255, 255), .5)); rect(img, 6, y + 1, 9, y + 1, dim(c, .7))
    for y in (4, 7, 10): px(img, 3, y, (108, 114, 131)); px(img, 12, y, (38, 41, 49))
    save(img, f"block/{pre}battery_side")
    # batarya on: cikis soketi
    img = casing(); rect(img, 5, 4, 10, 11, EDGE); rect(img, 4, 5, 11, 10, EDGE); rect(img, 5, 5, 10, 10, GLASS)
    for i in range(6, 10):
        px(img, i, 5, accent); px(img, i, 10, dim(accent, .6)); px(img, 5, i, accent); px(img, 10, i, dim(accent, .6))
    rect(img, 7, 7, 8, 8, lerp(accent, (255, 255, 255), .7)); px(img, 8, 8, accent)
    for (x, y) in ((3, 3), (12, 3), (3, 12), (12, 12)): px(img, x, y, (38, 41, 49))
    save(img, f"block/{pre}battery_front")


    # elektrikli firin on yuz: camin arkasinda isitici rezistanslar
    for lit in (False, True):
        img = casing(); rect(img, 3, 3, 12, 4, GLASS)
        px(img, 4, 3, accent); px(img, 5, 3, accent); px(img, 4, 4, dim(accent, .5)); px(img, 5, 4, dim(accent, .5))
        px(img, 11, 4, (90, 240, 120) if lit else (255, 90, 60))
        rect(img, 3, 6, 12, 13, EDGE); rect(img, 4, 7, 11, 12, (60, 22, 14) if lit else GLASS)
        for y in (8, 10, 12):
            for x in range(4, 12):
                px(img, x, y, ((255, 120, 40) if (x + y // 2) % 4 else (255, 214, 110)) if lit else (62, 44, 42))
            if lit:
                for x in range(4, 12): px(img, x, y - 1, lerp((60, 22, 14), (255, 120, 40), .35))
        px(img, 4, 7, (70, 76, 92))
        save(img, f"block/{pre}electric_furnace_front" + ("_on" if lit else ""))
    # ogutucu on yuz: birbirine gecen iki sira disli
    for lit in (False, True):
        img = casing(); rect(img, 3, 3, 12, 4, GLASS)
        px(img, 4, 3, accent); px(img, 5, 3, accent); px(img, 4, 4, dim(accent, .5)); px(img, 5, 4, dim(accent, .5))
        px(img, 11, 4, (90, 240, 120) if lit else (255, 90, 60))
        rect(img, 3, 6, 12, 13, EDGE); rect(img, 4, 7, 11, 12, GLASS)
        steel, steel_hi = ((176, 184, 200), (236, 240, 248)) if lit else ((112, 118, 132), (150, 156, 170))
        for x in range(4, 12):
            up = (x % 2 == 0)
            px(img, x, 7, steel); px(img, x, 12, dim(steel, .8))
            if up: px(img, x, 8, steel_hi); px(img, x, 9, steel)
            else: px(img, x, 11, steel); px(img, x, 10, steel_hi)
        if lit:
            for (x, y) in ((5, 10), (8, 9), (10, 10)): px(img, x, y, accent)   # kivilcim
        save(img, f"block/{pre}crusher_front" + ("_on" if lit else ""))

    cg, sp, bt = pre + "coal_generator", pre + "solar_panel", pre + "battery"
    w(f"assets/{M}/blockstates/{cg}.json", {"variants": {
        f"facing={f},lit={str(l).lower()}": {"model": B + cg + ("_on" if l else ""), **({"y": y} if y else {})}
        for f, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270)) for l in (False, True)}})
    for s in ("", "_on"):
        w(f"assets/{M}/models/block/{cg}{s}.json", {"parent": "minecraft:block/orientable", "textures": {
            "top": B + top, "front": B + cg + "_front" + s, "side": B + side}})
    w(f"assets/{M}/blockstates/{sp}.json", {"variants": {"": {"model": B + sp}}})
    w(f"assets/{M}/models/block/{sp}.json", {"parent": "minecraft:block/block", "textures": {
        "top": B + sp + "_top", "side": B + sp + "_side", "bottom": B + side, "particle": B + sp + "_side"},
        "elements": [{"from": [0, 0, 0], "to": [16, 6, 16], "faces": {
            "up": {"texture": "#top"}, "down": {"texture": "#bottom", "cullface": "down"},
            **{s: {"texture": "#side", "uv": [0, 0, 16, 6], "cullface": s} for s in ("north", "south", "east", "west")}}}]})
    w(f"assets/{M}/blockstates/{bt}.json", {"variants": {
        "facing=north": {"model": B + bt}, "facing=east": {"model": B + bt, "y": 90},
        "facing=south": {"model": B + bt, "y": 180}, "facing=west": {"model": B + bt, "y": 270},
        "facing=up": {"model": B + bt, "x": 270}, "facing=down": {"model": B + bt, "x": 90}}})
    w(f"assets/{M}/models/block/{bt}.json", {"parent": "minecraft:block/orientable", "textures": {
        "top": B + bt + "_side", "front": B + bt + "_front", "side": B + bt + "_side"}})
    ef, cr = pre + "electric_furnace", pre + "crusher"
    for m in (ef, cr):
        w(f"assets/{M}/blockstates/{m}.json", {"variants": {
            f"facing={f},lit={str(l).lower()}": {"model": B + m + ("_on" if l else ""), **({"y": y} if y else {})}
            for f, y in (("north", 0), ("east", 90), ("south", 180), ("west", 270)) for l in (False, True)}})
        for sfx in ("", "_on"):
            w(f"assets/{M}/models/block/{m}{sfx}.json", {"parent": "minecraft:block/orientable", "textures": {
                "top": B + top, "front": B + m + "_front" + sfx, "side": B + side}})
    for b, en_name, tr_name in ((cg, "Coal Generator", "Kömür Jeneratörü"), (sp, "Solar Panel", "Güneş Paneli"), (bt, "Battery", "Batarya"),
                                (ef, "Electric Furnace", "Elektrikli Fırın"), (cr, "Crusher", "Öğütücü")):
        w(f"assets/{M}/models/item/{b}.json", {"parent": B + b})
        blocks.append(b); en[f"block.{M}.{b}"] = en_pre + en_name; tr[f"block.{M}.{b}"] = tr_pre + tr_name
    if upgrade is None:
        shaped(cg, ["III", "IFI", "CRC"], {"I": I, "F": "minecraft:furnace", "C": C, "R": RS})
        shaped(sp, ["GGG", "LRL", "ICI"], {"G": "#c:glass_blocks", "L": "#c:gems/lapis", "R": RS, "I": I, "C": C})
        shaped(bt, ["ICI", "IRI", "IRI"], {"I": I, "C": C, "R": "#c:storage_blocks/redstone"})
        shaped(ef, ["ICI", "RFR", "ICI"], {"I": I, "C": C, "R": RS, "F": "minecraft:furnace"})
        shaped(cr, ["IFI", "PRP", "ICI"], {"I": I, "C": C, "R": RS, "F": "minecraft:flint", "P": "minecraft:piston"})
    elif upgrade:  # onceki kademenin etrafina 4 yukseltme malzemesi
        prev = TIERS[ti - 1][0]
        for kind in ("coal_generator", "solar_panel", "battery", "electric_furnace", "crusher"):
            shaped(pre + kind, [" U ", "UMU", " U "], {"U": upgrade, "M": f"{M}:{prev}{kind}"})

# --- kablolar ---
rot = {"north": {}, "east": {"y": 90}, "south": {"y": 180}, "west": {"y": 270}, "up": {"x": 270}, "down": {"x": 90}}
CABLES = [("copper_cable", (232, 132, 78), "Copper Cable", "Bakır Kablo"), ("gold_cable", (255, 206, 64), "Gold Cable", "Altın Kablo"),
          ("diamond_cable", (72, 228, 232), "Diamond Cable", "Elmas Kablo"), ("creative_cable", (224, 72, 255), "Creative Cable", "Yaratıcı Kablo")]
for c, base, en_name, tr_name in CABLES:
    # Kablo kollari dokunun ortasindaki 6 piksellik dikey/yatay bandi, cekirdek ise ortadaki 6x6 kareyi kullanir:
    # koyu yalitim + ortada parlak iletken cizgi.
    prof = [EDGE, (58, 62, 74), lerp(base, (255, 255, 255), .45), base, (44, 47, 57), EDGE]
    img = Image.new("RGBA", (16, 16)); rect(img, 0, 0, 15, 15, (44, 47, 57))
    for i in range(16):
        for k in range(6): px(img, 5 + k, i, prof[k])
    for i in range(16):
        if not 5 <= i <= 10:
            for k in range(6): px(img, i, 5 + k, prof[k])
    rect(img, 5, 5, 10, 10, EDGE); rect(img, 6, 6, 9, 9, (58, 62, 74)); rect(img, 7, 7, 8, 8, base)   # baglanti kutusu
    px(img, 7, 7, lerp(base, (255, 255, 255), .5)); px(img, 6, 6, (90, 96, 111))
    save(img, "block/" + c)
    t = {"texture": "#cable"}
    w(f"assets/{M}/models/block/{c}_core.json", {"parent": "minecraft:block/block", "textures": {"cable": B + c, "particle": B + c},
        "elements": [{"from": [5, 5, 5], "to": [11, 11, 11], "faces": {s: t for s in rot}}]})
    w(f"assets/{M}/models/block/{c}_side.json", {"textures": {"cable": B + c, "particle": B + c},
        "elements": [{"from": [5, 5, 0], "to": [11, 11, 5], "faces": {
            "north": {**t, "cullface": "north"}, "up": t, "down": t, "east": t, "west": t}}]})
    w(f"assets/{M}/blockstates/{c}.json", {"multipart": [{"apply": {"model": B + c + "_core"}}] + [
        {"when": {s: "true"}, "apply": {"model": B + c + "_side", **r, **({"uvlock": True} if r else {})}} for s, r in rot.items()]})
    # envanter modeli: iki ucu acik kisa kablo
    w(f"assets/{M}/models/item/{c}.json", {"parent": "minecraft:block/block", "textures": {"cable": B + c, "particle": B + c},
        "elements": [{"from": [5, 5, 0], "to": [11, 11, 16], "faces": {s: t for s in rot}}]})
    blocks.append(c); en[f"block.{M}.{c}"] = en_name; tr[f"block.{M}.{c}"] = tr_name
shaped("copper_cable", ["CCC"], {"C": C}, 6)
shaped("gold_cable", ["GRG"], {"G": G, "R": RS}, 6)
shaped("diamond_cable", ["DRD"], {"D": "#c:gems/diamond", "R": RS}, 6)

# --- GUI (koyu tema) ---
g = Image.new("RGBA", (256, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
d.rectangle([0, 0, 175, 165], fill=(14, 15, 19, 255)); d.rectangle([1, 1, 174, 164], fill=(46, 50, 60, 255))
d.rectangle([1, 1, 174, 1], fill=(92, 98, 114, 255)); d.rectangle([1, 1, 1, 164], fill=(74, 80, 94, 255))
d.rectangle([1, 164, 174, 164], fill=(28, 30, 37, 255)); d.rectangle([174, 1, 174, 164], fill=(32, 35, 42, 255))
d.rectangle([7, 15, 168, 15], fill=(50, 225, 235, 255)); d.rectangle([7, 16, 168, 16], fill=(30, 80, 92, 255))   # baslik alti isik seridi
d.rectangle([7, 78, 168, 78], fill=(34, 37, 45, 255))
for p in [(0, 0), (175, 0), (0, 165), (175, 165)]: g.putpixel(p, (0, 0, 0, 0))
def inset(x, y, wd, ht, fill=(27, 29, 36, 255)):
    d.rectangle([x, y, x + wd - 1, y + ht - 1], fill=fill)
    d.line([(x, y), (x + wd - 1, y)], fill=(16, 17, 22, 255)); d.line([(x, y), (x, y + ht - 1)], fill=(16, 17, 22, 255))
    d.line([(x + 1, y + ht - 1), (x + wd - 1, y + ht - 1)], fill=(78, 84, 98, 255)); d.line([(x + wd - 1, y + 1), (x + wd - 1, y + ht - 1)], fill=(78, 84, 98, 255))
inset(79, 43, 18, 18)
for r in range(3):
    for c in range(9): inset(7 + c * 18, 83 + r * 18, 18, 18)
for c in range(9): inset(7 + c * 18, 141, 18, 18)
inset(151, 16, 14, 54, fill=(12, 20, 26, 255))   # enerji cubugu
inset(80, 25, 16, 16, fill=(22, 18, 16, 255))    # yanma gostergesi
save(g, "gui/coal_generator")

# islem makinesi arayuzu: giris yuvasi -> ilerleme seridi -> cikis yuvasi
g2 = g.copy(); d = ImageDraw.Draw(g2)
d.rectangle([76, 22, 100, 64], fill=(46, 50, 60, 255))            # jenerator yuvalarini sil
inset(52, 34, 18, 18); inset(102, 30, 26, 26); inset(76, 39, 24, 8, fill=(18, 20, 26, 255))
p = os.path.join(R, f"assets/{M}/textures/gui/processing.png"); g2.save(p)

# --- tozlar ---
DUSTS = [("iron", (214, 206, 198), "Iron Dust", "Demir Tozu", "minecraft:iron_ingot"),
         ("gold", (250, 212, 72), "Gold Dust", "Altın Tozu", "minecraft:gold_ingot"),
         ("copper", (226, 130, 86), "Copper Dust", "Bakır Tozu", "minecraft:copper_ingot")]
HEAP = ["................", "................", "................", "................", "................", "......##........",
        ".....####..#....", "....######.##...", "...#########....", "..###########...", ".#############..", ".##############.",
        "################", ".##############.", "................", "................"]
for metal, col, en_name, tr_name, ingot in DUSTS:
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    for y, row in enumerate(HEAP):
        for x, ch in enumerate(row):
            if ch != "#": continue
            edge = y == 13 or x == 0 or row[x - 1] != "#" or x == 15 or row[x + 1] != "#" or HEAP[y - 1][x] != "#"
            c = lerp(col, (255, 255, 255), .35) if HEAP[y - 1][x] != "#" else dim(col, .62) if (y >= 12 or (edge and x > 8)) else col
            if (x * 7 + y * 13) % 5 == 0 and HEAP[y - 1][x] == "#": c = dim(c, .82)      # taneli gorunum
            px(img, x, y, c)
    name = metal + "_dust"
    p = os.path.join(R, f"assets/{M}/textures/item/{name}.png"); os.makedirs(os.path.dirname(p), exist_ok=True); img.save(p)
    w(f"assets/{M}/models/item/{name}.json", {"parent": "minecraft:item/generated", "textures": {"layer0": f"{M}:item/{name}"}})
    en[f"item.{M}.{name}"] = en_name; tr[f"item.{M}.{name}"] = tr_name
    w(f"data/c/tags/item/dusts/{metal}.json", {"replace": False, "values": [f"{M}:{name}"]})
    for kind, t in (("smelting", 200), ("blasting", 100)):
        w(f"data/{M}/recipe/{metal}_ingot_from_dust_{kind}.json", {"type": f"minecraft:{kind}", "category": "misc", "group": f"{metal}_ingot",
            "ingredient": {"tag": f"c:dusts/{metal}"}, "result": {"id": ingot}, "experience": 0.7, "cookingtime": t})
w("data/c/tags/item/dusts.json", {"replace": False, "values": [f"#c:dusts/{m[0]}" for m in DUSTS]})

# --- ogutme tarifleri ---
def crush(name, inp, out, count=1, time=200):
    w(f"data/{M}/recipe/crushing/{name}.json", {"type": f"{M}:crushing",
        "ingredient": {"tag": inp[1:]} if inp.startswith("#") else {"item": inp},
        "result": {"id": out, "count": count}, "time": time})
for metal in ("iron", "gold", "copper"):
    dust = f"{M}:{metal}_dust"
    crush(f"{metal}_dust_from_raw", f"#c:raw_materials/{metal}", dust, 2)
    crush(f"{metal}_dust_from_ore", f"#c:ores/{metal}", dust, 3, 300)
    crush(f"{metal}_dust_from_raw_block", f"#c:storage_blocks/raw_{metal}", dust, 18, 1200)
    crush(f"{metal}_dust_from_ingot", f"#c:ingots/{metal}", dust, 1, 100)
for name, inp, out, n in (("coal", "#c:ores/coal", "minecraft:coal", 3), ("diamond", "#c:ores/diamond", "minecraft:diamond", 2),
                          ("emerald", "#c:ores/emerald", "minecraft:emerald", 2), ("redstone", "#c:ores/redstone", "minecraft:redstone", 8),
                          ("lapis", "#c:ores/lapis", "minecraft:lapis_lazuli", 12), ("quartz", "#c:ores/quartz", "minecraft:quartz", 3)):
    crush(f"{name}_from_ore", inp, out, n, 300)
for name, inp, out, n in (("cobblestone", "minecraft:stone", "minecraft:cobblestone", 1), ("gravel", "minecraft:cobblestone", "minecraft:gravel", 1),
                          ("sand", "minecraft:gravel", "minecraft:sand", 1), ("sand_from_sandstone", "minecraft:sandstone", "minecraft:sand", 4),
                          ("red_sand_from_red_sandstone", "minecraft:red_sandstone", "minecraft:red_sand", 4),
                          ("bone_meal", "minecraft:bone", "minecraft:bone_meal", 6), ("blaze_powder", "minecraft:blaze_rod", "minecraft:blaze_powder", 4),
                          ("glowstone_dust", "minecraft:glowstone", "minecraft:glowstone_dust", 4), ("quartz_from_block", "minecraft:quartz_block", "minecraft:quartz", 4),
                          ("string", "#minecraft:wool", "minecraft:string", 4), ("flint", "minecraft:gravel", "minecraft:flint", 1)):
    if name == "flint": continue   # cakil -> kum ile cakisir
    crush(name, inp, out, n, 100)

# --- Yaratici kademe: Extended Crafting'in 9x9 (Ultimate) masasinda uretilir ---
# Tarifler yalnizca Extended Crafting yukluyken etkinlesir.
EC = "extendedcrafting:"
def ec_table(name, pattern, key, count=1):
    assert len(pattern) == 9 and all(len(r) == 9 for r in pattern), name
    w(f"data/{M}/recipe/extendedcrafting/{name}.json", {"type": EC + "shaped_table",
        "neoforge:conditions": [{"type": "neoforge:mod_loaded", "modid": "extendedcrafting"}],
        "tier": 4, "pattern": pattern,
        "key": {k: ({"tag": v[1:]} if v.startswith("#") else {"item": v}) for k, v in key.items()},
        "result": {"id": f"{M}:{name}", "count": count}})
EC_FRAME = {"C": EC + "crystaltine_ingot", "X": EC + "enhanced_ender_ingot", "U": EC + "the_ultimate_ingot", "N": "minecraft:nether_star"}
# K: cihaza ozgu malzeme (8 adet), M: cihazin Elit kademesi (ortada)
for kind, special in (("coal_generator", "#c:storage_blocks/coal"), ("solar_panel", "minecraft:daylight_detector"),
                      ("battery", "#c:storage_blocks/redstone"), ("electric_furnace", "minecraft:blast_furnace"),
                      ("crusher", "#c:storage_blocks/diamond")):
    ec_table("creative_" + kind, ["CCCCCCCCC", "CXXXXXXXC", "CXUNNNUXC", "CXNKKKNXC", "CXNKMKNXC", "CXNKKKNXC", "CXUNNNUXC", "CXXXXXXXC", "CCCCCCCCC"],
             {**EC_FRAME, "K": special, "M": f"{M}:elite_{kind}"})
ec_table("creative_cable", ["CCCCCCCCC", "CDDDDDDDC", "CDXXXXXDC", "CDXNNNXDC", "CDXNUNXDC", "CDXNNNXDC", "CDXXXXXDC", "CDDDDDDDC", "CCCCCCCCC"],
         {**EC_FRAME, "D": f"{M}:diamond_cable"}, 16)

# --- dil ---
en.update({"itemGroup.teknikmod": "Teknik Mod", "message.teknikmod.energy": "Energy: %s / %s FE", "message.teknikmod.rate": "Generating: %s FE/t",
           "tooltip.teknikmod.generation": "Generation: %s FE/t", "tooltip.teknikmod.capacity": "Capacity: %s FE", "tooltip.teknikmod.transfer": "Transfer: %s FE/t",
           "tooltip.teknikmod.coal_fuel": "Fuel: Coal, Charcoal, Block of Coal",
           "tooltip.teknikmod.speed": "Speed: %sx", "tooltip.teknikmod.usage": "Usage: %s FE/t", "message.teknikmod.progress": "Progress: %s%% (%s FE/t)",
           "tooltip.teknikmod.creative": "Creative tier: unlimited, needs no fuel or power",
           "tooltip.teknikmod.creative_recipe": "Crafted in the Extended Crafting Ultimate Table"})
tr.update({"itemGroup.teknikmod": "Teknik Mod", "message.teknikmod.energy": "Enerji: %s / %s FE", "message.teknikmod.rate": "Üretim: %s FE/t",
           "tooltip.teknikmod.generation": "Üretim: %s FE/t", "tooltip.teknikmod.capacity": "Kapasite: %s FE", "tooltip.teknikmod.transfer": "Aktarım: %s FE/t",
           "tooltip.teknikmod.coal_fuel": "Yakıt: Kömür, Odun Kömürü, Kömür Bloğu",
           "tooltip.teknikmod.speed": "Hız: %sx", "tooltip.teknikmod.usage": "Tüketim: %s FE/t", "message.teknikmod.progress": "İlerleme: %%%s (%s FE/t)",
           "tooltip.teknikmod.creative": "Yaratıcı kademe: sınırsız, yakıt ve enerji gerektirmez",
           "tooltip.teknikmod.creative_recipe": "Extended Crafting Ultimate Masasında üretilir"})
w(f"assets/{M}/lang/en_us.json", en); w(f"assets/{M}/lang/tr_tr.json", tr)

# --- loot + etiketler ---
for b in blocks:
    w(f"data/{M}/loot_table/blocks/{b}.json", {"type": "minecraft:block", "pools": [{"rolls": 1,
        "entries": [{"type": "minecraft:item", "name": f"{M}:{b}"}], "conditions": [{"condition": "minecraft:survives_explosion"}]}]})
w(f"data/{M}/tags/item/coal_generator_fuel.json", {"replace": False, "values": ["#minecraft:coals", "minecraft:coal_block"]})
w("data/minecraft/tags/block/mineable/pickaxe.json", {"replace": False, "values": [f"{M}:{b}" for b in blocks]})
w("data/minecraft/tags/block/needs_stone_tool.json", {"replace": False, "values": [f"{M}:{b}" for b in blocks if "cable" not in b]})
print(len(blocks), "blok")
