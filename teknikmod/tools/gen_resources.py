"""Dokulari, modelleri, dil dosyalarini, tarifleri ve loot tablolarini uretir.
Kullanim: python3 tools/gen_resources.py src/main/resources   (Pillow gerekir)"""
import json, os, random, shutil, sys
from PIL import Image, ImageDraw
R = sys.argv[1]
M = "teknikmod"
for d in (f"assets/{M}", f"data/{M}", "data/minecraft"):
    shutil.rmtree(os.path.join(R, d), ignore_errors=True)
def w(path, obj):
    p = os.path.join(R, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: json.dump(obj, f, indent=2, ensure_ascii=False); f.write("\n")
def save(img, name):
    p = os.path.join(R, f"assets/{M}/textures/{name}.png"); os.makedirs(os.path.dirname(p), exist_ok=True); img.save(p)

# kademe: onek, vurgu rengi (None = sade), EN/TR ad oneki, yukseltme malzemesi
TIERS = [("", None, "", "", None),
         ("advanced_", (240, 196, 60), "Advanced ", "Gelişmiş ", "#c:ingots/gold"),
         ("elite_", (80, 220, 215), "Elite ", "Elit ", "#c:gems/diamond")]

def noisy(base, var=8, size=16):
    img = Image.new("RGBA", (size, size))
    for x in range(size):
        for y in range(size):
            d = random.randint(-var, var)
            img.putpixel((x, y), tuple(max(0, min(255, c + d)) for c in base) + (255,))
    return img
def casing(accent):
    img = noisy((132, 136, 142)); d = ImageDraw.Draw(img)
    light, dark = (176, 180, 186, 255), (84, 87, 92, 255)
    d.line([(0, 0), (15, 0)], fill=light); d.line([(0, 0), (0, 15)], fill=light)
    d.line([(0, 15), (15, 15)], fill=dark); d.line([(15, 0), (15, 15)], fill=dark)
    rivet = accent + (255,) if accent else dark
    for p in [(2, 2), (13, 2), (2, 13), (13, 13)]: img.putpixel(p, rivet)  # percinler
    if accent:  # kademe seridi: koselerde renkli L seklinde kenar
        a = accent + (255,)
        for (x, y, dx, dy) in [(1, 1, 1, 1), (14, 1, -1, 1), (1, 14, 1, -1), (14, 14, -1, -1)]:
            d.line([(x, y), (x + 2 * dx, y)], fill=a); d.line([(x, y), (x, y + 2 * dy)], fill=a)
    return img

B = f"{M}:block/"
blocks, en, tr = [], {}, {}
def shaped(name, pattern, key, count=1):
    w(f"data/{M}/recipe/{name}.json", {"type": "minecraft:crafting_shaped", "category": "redstone", "pattern": pattern,
        "key": {k: ({"tag": v[1:]} if v.startswith("#") else {"item": v}) for k, v in key.items()},
        "result": {"id": f"{M}:{name}", "count": count}})
I, C, G, RS = "#c:ingots/iron", "#c:ingots/copper", "#c:ingots/gold", "#c:dusts/redstone"

for ti, (pre, accent, en_pre, tr_pre, upgrade) in enumerate(TIERS):
    random.seed(41 + ti)
    side, top = pre + "machine_side", pre + "machine_top"
    save(casing(accent), "block/" + side)
    img = casing(accent); ImageDraw.Draw(img).rectangle([5, 5, 10, 10], outline=(84, 87, 92, 255), fill=(110, 113, 118, 255)); save(img, "block/" + top)
    # komur jeneratoru
    for lit in (False, True):
        img = casing(accent); d = ImageDraw.Draw(img)
        d.rectangle([3, 3, 12, 6], fill=(60, 62, 66, 255))           # havalandirma
        for x in range(4, 12, 2): d.line([(x, 4), (x, 5)], fill=(30, 30, 32, 255))
        d.rectangle([4, 8, 11, 13], fill=(40, 40, 42, 255))          # yanma odasi
        if lit:
            d.rectangle([5, 10, 10, 13], fill=(255, 120, 20, 255)); d.rectangle([6, 11, 9, 13], fill=(255, 210, 60, 255)); d.point((7, 9), fill=(255, 120, 20, 255))
        else:
            d.rectangle([5, 12, 10, 13], fill=(24, 24, 26, 255))
        save(img, f"block/{pre}coal_generator_front" + ("_on" if lit else ""))
    # gunes paneli: kademe arttikca hucreler aciklasir, cerceve kademe rengini alir
    cell = [(28, 52, 120), (30, 70, 150), (24, 96, 170)][ti]
    grid = (accent or (150, 160, 175)) + (255,)
    img = noisy(cell, 5); d = ImageDraw.Draw(img)
    for i in (0, 5, 10, 15): d.line([(i, 0), (i, 15)], fill=grid); d.line([(0, i), (15, i)], fill=grid)
    for (x, y) in [(2, 2), (7, 7), (12, 12), (12, 2)]: img.putpixel((x, y), tuple(min(255, c + 70) for c in cell) + (255,))
    save(img, f"block/{pre}solar_panel_top")
    img = casing(accent); ImageDraw.Draw(img).line([(0, 0), (15, 0)], fill=cell + (255,)); save(img, f"block/{pre}solar_panel_side")
    # batarya
    img = casing(accent); d = ImageDraw.Draw(img)
    d.rectangle([6, 3, 9, 12], fill=(30, 30, 32, 255))
    for y, c in zip((10, 7, 4), ((200, 40, 40), (230, 170, 40), (70, 200, 80))): d.rectangle([7, y, 8, y + 1], fill=c + (255,))
    save(img, f"block/{pre}battery_side")
    img = casing(accent); d = ImageDraw.Draw(img)
    d.rectangle([5, 5, 10, 10], fill=(40, 40, 42, 255)); d.rectangle([6, 6, 9, 9], fill=(214, 120, 60, 255)); d.rectangle([7, 7, 8, 8], fill=(250, 200, 120, 255))
    save(img, f"block/{pre}battery_front")

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
    for b, en_name, tr_name in ((cg, "Coal Generator", "Kömür Jeneratörü"), (sp, "Solar Panel", "Güneş Paneli"), (bt, "Battery", "Batarya")):
        w(f"assets/{M}/models/item/{b}.json", {"parent": B + b})
        blocks.append(b); en[f"block.{M}.{b}"] = en_pre + en_name; tr[f"block.{M}.{b}"] = tr_pre + tr_name
    if upgrade is None:
        shaped(cg, ["III", "IFI", "CRC"], {"I": I, "F": "minecraft:furnace", "C": C, "R": RS})
        shaped(sp, ["GGG", "LRL", "ICI"], {"G": "#c:glass_blocks", "L": "#c:gems/lapis", "R": RS, "I": I, "C": C})
        shaped(bt, ["ICI", "IRI", "IRI"], {"I": I, "C": C, "R": "#c:storage_blocks/redstone"})
    else:  # onceki kademenin etrafina 4 yukseltme malzemesi
        prev = TIERS[ti - 1][0]
        for kind in ("coal_generator", "solar_panel", "battery"):
            shaped(pre + kind, [" U ", "UMU", " U "], {"U": upgrade, "M": f"{M}:{prev}{kind}"})

# --- kablolar ---
random.seed(7)
rot = {"north": {}, "east": {"y": 90}, "south": {"y": 180}, "west": {"y": 270}, "up": {"x": 270}, "down": {"x": 90}}
CABLES = [("copper_cable", (196, 108, 70), "Copper Cable", "Bakır Kablo"), ("gold_cable", (238, 200, 60), "Gold Cable", "Altın Kablo"),
          ("diamond_cable", (96, 220, 214), "Diamond Cable", "Elmas Kablo")]
for c, base, en_name, tr_name in CABLES:
    img = noisy(base, 10); d = ImageDraw.Draw(img); edge = tuple(int(v * .7) for v in base) + (255,)
    for i in (0, 15): d.line([(i, 0), (i, 15)], fill=edge); d.line([(0, i), (15, i)], fill=edge)
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

# --- GUI ---
g = Image.new("RGBA", (256, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
BG, LI, DK, BLK = (198, 198, 198, 255), (255, 255, 255, 255), (85, 85, 85, 255), (0, 0, 0, 255)
d.rectangle([0, 0, 175, 165], fill=BLK); d.rectangle([1, 1, 174, 164], fill=BG)
d.rectangle([1, 1, 173, 2], fill=LI); d.rectangle([1, 1, 2, 163], fill=LI)
d.rectangle([2, 163, 174, 164], fill=DK); d.rectangle([173, 2, 174, 164], fill=DK)
for p in [(0, 0), (175, 0), (0, 165), (175, 165)]: g.putpixel(p, (0, 0, 0, 0))
def inset(x, y, wd, ht, fill=(139, 139, 139, 255)):
    d.rectangle([x, y, x + wd - 1, y + ht - 1], fill=fill)
    d.line([(x, y), (x + wd - 2, y)], fill=(55, 55, 55, 255)); d.line([(x, y), (x, y + ht - 2)], fill=(55, 55, 55, 255))
    d.line([(x + 1, y + ht - 1), (x + wd - 1, y + ht - 1)], fill=LI); d.line([(x + wd - 1, y + 1), (x + wd - 1, y + ht - 1)], fill=LI)
inset(79, 43, 18, 18)
for r in range(3):
    for c in range(9): inset(7 + c * 18, 83 + r * 18, 18, 18)
for c in range(9): inset(7 + c * 18, 141, 18, 18)
inset(151, 16, 14, 54, fill=(40, 16, 16, 255))   # enerji cubugu
inset(80, 25, 16, 16, fill=(70, 70, 70, 255))    # yanma gostergesi
save(g, "gui/coal_generator")

# --- dil ---
en.update({"itemGroup.teknikmod": "Teknik Mod", "message.teknikmod.energy": "Energy: %s / %s FE", "message.teknikmod.rate": "Generating: %s FE/t",
           "tooltip.teknikmod.generation": "Generation: %s FE/t", "tooltip.teknikmod.capacity": "Capacity: %s FE", "tooltip.teknikmod.transfer": "Transfer: %s FE/t"})
tr.update({"itemGroup.teknikmod": "Teknik Mod", "message.teknikmod.energy": "Enerji: %s / %s FE", "message.teknikmod.rate": "Üretim: %s FE/t",
           "tooltip.teknikmod.generation": "Üretim: %s FE/t", "tooltip.teknikmod.capacity": "Kapasite: %s FE", "tooltip.teknikmod.transfer": "Aktarım: %s FE/t"})
w(f"assets/{M}/lang/en_us.json", en); w(f"assets/{M}/lang/tr_tr.json", tr)

# --- loot + etiketler ---
for b in blocks:
    w(f"data/{M}/loot_table/blocks/{b}.json", {"type": "minecraft:block", "pools": [{"rolls": 1,
        "entries": [{"type": "minecraft:item", "name": f"{M}:{b}"}], "conditions": [{"condition": "minecraft:survives_explosion"}]}]})
w("data/minecraft/tags/block/mineable/pickaxe.json", {"replace": False, "values": [f"{M}:{b}" for b in blocks]})
w("data/minecraft/tags/block/needs_stone_tool.json", {"replace": False, "values": [f"{M}:{b}" for b in blocks if "cable" not in b]})
print(len(blocks), "blok")
