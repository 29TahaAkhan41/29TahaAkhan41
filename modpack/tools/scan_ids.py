"""Mod jar'larını indirip içlerindeki eşya/blok ID'lerini çıkarır (görev doğrulaması için).

Kullanım: python3 modpack/tools/scan_ids.py <resolved.json> <çalışma_klasörü> [ek proje numaraları...]
Çıktı:    <çalışma_klasörü>/ids.json  {namespace: [isimler]}
Jar'lar işlendikten sonra silinir.
"""
import json
import os
import re
import sys
import urllib.request
import zipfile

resolved, work = sys.argv[1], sys.argv[2]
os.makedirs(work, exist_ok=True)
out_path = os.path.join(work, "ids.json")
ids = json.load(open(out_path)) if os.path.exists(out_path) else {}
done = set(ids.pop("__done__", []))
LANG = re.compile(r"^(?:item|block)\.([a-z0-9_.-]+)\.([a-z0-9_/.-]+)$")


def harvest(jar):
    found = {}
    with zipfile.ZipFile(jar) as z:
        for n in z.namelist():
            m = re.match(r"assets/([^/]+)/models/item/([^.]+)\.json$", n)
            if m:
                found.setdefault(m.group(1), set()).add(m.group(2))
            m = re.match(r"assets/([^/]+)/items/([^.]+)\.json$", n)
            if m:
                found.setdefault(m.group(1), set()).add(m.group(2))
            if re.match(r"assets/[^/]+/lang/en_us\.json$", n):
                try:
                    data = json.loads(z.read(n).decode("utf-8", "ignore"))
                except ValueError:
                    continue
                for k in data:
                    m = LANG.match(k)
                    if m:
                        found.setdefault(m.group(1), set()).add(m.group(2))
            if n.startswith("META-INF/jarjar/") and n.endswith(".jar"):
                inner = os.path.join(work, "inner.jar")
                with open(inner, "wb") as f:
                    f.write(z.read(n))
                try:
                    for ns, names in harvest(inner).items():
                        found.setdefault(ns, set()).update(names)
                except zipfile.BadZipFile:
                    pass
    return found


def url_for(f):
    if f.get("downloadUrl"):
        return f["downloadUrl"]
    fid = f["fileID"]
    return f"https://edge.forgecdn.net/files/{fid // 1000}/{fid % 1000}/{urllib.parse.quote(f['fileName'])}"


import urllib.parse  # noqa: E402

mods = json.load(open(resolved))["mods"]
for f in mods:
    key = str(f["fileID"])
    if key in done:
        continue
    jar = os.path.join(work, "mod.jar")
    try:
        req = urllib.request.Request(url_for(f), headers={"User-Agent": "modpack-builder"})
        with urllib.request.urlopen(req, timeout=120) as r, open(jar, "wb") as o:
            o.write(r.read())
        found = harvest(jar)
        for ns, names in found.items():
            ids[ns] = sorted(set(ids.get(ns, [])) | names)
        print(f"  {f['name'][:40]:<40} {sum(len(v) for v in found.values()):>5} id", flush=True)
        done.add(key)
    except Exception as e:  # noqa: BLE001
        print(f"  ! {f['name']}: {e}", flush=True)
    finally:
        if os.path.exists(jar):
            os.remove(jar)
    ids["__done__"] = sorted(done)
    json.dump(ids, open(out_path, "w"))
    ids.pop("__done__")
print("namespace:", len(ids))
