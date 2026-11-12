"""Sürüm listesi, sürüm JSON'ları ve inheritsFrom çözümü."""
import json

from . import http

MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
FABRIC_META = "https://meta.fabricmc.net/v2"


class VersionError(Exception):
    pass


def manifest():
    return http.fetch_json(MANIFEST_URL)


def list_versions(kinds=("release",)):
    return [v for v in manifest()["versions"] if v["type"] in kinds]


def resolve_alias(vid, man=None):
    """'latest' / 'latest-snapshot' takma adlarını gerçek sürüme çevirir."""
    if vid in ("latest", "release", "latest-release"):
        return (man or manifest())["latest"]["release"]
    if vid in ("snapshot", "latest-snapshot"):
        return (man or manifest())["latest"]["snapshot"]
    return vid


def load_raw(paths, vid):
    """Sürüm JSON'unu diskten okur; yoksa Mojang'dan indirir."""
    path = paths.version_json(vid)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    for v in manifest()["versions"]:
        if v["id"] == vid:
            http.download(v["url"], path, v.get("sha1"))
            return json.loads(path.read_text(encoding="utf-8"))
    raise VersionError(f"Sürüm bulunamadı: {vid}")


def lib_key(lib):
    """Sürüm numarası hariç kütüphane kimliği (grup:ad[:sınıflandırıcı])."""
    parts = lib.get("name", "").split("@")[0].split(":")
    return ":".join(parts[:2] + parts[3:4])


def merge(child, parent):
    out = dict(parent)
    for k, v in child.items():
        if k == "libraries":
            continue
        if k == "arguments" and "arguments" in parent:
            out[k] = {
                kind: parent[k].get(kind, []) + v.get(kind, [])
                for kind in set(parent[k]) | set(v)
            }
        else:
            out[k] = v
    # Çocuğun kütüphaneleri önce gelir ve aynı kütüphanenin ebeveyn sürümünü ezer.
    mine = child.get("libraries", [])
    overridden = {lib_key(lib) for lib in mine}
    libs = mine + [
        lib for lib in parent.get("libraries", []) if lib_key(lib) not in overridden
    ]
    out["libraries"] = libs
    out.pop("inheritsFrom", None)
    out["jar"] = parent.get("jar") or parent["id"]
    return out


def load(paths, vid):
    """inheritsFrom zinciri çözülmüş, tek parça sürüm JSON'u döndürür."""
    data = load_raw(paths, vid)
    depth = 0
    while "inheritsFrom" in data:
        depth += 1
        if depth > 8:
            raise VersionError("inheritsFrom döngüsü")
        data = merge(data, load_raw(paths, data["inheritsFrom"]))
    data.setdefault("jar", data["id"])
    return data


def installed(paths):
    if not paths.versions.is_dir():
        return []
    return sorted(
        d.name for d in paths.versions.iterdir() if (d / f"{d.name}.json").is_file()
    )


def install_fabric(paths, mc_version, loader=None):
    """Fabric profilini indirir ve yeni sürüm kimliğini döndürür."""
    try:
        loaders = http.fetch_json(f"{FABRIC_META}/versions/loader/{mc_version}")
    except http.HttpError as e:
        raise VersionError(f"Fabric {mc_version} için sorgulanamadı: {e}") from None
    if not loaders:
        raise VersionError(f"Fabric, Minecraft {mc_version} sürümünü desteklemiyor")
    if loader is None:
        stable = [l for l in loaders if l["loader"].get("stable")]
        loader = (stable or loaders)[0]["loader"]["version"]
    profile = http.fetch_json(
        f"{FABRIC_META}/versions/loader/{mc_version}/{loader}/profile/json"
    )
    vid = profile["id"]
    path = paths.version_json(vid)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, indent=2), encoding="utf-8")
    return vid
