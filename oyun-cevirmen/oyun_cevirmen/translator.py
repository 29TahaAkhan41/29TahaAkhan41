"""Çeviri motorları, önbellek ve yer tutucu korumalı toplu çeviri."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Callable, Iterable

from . import placeholders as ph

CONFIG_DIR = Path(os.environ.get("OYUN_CEVIRMEN_DIR", Path.home() / ".oyun_cevirmen"))

# Arayüzde gösterilen kaynak dil seçenekleri (kod -> ad)
SOURCE_LANGUAGES = {
    "auto": "Otomatik algıla",
    "en": "İngilizce",
    "ja": "Japonca",
    "zh-CN": "Çince (Basit)",
    "ko": "Korece",
    "ru": "Rusça",
    "de": "Almanca",
    "fr": "Fransızca",
    "es": "İspanyolca",
    "it": "İtalyanca",
    "pt": "Portekizce",
    "pl": "Lehçe",
}


class Backend:
    """Bir çeviri motoru. translate_batch, aynı sırada aynı sayıda sonuç döner."""

    name = "base"

    def translate_batch(self, texts: list[str], source: str, target: str) -> list[str]:
        raise NotImplementedError


class GoogleBackend(Backend):
    """Ücretsiz Google Çeviri (API anahtarı gerekmez, internet gerekir)."""

    name = "google"
    MAX_CHARS = 4500

    def _client(self, source: str, target: str):
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source=source, target=target)

    def translate_batch(self, texts, source, target):
        client = self._client(source, target)
        results: list[str] = []
        chunk: list[str] = []
        size = 0
        for t in texts:
            if chunk and size + len(t) + 1 > self.MAX_CHARS:
                results.extend(self._chunk(client, chunk))
                chunk, size = [], 0
            chunk.append(t)
            size += len(t) + 1
        if chunk:
            results.extend(self._chunk(client, chunk))
        return results

    def _chunk(self, client, chunk: list[str]) -> list[str]:
        # Satırları tek istekte gönder; satır sayısı tutmazsa tek tek çevir.
        if len(chunk) > 1:
            joined = client.translate("\n".join(chunk)) or ""
            lines = joined.split("\n")
            if len(lines) == len(chunk):
                return [l.strip() for l in lines]
        return [(client.translate(t) or t) if t.strip() else t for t in chunk]


class DeeplBackend(Backend):
    """DeepL (daha kaliteli, ücretsiz API anahtarı gerekir)."""

    name = "deepl"

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("DeepL için API anahtarı gerekli.")
        self.api_key = api_key

    def translate_batch(self, texts, source, target):
        from deep_translator import DeeplTranslator

        client = DeeplTranslator(
            api_key=self.api_key,
            source="en" if source == "auto" else source.split("-")[0].lower(),
            target=target,
            use_free_api=self.api_key.endswith(":fx"),
        )
        return [client.translate(t) or t for t in texts]


class ArgosBackend(Backend):
    """Tamamen çevrimdışı çeviri (argostranslate). İlk kullanımda dil paketi iner."""

    name = "argos"

    def translate_batch(self, texts, source, target):
        import argostranslate.package
        import argostranslate.translate

        src = "en" if source == "auto" else source.split("-")[0]
        installed = {(l.code) for l in argostranslate.translate.get_installed_languages()}
        if src not in installed or target not in installed:
            argostranslate.package.update_package_index()
            for pkg in argostranslate.package.get_available_packages():
                if pkg.from_code == src and pkg.to_code == target:
                    argostranslate.package.install_from_path(pkg.download())
                    break
            else:
                raise RuntimeError(f"Çevrimdışı {src}->{target} dil paketi bulunamadı.")
        return [argostranslate.translate.translate(t, src, target) for t in texts]


BACKENDS: dict[str, str] = {
    "google": "Google Çeviri (ücretsiz, çevrimiçi)",
    "deepl": "DeepL (API anahtarı ile)",
    "argos": "Argos (çevrimdışı)",
}


def make_backend(name: str, api_key: str = "") -> Backend:
    if name == "google":
        return GoogleBackend()
    if name == "deepl":
        return DeeplBackend(api_key)
    if name == "argos":
        return ArgosBackend()
    raise ValueError(f"Bilinmeyen çeviri motoru: {name}")


class Translator:
    """Önbellekli, yer tutucu korumalı çevirmen. İş parçacığı güvenlidir."""

    def __init__(
        self,
        backend: Backend,
        source: str = "auto",
        target: str = "tr",
        cache_file: Path | None = CONFIG_DIR / "onbellek.json",
    ):
        self.backend = backend
        self.source = source
        self.target = target
        self.cache_file = cache_file
        self._lock = threading.Lock()
        self._cache: dict[str, str] = {}
        if cache_file and cache_file.exists():
            try:
                self._cache = json.loads(cache_file.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self._cache = {}

    def _key(self, text: str) -> str:
        return f"{self.backend.name}|{self.source}|{self.target}|{text}"

    def save_cache(self) -> None:
        if not self.cache_file:
            return
        with self._lock:
            data = dict(self._cache)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.cache_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.cache_file)

    def translate(self, text: str) -> str:
        return self.translate_many([text])[0]

    def translate_many(
        self,
        texts: Iterable[str],
        progress: Callable[[int, int], None] | None = None,
        batch_size: int = 50,
    ) -> list[str]:
        texts = list(texts)
        result: dict[str, str] = {}
        todo: list[str] = []
        with self._lock:
            for t in dict.fromkeys(texts):
                if not ph.has_letters(t):
                    result[t] = t
                elif self._key(t) in self._cache:
                    result[t] = self._cache[self._key(t)]
                else:
                    todo.append(t)

        done = 0
        total = len(todo)
        for i in range(0, total, batch_size):
            batch = todo[i : i + batch_size]
            for original, translated in zip(batch, self._translate_uncached(batch)):
                result[original] = translated
                with self._lock:
                    self._cache[self._key(original)] = translated
            done += len(batch)
            if progress:
                progress(done, total)
        if todo:
            self.save_cache()
        return [result[t] for t in texts]

    def _translate_uncached(self, batch: list[str]) -> list[str]:
        protected = [ph.protect(t) for t in batch]
        raw = self.backend.translate_batch([p[0] for p in protected], self.source, self.target)
        out: list[str] = []
        for original, (_, found), tr in zip(batch, protected, raw):
            restored = ph.restore(tr or "", found) if found else (tr or original)
            if restored is None:
                restored = self._segmentwise(original)
            out.append(_match_edges(original, restored))
        return out

    def _segmentwise(self, text: str) -> str:
        """Yer tutucular bozulduysa: yalnızca aralarındaki metinleri çevir."""
        segs = ph.split_segments(text)
        idx = [i for i, (tr, s) in enumerate(segs) if tr and any(c.isalpha() for c in s)]
        if not idx:
            return text
        translated = self.backend.translate_batch(
            [segs[i][1].strip() for i in idx], self.source, self.target
        )
        parts = [s for _, s in segs]
        for i, tr in zip(idx, translated):
            parts[i] = _match_edges(segs[i][1], tr or segs[i][1])
        return "".join(parts)


def _match_edges(original: str, translated: str) -> str:
    """Baştaki/sondaki boşlukları orijinaldekiyle aynı yapar."""
    lead = original[: len(original) - len(original.lstrip())]
    trail = original[len(original.rstrip()) :]
    return lead + translated.strip() + trail
