"""Bir sürümün dosyalarını kurar: istemci jar'ı, kütüphaneler, native'ler, asset'ler."""
import json
import shutil
import zipfile
from pathlib import Path

from . import http, versions
from .paths import os_arch, os_name
from .rules import allowed

LIBRARIES_URL = "https://libraries.minecraft.net/"
RESOURCES_URL = "https://resources.download.minecraft.net/"


def maven_path(name: str) -> str:
    """'grup:ad:sürüm[:sınıflandırıcı][@uzantı]' -> depo içi göreli yol."""
    ext = "jar"
    if "@" in name:
        name, ext = name.split("@", 1)
    parts = name.split(":")
    group, artifact, version = parts[0], parts[1], parts[2]
    classifier = f"-{parts[3]}" if len(parts) > 3 else ""
    return f"{group.replace('.', '/')}/{artifact}/{version}/{artifact}-{version}{classifier}.{ext}"


class Library:
    """Çözülmüş kütüphane: indirilecek işler + classpath + açılacak native'ler."""

    def __init__(self):
        self.jobs, self.classpath, self.natives = [], [], []


def resolve_libraries(paths, version, features=None):
    out = Library()
    for lib in version.get("libraries", []):
        if not allowed(lib.get("rules"), features):
            continue
        downloads = lib.get("downloads")
        native_key = (lib.get("natives") or {}).get(os_name())
        if native_key:
            native_key = native_key.replace("${arch}", "32" if os_arch() == "x86" else "64")
        exclude = (lib.get("extract") or {}).get("exclude", [])
        if downloads is not None:
            art = downloads.get("artifact")
            if art and art.get("url"):
                rel = art.get("path") or maven_path(lib["name"])
                dest = paths.libraries / rel
                out.jobs.append(http.Job(art["url"], dest, art.get("sha1")))
                out.classpath.append(dest)
            nat = (downloads.get("classifiers") or {}).get(native_key) if native_key else None
            if nat:
                rel = nat.get("path") or maven_path(f"{lib['name']}:{native_key}")
                dest = paths.libraries / rel
                out.jobs.append(http.Job(nat["url"], dest, nat.get("sha1")))
                out.natives.append((dest, exclude))
        else:
            # Fabric/Forge tarzı: yalnızca Maven adı ve depo adresi verilir.
            base = lib.get("url") or LIBRARIES_URL
            if not base.endswith("/"):
                base += "/"
            name = f"{lib['name']}:{native_key}" if native_key else lib["name"]
            rel = maven_path(name)
            dest = paths.libraries / rel
            out.jobs.append(http.Job(base + rel, dest, lib.get("sha1")))
            if native_key:
                out.natives.append((dest, exclude))
            else:
                out.classpath.append(dest)
    return out


def extract_natives(natives, dest: Path):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    root = dest.resolve()
    for jar, exclude in natives:
        with zipfile.ZipFile(jar) as z:
            for info in z.infolist():
                n = info.filename
                if info.is_dir() or n.startswith("META-INF/"):
                    continue
                if any(n.startswith(e) for e in exclude):
                    continue
                target = (dest / n).resolve()
                if root not in target.parents:  # zip-slip koruması
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)


def install_assets(paths, version, progress=None):
    index = version.get("assetIndex")
    if not index:
        return
    index_path = paths.assets / "indexes" / f"{index['id']}.json"
    http.download(index["url"], index_path, index.get("sha1"))
    data = json.loads(index_path.read_text(encoding="utf-8"))
    jobs = []
    for obj in data["objects"].values():
        h = obj["hash"]
        jobs.append(
            http.Job(
                f"{RESOURCES_URL}{h[:2]}/{h}",
                paths.assets / "objects" / h[:2] / h,
                size=obj["size"],
            )
        )
    http.download_many(jobs, progress, "Asset'ler")
    # Çok eski sürümler asset'leri gerçek dosya adlarıyla ister.
    if data.get("virtual") or data.get("map_to_resources"):
        legacy = legacy_assets_dir(paths, version, data)
        for name, obj in data["objects"].items():
            dest = legacy / name
            if not dest.is_file():
                dest.parent.mkdir(parents=True, exist_ok=True)
                h = obj["hash"]
                shutil.copyfile(paths.assets / "objects" / h[:2] / h, dest)


def legacy_assets_dir(paths, version, index_data=None):
    if index_data and index_data.get("map_to_resources"):
        return paths.game / "resources"
    return paths.assets / "virtual" / version["assetIndex"]["id"]


def install(paths, vid, progress=None):
    """Sürümü eksiksiz kurar ve çözülmüş sürüm JSON'unu döndürür."""
    version = versions.load(paths, vid)
    jar_id = version["jar"]
    client = (version.get("downloads") or {}).get("client")
    if client:
        if progress:
            progress("İstemci", 0, 1)
        http.download(client["url"], paths.version_jar(jar_id), client.get("sha1"))
        if progress:
            progress("İstemci", 1, 1)
    libs = resolve_libraries(paths, version)
    http.download_many(libs.jobs, progress, "Kütüphaneler")
    install_assets(paths, version, progress)
    return version
