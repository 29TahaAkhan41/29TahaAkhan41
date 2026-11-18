"""Oyun Çevirmeni ana penceresi."""
from __future__ import annotations

import json
import os
import queue
import shutil
import sys
import threading
import time
import tkinter as tk
import traceback
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from . import file_translator as ft
from .overlay import Overlay, RegionSelector, enable_dpi_awareness
from .screen import OCR_ENGINES, Region, apply_colors, capture, image_signature, make_ocr, \
    monitors, signature_changed
from .translator import AI_BACKENDS, BACKENDS, CONFIG_DIR, KEY_HELP, SOURCE_LANGUAGES, Translator, \
    make_backend

SETTINGS_FILE = CONFIG_DIR / "ayarlar.json"


@dataclass
class Settings:
    source_lang: str = "en"
    backend: str = "google"
    deepl_key: str = ""  # eski sürümlerden kalan ayar; api_keys["deepl"]'e taşınır
    api_keys: dict = None  # motor -> API anahtarı
    ai_models: dict = None  # yapay zekâ motoru -> model adı (boşsa varsayılan)
    ocr_engine: str = "tesseract"
    tesseract_path: str = ""
    monitor: int = 0
    region: list | None = None  # [left, top, width, height] veya None = tüm monitör
    hotkey_translate: str = "F9"
    hotkey_toggle: str = "F10"
    hotkey_auto: str = "F11"
    auto_interval: float = 2.0
    opacity: float = 0.95
    match_colors: bool = True

    def __post_init__(self):
        self.api_keys = dict(self.api_keys or {})
        self.ai_models = dict(self.ai_models or {})
        if self.deepl_key and "deepl" not in self.api_keys:
            self.api_keys["deepl"] = self.deepl_key
        self.deepl_key = ""

    @classmethod
    def load(cls) -> "Settings":
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            names = {f.name for f in fields(cls)}
            return cls(**{k: v for k, v in data.items() if k in names})
        except (OSError, ValueError, TypeError):
            return cls()

    def save(self) -> None:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2),
                                 encoding="utf-8")


FROZEN = getattr(sys, "frozen", False)  # .exe olarak mı çalışıyoruz?


def find_tesseract() -> str:
    # .exe paketinin içindeki Tesseract (OyunCevirmeni.exe'nin yanındaki "tesseract" klasörü)
    if FROZEN:
        bundled = Path(sys.executable).parent / "tesseract" / "tesseract.exe"
        if bundled.is_file():
            return str(bundled)
    found = shutil.which("tesseract")
    if found:
        return found
    for p in (
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        "/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract",
    ):
        if os.path.isfile(p):
            return p
    return ""


def to_pynput_hotkey(text: str) -> str:
    """'ctrl+shift+T' / 'F9' -> '<ctrl>+<shift>+t' / '<f9>'"""
    special = {"ctrl", "alt", "shift", "cmd", "win", "tab", "space", "esc", "enter",
               "home", "end", "insert", "delete", "page_up", "page_down",
               "up", "down", "left", "right", "pause", "scroll_lock"}
    parts = []
    for p in text.lower().replace(" ", "").split("+"):
        if not p:
            continue
        p = {"win": "cmd", "escape": "esc", "del": "delete", "ins": "insert",
             "pgup": "page_up", "pgdn": "page_down", "control": "ctrl"}.get(p, p)
        if p in special or (p.startswith("f") and p[1:].isdigit()):
            parts.append(f"<{p}>")
        else:
            parts.append(p)
    return "+".join(parts)


def _key_by_label(mapping: dict[str, str], label: str) -> str:
    return next((k for k, v in mapping.items() if v == label), next(iter(mapping)))


