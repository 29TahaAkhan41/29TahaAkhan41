"""CurseForge'a içe aktarılabilir modpack zip'i üretir.

Kullanım:  CF_API_KEY=... python3 modpack/tools/build_pack.py
Çıktı:     modpack/dist/YildizYolu-<sürüm>.zip  (CurseForge → Import)
           modpack/dist/resolved.json            (bulunan dosyalar)
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mods import MODS  # noqa: E402


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
API = "https://api.curseforge.com/v1"
GAME, MC, NEOFORGE = 432, "1.21.1", 6
PACK_NAME, PACK_VERSION = "Yıldız Yolu", "1.0.0"
REQUIRED_DEP = 3
# İstemci tarafı modları: sunucu paketinde gereksiz ama CurseForge istemci zip'inde kalır.


def get(path, **params):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, headers={
        "x-api-key": os.environ.get("CF_API_KEY", "proxy-injected"),
        "Accept": "application/json",
        "User-Agent": "modpack-builder",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if attempt == 3:
                raise
        except urllib.error.URLError:
            if attempt == 3:
                raise
        time.sleep(2 ** attempt)


def post(path, body):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode(), headers={
        "x-api-key": os.environ.get("CF_API_KEY", "proxy-injected"),
        "Accept": "application/json", "Content-Type": "application/json",
        "User-Agent": "modpack-builder",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def best_file(mod_id):
    res = get(f"/mods/{mod_id}/files", gameVersion=MC, modLoaderType=NEOFORGE, pageSize=50)
    files = [f for f in (res or {}).get("data", []) if MC in f["gameVersions"]
             and any(v.lower() == "neoforge" for v in f["gameVersions"])]
    if not files:
        return None
    # Önce kararlı (1), sonra beta (2), sonra alfa (3); her grupta en yenisi.
    files.sort(key=lambda f: (f["releaseType"], -f["id"]))
    return files[0]


def latest_neoforge():
    url = "https://maven.neoforged.net/releases/net/neoforged/neoforge/maven-metadata.xml"
    with urllib.request.urlopen(url, timeout=30) as r:
        xml = r.read().decode()
    vers = [v for v in re.findall(r"<version>([^<]+)</version>", xml)
            if v.startswith("21.1.") and "beta" not in v]
    return max(vers, key=lambda v: [int(x) for x in v.split(".")])


def main():
    os.makedirs(DIST, exist_ok=True)
    resolved, missing = {}, []
    wanted = [(n, i, "liste") for n, i in MODS if i]
    missing += [(n, "proje numarası yok") for n, i in MODS if not i]
    info = {m["id"]: m for m in post("/mods", {"modIds": [i for _, i, _ in wanted]})["data"]}
    queue = list(wanted)
    while queue:
        name, pid, why = queue.pop(0)
        if pid in resolved:
            continue
        mod = info.get(pid) or (get(f"/mods/{pid}") or {}).get("data")
        if not mod:
            missing.append((name, "CurseForge'da bulunamadı"))
            continue
        f = best_file(pid)
        if not f:
            missing.append((mod["name"], "1.21.1 NeoForge dosyası yok"))
            continue
        resolved[pid] = {
            "name": mod["name"], "slug": mod["slug"], "projectID": pid, "fileID": f["id"],
            "fileName": f["fileName"], "releaseType": f["releaseType"], "reason": why,
            "downloadUrl": f.get("downloadUrl"),
        }
        tag = {1: "", 2: " (beta)", 3: " (alfa)"}[f["releaseType"]]
        print(f"  ✓ {mod['name'][:45]:<45} {f['fileName']}{tag}" + ("" if why == "liste" else f"   ← {why}"), flush=True)
        for dep in f.get("dependencies", []):
            if dep["relationType"] == REQUIRED_DEP and dep["modId"] not in resolved:
                queue.append((str(dep["modId"]), dep["modId"], f"{mod['name']} bağımlılığı"))

    neo = latest_neoforge()
    manifest = {
        "minecraft": {"version": MC, "modLoaders": [{"id": f"neoforge-{neo}", "primary": True}]},
        "manifestType": "minecraftModpack",
        "manifestVersion": 1,
        "name": PACK_NAME,
        "version": PACK_VERSION,
        "author": "",
        "files": [{"projectID": r["projectID"], "fileID": r["fileID"], "required": True}
                  for r in resolved.values()],
        "overrides": "overrides",
    }
    with open(os.path.join(DIST, "resolved.json"), "w", encoding="utf-8") as fp:
        json.dump({"neoforge": neo, "mods": list(resolved.values()), "missing": missing},
                  fp, ensure_ascii=False, indent=2)

    out = os.path.join(DIST, f"YildizYolu-{PACK_VERSION}.zip")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        z.writestr("modlist.html", "<ul>\n" + "\n".join(
            f'<li><a href="https://www.curseforge.com/minecraft/mc-mods/{r["slug"]}">{r["name"]}</a></li>'
            for r in sorted(resolved.values(), key=lambda r: r["name"].lower())) + "\n</ul>\n")
        src = os.path.join(ROOT, "overrides")
        for base, _, files in os.walk(src):
            for fn in files:
                full = os.path.join(base, fn)
                z.write(full, os.path.join("overrides", os.path.relpath(full, src)))

    print(f"\nNeoForge {neo}")
    print(f"Toplam {len(resolved)} mod (listeden ve bağımlılıklardan), eksik {len(missing)}")
    for n, why in missing:
        print(f"  ✗ {n}: {why}")
    print(f"Zip: {out}")


if __name__ == "__main__":
    main()
