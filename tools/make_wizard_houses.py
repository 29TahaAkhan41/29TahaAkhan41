#!/usr/bin/env python3
"""Generates the wizard house structure files, one per village type.

Run from the repository root:  python3 tools/make_wizard_houses.py   (needs: pip install nbtlib)

All variants share one layout (7 x 11 x 7, entrance on the west side like vanilla village
houses) and the wizard's signature details: purple windows, soul lantern, amethyst roof tip.
Only the building materials change, to match the houses of each village type.
"""
import os

from nbtlib import Compound, File, Int, List, String

OUT = "src/main/resources/data/spellmod/structure/village/wizard_house_%s.nbt"
DATA_VERSION = 5023  # Minecraft 26.3

# wall, base (bottom ring), corner pillar, floor, roof, door, entrance step
VARIANTS = {
    "plains":  dict(wall="oak_planks",       base="cobblestone",       corner="oak_log",            floor="oak_planks",
                    roof="dark_oak_planks",  door="oak_door",          step="oak_stairs"),
    "desert":  dict(wall="smooth_sandstone", base="sandstone",         corner="cut_sandstone",      floor="terracotta",
                    roof="terracotta",       door="jungle_door",       step="sandstone_stairs"),
    "savanna": dict(wall="acacia_planks",    base="yellow_terracotta", corner="acacia_log",         floor="acacia_planks",
                    roof="orange_terracotta", door="acacia_door",      step="acacia_stairs"),
    "snowy":   dict(wall="spruce_planks",    base="stripped_spruce_log", corner="stripped_spruce_log", floor="spruce_planks",
                    roof="snow_block",       door="spruce_door",       step="spruce_stairs"),
    "taiga":   dict(wall="spruce_planks",    base="mossy_cobblestone", corner="spruce_log",         floor="spruce_planks",
                    roof="cobblestone",      door="spruce_door",       step="cobblestone_stairs"),
}


def build(v):
    blocks = {}

    def put(x, y, z, name, props=None, nbt=None):
        props = dict(props or {})
        if name.endswith("_log"):
            props.setdefault("axis", "y")
        blocks[(x, y, z)] = ("minecraft:" + name, tuple(sorted(props.items())), nbt)

    def pane(east_west):
        ew, ns = str(east_west).lower(), str(not east_west).lower()
        return "purple_stained_glass_pane", dict(east=ew, west=ew, north=ns, south=ns, waterlogged="false")

    # Floor and walls.
    for x in range(1, 6):
        for z in range(1, 6):
            edge = x in (1, 5) or z in (1, 5)
            corner = x in (1, 5) and z in (1, 5)
            put(x, 0, z, v["corner"] if corner else (v["base"] if edge else v["floor"]))
            for y in range(1, 5):
                put(x, y, z, v["corner"] if corner else (v["wall"] if edge else "air"))

    # Door in the west wall, windows in the other three.
    for y, half in ((1, "lower"), (2, "upper")):
        put(1, y, 3, v["door"], dict(facing="east", half=half, hinge="right", open="false", powered="false"))
    for y in (2, 3):
        put(3, y, 1, *pane(True))
        put(3, y, 5, *pane(True))
        put(5, y, 3, *pane(False))

    # Furniture.
    put(4, 1, 3, "chest", dict(facing="west", type="single", waterlogged="false"),
        Compound({"LootTable": String("spellmod:chests/wizard_house"), "id": String("minecraft:chest")}))
    put(4, 1, 2, "lectern", dict(facing="west", has_book="false", powered="false"))
    for x, y in ((4, 1), (4, 2), (2, 1), (2, 2), (3, 1)):
        put(x, y, 4, "bookshelf")
    put(2, 1, 2, "cauldron")
    put(3, 4, 3, "soul_lantern", dict(hanging="true", waterlogged="false"))

    # Pointed roof with an amethyst tip.
    for y, inset in ((5, 0), (6, 1), (7, 2)):
        for x in range(inset, 7 - inset):
            for z in range(inset, 7 - inset):
                put(x, y, z, v["roof"])
    put(3, 8, 3, v["roof"])
    put(3, 9, 3, "amethyst_block")
    put(3, 10, 3, "lightning_rod", dict(facing="up", powered="false", waterlogged="false"))

    # Entrance: a jigsaw block that snaps onto a village street and then turns into a step.
    put(0, 0, 3, "jigsaw", dict(orientation="west_up"), Compound({
        "joint": String("aligned"),
        "final_state": String("minecraft:%s[facing=east,half=bottom,shape=straight,waterlogged=false]" % v["step"]),
        "name": String("minecraft:building_entrance"),
        "pool": String("minecraft:empty"),
        "id": String("minecraft:jigsaw"),
        "target": String("minecraft:building_entrance"),
    }))

    palette, index, out = [], {}, []
    for (x, y, z), (name, props, nbt) in sorted(blocks.items(), key=lambda kv: (kv[0][1], kv[0][2], kv[0][0])):
        key = (name, props)
        if key not in index:
            index[key] = len(palette)
            entry = Compound({"id": String(name)})
            if props:
                entry["properties"] = Compound({k: String(val) for k, val in props})
            palette.append(entry)
        block = Compound({"pos": List[Int]([Int(x), Int(y), Int(z)]), "state": Int(index[key])})
        if nbt is not None:
            block["nbt"] = nbt
        out.append(block)
    return File({
        "size": List[Int]([Int(7), Int(11), Int(7)]),
        "entities": List[Compound]([]),
        "blocks": List[Compound](out),
        "palette": List[Compound](palette),
        "DataVersion": Int(DATA_VERSION),
    })


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for village_type, variant in VARIANTS.items():
        build(variant).save(OUT % village_type, gzipped=True)
        print("wrote", OUT % village_type)
