"""Komut satırı arayüzü."""
import argparse
import json
import sys

from . import NAME, __version__, auth, http, install, java, launch, versions
from .paths import Paths


def progress_printer():
    state = {"label": None}

    def show(label, done, total):
        if not total:
            return
        if not sys.stdout.isatty():  # dosyaya/boruya yazarken satır kalabalığı yapma
            if done == total:
                print(f"{label}: {total} dosya tamam")
            return
        if state["label"] not in (None, label):
            print()
        state["label"] = label
        width = 28
        filled = width * done // total
        print(f"\r{label:<22} [{'#' * filled}{'.' * (width - filled)}] {done}/{total}",
              end="", flush=True)
        if done == total:
            print()
            state["label"] = None

    return show


def cmd_versions(paths, args):
    kinds = ("release", "snapshot", "old_beta", "old_alpha") if args.all else ("release",)
    have = set(versions.installed(paths))
    if args.installed:
        for vid in sorted(have):
            print(vid)
        return
    for v in versions.list_versions(kinds)[: args.limit]:
        mark = "*" if v["id"] in have else " "
        print(f"{mark} {v['id']:<24} {v['type']:<10} {v['releaseTime'][:10]}")
    print("\n* = kurulu")


def _resolve(paths, args):
    vid = versions.resolve_alias(args.version)
    if getattr(args, "fabric", False):
        vid = versions.install_fabric(paths, vid, getattr(args, "loader", None))
    return vid


def cmd_install(paths, args):
    vid = _resolve(paths, args)
    print(f"{vid} kuruluyor -> {paths.root}")
    version = install.install(paths, vid, progress_printer())
    java.ensure(paths, version, args.java, progress_printer())
    print(f"{vid} hazır.")


def cmd_launch(paths, args):
    session = auth.session(paths, offline=args.offline)
    vid = _resolve(paths, args)
    version = install.install(paths, vid, progress_printer())
    exe = java.ensure(paths, version, args.java, progress_printer())
    resolution = tuple(args.resolution) if args.resolution else None
    options = dict(memory_mb=args.memory, resolution=resolution, extra_jvm=args.jvm_arg)
    if args.dry_run:
        cmd = launch.build_command(paths, version, session, exe, **options)
        print(" ".join(launch.redact(cmd)))
        return
    print(f"{vid} başlatılıyor ({session['name']}, Java: {exe})")
    proc = launch.launch(paths, version, session, exe, **options)
    try:
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
    except KeyboardInterrupt:
        proc.terminate()
    code = proc.wait()
    if code:
        print(f"Oyun {code} koduyla kapandı.")
    return code


def cmd_login(paths, args):
    device = auth.start_device_login(paths)
    print(f"\nTarayıcıda şu adresi açın:  {device['verification_uri']}")
    print(f"ve şu kodu girin:           {device['user_code']}\n")
    print("Onay bekleniyor...")
    ms = auth.poll_device_login(paths, device)
    account = auth.finish_login(paths, ms)
    print(f"Giriş yapıldı: {account['name']}")


def cmd_logout(paths, args):
    print("Çıkış yapıldı." if auth.logout(paths, args.name) else "Hesap bulunamadı.")


def cmd_accounts(paths, args):
    data = auth.load_accounts(paths)
    if not data["accounts"]:
        print("Kayıtlı hesap yok. Giriş: python -m pylauncher login")
    for uuid, acc in data["accounts"].items():
        print(f"{'*' if uuid == data.get('active') else ' '} {acc['name']}  ({uuid})")


def cmd_config(paths, args):
    cfg = json.loads(paths.config.read_text(encoding="utf-8")) if paths.config.is_file() else {}
    if args.value is None:
        print(cfg.get(args.key, ""))
        return
    cfg[args.key] = args.value
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.config.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"{args.key} kaydedildi.")


def cmd_gui(paths, args):
    from . import gui
    gui.main(paths)


def build_parser():
    p = argparse.ArgumentParser(prog="pylauncher", description=f"{NAME} {__version__}")
    p.add_argument("--root", help="launcher veri dizini (varsayılan: ~/.pylauncher)")
    sub = p.add_subparsers(dest="command")

    s = sub.add_parser("versions", help="sürümleri listele")
    s.add_argument("--all", action="store_true", help="snapshot ve eski sürümler dahil")
    s.add_argument("--installed", action="store_true", help="yalnızca kurulu olanlar")
    s.add_argument("--limit", type=int, default=25)
    s.set_defaults(func=cmd_versions)

    def version_args(s):
        s.add_argument("version", nargs="?", default="latest",
                       help="örn. 1.21.1, latest, snapshot ya da kurulu bir sürüm kimliği")
        s.add_argument("--fabric", action="store_true", help="Fabric mod yükleyicisiyle")
        s.add_argument("--loader", help="belirli bir Fabric loader sürümü")
        s.add_argument("--java", help="kullanılacak java çalıştırılabilir dosyası")

    s = sub.add_parser("install", help="bir sürümü indir")
    version_args(s)
    s.set_defaults(func=cmd_install)

    s = sub.add_parser("launch", help="bir sürümü (gerekirse kurup) başlat")
    version_args(s)
    s.add_argument("--memory", type=int, default=2048, metavar="MB")
    s.add_argument("--resolution", type=int, nargs=2, metavar=("EN", "BOY"))
    s.add_argument("--jvm-arg", action="append", default=[], help="ek JVM argümanı")
    s.add_argument("--offline", action="store_true",
                   help="kayıtlı hesapla internet doğrulaması olmadan başlat")
    s.add_argument("--dry-run", action="store_true", help="komutu yaz, çalıştırma")
    s.set_defaults(func=cmd_launch)

    sub.add_parser("login", help="Microsoft hesabıyla giriş").set_defaults(func=cmd_login)
    s = sub.add_parser("logout", help="hesabı sil")
    s.add_argument("name", nargs="?")
    s.set_defaults(func=cmd_logout)
    sub.add_parser("accounts", help="hesapları listele").set_defaults(func=cmd_accounts)

    s = sub.add_parser("config", help="ayar oku/yaz (örn. client_id)")
    s.add_argument("key")
    s.add_argument("value", nargs="?")
    s.set_defaults(func=cmd_config)

    sub.add_parser("gui", help="grafik arayüzü aç").set_defaults(func=cmd_gui)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    paths = Paths(args.root)
    func = getattr(args, "func", cmd_gui)
    try:
        return func(paths, args) or 0
    except (auth.AuthError, versions.VersionError, java.JavaError) as e:
        print(f"Hata: {e}", file=sys.stderr)
    except (http.HttpError, OSError) as e:
        print(f"İndirme/dosya hatası: {e}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nİptal edildi.", file=sys.stderr)
    return 1
