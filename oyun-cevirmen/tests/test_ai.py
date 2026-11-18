import json

import pytest

from oyun_cevirmen import ai_backend
from oyun_cevirmen.ai_backend import AiBackend, _parse_array
from oyun_cevirmen.translator import Translator, make_backend

SOZ = {"New Game": "Yeni Oyun", "Hello ⟦0⟧!": "Merhaba ⟦0⟧!", "Quit": "Çıkış"}


class Resp:
    def __init__(self, status, content="", headers=None):
        self.status_code = status
        self._content = content
        self.headers = headers or {}
        self.text = content

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


class FakeSession:
    """Gelen JSON dizisini sözlükle çeviren sahte OpenAI uyumlu sunucu."""

    def __init__(self, script=None, fence=False):
        self.requests = []
        self.script = list(script or [])
        self.fence = fence

    def post(self, url, json=None, headers=None, timeout=None):
        self.requests.append({"url": url, "body": json, "headers": headers})
        if self.script:
            return self.script.pop(0)
        texts = __import__("json").loads(json["messages"][1]["content"])
        out = __import__("json").dumps([SOZ.get(t, t) for t in texts], ensure_ascii=False)
        return Resp(200, f"```json\n{out}\n```" if self.fence else out)


def test_translates_batch_and_keeps_placeholders():
    s = FakeSession(fence=True)
    t = Translator(AiBackend("gemini", "anahtar", session=s), source="en", cache_file=None)
    assert t.translate_many(["New Game", "Hello %s!", "Quit"]) == ["Yeni Oyun", "Merhaba %s!", "Çıkış"]
    assert len(s.requests) == 1  # hepsi tek istekte
    req = s.requests[0]
    assert req["url"].startswith("https://generativelanguage.googleapis.com")
    assert req["headers"]["Authorization"] == "Bearer anahtar"
    assert req["body"]["model"] == "gemini-2.5-flash"
    assert "English" in req["body"]["messages"][0]["content"]


def test_ollama_needs_no_key_and_custom_model():
    s = FakeSession()
    b = AiBackend("ollama", model="gemma3:4b", session=s)
    assert b.translate_batch(["Quit"], "en", "tr") == ["Çıkış"]
    assert "Authorization" not in s.requests[0]["headers"]
    assert s.requests[0]["body"]["model"] == "gemma3:4b"
    assert s.requests[0]["url"].startswith("http://localhost:11434")


def test_key_required_for_cloud_services():
    with pytest.raises(ValueError, match="aistudio"):
        make_backend("gemini", "")
    with pytest.raises(ValueError, match="groq"):
        make_backend("groq", "")


def test_wrong_length_falls_back_to_one_by_one():
    s = FakeSession(script=[Resp(200, '["Yeni Oyun"]')])  # 2 yerine 1 sonuç
    b = AiBackend("groq", "k", session=s)
    assert b.translate_batch(["New Game", "Quit"], "en", "tr") == ["Yeni Oyun", "Çıkış"]
    assert len(s.requests) == 3


def test_rate_limit_retries(monkeypatch):
    monkeypatch.setattr(ai_backend.time, "sleep", lambda s: None)
    s = FakeSession(script=[Resp(429, headers={"retry-after": "1"})])
    b = AiBackend("groq", "k", session=s)
    assert b.translate_batch(["Quit"], "en", "tr") == ["Çıkış"]
    assert len(s.requests) == 2


def test_bad_key_message():
    s = FakeSession(script=[Resp(401, "unauthorized")])
    with pytest.raises(RuntimeError, match="anahtarı geçersiz"):
        AiBackend("gemini", "yanlis", session=s).translate_batch(["Quit"], "en", "tr")


def test_parse_array():
    assert _parse_array('Tabii: ["a", "b"]', 2) == ["a", "b"]
    assert _parse_array("çeviri yok", 1) is None
    assert _parse_array('["a"]', 2) is None


def test_thinking_disabled_only_for_ollama():
    s = FakeSession()
    AiBackend("ollama", model="qwen3.8:27b", session=s).translate_batch(["Quit"], "en", "tr")
    assert s.requests[0]["body"]["reasoning_effort"] == "none"
    s2 = FakeSession()
    AiBackend("gemini", "k", session=s2).translate_batch(["Quit"], "en", "tr")
    assert "reasoning_effort" not in s2.requests[0]["body"]


def test_model_without_thinking_support_retries_without_setting():
    s = FakeSession(script=[Resp(400, '{"error":"model does not support thinking"}')])
    b = AiBackend("ollama", session=s)
    assert b.translate_batch(["Quit"], "en", "tr") == ["Çıkış"]
    assert "reasoning_effort" not in s.requests[1]["body"]
    b.translate_batch(["Quit"], "en", "tr")
    assert "reasoning_effort" not in s.requests[2]["body"]  # bir kez öğrenince bir daha göndermez


def test_think_block_is_ignored():
    reply = '<think>Kullanıcı ["x", "y"] istiyor...</think>\n["Yeni Oyun"]'
    assert _parse_array(reply, 1) == ["Yeni Oyun"]
