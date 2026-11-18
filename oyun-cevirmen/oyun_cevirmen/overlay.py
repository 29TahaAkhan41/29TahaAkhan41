"""Oyunun üstünde, orijinal yazıların yerine Türkçe çeviriyi gösteren katman."""
from __future__ import annotations

import sys
import tkinter as tk
import tkinter.font as tkfont

from PIL import ImageTk

from .screen import Region, TextBlock

IS_WINDOWS = sys.platform == "win32"


def enable_dpi_awareness() -> None:
    """Windows'ta ölçekleme (%125, %150) varken koordinatların doğru olması için."""
    if not IS_WINDOWS:
        return
    import ctypes

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _hwnd(win: tk.Misc) -> int:
    import ctypes

    return ctypes.windll.user32.GetAncestor(win.winfo_id(), 2)  # GA_ROOT


def make_click_through(win: tk.Toplevel) -> None:
    """Fare tıklamaları katmandan geçip oyuna gitsin."""
    if not IS_WINDOWS:
        return
    import ctypes

    GWL_EXSTYLE = -20
    WS_EX_LAYERED, WS_EX_TRANSPARENT = 0x80000, 0x20
    WS_EX_TOOLWINDOW, WS_EX_NOACTIVATE = 0x80, 0x08000000
    hwnd = _hwnd(win)
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(
        hwnd, GWL_EXSTYLE,
        style | WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE,
    )


def exclude_from_capture(win: tk.Toplevel) -> bool:
    """Katmanı ekran görüntüsünden gizler (Windows 10 2004+). Başarılıysa True."""
    if not IS_WINDOWS:
        return False
    import ctypes

    WDA_EXCLUDEFROMCAPTURE = 0x11
    return bool(ctypes.windll.user32.SetWindowDisplayAffinity(_hwnd(win), WDA_EXCLUDEFROMCAPTURE))


class Overlay:
    """Her metin bloğu için küçük, kenarlıksız, her zaman üstte bir pencere."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.windows: list[tk.Toplevel] = []
        self.visible = True
        self.capture_safe = IS_WINDOWS  # ilk pencerede doğrulanır
        self.opacity = 0.9
        self.bg = "#101418"
        self.fg = "#ffffff"
        self.font_family = "Segoe UI" if IS_WINDOWS else "DejaVu Sans"
        self.min_font_px = 10
        self.match_colors = True  # çeviri oyunun görünümüne uydurulsun (render.py)

    # -- yardımcılar --
    def _wrap(self, font: tkfont.Font, text: str, width: int) -> list[str]:
        lines: list[str] = []
        for para in text.split("\n"):
            cur = ""
            for word in para.split(" "):
                trial = f"{cur} {word}".strip()
                if cur and font.measure(trial) > width:
                    lines.append(cur)
                    cur = word
                else:
                    cur = trial
            lines.append(cur)
        return lines

    def _fit(self, block: TextBlock) -> tuple[tkfont.Font, list[str], int, int]:
        """Çeviriyi orijinal kutuya sığacak yazı boyutunu bulur."""
        text = block.translated or block.text
        size = max(self.min_font_px, int(block.line_height * 0.85))
        width = max(block.w, 40)
        while True:
            font = tkfont.Font(root=self.root, family=self.font_family, size=-size)
            lines = self._wrap(font, text, width)
            lh = font.metrics("linespace")
            height = lh * len(lines)
            if height <= block.h * 1.15 or size <= self.min_font_px:
                real_w = max(font.measure(l) for l in lines) if lines else width
                return font, lines, max(width, real_w), max(height, block.h)
            size -= 1

    # -- genel API --
    def show(self, blocks: list[TextBlock]) -> None:
        # Önce yenilerini oluştur, sonra eskileri kaldır: yenilemede yanıp sönme olmaz
        old = self.windows
        self.windows = []
        for b in blocks:
            if not b.translated or b.translated.strip() == b.text.strip():
                continue
            win = tk.Toplevel(self.root)
            win.overrideredirect(True)
            win.attributes("-topmost", True)
            try:
                win.attributes("-alpha", self.opacity)
            except tk.TclError:
                pass
            if self.match_colors and getattr(b, "patch", None) is not None:
                # Oyunun görünümüne uydurulmuş hazır resim (render.py)
                photo = ImageTk.PhotoImage(b.patch, master=self.root)
                label = tk.Label(win, image=photo, bd=0, highlightthickness=0)
                label.image = photo  # çöp toplayıcı silmesin
                label.pack()
                win.geometry(f"{b.patch.width}x{b.patch.height}+{b.px}+{b.py}")
            else:
                font, lines, w, h = self._fit(b)
                pad = 3
                win.configure(bg=self.bg)
                tk.Label(
                    win, text="\n".join(lines), font=font, fg=self.fg, bg=self.bg,
                    justify="left", anchor="nw", padx=pad, pady=0,
                ).pack(fill="both", expand=True)
                win.geometry(f"{w + pad * 2}x{h}+{b.x - pad}+{b.y}")
            win.update_idletasks()
            if IS_WINDOWS:
                try:
                    make_click_through(win)
                    if not exclude_from_capture(win):
                        self.capture_safe = False
                except Exception:
                    self.capture_safe = False
            if not self.visible:
                win.withdraw()
            self.windows.append(win)
        for w in old:
            try:
                w.destroy()
            except tk.TclError:
                pass

    def clear(self) -> None:
        for w in self.windows:
            try:
                w.destroy()
            except tk.TclError:
                pass
        self.windows.clear()

    def hide_temporarily(self) -> None:
        for w in self.windows:
            w.withdraw()

    def restore(self) -> None:
        if self.visible:
            for w in self.windows:
                w.deiconify()
                w.attributes("-topmost", True)

    def toggle(self) -> bool:
        self.visible = not self.visible
        if self.visible:
            self.restore()
        else:
            self.hide_temporarily()
        return self.visible


class RegionSelector:
    """Ekranda fareyle sürükleyerek çevrilecek alanı seçtirir."""

    def __init__(self, root: tk.Tk, bounds: Region, on_done):
        self.on_done = on_done
        self.bounds = bounds
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        try:
            self.win.attributes("-alpha", 0.35)
        except tk.TclError:
            pass
        self.win.geometry(f"{bounds.width}x{bounds.height}+{bounds.left}+{bounds.top}")
        self.canvas = tk.Canvas(self.win, bg="black", cursor="cross", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(
            bounds.width // 2, 40, fill="white", font=("Segoe UI", 18),
            text="Çevrilecek alanı fareyle seçin  (Esc: iptal)",
        )
        self.start = None
        self.rect = None
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._drag)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.win.bind("<Escape>", lambda e: self._finish(None))
        self.win.focus_force()

    def _press(self, e):
        self.start = (e.x, e.y)
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="#00ff88", width=3)

    def _drag(self, e):
        if self.rect:
            self.canvas.coords(self.rect, *self.start, e.x, e.y)

    def _release(self, e):
        if not self.start:
            return
        x0, y0 = self.start
        x, y, w, h = min(x0, e.x), min(y0, e.y), abs(e.x - x0), abs(e.y - y0)
        if w < 20 or h < 10:
            self._finish(None)
        else:
            self._finish(Region(self.bounds.left + x, self.bounds.top + y, w, h))

    def _finish(self, region):
        self.win.destroy()
        self.on_done(region)
