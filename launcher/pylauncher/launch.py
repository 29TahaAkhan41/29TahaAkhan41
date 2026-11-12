"""Oyunu başlatacak Java komut satırını kurar ve çalıştırır."""
import os
import subprocess

from . import NAME, __version__, install
from .paths import os_name
from .rules import allowed


def _expand(args, features):
    """Kurallı argümanları düz string listesine çevirir."""
    out = []
    for arg in args:
        if isinstance(arg, str):
            out.append(arg)
        elif allowed(arg.get("rules"), features):
            value = arg["value"]
            out += [value] if isinstance(value, str) else value
    return out


def _substitute(args, values):
    result = []
    for arg in args:
        for key, val in values.items():
            arg = arg.replace("${" + key + "}", str(val))
        result.append(arg)
    return result


def build_command(paths, version, session, java, memory_mb=2048,
                  resolution=None, extra_jvm=(), game_dir=None):
    game_dir = game_dir or paths.game
    features = {"has_custom_resolution": bool(resolution)}
    libs = install.resolve_libraries(paths, version, features)
    classpath = [str(p) for p in libs.classpath]
    classpath.append(str(paths.version_jar(version["jar"])))
    natives = paths.natives_dir(version["id"])
    index = version.get("assetIndex", {}).get("id", "legacy")

    values = {
        "auth_player_name": session["name"],
        "auth_uuid": session["uuid"],
        "auth_access_token": session["token"],
        "auth_session": session["token"],
        "auth_xuid": "",
        "clientid": "",
        "user_type": session["type"],
        "user_properties": "{}",
        "version_name": version["id"],
        "version_type": version.get("type", "release"),
        "game_directory": game_dir,
        "assets_root": paths.assets,
        "assets_index_name": index,
        "game_assets": paths.assets / "virtual" / index,
        "natives_directory": natives,
        "launcher_name": NAME,
        "launcher_version": __version__,
        "library_directory": paths.libraries,
        "classpath_separator": os.pathsep,
        "classpath": os.pathsep.join(classpath),
    }
    if resolution:
        values["resolution_width"], values["resolution_height"] = resolution

    arguments = version.get("arguments")
    if arguments:
        jvm = _expand(arguments.get("jvm", []), features)
        game = _expand(arguments.get("game", []), features)
    else:
        game = version.get("minecraftArguments", "").split()
        jvm = []
    if not arguments or not arguments.get("jvm"):
        # 1.12 ve öncesi JVM argümanı tanımlamaz.
        jvm = ["-Djava.library.path=${natives_directory}", "-cp", "${classpath}"]
        if os_name() == "osx":
            jvm.insert(0, "-XstartOnFirstThread")
        if resolution:
            game += ["--width", str(resolution[0]), "--height", str(resolution[1])]

    cmd = [str(java), f"-Xmx{memory_mb}M", f"-Xms{min(512, memory_mb)}M", *extra_jvm]
    cmd += _substitute(jvm, values)
    cmd.append(version["mainClass"])
    cmd += _substitute(game, values)
    return cmd


def redact(cmd):
    """Komutu ekrana basarken erişim token'ını gizler."""
    out, hide = [], False
    for arg in cmd:
        out.append("***" if hide else arg)
        hide = arg in ("--accessToken", "--session")
    return out


def launch(paths, version, session, java, game_dir=None, **options):
    """Native'leri açar ve oyunu başlatır; Popen nesnesini döndürür."""
    game_dir = game_dir or paths.game
    game_dir.mkdir(parents=True, exist_ok=True)
    libs = install.resolve_libraries(paths, version)
    install.extract_natives(libs.natives, paths.natives_dir(version["id"]))
    cmd = build_command(paths, version, session, java, game_dir=game_dir, **options)
    return subprocess.Popen(
        cmd, cwd=game_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
