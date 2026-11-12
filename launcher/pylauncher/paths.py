"""Launcher'ın disk üzerindeki dizin düzeni."""
import os
import platform
import sys
from pathlib import Path


def default_root() -> Path:
    env = os.environ.get("PYLAUNCHER_HOME")
    if env:
        return Path(env).expanduser()
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home())) / "PyLauncher"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "PyLauncher"
    return Path.home() / ".pylauncher"


class Paths:
    def __init__(self, root=None):
        self.root = Path(root).expanduser() if root else default_root()
        self.versions = self.root / "versions"
        self.libraries = self.root / "libraries"
        self.assets = self.root / "assets"
        self.runtimes = self.root / "runtimes"
        self.game = self.root / "game"
        self.accounts = self.root / "accounts.json"
        self.config = self.root / "config.json"

    def version_dir(self, vid):
        return self.versions / vid

    def version_json(self, vid):
        return self.versions / vid / f"{vid}.json"

    def version_jar(self, vid):
        return self.versions / vid / f"{vid}.jar"

    def natives_dir(self, vid):
        return self.versions / vid / "natives"


def os_name() -> str:
    """Mojang'ın sürüm dosyalarında kullandığı işletim sistemi adı."""
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "osx"
    return "linux"


def os_arch() -> str:
    m = platform.machine().lower()
    if m in ("arm64", "aarch64"):
        return "arm64"
    if m in ("x86_64", "amd64"):
        return "x64"
    return "x86"
