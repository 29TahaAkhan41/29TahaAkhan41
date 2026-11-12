"""Tkinter ile basit grafik arayüz. Uzun işler arka plan iş parçacığında çalışır."""
import queue
import threading
import webbrowser

from . import NAME, __version__, auth, install, java, launch, versions

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:  # bazı Linux dağıtımlarında ayrı paket
    tk = None


class App:
    def __init__(self, root, paths):
        self.root, self.paths = root, paths
        self.events = queue.Queue()
        self.busy = False
        self.manifest = []
        root.title(f"{NAME} {__version__}")
        root.minsize(560, 460)

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(6, weight=1)

        ttk.Label(frame, text="Hesap:").grid(row=0, column=0, sticky="w")
        self.account = tk.StringVar()
        ttk.Label(frame, textvariable=self.account).grid(row=0, column=1, sticky="w")
        self.login_btn = ttk.Button(frame, command=self.toggle_login)
        self.login_btn.grid(row=0, column=2, sticky="e")

        ttk.Label(frame, text="Sürüm:").grid(row=1, column=0, sticky="w", pady=6)
        self.version = tk.StringVar()
        self.version_box = ttk.Combobox(frame, textvariable=self.version, state="readonly")
        self.version_box.grid(row=1, column=1, columnspan=2, sticky="ew", pady=6)

        opts = ttk.Frame(frame)
        opts.grid(row=2, column=0, columnspan=3, sticky="w")
        self.snapshots = tk.BooleanVar()
        self.fabric = tk.BooleanVar()
        self.offline = tk.BooleanVar()
        ttk.Checkbutton(opts, text="Snapshot'lar", variable=self.snapshots,
                        command=self.fill_versions).pack(side="left")
        ttk.Checkbutton(opts, text="Fabric", variable=self.fabric).pack(side="left", padx=10)
        ttk.Checkbutton(opts, text="Çevrimdışı", variable=self.offline).pack(side="left")
        ttk.Label(opts, text="RAM (MB):").pack(side="left", padx=(16, 4))
        self.memory = tk.IntVar(value=2048)
        ttk.Spinbox(opts, from_=1024, to=32768, increment=512, width=7,
                    textvariable=self.memory).pack(side="left")

        self.status = tk.StringVar(value="Hazır")
        ttk.Label(frame, textvariable=self.status).grid(
            row=3, column=0, columnspan=3, sticky="w", pady=(10, 2))
        self.bar = ttk.Progressbar(frame)
        self.bar.grid(row=4, column=0, columnspan=3, sticky="ew")
        self.play_btn = ttk.Button(frame, text="Oyna", command=self.play)
        self.play_btn.grid(row=5, column=0, columnspan=3, sticky="ew", pady=8)

        self.log = tk.Text(frame, height=12, state="disabled", wrap="word")
        self.log.grid(row=6, column=0, columnspan=3, sticky="nsew")

        self.refresh_account()
        self.run(self.load_manifest)
        root.after(100, self.pump)

    # --- iş parçacığı köprüsü ---

    def run(self, fn):
        def worker():
            try:
                fn()
            except Exception as e:  # kullanıcıya göster, arayüzü ayakta tut
                self.events.put(("error", str(e)))
            finally:
                self.events.put(("idle", None))
        threading.Thread(target=worker, daemon=True).start()

    def progress(self, label, done, total):
        self.events.put(("progress", (label, done, total)))

    def pump(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "progress":
                    label, done, total = data
                    self.status.set(f"{label}: {done}/{total}")
                    self.bar.configure(maximum=max(total, 1), value=done)
                elif kind == "status":
                    self.status.set(data)
                elif kind == "log":
                    self.log.configure(state="normal")
                    self.log.insert("end", data)
                    self.log.see("end")
                    self.log.configure(state="disabled")
                elif kind == "versions":
                    self.manifest = data
                    self.fill_versions()
                elif kind == "account":
                    self.refresh_account()
                elif kind == "error":
                    self.status.set("Hata")
                    messagebox.showerror(NAME, data)
                elif kind == "idle":
                    self.busy = False
                    self.play_btn.configure(state="normal")
        except queue.Empty:
            pass
        self.root.after(100, self.pump)

    # --- işlemler ---

    def load_manifest(self):
        self.events.put(("versions", versions.manifest()["versions"]))

    def fill_versions(self):
        kinds = ("release", "snapshot") if self.snapshots.get() else ("release",)
        remote = [v["id"] for v in self.manifest if v["type"] in kinds]
        local = [v for v in versions.installed(self.paths) if v not in remote]
        self.version_box.configure(values=local + remote)
        if not self.version.get() and remote:
            self.version.set(remote[0])

    def refresh_account(self):
        acc = auth.active_account(self.paths)
        self.account.set(acc["name"] if acc else "giriş yapılmadı")
        self.login_btn.configure(text="Çıkış" if acc else "Microsoft ile giriş")

    def toggle_login(self):
        if auth.active_account(self.paths):
            auth.logout(self.paths)
            self.refresh_account()
            return
        if self.busy:
            return
        self.busy = True

        def work():
            device = auth.start_device_login(self.paths)
            self.events.put(("status", f"Tarayıcıda kodu girin: {device['user_code']}"))
            self.events.put(("log", f"{device['verification_uri']} adresinde "
                                    f"{device['user_code']} kodunu girin.\n"))
            webbrowser.open(device["verification_uri"])
            ms = auth.poll_device_login(self.paths, device)
            auth.finish_login(self.paths, ms)
            self.events.put(("account", None))
            self.events.put(("status", "Giriş yapıldı"))

        self.run(work)

    def play(self):
        if self.busy or not self.version.get():
            return
        self.busy = True
        self.play_btn.configure(state="disabled")
        vid, fabric = self.version.get(), self.fabric.get()
        offline, memory = self.offline.get(), self.memory.get()

        def work():
            session = auth.session(self.paths, offline=offline)
            target = vid
            if fabric and "fabric-loader" not in vid:
                target = versions.install_fabric(self.paths, vid)
            version = install.install(self.paths, target, self.progress)
            exe = java.ensure(self.paths, version, progress=self.progress)
            self.events.put(("status", f"{target} çalışıyor"))
            proc = launch.launch(self.paths, version, session, exe, memory_mb=memory)
            for line in proc.stdout:
                self.events.put(("log", line))
            self.events.put(("status", f"Oyun kapandı (kod {proc.wait()})"))

        self.run(work)


def main(paths):
    if tk is None:
        raise SystemExit(
            "Tkinter bulunamadı. Linux'ta 'python3-tk' paketini kurun "
            "ya da komut satırını kullanın: python -m pylauncher --help"
        )
    root = tk.Tk()
    App(root, paths)
    root.mainloop()
