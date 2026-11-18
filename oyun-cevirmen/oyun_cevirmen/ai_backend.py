"""Yapay zekâ (büyük dil modeli) ile çeviri.

Ücretsiz kullanılabilen servisler (hepsi OpenAI uyumlu sohbet API'si sunar):
  - Google Gemini   : aistudio.google.com'dan ücretsiz API anahtarı
  - Groq            : console.groq.com'dan ücretsiz API anahtarı
  - Ollama          : bilgisayarınızda yerel çalışır, anahtar ve internet gerekmez

Yapay zekâ, klasik çeviri motorlarından farklı olarak bağlamı anlar: oyun
terimlerini (HP, mana, quest, crafting...) oyuncuların kullandığı biçimde çevirir
ve menüdeki kısa yazıları doğru yorumlar.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass

from .translator import Backend


@dataclass(frozen=True)
class AiService:
    label: str
    url: str
    default_model: str
    needs_key: bool
    key_help: str


AI_SERVICES: dict[str, AiService] = {
    "gemini": AiService(
        "Google Gemini (ücretsiz anahtar)",
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "gemini-2.5-flash",
        True,
        "Ücretsiz anahtar: https://aistudio.google.com/apikey",
    ),
    "groq": AiService(
        "Groq (ücretsiz anahtar, çok hızlı)",
        "https://api.groq.com/openai/v1/chat/completions",
        "llama-3.3-70b-versatile",
        True,
        "Ücretsiz anahtar: https://console.groq.com/keys",
    ),
    "ollama": AiService(
        "Ollama (yerel yapay zekâ, internetsiz)",
        "http://localhost:11434/v1/chat/completions",
        "qwen2.5:7b",
        False,
        "Kurulum: https://ollama.com  ardından:  ollama pull qwen2.5:7b",
    ),
}

LANG_NAMES = {
    "auto": "the source language (detect it)", "en": "English", "ja": "Japanese",
    "zh-CN": "Simplified Chinese", "ko": "Korean", "ru": "Russian", "de": "German",
    "fr": "French", "es": "Spanish", "it": "Italian", "pt": "Portuguese", "pl": "Polish",
}

SYSTEM_PROMPT = """You are a professional video game localizer translating {src} into Turkish.

You receive a JSON array of strings taken from a game: menu items, buttons, item names,
quest text, dialogue and HUD labels. Some come from on-screen text recognition and may
contain small recognition errors; translate what was clearly meant.

Rules:
- Reply with only a JSON array of strings, the same length and order as the input.
- Write natural Turkish that Turkish gamers would expect (e.g. "Yeni Oyun", "Envanter",
  "Görev", "Kaydet"). Keep menu and button labels short.
- Markers like ⟦0⟧, ⟦1⟧ stand for codes the game needs. Copy every marker exactly once,
  unchanged, placing it where it belongs in the Turkish sentence.
- Keep character names, place names and brand names as they are.
- If a string is already Turkish, or is only numbers or symbols, return it unchanged."""


class AiBackend(Backend):
    """OpenAI uyumlu sohbet API'si ile toplu çeviri."""

    MAX_CHARS = 3000  # tek istekte gönderilecek yaklaşık metin miktarı

    def __init__(self, service: str, api_key: str = "", model: str = "", session=None):
        if service not in AI_SERVICES:
            raise ValueError(f"Bilinmeyen yapay zekâ servisi: {service}")
        self.service = AI_SERVICES[service]
        if self.service.needs_key and not api_key:
            raise ValueError(f"{self.service.label} için API anahtarı gerekli. "
                             f"{self.service.key_help}")
        self.name = f"ai-{service}"
        self.api_key = api_key
        self.model = model.strip() or self.service.default_model
        if session is None:
            import requests

            session = requests.Session()
        self.session = session

    # -- genel API --
    def translate_batch(self, texts, source, target):
        results: list[str] = []
        chunk: list[str] = []
        size = 0
        for t in texts:
            if chunk and size + len(t) > self.MAX_CHARS:
                results += self._translate_chunk(chunk, source)
                chunk, size = [], 0
            chunk.append(t)
            size += len(t)
        if chunk:
            results += self._translate_chunk(chunk, source)
        return results

    # -- iç işler --
    def _translate_chunk(self, chunk: list[str], source: str) -> list[str]:
        out = self._ask(chunk, source)
        if out is not None:
            return out
        # Model dizi uzunluğunu tutturamadıysa tek tek çevir
        return [(self._ask([t], source) or [t])[0] for t in chunk]

    def _ask(self, chunk: list[str], source: str) -> list[str] | None:
        system = SYSTEM_PROMPT.format(src=LANG_NAMES.get(source, source))
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(chunk, ensure_ascii=False)},
            ],
            "temperature": 0.2,
        }
        reply = self._post(body)
        return _parse_array(reply, len(chunk))

    def _post(self, body: dict) -> str:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        for attempt in range(4):
            try:
                r = self.session.post(self.service.url, json=body, headers=headers, timeout=120)
            except Exception as e:
                if "localhost" in self.service.url:
                    raise ConnectionError(
                        "Ollama'ya bağlanılamadı. Ollama'nın kurulu ve açık olduğundan emin olun."
                    ) from e
                raise
            if r.status_code == 429 or r.status_code >= 500:
                # Ücretsiz katmanda dakikalık sınır aşıldı veya sunucu meşgul: bekle, tekrar dene
                wait = _retry_after(r) or 2 ** attempt * 3
                if attempt < 3:
                    time.sleep(min(wait, 60))
                    continue
            if r.status_code == 429:
                raise RuntimeError("Yapay zekâ servisinin ücretsiz kullanım sınırına ulaşıldı. "
                                   "Bir süre bekleyin veya başka bir motor seçin.")
            if r.status_code in (401, 403):
                raise RuntimeError("API anahtarı geçersiz veya yetkisiz. Anahtarı kontrol edin.")
            if r.status_code == 404:
                raise RuntimeError(f"Model bulunamadı: '{self.model}'. Model adını kontrol edin"
                                   + (" (ollama pull ile indirin)."
                                      if "localhost" in self.service.url else "."))
            if r.status_code >= 400:
                raise RuntimeError(f"Yapay zekâ servisi hata verdi ({r.status_code}): "
                                   f"{r.text[:300]}")
            data = r.json()
            return data["choices"][0]["message"]["content"] or ""
        return ""


def _retry_after(response) -> float | None:
    try:
        return float(response.headers.get("retry-after", ""))
    except (TypeError, ValueError):
        return None


def _parse_array(reply: str, expected: int) -> list[str] | None:
    """Model cevabındaki JSON dizisini çıkarır; uzunluk tutmazsa None."""
    text = reply.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)  # kod bloğu çitlerini at
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        return None
    try:
        arr = json.loads(text[start : end + 1])
    except ValueError:
        return None
    if not isinstance(arr, list) or len(arr) != expected:
        return None
    return [s if isinstance(s, str) else str(s) for s in arr]
