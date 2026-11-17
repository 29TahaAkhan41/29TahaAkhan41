"""Görevlerde ve KubeJS tariflerinde kullanılan eşya ID'lerini gerçek mod jar'larından çıkarılan listeyle karşılaştırır.

Kullanım: python3 modpack/tools/validate.py <ids.json> <vanilla.json>
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from quests import CHAPTERS, FINAL  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ids = json.load(open(sys.argv[1]))
ids.pop("__done__", None)
ids["minecraft"] = sorted(set(ids.get("minecraft", [])) | set(json.load(open(sys.argv[2]))))
ids["kubejs"] = ["stellar_essence", "cosmic_core", "creative_catalyst", "flight_ring",
                 "heart_of_the_stars", "completion_medal",
                 "tech_core", "magic_core", "nature_core", "world_core"]
ids.setdefault("ftbquests", []).append("book")
known = {ns: set(v) for ns, v in ids.items()}


def ok(item):
    ns, _, name = item.partition(":")
    return name in known.get(ns, ())


RECIPE_TYPES = {"extendedcrafting:shaped_table"}
bad = []
for ch in CHAPTERS:
    for r, row in enumerate(ch["rows"]):
        for i, q in enumerate(row):
            if q[0] != "checkmark" and not ok(q[0]):
                bad.append((f"görev {ch['key']}/{r}/{i}", q[0]))
    if not ok(ch["icon"]):
        bad.append((f"ikon {ch['key']}", ch["icon"]))
    if not ok(ch["reward"][0]):
        bad.append((f"ödül {ch['key']}", ch["reward"][0]))

js = open(os.path.join(ROOT, "overrides/kubejs/server_scripts/tarifler.js"), encoding="utf-8").read()
for item in sorted(set(re.findall(r"'([a-z0-9_]+:[a-z0-9_/]+)'", js))):
    if item in RECIPE_TYPES or item.startswith(("kubejs:creative/",)):
        continue
    if not ok(item):
        bad.append(("tarif", item))

missing_ns = sorted({b[1].split(":")[0] for b in bad if b[1].split(":")[0] not in known})
for where, item in bad:
    print(f"  ✗ {item:<55} {where}")
print(f"\n{len(bad)} hatalı ID. Hiç bulunmayan namespace'ler: {missing_ns}")
