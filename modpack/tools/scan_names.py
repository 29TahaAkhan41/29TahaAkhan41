"""Mod jar'larından (ve Minecraft istemcisinden) eşyaların İngilizce adlarını toplar.

Kullanım: python3 modpack/tools/scan_names.py <resolved.json> <çalışma_klasörü>
Çıktı:    <çalışma_klasörü>/names.json  {"mod:eşya": "English Name"}
"""
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import zipfile

resolved, work = sys.argv[1], sys.argv[2]
os.makedirs(work, exist_ok=True)
out = os.path.join(work, "names.json")
names = json.load(open(out)) if os.path.exists(out) else {}
done = set(names.pop("__done__", []))
KEY = re.compile(r"^(?:item|block)\.([a-z0-9_.-]+)\.([a-z0-9_/.-]+)$")


def harvest(data):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for n in z.namelist():
            if re.match(r"assets/[^/]+/lang/en_us\.json$", n):
                try:
                    lang = json.loads(z.read(n).decode("utf-8", "ignore"))
                except ValueError:
                    continue
                for k, v in lang.items():
                    m = KEY.match(k)
                    if m and isinstance(v, str):
                        # item.* öncelikli; block.* yalnızca boşsa
                        key = f"{m.group(1)}:{m.group(2)}"
                        if k.startswith("item.") or key not in names:
                            names[key] = v
            elif n.startswith("META-INF/jarjar/") and n.endswith(".jar"):
                try:
                    harvest(z.read(n))
                except zipfile.BadZipFile:
                    pass


def save():
    names["__done__"] = sorted(done)
    json.dump(names, open(out, "w"), ensure_ascii=False)
    names.pop("__done__")


if "vanilla" not in done:
    man = json.load(urllib.request.urlopen("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"))
    v = next(x for x in man["versions"] if x["id"] == "1.21.1")
    client = json.load(urllib.request.urlopen(v["url"]))["downloads"]["client"]["url"]
    harvest(urllib.request.urlopen(client).read())
    done.add("vanilla")
    save()
    print("vanilla ok", flush=True)

for f in json.load(open(resolved))["mods"]:
    key = str(f["fileID"])
    if key in done:
        continue
    url = f.get("downloadUrl") or (
        f"https://edge.forgecdn.net/files/{f['fileID'] // 1000}/{f['fileID'] % 1000}/{urllib.parse.quote(f['fileName'])}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "modpack-builder"})
        harvest(urllib.request.urlopen(req, timeout=120).read())
        done.add(key)
        print("  ", f["name"], flush=True)
    except Exception as e:  # noqa: BLE001
        print("  !", f["name"], e, flush=True)
    save()
print("toplam ad:", len(names))
