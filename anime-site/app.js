(() => {
  "use strict";
  const app = document.getElementById("app");
  const search = document.getElementById("search");
  const CATALOG = window.CATALOG || [];

  // ---------- Kalıcı veri (localStorage) ----------
  const store = {
    get(key, fallback) {
      try { const v = localStorage.getItem("anitr:" + key); return v ? JSON.parse(v) : fallback; }
      catch { return fallback; }
    },
    set(key, value) {
      try { localStorage.setItem("anitr:" + key, JSON.stringify(value)); } catch { /* yoksay */ }
    }
  };
  const getProgress = () => store.get("progress", {});
  const getFavs = () => store.get("favs", []);
  const settings = Object.assign({ size: "1.4rem", color: "#ffffff", bg: "rgba(0,0,0,.65)" }, store.get("subs", {}));
  applySubStyle();

  function applySubStyle() {
    const r = document.documentElement.style;
    r.setProperty("--sub-size", settings.size);
    r.setProperty("--sub-color", settings.color);
    r.setProperty("--sub-bg", settings.bg);
  }

  // ---------- Yardımcılar ----------
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const find = (id) => CATALOG.find((a) => a.id === id);
  const trLower = (s) => s.toLocaleLowerCase("tr-TR");
  const fmtTime = (t) => {
    t = Math.floor(t || 0);
    const m = Math.floor(t / 60), s = String(t % 60).padStart(2, "0");
    return `${m}:${s}`;
  };
  const gradient = (a) => `linear-gradient(160deg, ${a.colors[0]}, ${a.colors[1]})`;

  function posterHTML(a) {
    return `<div class="poster" style="background:${gradient(a)}">
      <span class="badge">TR ALTYAZI</span>
      <div><div class="ptitle">${esc(a.title)}</div><div class="pjp">${esc(a.jp || "")}</div></div>
    </div>`;
  }

  function cardHTML(a) {
    const prog = getProgress()[a.id];
    const bar = prog && prog.duration
      ? `<div class="progress"><i style="width:${Math.min(100, (prog.time / prog.duration) * 100)}%"></i></div>` : "";
    return `<a class="card" href="#/anime/${a.id}">
      ${posterHTML(a)}
      ${bar}
      <div class="meta"><div class="name">${esc(a.title)}</div>
      ${a.year} · ★ ${a.rating} · ${a.episodes.length} bölüm</div>
    </a>`;
  }

  // ---------- Sayfalar ----------
  let activeGenre = "Tümü";

  function viewHome() {
    const q = trLower(search.value.trim());
    const featured = CATALOG[0];
    const genres = ["Tümü", ...new Set(CATALOG.flatMap((a) => a.genres))];
    const list = CATALOG.filter((a) =>
      (activeGenre === "Tümü" || a.genres.includes(activeGenre)) &&
      (!q || trLower(a.title + " " + (a.jp || "") + " " + a.genres.join(" ")).includes(q)));

    const progress = getProgress();
    const continuing = Object.entries(progress)
      .sort((x, y) => y[1].at - x[1].at)
      .map(([id]) => find(id)).filter(Boolean);

    app.innerHTML = `
      ${q ? "" : `<section class="hero" style="background:
          linear-gradient(90deg, rgba(13,14,20,.95) 20%, rgba(13,14,20,.2)), ${gradient(featured)}">
        <span class="jp">${esc(featured.jp)}</span>
        <h1>${esc(featured.title)}</h1>
        <p>${esc(featured.synopsis)}</p>
        <div class="actions">
          <a class="btn" href="#/izle/${featured.id}/1">▶ Hemen İzle</a>
          <a class="btn ghost" href="#/anime/${featured.id}">Detaylar</a>
        </div>
      </section>`}

      ${continuing.length && !q ? `<h2>İzlemeye Devam Et</h2>
        <div class="grid">${continuing.map(cardHTML).join("")}</div>` : ""}

      <h2>${q ? `“${esc(search.value)}” için sonuçlar` : "Tüm Animeler"}</h2>
      <div class="chips">${genres.map((g) =>
        `<button class="chip ${g === activeGenre ? "active" : ""}" data-genre="${esc(g)}">${esc(g)}</button>`).join("")}</div>
      <div class="grid" style="margin-top:16px">
        ${list.length ? list.map(cardHTML).join("") : `<p class="empty">Sonuç bulunamadı.</p>`}
      </div>`;

    app.querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => {
      activeGenre = b.dataset.genre; viewHome();
    }));
  }

  function viewDetail(id) {
    const a = find(id);
    if (!a) return viewNotFound();
    const favs = getFavs();
    const isFav = favs.includes(a.id);
    app.innerHTML = `
      <section class="detail">
        ${posterHTML(a)}
        <div>
          <h1 style="margin:0">${esc(a.title)}</h1>
          <div class="hint">${esc(a.jp || "")} · ${a.year} · ★ ${a.rating}</div>
          <div class="tags">${a.genres.map((g) => `<span class="tag">${esc(g)}</span>`).join("")}</div>
          <p style="line-height:1.6">${esc(a.synopsis)}</p>
          <div class="actions">
            <a class="btn" href="#/izle/${a.id}/1">▶ 1. Bölümü İzle</a>
            <button class="btn ghost" id="fav">${isFav ? "✓ Listemde" : "+ Listeme Ekle"}</button>
          </div>
          <p class="credit">${esc(a.credit || "")}</p>
        </div>
      </section>
      <h2>Bölümler</h2>
      <div class="episodes">
        ${a.episodes.map((e) => `<a class="ep" href="#/izle/${a.id}/${e.n}">
          <span class="num">${e.n}</span>
          <div><div>${esc(e.title)}</div><div class="hint">${esc(e.duration || "")}</div></div>
          ${e.subs ? `<span class="sub-flag">Türkçe Altyazı</span>` : ""}
        </a>`).join("")}
      </div>`;

    document.getElementById("fav").addEventListener("click", () => {
      const f = getFavs();
      store.set("favs", f.includes(a.id) ? f.filter((x) => x !== a.id) : [...f, a.id]);
      viewDetail(id);
    });
  }

  function viewList() {
    const favs = getFavs().map(find).filter(Boolean);
    app.innerHTML = `<h2>Listem</h2>
      ${favs.length ? `<div class="grid">${favs.map(cardHTML).join("")}</div>`
        : `<p class="empty">Listende henüz anime yok. Bir animenin sayfasından “Listeme Ekle”ye bas.</p>`}`;
  }

  function subtitleControls() {
    const sizes = [["1rem", "Küçük"], ["1.4rem", "Orta"], ["1.9rem", "Büyük"], ["2.5rem", "Çok büyük"]];
    const bgs = [["rgba(0,0,0,.65)", "Yarı saydam"], ["rgba(0,0,0,1)", "Siyah"], ["transparent", "Yok"]];
    return `
      <label>Altyazı
        <select id="subToggle"><option value="on">Türkçe</option><option value="off">Kapalı</option></select></label>
      <label>Boyut <select id="subSize">${sizes.map(([v, t]) =>
        `<option value="${v}" ${v === settings.size ? "selected" : ""}>${t}</option>`).join("")}</select></label>
      <label>Renk <input type="color" id="subColor" value="${settings.color}"></label>
      <label>Arka plan <select id="subBg">${bgs.map(([v, t]) =>
        `<option value="${v}" ${v === settings.bg ? "selected" : ""}>${t}</option>`).join("")}</select></label>
      <label>Senkron
        <button class="chip" id="subMinus" title="Altyazıyı 0,5 sn erkene al">−0,5 sn</button>
        <span id="subOffset">0,0 sn</span>
        <button class="chip" id="subPlus" title="Altyazıyı 0,5 sn geciktir">+0,5 sn</button></label>`;
  }

  // Oynatıcıya ortak davranışları bağlar (altyazı ayarları, kısayollar, senkron)
  function wirePlayer(video) {
    let offset = 0;
    const track = () => video.textTracks[0];

    const subToggle = document.getElementById("subToggle");
    subToggle.addEventListener("change", () => {
      if (track()) track().mode = subToggle.value === "on" ? "showing" : "hidden";
    });
    document.getElementById("subSize").addEventListener("change", (e) => {
      settings.size = e.target.value; store.set("subs", settings); applySubStyle();
    });
    document.getElementById("subColor").addEventListener("input", (e) => {
      settings.color = e.target.value; store.set("subs", settings); applySubStyle();
    });
    document.getElementById("subBg").addEventListener("change", (e) => {
      settings.bg = e.target.value; store.set("subs", settings); applySubStyle();
    });
    const shift = (d) => {
      const t = track();
      if (!t || !t.cues) return;
      for (const c of Array.from(t.cues)) {
        c.startTime = Math.max(0, c.startTime + d);
        c.endTime = Math.max(0, c.endTime + d);
      }
      offset += d;
      document.getElementById("subOffset").textContent =
        (offset > 0 ? "+" : "") + offset.toFixed(1).replace(".", ",") + " sn";
    };
    document.getElementById("subMinus").addEventListener("click", () => shift(-0.5));
    document.getElementById("subPlus").addEventListener("click", () => shift(0.5));

    // Altyazıyı varsayılan olarak aç
    const show = () => { if (track()) track().mode = "showing"; };
    video.textTracks.addEventListener?.("addtrack", show);
    show();

    // Klavye kısayolları
    const onKey = (e) => {
      if (!document.body.contains(video)) return document.removeEventListener("keydown", onKey);
      if (["INPUT", "SELECT", "TEXTAREA"].includes(e.target.tagName)) return;
      const k = e.key.toLowerCase();
      if (k === " " || k === "k") { e.preventDefault(); video.paused ? video.play() : video.pause(); }
      else if (k === "arrowright" || k === "l") { video.currentTime += k === "l" ? 10 : 5; }
      else if (k === "arrowleft" || k === "j") { video.currentTime -= k === "j" ? 10 : 5; }
      else if (k === "f") { document.fullscreenElement ? document.exitFullscreen() : video.parentElement.requestFullscreen?.(); }
      else if (k === "m") { video.muted = !video.muted; }
      else if (k === "c") { subToggle.value = subToggle.value === "on" ? "off" : "on"; subToggle.dispatchEvent(new Event("change")); }
    };
    document.addEventListener("keydown", onKey);
  }

  const shortcutsHint = `<p class="hint">Kısayollar: <kbd>Boşluk</kbd> oynat/duraklat ·
    <kbd>←</kbd>/<kbd>→</kbd> 5 sn · <kbd>J</kbd>/<kbd>L</kbd> 10 sn · <kbd>F</kbd> tam ekran ·
    <kbd>M</kbd> sessiz · <kbd>C</kbd> altyazı aç/kapa</p>`;

  function viewWatch(id, n) {
    const a = find(id);
    const ep = a && a.episodes.find((e) => e.n === Number(n));
    if (!ep) return viewNotFound();
    const next = a.episodes.find((e) => e.n === ep.n + 1);
    const prev = a.episodes.find((e) => e.n === ep.n - 1);

    app.innerHTML = `
      <div class="player-wrap">
        <video id="video" controls playsinline preload="metadata">
          <source src="${esc(ep.video)}">
          ${ep.subs ? `<track kind="subtitles" srclang="tr" label="Türkçe" src="${esc(ep.subs)}" default>` : ""}
          Tarayıcınız video etiketini desteklemiyor.
        </video>
      </div>
      <div class="player-bar">
        ${subtitleControls()}
        <span class="spacer"></span>
        ${prev ? `<a class="btn ghost" href="#/izle/${a.id}/${prev.n}">← Önceki</a>` : ""}
        ${next ? `<a class="btn" href="#/izle/${a.id}/${next.n}">Sonraki Bölüm →</a>` : ""}
      </div>
      <h1 class="watch-title"><a href="#/anime/${a.id}">${esc(a.title)}</a> · ${ep.n}. Bölüm</h1>
      <div class="hint">${esc(ep.title)} · ${esc(a.credit || "")}</div>
      ${shortcutsHint}
      <div id="resume"></div>`;

    const video = document.getElementById("video");
    wirePlayer(video);

    // Kaldığın yerden devam et
    const saved = getProgress()[a.id];
    if (saved && saved.ep === ep.n && saved.time > 10 && saved.time < (saved.duration || Infinity) - 15) {
      video.addEventListener("loadedmetadata", () => { video.currentTime = saved.time; }, { once: true });
      document.getElementById("resume").innerHTML =
        `<p class="hint">⏱ Kaldığın yerden devam ediliyor: ${fmtTime(saved.time)}</p>`;
    }

    let last = 0;
    video.addEventListener("timeupdate", () => {
      if (Math.abs(video.currentTime - last) < 5) return;
      last = video.currentTime;
      const p = getProgress();
      p[a.id] = { ep: ep.n, time: video.currentTime, duration: video.duration || 0, at: Date.now() };
      store.set("progress", p);
    });
    video.addEventListener("ended", () => {
      if (next) location.hash = `#/izle/${a.id}/${next.n}`;
    });
  }

  // ---------- Kendi dosyanı izle (yerel video + .srt / .vtt) ----------
  // Türkçe .srt dosyaları sık sık Windows-1254 kodlamasıyla gelir; ş, ğ, ı bozulmasın diye algılıyoruz.
  function decodeSubtitle(buffer) {
    try { return new TextDecoder("utf-8", { fatal: true }).decode(buffer); }
    catch { return new TextDecoder("windows-1254").decode(buffer); }
  }
  function srtToVtt(text) {
    const body = text.replace(/^\uFEFF/, "").replace(/\r+/g, "")
      .replace(/(\d\d:\d\d:\d\d),(\d\d\d)/g, "$1.$2")   // 00:00:01,000 -> 00:00:01.000
      .replace(/\{\\an\d\}/g, "");                       // ASS konum etiketlerini temizle
    return body.trimStart().startsWith("WEBVTT") ? body : "WEBVTT\n\n" + body;
  }

  function viewLocal() {
    app.innerHTML = `
      <h2>Kendi Dosyanı İzle</h2>
      <p class="hint">Bilgisayarındaki bir videoyu ve Türkçe altyazı dosyasını (.srt veya .vtt) seç.
        Dosyalar hiçbir yere yüklenmez, yalnızca tarayıcında oynatılır. Türkçe karakter kodlaması
        (UTF-8 / Windows-1254) otomatik algılanır.</p>
      <div class="drop" id="drop">
        <div class="row"><strong>1. Video:</strong> <input type="file" id="fVideo" accept="video/*,.mkv"></div>
        <div class="row"><strong>2. Altyazı:</strong> <input type="file" id="fSub" accept=".srt,.vtt"></div>
        <div class="hint">…ya da ikisini birden bu kutuya sürükleyip bırak.</div>
      </div>
      <div id="localPlayer" style="margin-top:20px"></div>`;

    let videoFile = null, subFile = null;
    const fVideo = document.getElementById("fVideo"), fSub = document.getElementById("fSub");
    const drop = document.getElementById("drop");

    const render = async () => {
      if (!videoFile) return;
      let trackTag = "";
      if (subFile) {
        const text = decodeSubtitle(await subFile.arrayBuffer());
        const vtt = srtToVtt(text);
        const url = URL.createObjectURL(new Blob([vtt], { type: "text/vtt" }));
        trackTag = `<track kind="subtitles" srclang="tr" label="Türkçe" src="${url}" default>`;
      }
      document.getElementById("localPlayer").innerHTML = `
        <div class="player-wrap"><video id="video" controls playsinline
          src="${URL.createObjectURL(videoFile)}">${trackTag}</video></div>
        <div class="player-bar">${subtitleControls()}</div>
        <h1 class="watch-title">${esc(videoFile.name)}</h1>
        <div class="hint">${subFile ? "Altyazı: " + esc(subFile.name) : "Altyazı seçilmedi"}</div>
        <p class="hint">Not: Tarayıcılar genelde MP4 (H.264) ve WebM oynatır; bazı MKV dosyaları oynatılamayabilir.</p>
        ${shortcutsHint}`;
      wirePlayer(document.getElementById("video"));
    };

    const take = (files) => {
      for (const f of files) {
        if (/\.(srt|vtt)$/i.test(f.name)) subFile = f;
        else if (f.type.startsWith("video/") || /\.(mkv|mp4|webm|mov)$/i.test(f.name)) videoFile = f;
      }
      render();
    };
    fVideo.addEventListener("change", () => take(fVideo.files));
    fSub.addEventListener("change", () => take(fSub.files));
    drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("over"));
    drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); take(e.dataTransfer.files); });
  }

  function viewNotFound() {
    app.innerHTML = `<h2>Sayfa bulunamadı</h2><p><a class="btn" href="#/">Ana sayfaya dön</a></p>`;
  }

  // ---------- Yönlendirici ----------
  function route() {
    const parts = location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
    document.querySelectorAll(".topbar nav a").forEach((l) =>
      l.classList.toggle("active", l.getAttribute("href") === "#/" + (parts[0] || "")));
    window.scrollTo(0, 0);
    if (!parts.length) return viewHome();
    if (parts[0] === "anime") return viewDetail(parts[1]);
    if (parts[0] === "izle") return viewWatch(parts[1], parts[2] || 1);
    if (parts[0] === "liste") return viewList();
    if (parts[0] === "yerel") return viewLocal();
    viewNotFound();
  }

  search.addEventListener("input", () => {
    if (location.hash && location.hash !== "#/") location.hash = "#/";
    else viewHome();
  });
  window.addEventListener("hashchange", route);
  route();
})();
