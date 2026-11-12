"""Java bulma ve gerekirse Mojang'ın resmi Java çalışma ortamını indirme."""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import http
from .paths import os_arch, os_name

RUNTIME_INDEX = (
    "https://launchermeta.mojang.com/v1/products/java-runtime/"
    "2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json"
)
EXE = "javaw.exe" if sys.platform == "win32" else "java"


class JavaError(Exception):
    pass


def runtime_platform():
    name, arch = os_name(), os_arch()
    if name == "windows":
        return {"x64": "windows-x64", "x86": "windows-x86", "arm64": "windows-arm64"}[arch]
    if name == "osx":
        return "mac-os-arm64" if arch == "arm64" else "mac-os"
    return {"x64": "linux", "x86": "linux-i386"}.get(arch)


def java_major(java) -> int:
    """'java -version' çıktısından ana sürümü okur (8, 17, 21...). Hata: 0."""
    try:
        out = subprocess.run(
            [str(java), "-version"], capture_output=True, text=True, timeout=20
        )
    except (OSError, subprocess.SubprocessError):
        return 0
    m = re.search(r'version "(\d+)(?:\.(\d+))?', out.stderr + out.stdout)
    if not m:
        return 0
    major = int(m.group(1))
    return int(m.group(2) or 0) if major == 1 else major


def system_candidates():
    names = ["java.exe"] if sys.platform == "win32" else ["java"]
    found = []
    home = os.environ.get("JAVA_HOME")
    if home:
        found += [Path(home) / "bin" / n for n in names]
    which = shutil.which("java")
    if which:
        found.append(Path(which))
    roots = {
        "linux": ["/usr/lib/jvm"],
        "osx": ["/Library/Java/JavaVirtualMachines"],
        "windows": [r"C:\Program Files\Java", r"C:\Program Files\Eclipse Adoptium"],
    }[os_name()]
    for root in roots:
        r = Path(root)
        if r.is_dir():
            for d in sorted(r.iterdir(), reverse=True):
                for sub in ("bin", "Contents/Home/bin"):
                    found += [d / sub / n for n in names]
    return [p for p in found if p.is_file()]


def find_system(major):
    for cand in system_candidates():
        if java_major(cand) == major:
            return cand
    return None


def runtime_exe(paths, component):
    base = paths.runtimes / component
    sub = "jre.bundle/Contents/Home/bin" if os_name() == "osx" else "bin"
    return base / sub / EXE


def install_runtime(paths, component, progress=None):
    """Mojang'ın dağıttığı Java çalışma ortamını runtimes/ altına kurar."""
    exe = runtime_exe(paths, component)
    marker = paths.runtimes / component / ".complete"
    if marker.is_file() and exe.is_file():
        return exe
    plat = runtime_platform()
    entries = http.fetch_json(RUNTIME_INDEX).get(plat or "", {}).get(component) or []
    if not entries:
        raise JavaError(
            f"Bu platform için hazır Java yok ({component}). "
            "Lütfen Java'yı elle kurun ya da --java ile yolunu verin."
        )
    files = http.fetch_json(entries[0]["manifest"]["url"])["files"]
    base = paths.runtimes / component
    jobs, links, execs = [], [], []
    for rel, info in files.items():
        target = base / rel
        if info["type"] == "directory":
            target.mkdir(parents=True, exist_ok=True)
        elif info["type"] == "file":
            raw = info["downloads"]["raw"]
            jobs.append(http.Job(raw["url"], target, raw["sha1"]))
            if info.get("executable"):
                execs.append(target)
        elif info["type"] == "link":
            links.append((target, info["target"]))
    http.download_many(jobs, progress, f"Java ({component})")
    if sys.platform != "win32":
        for p in execs:
            p.chmod(0o755)
        for link, dest in links:
            link.parent.mkdir(parents=True, exist_ok=True)
            if not link.is_symlink() and not link.exists():
                os.symlink(dest, link)
    marker.write_text("ok")
    return exe


def ensure(paths, version, override=None, progress=None):
    """Sürümün istediği Java'yı döndürür: elle verilen > sistemdeki > indirilen."""
    if override:
        if not Path(override).is_file():
            raise JavaError(f"Java bulunamadı: {override}")
        return Path(override)
    want = version.get("javaVersion") or {"component": "jre-legacy", "majorVersion": 8}
    exe = runtime_exe(paths, want["component"])
    if exe.is_file() and (paths.runtimes / want["component"] / ".complete").is_file():
        return exe
    system = find_system(want["majorVersion"])
    if system:
        return system
    return install_runtime(paths, want["component"], progress)
