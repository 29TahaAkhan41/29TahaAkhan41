"""Writes the electric furnace's recipes (run: python3 tools/make_recipes.py).

The furnace runs recipes of its own type, `solartech:electric_smelting`: Horizon gives a
native mod the recipes of types outside `minecraft`, not vanilla's smelting table. A data
pack adds more with the same shape."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "content/data/solartech/recipe/electric_smelting"

# ingredient -> result
RECIPES = {
    # Metals
    "raw_iron": "iron_ingot", "raw_gold": "gold_ingot", "raw_copper": "copper_ingot",
    "iron_ore": "iron_ingot", "deepslate_iron_ore": "iron_ingot",
    "gold_ore": "gold_ingot", "deepslate_gold_ore": "gold_ingot", "nether_gold_ore": "gold_ingot",
    "copper_ore": "copper_ingot", "deepslate_copper_ore": "copper_ingot",
    "ancient_debris": "netherite_scrap",
    # Ores mined with silk touch
    "coal_ore": "coal", "deepslate_coal_ore": "coal",
    "diamond_ore": "diamond", "deepslate_diamond_ore": "diamond",
    "emerald_ore": "emerald", "deepslate_emerald_ore": "emerald",
    "lapis_ore": "lapis_lazuli", "deepslate_lapis_ore": "lapis_lazuli",
    "redstone_ore": "redstone", "deepslate_redstone_ore": "redstone",
    "nether_quartz_ore": "quartz",
    # Stone and building
    "cobblestone": "stone", "stone": "smooth_stone", "cobbled_deepslate": "deepslate",
    "sand": "glass", "red_sand": "glass", "sandstone": "smooth_sandstone",
    "red_sandstone": "smooth_red_sandstone", "clay_ball": "brick", "clay": "terracotta",
    "netherrack": "nether_brick", "stone_bricks": "cracked_stone_bricks",
    "quartz_block": "smooth_quartz", "basalt": "smooth_basalt", "wet_sponge": "sponge",
    # Plants
    "cactus": "green_dye", "kelp": "dried_kelp", "chorus_fruit": "popped_chorus_fruit",
    "sea_pickle": "lime_dye",
    # Charcoal
    **{f"{wood}_log": "charcoal" for wood in
       ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "pale_oak")},
    # Food
    "beef": "cooked_beef", "porkchop": "cooked_porkchop", "chicken": "cooked_chicken",
    "mutton": "cooked_mutton", "rabbit": "cooked_rabbit", "cod": "cooked_cod",
    "salmon": "cooked_salmon", "potato": "baked_potato",
}

OUT.mkdir(parents=True, exist_ok=True)
for old in OUT.glob("*.json"):
    old.unlink()
for ingredient, result in RECIPES.items():
    recipe = {
        "type": "solartech:electric_smelting",
        "ingredient": f"minecraft:{ingredient}",
        "result": {"id": f"minecraft:{result}"},
    }
    (OUT / f"{ingredient}.json").write_text(json.dumps(recipe, indent=2) + "\n")
print(len(RECIPES), "recipes")
