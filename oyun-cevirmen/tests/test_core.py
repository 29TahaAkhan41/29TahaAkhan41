import json
from pathlib import Path

from oyun_cevirmen import file_translator as ft
from oyun_cevirmen import placeholders as ph
from oyun_cevirmen.screen import group_words
from oyun_cevirmen.translator import Backend, Translator

SOZLUK = {"Hello": "Merhaba", "World": "Dünya", "Start Game": "Oyunu Başlat",
          "Options": "Seçenekler", "Quit": "Çıkış", "Health": "Can"}


class FakeBackend(Backend):
    name = "fake"

    def __init__(self, break_tokens=False):
        self.calls = 0
        self.break_tokens = break_tokens

    def translate_batch(self, texts, source, target):
        self.calls += 1
        out = []
        for t in texts:
            r = t
            for en, tr in SOZLUK.items():
                r = r.replace(en, tr)
            if self.break_tokens:
                r = r.replace("⟦", "[").replace("⟧", "]")
            out.append(r)
        return out


def tr(**kw):
    return Translator(FakeBackend(**kw), source="en", cache_file=None)


def test_protect_restore_roundtrip():
    s = "§aHello %s, {0} <b>World</b>\\n%1$d [color=red]Quit[/color] $NAME$"
    prot, found = ph.protect(s)
    assert "%s" not in prot and "§a" not in prot and "<b>" not in prot
    assert ph.restore(prot, found) == s


def test_placeholders_kept_after_translation():
    assert tr().translate("§eHello %s!") == "§eMerhaba %s!"
    assert tr().translate("Hello {player}\nWorld") == "Merhaba {player}\nDünya"


def test_broken_tokens_fall_back_to_segments():
    assert tr(break_tokens=True).translate("Hello %s World") == "Merhaba %s Dünya"


def test_numbers_and_symbols_not_sent():
    b = FakeBackend()
    t = Translator(b, cache_file=None)
    assert t.translate_many(["123", "%d/%d", "  "]) == ["123", "%d/%d", "  "]
    assert b.calls == 0


def test_cache(tmp_path):
    b = FakeBackend()
    t = Translator(b, cache_file=tmp_path / "c.json")
    t.translate("Hello")
    t2 = Translator(b, cache_file=tmp_path / "c.json")
    assert t2.translate("Hello") == "Merhaba" and b.calls == 1


def test_json_file(tmp_path):
    src = tmp_path / "en_us.json"
    src.write_text(json.dumps({"menu.start": "Start Game", "menu.opt": "Options",
                               "nested": {"q": ["Quit", 5]}, "tex": "textures/a.png",
                               "id": "minecraft:stone"}, indent=4), encoding="utf-8")
    dst = ft.default_output_path(src)
    assert dst.name == "tr_tr.json"
    ft.translate_file(src, dst, tr())
    data = json.loads(dst.read_text(encoding="utf-8"))
    assert data["menu.start"] == "Oyunu Başlat"
    assert data["nested"]["q"] == ["Çıkış", 5]
    assert data["tex"] == "textures/a.png" and data["id"] == "minecraft:stone"
    assert '\n    "menu.start"' in dst.read_text(encoding="utf-8")


def test_lang_and_ini(tmp_path):
    src = tmp_path / "en_US.lang"
    src.write_text("# comment\nitem.a=Hello\r\n[Section]\nb = World\nnum=12\n", encoding="utf-8")
    ft.translate_file(src, tmp_path / "out.lang", tr())
    out = (tmp_path / "out.lang").read_bytes().decode("utf-8")
    assert out == "# comment\nitem.a=Merhaba\r\n[Section]\nb = Dünya\nnum=12\n"


def test_po(tmp_path):
    src = tmp_path / "game.po"
    src.write_text('msgid ""\nmsgstr ""\n"Language: en\\n"\n\nmsgid "Quit"\nmsgstr ""\n\n'
                   'msgid "Options"\nmsgstr "Ayarlar"\n', encoding="utf-8")
    ft.translate_file(src, tmp_path / "o.po", tr())
    out = (tmp_path / "o.po").read_text(encoding="utf-8")
    assert 'msgid "Quit"\nmsgstr "Çıkış"' in out
    assert 'msgstr "Ayarlar"' in out  # zaten çevrilmiş olana dokunma
    assert '"Language: en\\n"' in out


def test_csv(tmp_path):
    src = tmp_path / "loc.csv"
    src.write_text("key,text\nui_start,Start Game\nui_hp,\"Health, max\"\n", encoding="utf-8")
    ft.translate_file(src, tmp_path / "o.csv", tr())
    assert (tmp_path / "o.csv").read_text(encoding="utf-8") == \
        "key,text\nui_start,Oyunu Başlat\nui_hp,\"Can, max\"\n"


def test_yaml(tmp_path):
    src = tmp_path / "l_english.yml"
    src.write_text('l_english:\n  start:0 "Start Game"  # c\n  quit: Quit\n', encoding="utf-8")
    dst = ft.default_output_path(src)
    assert dst.name == "l_turkish.yml"
    ft.translate_file(src, dst, tr())
    assert dst.read_text(encoding="utf-8") == \
        'l_turkish:\n  start:0 "Oyunu Başlat"  # c\n  quit: Çıkış\n'.replace("l_turkish", "l_english")


def test_xml(tmp_path):
    src = tmp_path / "s.xml"
    src.write_text('<?xml version="1.0"?>\n<r><s id="a" text="Hello">Options</s>'
                   '<s id="b">Quit &amp; Hello</s></r>', encoding="utf-8")
    ft.translate_file(src, tmp_path / "o.xml", tr())
    out = (tmp_path / "o.xml").read_text(encoding="utf-8")
    assert 'text="Merhaba"' in out and ">Seçenekler<" in out and ">Çıkış &amp; Merhaba<" in out
    assert 'id="a"' in out


def test_folder(tmp_path):
    (tmp_path / "in" / "sub").mkdir(parents=True)
    (tmp_path / "in" / "sub" / "a.txt").write_text("Hello\nWorld\n", encoding="utf-8")
    (tmp_path / "in" / "bad.json").write_text("{bozuk", encoding="utf-8")
    rep = dict(ft.translate_folder(tmp_path / "in", tmp_path / "out", tr()))
    assert (tmp_path / "out" / "sub" / "a.txt").read_text(encoding="utf-8") == "Merhaba\nDünya\n"
    assert any(isinstance(v, str) and v.startswith("HATA") for v in rep.values())


def test_group_words_lines_and_blocks():
    w = lambda x, y, t, h=20: {"x": x, "y": y, "w": len(t) * 10, "h": h, "text": t, "conf": 90}
    words = [
        w(100, 100, "Start"), w(160, 100, "Game"),          # buton 1
        w(100, 300, "Options"),                              # buton 2 (uzak)
        w(500, 500, "The"), w(540, 500, "knight"), w(610, 500, "said"),
        w(500, 524, "hello"), w(560, 524, "there"),         # 2 satırlık diyalog
    ]
    blocks = group_words(words, (10, 20))
    texts = sorted(b.text for b in blocks)
    assert texts == ["Options", "Start Game", "The knight said hello there"]
    sg = next(b for b in blocks if b.text == "Start Game")
    assert (sg.x, sg.y) == (110, 120)
