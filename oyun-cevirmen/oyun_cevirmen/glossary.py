"""Oyun arayüzü sözlüğü ve Türkçe büyük/küçük harf işlemleri.

Menü ve buton yazıları çok kısadır; çeviri motorları bunları bağlamsız çevirince
"Quit Game" -> "OYNU", "Extras" -> "EKLER" gibi hatalar çıkar. Sık görülen arayüz
yazıları için burada hazır, oyuncuların alıştığı Türkçe karşılıklar var. Kullanıcı
kendi düzeltmelerini ~/.oyun_cevirmen/sozluk.json dosyasına ekleyebilir; onlar
önceliklidir.
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

# İngilizce (küçük harf) -> Türkçe. Anahtarlar normalize edilerek eşleştirilir.
BUILTIN_EN: dict[str, str] = {
    # Ana menü
    "start game": "Oyuna Başla", "start": "Başla", "new game": "Yeni Oyun",
    "continue": "Devam Et", "resume": "Devam Et", "resume game": "Oyuna Devam Et",
    "load game": "Oyun Yükle", "load": "Yükle", "save game": "Oyunu Kaydet", "save": "Kaydet",
    "save and quit": "Kaydet ve Çık", "quit": "Çık", "quit game": "Oyundan Çık",
    "exit": "Çıkış", "exit game": "Oyundan Çık", "quit to menu": "Menüye Dön",
    "quit to main menu": "Ana Menüye Dön", "main menu": "Ana Menü", "quit to desktop": "Masaüstüne Çık",
    "options": "Seçenekler", "settings": "Ayarlar", "extras": "Ekstralar",
    "achievements": "Başarımlar", "credits": "Yapımcılar", "play": "Oyna",
    "play game": "Oyunu Oyna", "single player": "Tek Oyunculu", "multiplayer": "Çok Oyunculu",
    "co-op": "Ortak Oyun", "online": "Çevrimiçi", "leaderboards": "Sıralamalar",
    "tutorial": "Eğitim", "help": "Yardım", "how to play": "Nasıl Oynanır",
    "profile": "Profil", "store": "Mağaza", "shop": "Dükkân", "news": "Haberler",
    "chapter select": "Bölüm Seç", "level select": "Seviye Seç", "select profile": "Profil Seç",
    # Duraklatma ve onay
    "paused": "Duraklatıldı", "pause": "Duraklat", "back": "Geri", "return": "Geri Dön",
    "apply": "Uygula", "cancel": "İptal", "confirm": "Onayla", "accept": "Kabul Et",
    "yes": "Evet", "no": "Hayır", "ok": "Tamam", "close": "Kapat", "delete": "Sil",
    "select": "Seç", "reset": "Sıfırla", "reset to default": "Varsayılana Sıfırla",
    "restore defaults": "Varsayılanları Geri Yükle", "default": "Varsayılan",
    "are you sure?": "Emin misiniz?", "retry": "Tekrar Dene", "restart": "Yeniden Başlat",
    "restart level": "Bölümü Yeniden Başlat", "skip": "Geç", "next": "İleri",
    "previous": "Önceki", "press any key": "Herhangi bir tuşa basın",
    "press any button": "Herhangi bir düğmeye basın", "loading": "Yükleniyor",
    "saving...": "Kaydediliyor...",
    # Ayarlar
    "game": "Oyun", "gameplay": "Oynanış", "graphics": "Grafik", "video": "Görüntü",
    "display": "Ekran", "audio": "Ses", "sound": "Ses", "controls": "Kontroller",
    "keyboard": "Klavye", "controller": "Oyun Kumandası", "gamepad": "Oyun Kumandası",
    "mouse": "Fare", "language": "Dil", "brightness": "Parlaklık", "volume": "Ses Düzeyi",
    "master volume": "Ana Ses", "music": "Müzik", "music volume": "Müzik Sesi",
    "sound effects": "Ses Efektleri", "sfx": "Ses Efektleri", "fullscreen": "Tam Ekran",
    "full screen": "Tam Ekran", "windowed": "Pencereli", "borderless": "Kenarlıksız",
    "resolution": "Çözünürlük", "subtitles": "Altyazılar", "difficulty": "Zorluk",
    "easy": "Kolay", "normal": "Normal", "hard": "Zor", "on": "Açık", "off": "Kapalı",
    "keybindings": "Tuş Atamaları", "key bindings": "Tuş Atamaları",
    "accessibility": "Erişilebilirlik", "camera": "Kamera", "sensitivity": "Hassasiyet",
    # Oyun içi
    "inventory": "Envanter", "map": "Harita", "quests": "Görevler", "quest": "Görev",
    "quest log": "Görev Günlüğü", "journal": "Günlük", "skills": "Yetenekler",
    "abilities": "Yetenekler", "equipment": "Ekipman", "items": "Eşyalar",
    "character": "Karakter", "stats": "İstatistikler", "crafting": "Üretim",
    "health": "Can", "mana": "Mana", "stamina": "Dayanıklılık", "level": "Seviye",
    "level up": "Seviye Atladın", "game over": "Oyun Bitti", "you died": "Öldün",
    "victory": "Zafer", "defeat": "Yenilgi", "gold": "Altın", "coins": "Para",
    "objective": "Hedef", "new objective": "Yeni Hedef", "quest complete": "Görev Tamamlandı",
    "quest completed": "Görev Tamamlandı", "mission complete": "Görev Tamamlandı",
    "checkpoint": "Kontrol Noktası", "game saved": "Oyun Kaydedildi", "use": "Kullan",
    "equip": "Kuşan", "unequip": "Çıkar", "drop": "Bırak", "talk": "Konuş",
    "interact": "Etkileşim", "open": "Aç", "pick up": "Al", "attack": "Saldır",
    "jump": "Zıpla", "sprint": "Koş", "inspect": "İncele", "rest": "Dinlen",
}

TR_LOWER = str.maketrans({"I": "ı", "İ": "i"})
TR_UPPER = str.maketrans({"i": "İ", "ı": "I"})


def tr_upper(s: str) -> str:
    return s.translate(TR_UPPER).upper()


def tr_lower(s: str) -> str:
    return s.translate(TR_LOWER).lower()


def is_all_caps(s: str) -> bool:
    """BÜYÜK HARFLİ mi? OCR'ın tek tük küçük okuduğu harfler ("QUlT") yanıltmasın."""
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 2 and sum(c.isupper() for c in letters) / len(letters) >= 0.8


