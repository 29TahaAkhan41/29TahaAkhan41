import json

from oyun_cevirmen.glossary import Glossary, match_case, tr_upper
from oyun_cevirmen.translator import Backend, Translator


class Recorder(Backend):
    """Gönderilen metni kaydeder; Google gibi davranır (normal yazıyı doğru çevirir)."""
    name = "rec"
    TR = {"Talk to the old man": "Yaşlı adamla konuş", "Hollow knight": "Hollow knight",
          "Visit the city of tears": "Gözyaşı şehrini ziyaret et"}

    def __init__(self):
        self.sent = []

    def translate_batch(self, texts, s, t):
        self.sent += texts
        return [self.TR.get(x, x) for x in texts]


def make(tmp_path=None, user=None):
    f = None
    if tmp_path is not None:
        f = tmp_path / "sozluk.json"
        if user:
            f.write_text(json.dumps(user, ensure_ascii=False), encoding="utf-8")
    b = Recorder()
    return Translator(b, source="en", cache_file=None, glossary=Glossary(f)), b


def test_menu_items_from_photo():
    # Kullanıcının Hollow Knight fotoğrafındaki hatalı çeviriler
    t, b = make()
    out = t.translate_many(["START GAME", "OPTIONS", "ACHIEVEMENTS", "EXTRAS", "QUIT GAME"])
    assert out == ["OYUNA BAŞLA", "SEÇENEKLER", "BAŞARIMLAR", "EKSTRALAR", "OYUNDAN ÇIK"]
    assert b.sent == []  # hiçbiri çeviri motoruna gitmedi


def test_ocr_errors_still_match():
    t, _ = make()
    assert t.translate("STARTGAME") == "OYUNA BAŞLA"     # boşluk yutulmuş
    assert t.translate("QUlT GAME") == "OYUNDAN ÇIK"     # l / I karışıklığı
    assert t.translate("Achievernents") == "Başarımlar"  # rn / m karışıklığı
    assert t.translate("options") == "seçenekler"        # harf biçimi korunur


def test_caps_sent_in_normal_case_and_uppercased_back():
    t, b = make()
    assert t.translate("TALK TO THE OLD MAN") == "YAŞLI ADAMLA KONUŞ"
    assert b.sent == ["Talk to the old man"]
    assert t.translate("VISIT THE CITY OF TEARS") == "GÖZYAŞI ŞEHRİNİ ZİYARET ET"  # i -> İ


def test_untranslated_proper_name_not_mangled():
    t, _ = make()
    # Çevirmen özel adı değiştirmeden döndürürse Türkçe büyütme uygulanmamalı ("KNİGHT" olmasın)
    assert t.translate("HOLLOW KNIGHT") == "HOLLOW KNIGHT"


def test_user_glossary_overrides(tmp_path):
    t, b = make(tmp_path, {"Geo": "Geo", "Options": "Ayarlar", "Hallownest": "Hallownest"})
    assert t.translate("OPTIONS") == "AYARLAR"
    assert t.translate("Geo") == "Geo"
    assert b.sent == []


def test_turkish_case_helpers():
    assert tr_upper("ışık ve iğne") == "IŞIK VE İĞNE"
    assert match_case("QUIT", "çık") == "ÇIK"
    assert match_case("quit", "Çık") == "çık"
    assert match_case("Quit", "Çık") == "Çık"


def test_long_sentences_not_glossary_matched():
    g = Glossary(None)
    assert g.lookup("Start the game when you are ready to fight the boss") is None