class App:
    def __init__(self):
        enable_dpi_awareness()
        self.root = tk.Tk()
        self.root.title("Oyun Çevirmeni — Her şeyi Türkçe yap")
        self.root.geometry("780x820")
        self.root.minsize(700, 700)
        self.s = Settings.load()
        if not self.s.tesseract_path or not os.path.isfile(self.s.tesseract_path):
            self.s.tesseract_path = find_tesseract()

        self.events: queue.Queue = queue.Queue()
        self.overlay = Overlay(self.root)
        self.overlay.opacity = self.s.opacity
        self.overlay.match_colors = self.s.match_colors
        self.busy = False
        self.auto_on = False
        self.last_sig: bytes | None = None
        self.hotkeys = None
        self._translator: Translator | None = None
        self._translator_key = None
        self._ocr = None
        self._ocr_key = None

        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")

        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        self.live_tab = ttk.Frame(nb, padding=10)
        self.file_tab = ttk.Frame(nb, padding=10)
        nb.add(self.live_tab, text="  🎮  Canlı Ekran Çevirisi  ")
        nb.add(self.file_tab, text="  📁  Dil Dosyası Çevirisi  ")
        self._build_live()
        self._build_files()

        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.root.after(50, self._pump)
        self._register_hotkeys()

    # ------------------------------------------------------------------ ortak
    def _common_settings(self, parent) -> None:
        box = ttk.LabelFrame(parent, text="Çeviri", padding=8)
        box.pack(fill="x", pady=(0, 8))
        ttk.Label(box, text="Oyunun dili:").grid(row=0, column=0, sticky="w")
        self.var_src = tk.StringVar(value=SOURCE_LANGUAGES.get(self.s.source_lang, "İngilizce"))
        ttk.Combobox(box, textvariable=self.var_src, values=list(SOURCE_LANGUAGES.values()),
                     state="readonly", width=22).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(box, text="→  Türkçe").grid(row=0, column=2, sticky="w")
        ttk.Label(box, text="Çeviri motoru:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.var_backend = tk.StringVar(value=BACKENDS.get(self.s.backend))
        ttk.Combobox(box, textvariable=self.var_backend, values=list(BACKENDS.values()),
                     state="readonly", width=34).grid(row=1, column=1, columnspan=2,
                                                      sticky="w", padx=6, pady=(6, 0))
        ttk.Label(box, text="API anahtarı:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.var_key = tk.StringVar()
        self.ent_key = ttk.Entry(box, textvariable=self.var_key, width=40, show="•")
        self.ent_key.grid(row=2, column=1, columnspan=2, sticky="w", padx=6, pady=(6, 0))
        ttk.Label(box, text="Model:").grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.var_model = tk.StringVar()
        self.ent_model = ttk.Entry(box, textvariable=self.var_model, width=26)
        self.ent_model.grid(row=3, column=1, sticky="w", padx=6, pady=(6, 0))
        self.lbl_key_help = ttk.Label(box, text="", foreground="#777")
        self.lbl_key_help.grid(row=4, column=0, columnspan=3, sticky="w", pady=(4, 0))
        self._shown_backend = self.s.backend
        self._load_backend_fields()
        self.var_backend.trace_add("write", lambda *_: self._on_backend_change())

    def _load_backend_fields(self) -> None:
        """Seçili motorun anahtarını/modelini alanlara yükler, gereksiz alanları kapatır."""
        from .ai_backend import AI_SERVICES

        b = self._shown_backend
        self.var_key.set(self.s.api_keys.get(b, ""))
        self.var_model.set(self.s.ai_models.get(b, ""))
        needs_key = b in KEY_HELP
        self.ent_key.config(state="normal" if needs_key else "disabled")
        self.ent_model.config(state="normal" if b in AI_BACKENDS else "disabled")
        help_text = KEY_HELP.get(b, "Anahtar gerekmez.")
        if b in AI_SERVICES:
            help_text += f"   Varsayılan model: {AI_SERVICES[b].default_model}"
            if b == "ollama":
                help_text = AI_SERVICES[b].key_help
        self.lbl_key_help.config(text=help_text)

    def _store_backend_fields(self) -> None:
        b = self._shown_backend
        key, model = self.var_key.get().strip(), self.var_model.get().strip()
        if b in KEY_HELP:
            self.s.api_keys[b] = key
        if b in AI_BACKENDS:
            self.s.ai_models[b] = model

    def _on_backend_change(self) -> None:
        self._store_backend_fields()
        self._shown_backend = _key_by_label(BACKENDS, self.var_backend.get())
        self._load_backend_fields()

    def _collect(self) -> None:
        self.s.source_lang = _key_by_label(SOURCE_LANGUAGES, self.var_src.get())
        self._store_backend_fields()
        self.s.backend = _key_by_label(BACKENDS, self.var_backend.get())
        self.s.ocr_engine = _key_by_label(OCR_ENGINES, self.var_ocr.get())
        self.s.tesseract_path = self.var_tess.get().strip()
        self.s.monitor = max(0, self.cmb_mon.current())
        try:
            self.s.auto_interval = max(0.5, float(self.var_interval.get().replace(",", ".")))
        except ValueError:
            pass
        self.s.opacity = round(self.var_opacity.get(), 2)
        self.s.match_colors = bool(self.var_colors.get())
        self.overlay.opacity = self.s.opacity
        self.overlay.match_colors = self.s.match_colors
        self.s.save()

    def translator(self) -> Translator:
        api_key = self.s.api_keys.get(self.s.backend, "")
        model = self.s.ai_models.get(self.s.backend, "")
        key = (self.s.backend, api_key, model, self.s.source_lang)
        if self._translator is None or self._translator_key != key:
            self._translator = Translator(make_backend(self.s.backend, api_key, model),
                                          source=self.s.source_lang, target="tr")
            self._translator_key = key
        return self._translator

    def _pump(self) -> None:
        """Arka plan iş parçacıklarından gelen olayları ana iş parçacığında işler."""
        try:
            while True:
                fn, args = self.events.get_nowait()
                fn(*args)
        except queue.Empty:
            pass
        self.root.after(30, self._pump)

    def post(self, fn, *args) -> None:
        self.events.put((fn, args))

    # ----------------------------------------------------------- canlı çeviri
    def _build_live(self) -> None:
        t = self.live_tab
        ttk.Label(
            t, wraplength=700, justify="left",
            text="Oyundaki menü, buton, diyalog ve tüm yazıları ekrandan okuyup üstüne "
                 "Türkçesini yazar. Oyunu 'Pencereli' veya 'Kenarlıksız pencere' modunda "
                 "çalıştırın (tam ekran modunda katman görünmeyebilir).",
        ).pack(fill="x", pady=(0, 8))
        self._common_settings(t)

        box = ttk.LabelFrame(t, text="Ekran ve yazı tanıma (OCR)", padding=8)
        box.pack(fill="x", pady=(0, 8))
        ttk.Label(box, text="Monitör:").grid(row=0, column=0, sticky="w")
        try:
            self.mons = monitors()
        except Exception:
            self.mons = [Region(0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight())]
        self.cmb_mon = ttk.Combobox(
            box, state="readonly", width=28,
            values=[f"Monitör {i + 1} ({m.width}x{m.height})" for i, m in enumerate(self.mons)])
        self.cmb_mon.current(min(self.s.monitor, len(self.mons) - 1))
        self.cmb_mon.grid(row=0, column=1, sticky="w", padx=6)
        self.lbl_region = ttk.Label(box, text="")
        self.lbl_region.grid(row=1, column=1, sticky="w", padx=6, pady=(4, 0))
        ttk.Label(box, text="Alan:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        rb = ttk.Frame(box)
        rb.grid(row=1, column=2, sticky="w", pady=(4, 0))
        ttk.Button(rb, text="Alan seç…", command=self.select_region).pack(side="left")
        ttk.Button(rb, text="Tüm ekran", command=self.clear_region).pack(side="left", padx=4)
        self._update_region_label()

        ttk.Label(box, text="OCR motoru:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.var_ocr = tk.StringVar(value=OCR_ENGINES.get(self.s.ocr_engine))
        ttk.Combobox(box, textvariable=self.var_ocr, values=list(OCR_ENGINES.values()),
                     state="readonly", width=44).grid(row=2, column=1, columnspan=2,
                                                      sticky="w", padx=6, pady=(6, 0))
        ttk.Label(box, text="Tesseract yolu:").grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.var_tess = tk.StringVar(value=self.s.tesseract_path)
        ttk.Entry(box, textvariable=self.var_tess, width=46).grid(
            row=3, column=1, columnspan=2, sticky="w", padx=6, pady=(6, 0))

        box = ttk.LabelFrame(t, text="Kullanım", padding=8)
        box.pack(fill="x", pady=(0, 8))
        self.var_hk = []
        for i, (label, attr) in enumerate((("Ekranı çevir", "hotkey_translate"),
                                            ("Çeviriyi göster/gizle", "hotkey_toggle"),
                                            ("Otomatik mod aç/kapa", "hotkey_auto"))):
            ttk.Label(box, text=f"{label}:").grid(row=i, column=0, sticky="w")
            v = tk.StringVar(value=getattr(self.s, attr))
            ttk.Entry(box, textvariable=v, width=14).grid(row=i, column=1, sticky="w", padx=6)
            self.var_hk.append((attr, v))
        ttk.Button(box, text="Kısayolları uygula", command=self._apply_hotkeys).grid(
            row=0, column=2, sticky="w")
        ttk.Label(box, text="Otomatik yenileme (sn):").grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.var_interval = tk.StringVar(value=str(self.s.auto_interval))
        ttk.Entry(box, textvariable=self.var_interval, width=6).grid(
            row=3, column=1, sticky="w", padx=6, pady=(6, 0))
        ttk.Label(box, text="Katman opaklığı:").grid(row=4, column=0, sticky="w", pady=(6, 0))
        self.var_opacity = tk.DoubleVar(value=self.s.opacity)
        ttk.Scale(box, from_=0.4, to=1.0, variable=self.var_opacity, length=160).grid(
            row=4, column=1, columnspan=2, sticky="w", padx=6, pady=(6, 0))
        self.var_colors = tk.BooleanVar(value=self.s.match_colors)
        ttk.Checkbutton(box, text="Çeviri kutuları oyunun renklerini alsın",
                        variable=self.var_colors).grid(row=5, column=0, columnspan=3,
                                                       sticky="w", pady=(6, 0))

        btns = ttk.Frame(t)
        btns.pack(fill="x", pady=(0, 6))
        ttk.Button(btns, text="▶ Şimdi çevir", command=self.translate_screen).pack(side="left")
        self.btn_auto = ttk.Button(btns, text="⟳ Otomatik modu başlat", command=self.toggle_auto)
        self.btn_auto.pack(side="left", padx=6)
        ttk.Button(btns, text="✕ Temizle", command=self.overlay.clear).pack(side="left")
        self.lbl_status = ttk.Label(t, text="Hazır.", foreground="#2a7")
        self.lbl_status.pack(fill="x")

        self.log = tk.Text(t, height=8, wrap="word", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, pady=(6, 0))

    def _update_region_label(self) -> None:
        r = self.s.region
        self.lbl_region.config(text=f"{r[2]}x{r[3]} @ ({r[0]},{r[1]})" if r else "Tüm monitör")

    def current_region(self) -> Region:
        if self.s.region:
            return Region(*self.s.region)
        return self.mons[min(max(0, self.cmb_mon.current()), len(self.mons) - 1)]

    def select_region(self) -> None:
        self.root.iconify()
        mon = self.mons[max(0, self.cmb_mon.current())]

        def done(region):
            self.root.deiconify()
            if region:
                self.s.region = [region.left, region.top, region.width, region.height]
                self._update_region_label()
                self.s.save()

        self.root.after(250, lambda: RegionSelector(self.root, mon, done))

    def clear_region(self) -> None:
        self.s.region = None
        self._update_region_label()
        self.s.save()

    def status(self, text: str, error: bool = False) -> None:
        self.lbl_status.config(text=text, foreground="#c33" if error else "#2a7")

    def translate_screen(self, auto: bool = False) -> None:
        if self.busy:
            return
        self._collect()
        self.busy = True
        if not auto:
            self.status("Ekran okunuyor…")
        if self.overlay.capture_safe:
            self._capture_and_run(auto, restore=False)
        else:
            # Katman ekran görüntüsüne girmesin diye kısa süre gizle
            self.overlay.hide_temporarily()
            self.root.after(80, lambda: self._capture_and_run(auto, restore=True))

    def _capture_and_run(self, auto: bool, restore: bool) -> None:
        region = self.current_region()
        try:
            img = capture(region)
        except Exception as e:
            self.busy = False
            self.status(f"Ekran görüntüsü alınamadı: {e}", True)
            return
        finally:
            if restore:
                self.overlay.restore()
        self._own_rect = self._window_rect()
        sig = image_signature(img)
        if auto and not signature_changed(self.last_sig, sig):
            self.busy = False
            return
        self.last_sig = sig
        threading.Thread(target=self._work, args=(img, region, auto), daemon=True).start()

    def _window_rect(self):
        """Uygulamanın kendi penceresi (simge durumundaysa None)."""
        if self.root.state() != "normal":
            return None
        r = self.root
        return (r.winfo_rootx(), r.winfo_rooty(),
                r.winfo_rootx() + r.winfo_width(), r.winfo_rooty() + r.winfo_height())

    def _get_ocr(self):
        key = (self.s.ocr_engine, self.s.source_lang, self.s.tesseract_path)
        if self._ocr is None or self._ocr_key != key:
            self._ocr = make_ocr(self.s.ocr_engine, self.s.source_lang, self.s.tesseract_path)
            self._ocr_key = key
        return self._ocr

    def _work(self, img, region: Region, auto: bool) -> None:
        try:
            t0 = time.time()
            offset = (region.left, region.top)
            blocks = self._get_ocr().read(img, offset)
            own = getattr(self, "_own_rect", None)
            if own:
                blocks = [b for b in blocks if not (own[0] <= b.x + b.w / 2 <= own[2]
                                                    and own[1] <= b.y + b.h / 2 <= own[3])]
            if not blocks:
                self.post(self._done, [], auto, "Ekranda okunabilir yazı bulunamadı.", t0)
                return
            translated = self.translator().translate_many([b.text for b in blocks])
            for b, tr in zip(blocks, translated):
                b.translated = tr
            apply_colors(img, blocks, offset)
            self.post(self._done, blocks, auto, None, t0)
        except Exception as e:
            msg = _friendly_error(e)
            traceback.print_exc()
            self.post(self._fail, msg)

    def _done(self, blocks, auto, note, t0) -> None:
        self.busy = False
        self.overlay.show(blocks)
        if note:
            if not auto:
                self.status(note)
            return
        self.status(f"{len(blocks)} metin çevrildi ({time.time() - t0:.1f} sn).")
        self.log.delete("1.0", "end")
        for b in blocks:
            self.log.insert("end", f"{b.text}\n   → {b.translated}\n")

    def _fail(self, msg) -> None:
        self.busy = False
        self.status(msg, True)
        if self.auto_on:
            self.toggle_auto()

    def toggle_auto(self) -> None:
        self.auto_on = not self.auto_on
        self.btn_auto.config(text="■ Otomatik modu durdur" if self.auto_on
                             else "⟳ Otomatik modu başlat")
        self.status("Otomatik mod açık: ekran değiştikçe çevrilecek." if self.auto_on
                    else "Otomatik mod kapalı.")
        if self.auto_on:
            self.last_sig = None
            self._auto_tick()

    def _auto_tick(self) -> None:
        if not self.auto_on:
            return
        self.translate_screen(auto=True)
        self.root.after(int(self.s.auto_interval * 1000), self._auto_tick)

    def toggle_overlay(self) -> None:
        shown = self.overlay.toggle()
        self.status("Çeviri gösteriliyor." if shown else "Çeviri gizlendi.")

    # --------------------------------------------------------------- kısayollar
    def _apply_hotkeys(self) -> None:
        for attr, v in self.var_hk:
            setattr(self.s, attr, v.get().strip())
        self.s.save()
        self._register_hotkeys()

    def _register_hotkeys(self) -> None:
        if self.hotkeys:
            self.hotkeys.stop()
            self.hotkeys = None
        try:
            from pynput import keyboard
        except ImportError:
            self.status("pynput kurulu değil: kısayol tuşları çalışmaz (butonları kullanın).", True)
            return
        mapping = {
            to_pynput_hotkey(self.s.hotkey_translate): lambda: self.post(self.translate_screen),
            to_pynput_hotkey(self.s.hotkey_toggle): lambda: self.post(self.toggle_overlay),
            to_pynput_hotkey(self.s.hotkey_auto): lambda: self.post(self.toggle_auto),
        }
        try:
            self.hotkeys = keyboard.GlobalHotKeys({k: v for k, v in mapping.items() if k})
            self.hotkeys.start()
            self.status(f"Hazır. {self.s.hotkey_translate}: çevir · {self.s.hotkey_toggle}: "
                        f"göster/gizle · {self.s.hotkey_auto}: otomatik")
        except Exception as e:
            self.status(f"Kısayol tuşları ayarlanamadı: {e}", True)

    # ---------------------------------------------------------- dosya çevirisi
    def _build_files(self) -> None:
        t = self.file_tab
        ttk.Label(
            t, wraplength=700, justify="left",
            text="Oyunun dil dosyalarını (ör. Minecraft modlarının en_us.json'u, Unity/RPG Maker "
                 "JSON'ları, .lang, .po, .csv, .yml, .xml, .ini, .txt) doğrudan Türkçeye çevirir. "
                 "%s, {0}, §a, <b> gibi kodlar korunur. Orijinal dosya değiştirilmez.",
        ).pack(fill="x", pady=(0, 8))

        # Çeviri ayarları canlı sekmeyle ortak (aynı değişkenler)
        info = ttk.Label(t, text="Dil ve çeviri motoru 'Canlı Ekran Çevirisi' sekmesindeki "
                                 "ayarlardan alınır.", foreground="#777")
        info.pack(fill="x", pady=(0, 8))

        box = ttk.LabelFrame(t, text="Kaynak", padding=8)
        box.pack(fill="x", pady=(0, 8))
        self.var_in = tk.StringVar()
        self.var_out = tk.StringVar()
        ttk.Label(box, text="Dosya/klasör:").grid(row=0, column=0, sticky="w")
        ttk.Entry(box, textvariable=self.var_in, width=52).grid(row=0, column=1, padx=6)
        bf = ttk.Frame(box)
        bf.grid(row=0, column=2)
        ttk.Button(bf, text="Dosya…", command=self._pick_file).pack(side="left")
        ttk.Button(bf, text="Klasör…", command=self._pick_folder).pack(side="left", padx=4)
        ttk.Label(box, text="Çıktı:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(box, textvariable=self.var_out, width=52).grid(row=1, column=1, padx=6, pady=(6, 0))
        ttk.Button(box, text="Seç…", command=self._pick_out).grid(row=1, column=2, sticky="w",
                                                                pady=(6, 0))

        self.btn_file = ttk.Button(t, text="▶ Türkçeye çevir", command=self._start_file)
        self.btn_file.pack(anchor="w", pady=(0, 6))
        self.pbar = ttk.Progressbar(t, mode="determinate")
        self.pbar.pack(fill="x")
        self.lbl_file = ttk.Label(t, text="")
        self.lbl_file.pack(fill="x", pady=(4, 0))
        self.file_log = tk.Text(t, height=12, wrap="word", font=("Consolas", 9))
        self.file_log.pack(fill="both", expand=True, pady=(6, 0))

    def _pick_file(self) -> None:
        p = filedialog.askopenfilename(filetypes=[
            ("Dil dosyaları", " ".join(f"*{e}" for e in ft.SUPPORTED)), ("Tümü", "*.*")])
        if p:
            self.var_in.set(p)
            self.var_out.set(str(ft.default_output_path(Path(p))))

    def _pick_folder(self) -> None:
        p = filedialog.askdirectory()
        if p:
            self.var_in.set(p)
            self.var_out.set(p.rstrip("/\\") + "_tr")

    def _pick_out(self) -> None:
        src = Path(self.var_in.get())
        if src.is_dir():
            p = filedialog.askdirectory()
        else:
            p = filedialog.asksaveasfilename(initialfile=ft.default_output_path(src).name,
                                             defaultextension=src.suffix)
        if p:
            self.var_out.set(p)

    def _start_file(self) -> None:
        src, dst = Path(self.var_in.get().strip()), Path(self.var_out.get().strip())
        if not src.exists():
            messagebox.showerror("Oyun Çevirmeni", "Lütfen bir dosya veya klasör seçin.")
            return
        if not self.var_out.get().strip():
            dst = ft.default_output_path(src) if src.is_file() else Path(str(src) + "_tr")
            self.var_out.set(str(dst))
        if dst.resolve() == src.resolve():
            messagebox.showerror("Oyun Çevirmeni", "Çıktı, kaynakla aynı olamaz.")
            return
        self._collect()
        self.btn_file.config(state="disabled")
        self.file_log.delete("1.0", "end")
        threading.Thread(target=self._file_work, args=(src, dst), daemon=True).start()

    def _file_progress(self, done, total) -> None:
        self.pbar.config(maximum=max(total, 1), value=done)
        self.lbl_file.config(text=f"{done} / {total} metin çevrildi")

    def _file_work(self, src: Path, dst: Path) -> None:
        try:
            tr = self.translator()
            if src.is_file():
                n = ft.translate_file(src, dst, tr,
                                      lambda d, t: self.post(self._file_progress, d, t))
                self.post(self._file_done, f"✔ {n} metin çevrildi → {dst}")
            else:
                def prog(name, i, total):
                    self.post(self._file_progress, i, total)
                    if name:
                        self.post(self.lbl_file.config, {"text": f"Çevriliyor: {name}"})

                report = ft.translate_folder(src, dst, tr, prog)
                lines = [f"{'✔' if isinstance(r, int) else '✖'} {p.relative_to(src)}: "
                         f"{r if isinstance(r, str) else f'{r} metin'}" for p, r in report]
                self.post(self._file_done,
                          f"{len(report)} dosya işlendi → {dst}\n" + "\n".join(lines))
        except Exception as e:
            traceback.print_exc()
            self.post(self._file_done, f"✖ Hata: {_friendly_error(e)}")

    def _file_done(self, msg: str) -> None:
        self.btn_file.config(state="normal")
        self.file_log.insert("end", msg + "\n")

    # ------------------------------------------------------------------ çıkış
    def quit(self) -> None:
        try:
            self._collect()
        except Exception:
            pass
        if self.hotkeys:
            self.hotkeys.stop()
        if self._translator:
            self._translator.save_cache()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def _friendly_error(e: Exception) -> str:
    name = type(e).__name__
    text = str(e)
    if "TesseractNotFound" in name or "tesseract is not installed" in text:
        return ("Tesseract bulunamadı. README'deki adımlarla kurun ve 'Tesseract yolu' "
                "alanına tesseract.exe'nin yolunu yazın.")
    if "Failed loading language" in text or "Error opening data file" in text:
        return "Bu oyun dili için Tesseract dil paketi kurulu değil (kurulumda dil paketini seçin)."
    if isinstance(e, ModuleNotFoundError):
        if FROZEN:
            return (f"Bu özellik ({e.name}) .exe sürümünde yok. Lütfen başka bir OCR/çeviri "
                    "motoru seçin veya uygulamayı Python ile çalıştırın (README).")
        return f"Eksik paket: {e.name}. Komut: pip install -r requirements.txt"
    if "TooManyRequests" in name:
        return ("Google Çeviri çok fazla istek nedeniyle geçici olarak yanıt vermiyor. "
                "Biraz bekleyin, yenileme süresini artırın veya başka bir çeviri motoru seçin.")
    if isinstance(e, (ValueError, RuntimeError, ConnectionError)) and \
            any(w in text for w in ("API anahtarı", "Ollama", "Yapay zekâ", "Model bulunamadı")):
        return text
    if "Connection" in name or "Timeout" in name or "RequestError" in name:
        return "Çeviri sunucusuna ulaşılamadı. İnternet bağlantınızı kontrol edin."
    return f"{name}: {text}"


def main() -> None:
    if sys.stderr is None or sys.stdout is None:
        # Konsolsuz .exe: hataları bir dosyaya yaz (yoksa yazdırma çökmeye yol açar)
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        log = open(CONFIG_DIR / "hata.log", "a", encoding="utf-8", buffering=1)
        sys.stdout = sys.stdout or log
        sys.stderr = sys.stderr or log
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    App().run()