def _key(s: str) -> str:
    """Eşleştirme anahtarı: yalnızca harfler ve rakamlar, küçük harf.

    OCR'ın boşluk yutması ("STARTGAME") veya noktalama hataları eşleşmeyi bozmasın.
    """
    # i/ı/İ ayrımı yapılmaz: İngilizce "QUIT" ile Türkçe "quıt" aynı anahtara düşsün
    low = s.lower().replace("\u0307", "").replace("ı", "i")
    low = re.sub(r"[^0-9a-zğüşöçâîû|!]", "", low)
    # OCR'ın sık karıştırdığı karakterler (iki tarafa da aynı uygulanır):
    # l / I / 1 / | / !  ->  i,   0 -> o,   rn -> m,   vv -> w
    low = low.translate(str.maketrans({"l": "i", "1": "i", "|": "i", "!": "i", "0": "o"}))
    return low.replace("rn", "m").replace("vv", "w")


def match_case(original: str, translated: str) -> str:
    """Çevirinin büyük/küçük harf biçimini orijinale uydurur."""
    if is_all_caps(original):
        return tr_upper(translated)
    letters = [c for c in original if c.isalpha()]
    if letters and all(c.islower() for c in letters):
        return tr_lower(translated)
    return translated


class Glossary:
    def __init__(self, user_file: Path | None = None, use_builtin: bool = True):
        self.user_file = user_file
        self.use_builtin = use_builtin
        self._mtime = None
        self._load()

    def _load(self) -> None:
        entries: dict[str, str] = dict(BUILTIN_EN) if self.use_builtin else {}
        if self.user_file and self.user_file.exists():
            try:
                user = json.loads(self.user_file.read_text(encoding="utf-8"))
                entries.update({k: v for k, v in user.items()
                                if isinstance(v, str) and not k.startswith("_")})
                self._mtime = self.user_file.stat().st_mtime
            except (OSError, ValueError):
                pass
        self.entries = entries
        self.by_key = {_key(k): v for k, v in entries.items() if _key(k)}
        self._keys = list(self.by_key)

    def _reload_if_changed(self) -> None:
        if self.user_file and self.user_file.exists():
            try:
                if self.user_file.stat().st_mtime != self._mtime:
                    self._load()
            except OSError:
                pass

    def lookup(self, text: str) -> str | None:
        """Metin sözlükteki bir girişe denk geliyorsa çevirisini (harf biçimi uydurulmuş) döner."""
        self._reload_if_changed()
        k = _key(text)
        if not k or len(text) > 40:
            return None
        hit = self.by_key.get(k)
        if hit is None and len(k) >= 6:
            # OCR'ın tek-iki harf hatası ("QUlT GAME", "Achievernents")
            close = difflib.get_close_matches(k, self._keys, n=1, cutoff=0.88)
            if close:
                hit = self.by_key[close[0]]
        return match_case(text, hit) if hit is not None else None

    def ensure_user_file(self) -> Path:
        """Kullanıcı sözlüğü yoksa örnekli bir dosya oluşturur ve yolunu döner."""
        assert self.user_file
        if not self.user_file.exists():
            self.user_file.parent.mkdir(parents=True, exist_ok=True)
            sample = {
                "_aciklama": "Soldaki yazı oyunda nasıl geçiyorsa (büyük/küçük harf fark etmez), "
                             "sağa istediğiniz Türkçesini yazın. Kaydedince hemen geçerli olur.",
                "Hallownest": "Hallownest",
                "Geo": "Geo",
            }
            self.user_file.write_text(json.dumps(sample, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
        return self.user_file
