#!/usr/bin/env python3
"""Nehir derleyicisi.

Nehir kaynak kodunu (.nehir) doğrudan x86-64 Linux assembly'sine çevirir,
ardından `as` ve `ld` ile libc'siz, bağımsız bir çalıştırılabilir dosya üretir.

Aşamalar:  kaynak -> Sözcükleyici -> Ayrıştırıcı (AST) -> Kod üretici -> .s -> as/ld
"""
import difflib
import errno
import os
import subprocess
import sys


class Konum(int):
    """Bir satır numarası gibi davranır ama sütunu ve uzunluğu da taşır;
    hata mesajları kaynak satırında tam yeri gösterebilsin diye."""

    def __new__(cls, satır, sütun=1, uzunluk=1, dosya=0):
        k = super().__new__(cls, satır)
        k.sütun, k.uzunluk = sütun, uzunluk
        k.dosya = dosya     # derlemedeki kaçıncı dosya (0 ana dosya, sonrakiler modüller)
        return k


class NehirHatası(Exception):
    def __init__(self, mesaj, satır=None, ipucu=None, ilgili=None, ilgili_not="ilk tanım burada"):
        super().__init__(mesaj)
        self.mesaj = mesaj
        self.satır = satır
        self.ipucu = ipucu
        self.ilgili = ilgili            # hatayla ilgili ikinci bir yer (örneğin ilk tanım)
        self.ilgili_not = ilgili_not    # o yerin yanına yazılacak açıklama


def gizli_eki(ad):
    """Dosyaya özel adların sonundaki görünmez işaretlerin sayısı (özel değilse 0)."""
    return len(ad) - len(ad.rstrip("\u2063"))


ÖZEL_AD_İPUCU = "'_' ile başlayan adlar yalnızca tanımlandıkları dosyada geçerlidir"


def benzerler(ad, adaylar):
    """Yazım hatası için 'şunu mu demek istediniz' ipucu; benzer ad yoksa None. Başka
    dosyalara özel adlar önerilmez."""
    adaylar = [a for a in adaylar if gizli_eki(a) == gizli_eki(ad)]
    yakın = difflib.get_close_matches(ad, sorted(set(adaylar) - {ad}), n=2, cutoff=0.7)
    if not yakın:
        return None
    return " ya da ".join(f"'{y}'" for y in yakın) + " mi demek istediniz?"


# ───────────────────────────── Sözcükleyici ─────────────────────────────

# Her anahtar kelimenin Türkçe, ASCII-Türkçe ve İngilizce yazımı aynı şeye çıkar.
ANAHTARLAR = {
    "eğer": "eğer", "eger": "eğer", "if": "eğer",
    "değilse": "değilse", "degilse": "değilse", "else": "değilse",
    "iken": "iken", "while": "iken",
    "her": "her", "each": "her",
    "dur": "dur", "break": "dur",
    "devam": "devam", "continue": "devam",
    "işlev": "işlev", "islev": "işlev", "fonksiyon": "işlev", "fn": "işlev",
    "kayıt": "kayıt", "kayit": "kayıt", "record": "kayıt",
    "kullan": "kullan", "use": "kullan", "import": "kullan",
    "ortak": "ortak", "shared": "ortak",
    "yok": "yok", "none": "yok",
    "döndür": "döndür", "dondur": "döndür", "return": "döndür",
    "yazdır": "yazdır", "yazdir": "yazdır", "print": "yazdır",
    "doğru": "doğru", "dogru": "doğru", "true": "doğru",
    "yanlış": "yanlış", "yanlis": "yanlış", "false": "yanlış",
    "ve": "ve", "and": "ve",
    "veya": "veya", "or": "veya",
    "değil": "değil", "degil": "değil", "not": "değil",
}

# Yerleşik işlevler: yazım -> asıl ad
YERLEŞİKLER = {
    "uzunluk": "uzunluk", "len": "uzunluk",
    "ekle": "ekle", "push": "ekle",
    "aralık": "aralık", "aralik": "aralık", "range": "aralık",
    "metne": "metne", "str": "metne",
    "sayıya": "sayıya", "sayiya": "sayıya", "num": "sayıya",
    "dilim": "dilim", "slice": "dilim",
    "bul": "bul", "find": "bul",
    "sil": "sil", "remove": "sil",
    "böl": "böl", "bol": "böl", "split": "böl",
    "birleş": "birleş", "birles": "birleş", "join": "birleş",
    "var": "var", "has": "var",
    "anahtarlar": "anahtarlar", "keys": "anahtarlar",
    "değerler": "değerler", "degerler": "değerler", "values": "değerler",
    "dosya_oku": "dosya_oku", "read_file": "dosya_oku",
    "dosya_yaz": "dosya_yaz", "write_file": "dosya_yaz",
    "dosya_ekle": "dosya_ekle", "append_file": "dosya_ekle",
    "dosya_var": "dosya_var", "file_exists": "dosya_var",
    "dosya_sil": "dosya_sil", "delete_file": "dosya_sil",
    "argümanlar": "argümanlar", "argumanlar": "argümanlar", "args": "argümanlar",
    "çık": "çık", "cik": "çık", "exit": "çık",
    "uyar": "uyar", "warn": "uyar",
    "baytlar": "baytlar", "bytes": "baytlar",
    "karakter": "karakter", "char": "karakter",
    "işletim_sistemi": "işletim_sistemi", "isletim_sistemi": "işletim_sistemi", "os_name": "işletim_sistemi",
    "uçbirim_mi": "uçbirim_mi", "ucbirim_mi": "uçbirim_mi", "is_terminal": "uçbirim_mi",
    "ortam_var": "ortam_var", "has_env": "ortam_var",
    "dosya_hatası": "dosya_hatası", "dosya_hatasi": "dosya_hatası", "file_error": "dosya_hatası",
    "oku": "oku", "read": "oku",
    "girdi_var": "girdi_var", "has_input": "girdi_var",
    "zaman": "zaman", "time_ms": "zaman",
    "bekle": "bekle", "sleep": "bekle",
    "rastgele": "rastgele", "random": "rastgele",
    "rastgele_tohum": "rastgele_tohum", "seed_random": "rastgele_tohum",
    "tuş_kipi": "tuş_kipi", "tus_kipi": "tuş_kipi", "key_mode": "tuş_kipi",
    "tuş": "tuş", "tus": "tuş", "key": "tuş",
    "göster": "göster", "goster": "göster", "show": "göster",
    "uçbirim_boyutu": "uçbirim_boyutu", "ucbirim_boyutu": "uçbirim_boyutu",
    "terminal_size": "uçbirim_boyutu",
    "çöp_topla": "çöp_topla", "cop_topla": "çöp_topla", "collect_garbage": "çöp_topla",
    "ondalığa": "ondalığa", "ondaliga": "ondalığa", "float": "ondalığa",
    "yuvarla": "yuvarla", "round": "yuvarla",
    "taban": "taban", "floor": "taban",
    "tavan": "tavan", "ceil": "tavan",
    "karekök": "karekök", "karekok": "karekök", "sqrt": "karekök",
    "mutlak": "mutlak", "abs": "mutlak",
    "sin": "sin", "cos": "cos", "atan2": "atan2",
    "pi": "pi",
    "bit_ve": "bit_ve", "bit_and": "bit_ve",
    "bit_veya": "bit_veya", "bit_or": "bit_veya",
    "bit_yada": "bit_yada", "bit_xor": "bit_yada",
    "bit_değil": "bit_değil", "bit_degil": "bit_değil", "bit_not": "bit_değil",
    "sola_kaydır": "sola_kaydır", "sola_kaydir": "sola_kaydır", "shift_left": "sola_kaydır",
    "sağa_kaydır": "sağa_kaydır", "saga_kaydir": "sağa_kaydır", "shift_right": "sağa_kaydır",
    "en_küçük": "en_küçük", "en_kucuk": "en_küçük", "min": "en_küçük",
    "en_büyük": "en_büyük", "en_buyuk": "en_büyük", "max": "en_büyük",
    "sınırla": "sınırla", "sinirla": "sınırla", "clamp": "sınırla",
    "işaret": "işaret", "isaret": "işaret", "sign": "işaret",
    "üs": "üs", "us": "üs", "pow": "üs",
    "tan": "tan", "atan": "atan", "asin": "asin", "acos": "acos",
    "üstel": "üstel", "ustel": "üstel", "exp": "üstel",
    "ln": "ln", "log": "ln",
    "ekran_aç": "ekran_aç", "ekran_ac": "ekran_aç", "screen_open": "ekran_aç",
    "ekran_kapat": "ekran_kapat", "screen_close": "ekran_kapat",
    "ekran_temizle": "ekran_temizle", "screen_clear": "ekran_temizle",
    "ekran_yaz": "ekran_yaz", "screen_text": "ekran_yaz",
    "ekran_doldur": "ekran_doldur", "screen_fill": "ekran_doldur",
    "ekran_çiz": "ekran_çiz", "ekran_ciz": "ekran_çiz", "screen_draw": "ekran_çiz",
    "rgb": "rgb",
    "sırala": "sırala", "sirala": "sırala", "sort": "sırala",
    "ters_çevir": "ters_çevir", "ters_cevir": "ters_çevir", "reverse": "ters_çevir",
    "tuş_bırakma_var": "tuş_bırakma_var", "tus_birakma_var": "tuş_bırakma_var",
    "key_release_supported": "tuş_bırakma_var",
}

İŞLEÇLER = ["->", "→", "==", "!=", "<=", ">=",
            "+", "-", "*", "/", "%", "<", ">", "(", ")", "{", "}", "[", "]", ",", "|", ":", "."]

KAÇIŞLAR = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\"}


def uzaklık(a, b):
    """Düzenleme (Levenshtein) uzaklığı."""
    önceki = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        şimdiki = [i]
        for j, y in enumerate(b, 1):
            şimdiki.append(min(önceki[j] + 1, şimdiki[j - 1] + 1, önceki[j - 1] + (x != y)))
        önceki = şimdiki
    return önceki[-1]


class Sözcük:
    def __init__(self, tür, değer, satır, yeni_satır, yazım):
        self.tür, self.değer, self.satır = tür, değer, satır
        self.yeni_satır = yeni_satır    # bu sözcük satırının ilk sözcüğü mü?
        self.yazım = yazım              # kaynakta yazıldığı hâli

    def __repr__(self):
        return f"{self.tür}:{self.değer!r}"


def sözcükle(kaynak, dosya=0):
    sözcükler, i, satır, n = [], 0, 1, len(kaynak)
    satır_başı = 0
    son_satır = 0

    def konum(baş, son):
        return Konum(satır, baş - satır_başı + 1, max(son - baş, 1), dosya)

    def ekle(tür, değer, baş, son):
        nonlocal son_satır
        sözcükler.append(Sözcük(tür, değer, konum(baş, son), satır != son_satır, kaynak[baş:son]))
        son_satır = satır

    while i < n:
        c = kaynak[i]
        if c == "\n":
            satır += 1
            i += 1
            satır_başı = i
        elif c.isspace():
            i += 1
        elif c == ";":
            son_satır = 0       # ';' de deyimleri ayırır
            i += 1
        elif c == "#":
            while i < n and kaynak[i] != "\n":
                i += 1
        elif c == "0" and i + 1 < n and kaynak[i + 1] in "xXbB":    # 0xFF, 0b1010
            taban = 16 if kaynak[i + 1] in "xX" else 2
            geçerli = "0123456789abcdefABCDEF" if taban == 16 else "01"
            j = i + 2
            while j < n and (kaynak[j] in geçerli or kaynak[j] == "_"):
                j += 1
            rakamlar = kaynak[i + 2:j].replace("_", "")
            if not rakamlar:
                raise NehirHatası(f"'{kaynak[i:i + 2]}' ardından {'onaltılık' if taban == 16 else 'ikili'} "
                                  f"rakamlar gelmeli", konum(i, j))
            değer = int(rakamlar, taban)
            if değer >= 2 ** 63:
                raise NehirHatası("sayı çok büyük; en fazla 9223372036854775807 olabilir", konum(i, j))
            ekle("SAYI", değer, i, j)
            i = j
        elif c in "0123456789":     # yalnızca ASCII rakamları (int() '²' gibi rakamları çeviremez)
            j = i
            while j < n and (kaynak[j] in "0123456789" or kaynak[j] == "_"):
                j += 1
            if j + 1 < n and kaynak[j] == "." and kaynak[j + 1] in "0123456789":
                # Ondalık sayı: yazıldığı gibi saklanır, ikili değerine çeviriyi derleyici yapar
                j += 1
                while j < n and (kaynak[j] in "0123456789" or kaynak[j] == "_"):
                    j += 1
                ekle("ONDALIK", kaynak[i:j].replace("_", ""), i, j)
                i = j
                continue
            değer = int(kaynak[i:j].replace("_", ""))
            if değer >= 2 ** 63:
                raise NehirHatası("sayı çok büyük; en fazla 9223372036854775807 olabilir", konum(i, j))
            ekle("SAYI", değer, i, j)
            i = j
        elif c == '"':
            j, parçalar = i + 1, []
            while True:
                if j >= n or kaynak[j] == "\n":
                    raise NehirHatası("metin kapatılmamış", konum(i, j),
                                      "metinler aynı satırda \" ile kapanmalı; "
                                      "satır sonu için \\n yazın")
                if kaynak[j] == '"':
                    break
                if kaynak[j] == "\\":
                    j += 1
                    if j >= n or kaynak[j] not in KAÇIŞLAR:
                        raise NehirHatası("geçersiz kaçış dizisi", konum(j - 1, j + 1),
                                          "geçerli olanlar: \\n  \\t  \\r  \\\"  \\\\")
                    parçalar.append(KAÇIŞLAR[kaynak[j]])
                else:
                    parçalar.append(kaynak[j])
                j += 1
            ekle("METİN", "".join(parçalar), i, j + 1)
            i = j + 1
        elif c.isalpha() or c == "_":
            j = i
            while j < n and (kaynak[j].isalnum() or kaynak[j] == "_"):
                j += 1
            ad = kaynak[i:j]
            if ad in ANAHTARLAR:
                ekle("ANAHTAR", ANAHTARLAR[ad], i, j)
            else:
                ekle("AD", ad, i, j)
            i = j
        else:
            for iş in İŞLEÇLER:
                if kaynak.startswith(iş, i):
                    ekle("İŞLEÇ", "->" if iş == "→" else iş, i, i + len(iş))
                    i += len(iş)
                    break
            else:
                if c == "=":
                    raise NehirHatası("Nehir'de '=' ile atama yok", konum(i, i + 1),
                                      "değer soldan sağa akar: 5 -> x   (eşitlik sınaması için ==)")
                raise NehirHatası(f"tanınmayan karakter: {c!r}", konum(i, i + 1))
    özel_adları_ayır(sözcükler, dosya)
    ekle("SON", None, n, n)
    return sözcükler


# Bir dosyada '_' ile başlayan adlar (işlev, kayıt, değişken) yalnızca o dosyada geçerlidir:
# adın sonuna dosyaya özgü, ekranda görünmeyen bir işaret (dosya numarası + 1 kez U+2063)
# eklenir; böylece iki modüldeki '_yardımcı' karışmaz, hata mesajlarında ad aynen görünür.
# '.' sonrasındaki alan ve yöntem adlarına ve kayıt tanımındaki alan adlarına dokunulmaz.
# kendi/sozcukleyici.nehir'deki özel_adları_ayır ile aynı olmalıdır.
GİZLİ_İŞARET = "\u2063"


def özel_adları_ayır(sözcükler, dosya):
    işaret = GİZLİ_İŞARET * (dosya + 1)
    durum, derinlik, önceki = 0, 0, None     # durum: 1 kayıt adı, 2 '{' bekleniyor, 3 kayıt gövdesi
    for s in sözcükler:
        alan_adı = False
        if s.tür == "ANAHTAR" and s.değer == "kayıt":
            durum = 1
        elif durum == 1 and s.tür == "AD":
            durum = 2
        elif durum == 2 and s.tür == "İŞLEÇ" and s.değer == "{":
            durum, derinlik = 3, 1
        elif durum == 3:
            if s.tür == "İŞLEÇ" and s.değer in ("{", "["):
                derinlik += 1
            elif s.tür == "İŞLEÇ" and s.değer in ("}", "]"):
                derinlik -= 1
                if derinlik == 0:
                    durum = 0
            elif s.tür == "AD" and derinlik == 1 and önceki is not None and önceki.tür == "İŞLEÇ" \
                    and önceki.değer in ("{", ","):
                alan_adı = True
        else:
            durum = 0 if durum != 3 else durum
        if s.tür == "AD" and s.değer.startswith("_") and not alan_adı \
                and not (önceki is not None and önceki.tür == "İŞLEÇ" and önceki.değer == "."):
            s.değer += işaret
        önceki = s


# ───────────────────────────── Ayrıştırıcı ─────────────────────────────
# AST düğümleri basit demetlerdir; ilk eleman düğüm türü, son eleman satır no.
#
#   ("sayı", değer, satır)            ("metin", değer, satır)
#   ("değişken", ad, satır)           ("çağrı", ad, [argümanlar], satır)
#   ("liste", [elemanlar], satır)     ("dizin", ifade, dizin_ifadesi, satır)
#   ("sözlük", [(anahtar, değer), ...], satır)
#   ("alan", ifade, alan_adı, satır)  ("yok", satır)
#   ("yöntem", nesne_ifadesi, yöntem_adı, [argümanlar], satır)      nesne.yöntem(...)
#   ("tekli", işleç, ifade, satır)    ("ikili", işleç, sol, sağ, satır)
#   ("akış", kaynak_ifade, [hedefler], satır)
#   ("dur", satır)  ("devam", satır)              döngüden çık / sonraki tura geç
#
# Hedefler:
#   ("yazdır", satır)  ("döndür", satır)  ("ad", ad, argümanlar|None, satır)
#   ("eleman", kap_ifadesi, dizin_ifadesi, satır) değer -> liste[dizin], değer -> sözlük[anahtar]
#   ("alan_yaz", kayıt_ifadesi, alan_adı, satır)  değer -> kayıt.alan
#   ("yöntem_hedef", nesne_ifadesi, yöntem_adı, [argümanlar], satır)  değer -> nesne.yöntem(...)
#   ("ortak", ad, satır)                          değer -> ortak ad
#   ("eğer", blok, değilse_blok|None, satır)  ("iken", blok, satır)
#   ("her", değişken, blok, satır)                liste -> her (x) { ... }
#   ("çatal", [[hedefler], [hedefler], ...], satır)   değer -> (a | b -> c)

SONLANDIRAN = ("eğer", "iken", "her", "döndür")   # bu hedeflerden sonra akış devam etmez


class Ayrıştırıcı:
    def __init__(self, sözcükler, işlevler=None, kayıtlar=None, içe_aktar=None):
        self.s = sözcükler
        self.k = 0
        # İşlev ve kayıt adları bütün modüllerde ortaktır; sözlükler paylaşılır.
        self.işlevler = {} if işlevler is None else işlevler   # ad -> (parametreler, gövde, satır)
        self.kayıtlar = {} if kayıtlar is None else kayıtlar   # ad -> ([(alan, tür ifadesi|None, satır)], satır)
        self.içe_aktar = içe_aktar      # (yol metni, konum) -> modülün üst düzey deyimleri

    @property
    def şimdiki(self):
        return self.s[self.k]

    def bak(self, tür, değer=None):
        s = self.şimdiki
        return s.tür == tür and (değer is None or s.değer == değer)

    def aynı_satırda(self, değer):
        """Ardıl '(' ve '[' yalnızca aynı satırdaysa önceki ifadeye bağlanır;
        böylece yeni satırda '[' ya da '(' ile başlayan deyim ayrı kalır."""
        return self.bak("İŞLEÇ", değer) and not self.şimdiki.yeni_satır

    def al(self, tür, değer=None):
        if self.bak(tür, değer):
            self.k += 1
            return self.s[self.k - 1]
        return None

    def bekle(self, tür, değer=None):
        s = self.al(tür, değer)
        if s is None:
            beklenen = {"AD": "bir ad"}.get(tür, tür) if değer is None else f"'{değer}'"
            raise NehirHatası(f"{beklenen} bekleniyordu, {self.bulunan()} bulundu", self.şimdiki.satır)
        return s

    def bulunan(self):
        s = self.şimdiki
        return "dosya sonu" if s.tür == "SON" else f"'{s.yazım}'"

    def program(self):
        deyimler = []
        while not self.bak("SON"):
            if self.bak("ANAHTAR", "işlev"):
                self.işlev_tanımı()
            elif self.bak("ANAHTAR", "kayıt"):
                self.kayıt_tanımı()
            elif self.al("ANAHTAR", "kullan"):
                # Modülün işlevleri ve kayıtları ortak tablolara girer; üst düzey
                # deyimleri tam bu noktada çalışacak şekilde araya eklenir.
                yol = self.bekle("METİN")
                deyimler += self.içe_aktar(yol.değer, yol.satır)
            else:
                deyimler.append(self.deyim())
        return deyimler

    def yeni_ad(self, sözcük):
        """Yeni bir işlev ya da kayıt adı. Yerleşik bir işlevle aynı olabilir; o zaman
        programın kendi tanımı yerleşik olanı gölgeler."""
        ad = sözcük.değer
        if ad in self.işlevler or ad in self.kayıtlar:
            ilk = self.işlevler[ad][2] if ad in self.işlevler else self.kayıtlar[ad][1]
            raise NehirHatası(f"'{ad}' adı zaten bir {'işlev' if ad in self.işlevler else 'kayıt'} "
                              f"için kullanılmış", sözcük.satır, ilgili=ilk)
        return ad

    def kayıt_tanımı(self):
        """kayıt Ad { alan, alan: Tür, ... }"""
        self.bekle("ANAHTAR", "kayıt")
        ad_sözcüğü = self.bekle("AD")
        ad = self.yeni_ad(ad_sözcüğü)
        self.bekle("İŞLEÇ", "{")
        alanlar = []
        while not self.bak("İŞLEÇ", "}"):
            alan = self.bekle("AD")
            if any(a[0] == alan.değer for a in alanlar):
                raise NehirHatası(f"'{ad}' kaydında '{alan.değer}' alanı iki kez tanımlanmış", alan.satır)
            tür = self.tür_ifadesi() if self.al("İŞLEÇ", ":") else None
            alanlar.append((alan.değer, tür, alan.satır))
            if not self.al("İŞLEÇ", ","):
                break
        self.bekle("İŞLEÇ", "}")
        self.kayıtlar[ad] = (alanlar, ad_sözcüğü.satır)

    def tür_ifadesi(self):
        """Tür adı:  sayı | metin | KayıtAdı | [Tür] | {Tür: Tür}"""
        s = self.şimdiki
        if self.al("İŞLEÇ", "["):
            eleman = self.tür_ifadesi()
            self.bekle("İŞLEÇ", "]")
            return ("liste", eleman, s.satır)
        if self.al("İŞLEÇ", "{"):
            anahtar = self.tür_ifadesi()
            self.bekle("İŞLEÇ", ":")
            değer = self.tür_ifadesi()
            self.bekle("İŞLEÇ", "}")
            return ("sözlük", anahtar, değer, s.satır)
        if self.al("AD"):
            return ("ad", s.değer, s.satır)
        raise NehirHatası(f"bir tür bekleniyordu, {self.bulunan()} bulundu", s.satır,
                          "türler: sayı, metin, bir kayıt adı, [Tür], {Tür: Tür}")

    def işlev_tanımı(self):
        self.bekle("ANAHTAR", "işlev")
        ad_sözcüğü = self.bekle("AD")
        if self.al("İŞLEÇ", "."):
            # Yöntem:  işlev Kayıt.ad(nesne, ...) — kaydın adıyla ayrı bir ad alanında durur.
            yöntem = self.bekle("AD")
            if ad_sözcüğü.değer not in self.kayıtlar:
                raise NehirHatası(f"'{ad_sözcüğü.değer}' adında bir kayıt yok", ad_sözcüğü.satır,
                                  "yöntemin kaydı, yöntemden önce tanımlanmalı:  kayıt Ad { ... }")
            ad, satır = ad_sözcüğü.değer + "." + yöntem.değer, ad_sözcüğü.satır
            if ad in self.işlevler:
                raise NehirHatası(f"'{ad}' yöntemi zaten tanımlanmış", yöntem.satır, ilgili=self.işlevler[ad][2])
        else:
            ad, satır = self.yeni_ad(ad_sözcüğü), ad_sözcüğü.satır
        self.bekle("İŞLEÇ", "(")
        parametreler = []
        if not self.bak("İŞLEÇ", ")"):
            parametreler.append(self.bekle("AD").değer)
            while self.al("İŞLEÇ", ","):
                parametreler.append(self.bekle("AD").değer)
        self.bekle("İŞLEÇ", ")")
        if len(set(parametreler)) != len(parametreler):
            raise NehirHatası(f"'{ad}' işlevinde aynı parametre adı iki kez kullanılmış", satır)
        self.işlevler[ad] = (parametreler, None, satır)   # özyineleme için önce kaydet
        self.işlevler[ad] = (parametreler, self.blok(), satır)

    def blok(self):
        açılış = self.bekle("İŞLEÇ", "{")
        deyimler = []
        while not self.bak("İŞLEÇ", "}"):
            if self.bak("ANAHTAR", "işlev"):
                raise NehirHatası("işlevler yalnızca en üst düzeyde tanımlanabilir", self.şimdiki.satır)
            if self.bak("SON"):
                raise NehirHatası("bu blok kapatılmamış", açılış.satır,
                                  "eşleşen '}' eksik")
            deyimler.append(self.deyim())
        self.bekle("İŞLEÇ", "}")
        return deyimler

    def deyim(self):
        satır = self.şimdiki.satır
        if self.al("ANAHTAR", "dur"):
            return ("dur", satır)
        if self.al("ANAHTAR", "devam"):
            return ("devam", satır)
        return ("akış", self.ifade(), self.zincir(), satır)

    def zincir(self):
        """Sıfır ya da daha çok '-> hedef'."""
        hedefler = []
        while self.al("İŞLEÇ", "->"):
            hedefler.append(self.hedef())
            if hedefler[-1][0] in SONLANDIRAN:
                break
        return hedefler

    def hedef(self):
        s = self.şimdiki
        if self.al("ANAHTAR", "yazdır"):
            return ("yazdır", s.satır)
        if self.al("ANAHTAR", "döndür"):
            return ("döndür", s.satır)
        if self.al("ANAHTAR", "ortak"):
            ad = self.bekle("AD")
            return ("ortak", ad.değer, ad.satır)
        if self.al("ANAHTAR", "eğer"):
            blok = self.blok()
            değilse = self.blok() if self.al("ANAHTAR", "değilse") else None
            return ("eğer", blok, değilse, s.satır)
        if self.al("ANAHTAR", "iken"):
            return ("iken", self.blok(), s.satır)
        if self.al("ANAHTAR", "her"):
            self.bekle("İŞLEÇ", "(")
            değişken = self.bekle("AD").değer
            self.bekle("İŞLEÇ", ")")
            return ("her", değişken, self.blok(), s.satır)
        if self.al("İŞLEÇ", "("):
            dallar = [self.dal()]
            while self.al("İŞLEÇ", "|"):
                dallar.append(self.dal())
            self.bekle("İŞLEÇ", ")")
            return ("çatal", dallar, s.satır)
        if self.al("AD"):
            if self.aynı_satırda("("):
                return ("ad", s.değer, self.argümanlar(), s.satır)
            if not (self.aynı_satırda("[") or self.bak("İŞLEÇ", ".")):
                return ("ad", s.değer, None, s.satır)
            # a[i].x[j] gibi bir hedefte son erişim yazılacak yerdir; öncekiler okunur.
            kap = ("değişken", s.değer, s.satır)
            while True:
                if self.al("İŞLEÇ", "."):
                    alan = self.bekle("AD")
                    if self.aynı_satırda("("):
                        # değer -> nesne.yöntem(...): akan değer, nesneden sonraki ilk argümandır
                        return ("yöntem_hedef", kap, alan.değer, self.argümanlar(), alan.satır)
                    son = ("alan", kap, alan.değer, alan.satır)
                else:
                    köşe = self.bekle("İŞLEÇ", "[")
                    dizin = self.ifade()
                    self.bekle("İŞLEÇ", "]")
                    son = ("dizin", kap, dizin, köşe.satır)
                if not (self.aynı_satırda("[") or self.bak("İŞLEÇ", ".")):
                    break
                kap = son
            if son[0] == "alan":
                return ("alan_yaz", son[1], son[2], son[3])
            return ("eleman", son[1], son[2], s.satır)
        raise NehirHatası(f"'->' sonrasında bir hedef bekleniyordu, {self.bulunan()} bulundu", s.satır,
                          "hedef olabilenler: değişken, işlev, yazdır, döndür, eğer, iken, her, ( çatal )")

    def dal(self):
        """Çatalın bir kolu:  hedef (-> hedef)*"""
        hedefler = [self.hedef()]
        if hedefler[0][0] not in SONLANDIRAN:
            hedefler += self.zincir()
        for h in hedefler:
            if h[0] in ("iken", "her"):
                raise NehirHatası(f"çatalın kolunda '{h[0]}' kullanılamaz", h[-1])
        return hedefler

    def argümanlar(self):
        self.bekle("İŞLEÇ", "(")
        liste = self.ifade_listesi(")")
        self.bekle("İŞLEÇ", ")")
        return liste

    def ifade_listesi(self, kapanış):
        liste = []
        if not self.bak("İŞLEÇ", kapanış):
            liste.append(self.ifade())
            while self.al("İŞLEÇ", ","):
                liste.append(self.ifade())
        return liste

    # İfadeler — öncelik düşükten yükseğe: veya, ve, değil, karşılaştırma, + -, * / %, tekli
    def ifade(self):
        sol = self.ve_ifadesi()
        while (s := self.al("ANAHTAR", "veya")):
            sol = ("ikili", "veya", sol, self.ve_ifadesi(), s.satır)
        return sol

    def ve_ifadesi(self):
        sol = self.değil_ifadesi()
        while (s := self.al("ANAHTAR", "ve")):
            sol = ("ikili", "ve", sol, self.değil_ifadesi(), s.satır)
        return sol

    def değil_ifadesi(self):
        if (s := self.al("ANAHTAR", "değil")):
            return ("tekli", "değil", self.değil_ifadesi(), s.satır)
        return self.karşılaştırma()

    def ikili_düzey(self, alt, işleçler):
        sol = alt()
        while self.şimdiki.tür == "İŞLEÇ" and self.şimdiki.değer in işleçler:
            if self.şimdiki.değer == "-" and self.şimdiki.yeni_satır:
                break   # satır başındaki '-' yeni bir deyimin eksi işaretidir
            s = self.al("İŞLEÇ")
            sol = ("ikili", s.değer, sol, alt(), s.satır)
        return sol

    def karşılaştırma(self):
        return self.ikili_düzey(self.toplama, ("==", "!=", "<", ">", "<=", ">="))

    def toplama(self):
        return self.ikili_düzey(self.çarpma, ("+", "-"))

    def çarpma(self):
        return self.ikili_düzey(self.tekli, ("*", "/", "%"))

    def tekli(self):
        if (s := self.al("İŞLEÇ", "-")):
            return ("tekli", "-", self.tekli(), s.satır)
        return self.ardıl()

    def ardıl(self):
        e = self.birincil()
        while True:
            if self.aynı_satırda("["):
                s = self.al("İŞLEÇ")
                dizin = self.ifade()
                self.bekle("İŞLEÇ", "]")
                e = ("dizin", e, dizin, s.satır)
            elif self.al("İŞLEÇ", "."):
                alan = self.bekle("AD")
                if self.aynı_satırda("("):
                    e = ("yöntem", e, alan.değer, self.argümanlar(), alan.satır)
                else:
                    e = ("alan", e, alan.değer, alan.satır)
            else:
                return e

    def birincil(self):
        s = self.şimdiki
        if self.al("SAYI"):
            return ("sayı", s.değer, s.satır)
        if self.al("ONDALIK"):
            return ("ondalık", s.değer, s.satır)
        if self.al("METİN"):
            return ("metin", s.değer, s.satır)
        if self.al("ANAHTAR", "doğru"):
            return ("sayı", 1, s.satır)
        if self.al("ANAHTAR", "yanlış"):
            return ("sayı", 0, s.satır)
        if self.al("ANAHTAR", "yok"):
            return ("yok", s.satır)
        if self.al("AD"):
            if self.aynı_satırda("("):
                return ("çağrı", s.değer, self.argümanlar(), s.satır)
            return ("değişken", s.değer, s.satır)
        if self.al("İŞLEÇ", "("):
            iç = self.ifade()
            self.bekle("İŞLEÇ", ")")
            return iç
        if self.al("İŞLEÇ", "["):
            elemanlar = self.ifade_listesi("]")
            self.bekle("İŞLEÇ", "]")
            return ("liste", elemanlar, s.satır)
        if self.al("İŞLEÇ", "{"):
            çiftler = []
            while not self.bak("İŞLEÇ", "}"):
                anahtar = self.ifade()
                self.bekle("İŞLEÇ", ":")
                çiftler.append((anahtar, self.ifade()))
                if not self.al("İŞLEÇ", ","):
                    break
            self.bekle("İŞLEÇ", "}")
            return ("sözlük", çiftler, s.satır)
        ipucu = None
        if s.tür == "ANAHTAR" and s.değer in ("yazdır", "döndür", "eğer", "iken", "her"):
            ipucu = (f"'{s.yazım}' bir hedeftir; değer ona soldan akar:  "
                     + ("liste" if s.değer == "her" else "koşul" if s.değer in ("eğer", "iken") else "değer")
                     + f" -> {s.yazım}" + (" (x) { ... }" if s.değer == "her" else
                                           " { ... }" if s.değer in ("eğer", "iken") else ""))
        elif s.tür == "ANAHTAR" and s.değer == "ortak":
            ipucu = f"'{s.yazım}' bir hedefin başına yazılır:  değer -> {s.yazım} ad"
        elif s.tür == "ANAHTAR" and s.değer in ("kullan", "işlev", "kayıt"):
            ipucu = f"'{s.yazım}' yalnızca dosyanın en üst düzeyinde kullanılabilir"
        elif s.tür == "ANAHTAR" and s.değer == "değilse":
            ipucu = f"'{s.yazım}' yalnızca bir 'eğer' bloğunun hemen ardından gelebilir"
        raise NehirHatası(f"bir ifade bekleniyordu, {self.bulunan()} bulundu", s.satır, ipucu)


# ───────────────────────────── Kod üretici ─────────────────────────────
# Basit bir strateji: her ifadenin sonucu rax'te kalır. İkili işlemlerde sol
# taraf yığına itilir, sağ taraf hesaplanır, sonra ikisi birleştirilir.
#
# Değerler 64 bitliktir:
#   sayı   tam sayının kendisi
#   metin  baytların adresi (uzunluk 8 bayt öncesinde durur; baytların ardında her
#          zaman bir sıfır baytı vardır, böylece metin dosya yolu olarak çekirdeğe verilebilir)
#   liste  {uzunluk, kapasite, veri adresi} başlığının adresi; elemanlar da 64 bitlik
#          değerlerdir (sayı, metin ya da başka listeler)
#   sözlük {sayı, kapasite, anahtarlar, değerler, tablo boyu, tablo} başlığının adresi.
#          Anahtarlar ve değerler eklenme sırasıyla iki dizide durur; tablo, anahtarın
#          hash'inden dizideki yerine (dizin + 1, boşsa 0) götüren açık adresli bir dizindir.
#
#   kayıt  alanların art arda durduğu belleğin adresi; `yok` 0 adresidir
#   işlev  işlevin kodunun adresi
#
# Yazdırma ve eşitlik gibi türe bağlı işlemler için derleyici her türün bir
# tanımını üretir: {tür kodu, 1. parametre tanımı, 2. parametre tanımı};
# tür kodu 0 sayı, 1 metin, 2 liste, 3 sözlük, 5 işlev. Kayıt tanımı farklıdır:
# {4, ad, alan sayısı, (alan adı, alan türü tanımı)...}.
# Türler derleme anında izlenir. İşlevlerin parametre türleri ilk çağrıdan
# çıkarılır; bu yüzden işlevler ilk çağrıldıkları anda derlenir.

class TürDeğişkeni:
    """Henüz bilinmeyen bir tür (`[]` listesinin eleman türü gibi). Öğrenildiğinde
    `bağ` ile gerçek türe bağlanır; aynı değişkeni paylaşan her yer birlikte güncellenir."""

    def __init__(self, yalnız_kayıt=False):
        self.bağ = None
        self.yalnız_kayıt = yalnız_kayıt    # `yok` değerinin türü: yalnızca bir kayıt türü olabilir

    def __str__(self):
        return "yok" if self.yalnız_kayıt else "henüz bilinmeyen tür"


def çöz(tür):
    while isinstance(tür, TürDeğişkeni) and tür.bağ is not None:
        tür = tür.bağ
    return tür


def bilinen(tür):
    """Çözülmüş tür; hâlâ bilinmiyorsa None."""
    tür = çöz(tür)
    return None if isinstance(tür, TürDeğişkeni) else tür


class Liste:
    def __init__(self, eleman=None):
        self._eleman = TürDeğişkeni() if eleman is None else eleman

    @property
    def eleman(self):
        return bilinen(self._eleman)

    def parametreler(self):
        return [self._eleman]

    def __str__(self):
        return "boş liste" if self.eleman is None else f"{self.eleman} listesi"


class Sözlük:
    def __init__(self, anahtar=None, değer=None):
        self._anahtar = TürDeğişkeni() if anahtar is None else anahtar
        self._değer = TürDeğişkeni() if değer is None else değer

    @property
    def anahtar(self):
        return bilinen(self._anahtar)

    @property
    def değer(self):
        return bilinen(self._değer)

    def parametreler(self):
        return [self._anahtar, self._değer]

    def __str__(self):
        if self.anahtar is None or self.değer is None:
            return "boş sözlük"
        return f"{self.anahtar} → {self.değer} sözlüğü"


class Kayıt:
    """Adıyla ayırt edilen kayıt türü; her tanım için tek bir nesne vardır."""

    def __init__(self, ad, alanlar):
        self.ad = ad
        self.alanlar = alanlar                              # alan adları
        self.türler = [TürDeğişkeni() for _ in alanlar]     # tanımdan ya da kullanımdan öğrenilir

    def parametreler(self):
        return []       # kayıtlar kendilerine gönderme yapabilir; içlerine inilmez

    def __str__(self):
        return self.ad


class İşlevTürü:
    """Değer olarak kullanılan işlevin türü: parametre türleri ve dönüş türü."""

    def __init__(self, parametreler, dönüş):
        self._parametreler, self._dönüş = list(parametreler), dönüş

    def parametreler(self):
        return self._parametreler + [self._dönüş]

    def __str__(self):
        def ad(t):
            t = çöz(t)
            return "?" if isinstance(t, TürDeğişkeni) and not t.yalnız_kayıt else str(t)
        return f"işlev({', '.join(map(ad, self._parametreler))}) -> {ad(self._dönüş)}"


def kayıtsı(tür):
    """Bir kayıt ya da `yok` mu?"""
    return isinstance(tür, Kayıt) or (isinstance(tür, TürDeğişkeni) and tür.yalnız_kayıt)


def içerir(tür, hedef):
    tür = çöz(tür)
    if tür is hedef:
        return True
    return isinstance(tür, (Liste, Sözlük, İşlevTürü)) and any(içerir(p, hedef) for p in tür.parametreler())


def sözlük_içerir(tür):
    tür = çöz(tür)
    return isinstance(tür, Sözlük) or (isinstance(tür, Liste) and sözlük_içerir(tür._eleman))


def birleştir(a, b):
    """İki türü eşitlemeye çalışır; bilinmeyen türleri doldurur."""
    a, b = çöz(a), çöz(b)
    if a is b:
        return True
    if isinstance(b, TürDeğişkeni):
        a, b = b, a
    if isinstance(a, TürDeğişkeni):
        if isinstance(b, TürDeğişkeni) and b.yalnız_kayıt:
            a, b = b, a
        if a.yalnız_kayıt:
            if isinstance(b, TürDeğişkeni):
                b.yalnız_kayıt = True
            elif not isinstance(b, Kayıt):
                return False
        if içerir(b, a):        # bir liste kendi elemanı olamaz
            return False
        a.bağ = b
        return True
    if type(a) is not type(b) or isinstance(a, Kayıt):     # farklı iki kayıt türü
        return False
    if isinstance(a, str):
        return a == b
    if len(a.parametreler()) != len(b.parametreler()):     # farklı sayıda parametreli işlevler
        return False
    return all(birleştir(x, y) for x, y in zip(a.parametreler(), b.parametreler()))


class İşlevBaşlığı:
    """İşlevin etiket satırı. Açıklamadaki türler derlemenin sonunda kesinleşir."""

    def __init__(self, ad, bilgi):
        self.ad, self.bilgi = ad, bilgi

    def __str__(self):
        b = self.bilgi
        return f"{b['etiket']}:    # işlev {self.ad}({', '.join(map(str, map(çöz, b['türler'])))}) -> {çöz(b['dönüş'])}"


class TürKoduSatırı:
    """Bir yazmaca, değerin çalışma zamanı tür tanımının adresini yükler. Tür
    (örneğin boş listenin eleman türü) sonradan belli olabileceği için satır
    ancak derlemenin sonunda metne çevrilir."""

    def __init__(self, tür, yazmaç="rsi"):
        self.tür, self.yazmaç = tür, yazmaç


KARŞILAŞTIRMA = {"==": "sete", "!=": "setne", "<": "setl", ">": "setg", "<=": "setle", ">=": "setge"}

BOŞ_LİSTE_HATASI = ("bu listenin eleman türü henüz belli değil; "
                    "önce içine bir eleman akmalı")
BOŞ_SÖZLÜK_HATASI = ("bu sözlüğün anahtar ve değer türleri henüz belli değil; "
                     "önce içine bir değer akmalı:  değer -> sözlük[anahtar]")

# Programı bitiren yerleşik işlevin bütün yazımları.
ÇIKIŞ_ADLARI = {ad for ad, asıl in YERLEŞİKLER.items() if asıl == "çık"}

# Hata verebilen çalışma zamanı işlemleri; öncesinde r15'e kaynak dosyası ve satırı yüklenir.
RİSKLİ = {"jz __sifira_bolme", "jz __yok_hatasi", "call __ayir"} | {"call " + ad for ad in (
    "__liste_al", "__liste_koy", "__metin_al", "__metinden_sayi", "__liste_yeni",
    "__liste_ekle", "__aralik", "__metin_birlestir", "__sayidan_metin", "__oku",
    "__metin_dilim", "__liste_dilim", "__liste_birlestir", "__liste_sil",
    "__metin_bol", "__liste_birles", "__metin_baytlar", "__karakter", "__sozluk_yeni", "__sozluk_koy", "__sozluk_al",
    "__sozluk_sil", "__sozluk_liste", "__dosya_oku", "__dosya_yaz", "__dosya_sil",
    "__argumanlar", "__metin_karakter", "__rastgele", "__tus", "__ucbirim_boyutu",
    "__ondalik_metin", "__metinden_ondalik", "__us_sayi", "__liste_en", "__ekran_ac",
    "__ekran_temizle", "__ekran_yaz", "__ekran_doldur", "__ekran_ciz", "__liste_sirala",
    "__liste_ters", "__sayi_bol", "__sayi_kalan", "__ondalik_tama", "__ondalik_yuvarla")}

# ── gözetleme deliği eniyilemesi ──
# Üretilen kod her ara değeri yığına iter. Ardışık birkaç satırlık kalıplar daha kısa ve eşdeğer
# satırlarla değiştirilir. Kendi/kod_uretici.nehir'deki gözetle ile birebir aynı olmalıdır.

def ölü_mü(satırlar, j, yazmaçlar):
    """j'den sonra, bir çağrıdan önce bu yazmaçlar (adlarının geçtiği bir satır) okunmuyor mu?
    Etiket, sıçrama ya da dönüşte bilinemez sayılır."""
    while j < len(satırlar):
        l = satırlar[j]
        if l.startswith("    call "):
            return all(y not in l for y in yazmaçlar)
        if not l.startswith("    ") or l.startswith("    j") or l == "    ret" \
                or any(y in l for y in yazmaçlar):
            return False
        j += 1
    return False


RAX_ADLARI = ["rax", "eax", "al", "ah"]
RAX_RCX_ADLARI = RAX_ADLARI + ["rcx", "ecx", "cl", "ch"]


def gözetle(satırlar):
    değişti = True
    while değişti:
        değişti = False
        yeni, i, n = [], 0, len(satırlar)
        while i < n:
            a = satırlar[i]
            if a == "    push rax" and i + 3 < n and satırlar[i + 2] == "    mov rcx, rax" \
                    and satırlar[i + 3] in ("    pop rax", "    pop rsi") \
                    and (satırlar[i + 1].startswith("    mov rax, ") or satırlar[i + 1].startswith("    lea rax, ")):
                # push rax / mov rax, X / mov rcx, rax / pop rax  ->  mov rcx, X
                x = satırlar[i + 1][13:]
                if "rax" not in x and "rsp" not in x and "rcx" not in x \
                        and (satırlar[i + 3] == "    pop rax" or ölü_mü(satırlar, i + 4, RAX_ADLARI)):
                    if satırlar[i + 3] == "    pop rsi":
                        yeni.append("    mov rsi, rax")
                    yeni.append(satırlar[i + 1][:8] + "rcx, " + x)
                    i += 4
                    değişti = True
                    continue
            if a == "    mov rcx, rax" and satırlar[i + 1:i + 4] == ["    pop rax", "    mov rdi, rax", "    mov rsi, rcx"] \
                    and ölü_mü(satırlar, i + 4, RAX_RCX_ADLARI):
                # mov rcx, rax / pop rax / mov rdi, rax / mov rsi, rcx  ->  mov rsi, rax / pop rdi
                yeni += ["    mov rsi, rax", "    pop rdi"]
                i += 4
                değişti = True
                continue
            if a == "    push rax" and i + 1 < n and satırlar[i + 1].startswith("    pop "):
                # push rax / pop r  ->  mov r, rax
                if satırlar[i + 1] != "    pop rax":
                    yeni.append("    mov " + satırlar[i + 1][8:] + ", rax")
                i += 2
                değişti = True
                continue
            yeni.append(a)
            i += 1
        satırlar = yeni
    return satırlar


# Yan etkisi olmayan yerleşikler: sonuçları atılıyorsa büyük olasılıkla bir yanlışlık vardır.
SAF_YERLEŞİKLER = {
    "uzunluk", "aralık", "metne", "sayıya", "dilim", "bul", "böl", "birleş", "var", "anahtarlar",
    "değerler", "baytlar", "karakter", "işletim_sistemi", "uçbirim_mi", "ortam_var", "dosya_hatası",
    "dosya_var", "girdi_var", "zaman", "uçbirim_boyutu", "ondalığa", "yuvarla", "taban", "tavan",
    "karekök", "mutlak", "sin", "cos", "atan2", "pi", "bit_ve", "bit_veya", "bit_yada", "bit_değil",
    "sola_kaydır", "sağa_kaydır", "en_küçük", "en_büyük", "sınırla", "işaret", "üs", "tan", "atan",
    "asin", "acos", "üstel", "ln", "rgb", "sırala", "ters_çevir", "argümanlar"}

# Ekran işlevleri: kabul ettikleri argüman türleri, açıklaması ve çalışma zamanı yordamı.
# Argümanlar yığında kalır; yordam onları rdi'nin gösterdiği yerden okur. Eksik renkler -1'dir.
EKRAN_İŞLEVLERİ = {
    "ekran_aç": ([["sayı", "sayı"]], "genişlik, yükseklik", "__ekran_ac"),
    "ekran_kapat": ([[]], "argümansız", "__ekran_kapat"),
    "ekran_temizle": ([[], ["sayı"]], "arka plan rengi", "__ekran_temizle"),
    "ekran_yaz": ([["sayı", "sayı", "metin"], ["sayı", "sayı", "metin", "sayı", "sayı"]],
                  "x, y, metin, yazı rengi, arka plan rengi", "__ekran_yaz"),
    "ekran_doldur": ([["sayı"] * 4 + ["metin"], ["sayı"] * 4 + ["metin", "sayı", "sayı"]],
                     "x, y, genişlik, yükseklik, karakter, yazı rengi, arka plan rengi", "__ekran_doldur"),
    "ekran_çiz": ([[]], "argümansız", "__ekran_ciz"),
}

YIĞIN_BOYUTU = 256 * 1024 * 1024    # bss'te ayrılır; dokunulmadıkça bellek harcamaz

# Çalışma zamanı: üretilen her programın sonuna eklenen assembly. İşletim sistemine özgü
# katman (calisma_zamani_<hedef>.s) ile ortak kısımdan (calisma_zamani.s) oluşur. Ayrı
# dosyalardadır, çünkü Nehir ile yazılmış derleyici (kendi/) de aynı dosyaları kullanır.
HEDEFLER = ("linux", "windows")
VARSAYILAN_HEDEF = "windows" if sys.platform == "win32" else "linux"


def çalışma_zamanı(hedef):
    dizin = os.path.dirname(os.path.abspath(__file__))
    metin = ""
    for ad in (f"calisma_zamani_{hedef}.s", "calisma_zamani.s"):
        with open(os.path.join(dizin, ad), encoding="utf-8") as f:
            metin += f.read()
    return metin.replace("YIGIN_BOYUTU", str(YIĞIN_BOYUTU))


class KodÜretici:
    def __init__(self, deyimler, işlevler, dosya_adları=("<girdi>",), kayıtlar=None, hedef=VARSAYILAN_HEDEF):
        self.dosya_adları = dosya_adları
        self.hedef_sistem = hedef
        # Önce bütün kayıt türleri oluşturulur, sonra alan türleri çözülür;
        # böylece kayıtlar kendilerine ve birbirlerine gönderme yapabilir.
        self.kayıtlar = {ad: Kayıt(ad, [a[0] for a in alanlar])
                         for ad, (alanlar, _) in (kayıtlar or {}).items()}
        self.kayıt_etiketleri = {}
        for ad, (alanlar, _) in (kayıtlar or {}).items():
            for değişken, (_, tür, _) in zip(self.kayıtlar[ad].türler, alanlar):
                if tür is not None:
                    değişken.bağ = self.tür_çöz(tür)
        self.konum = 0            # o anda derlenen düğümün satırı
        self.deyimler = deyimler
        self.işlevler = işlevler
        # Her işlev için: etiket, parametre türleri (ilk çağrıda belirlenir) ve dönüş türü.
        self.bilgi = {ad: {"etiket": f"f{i}", "türler": None, "dönüş": None,
                           "başladı": False, "bitti": False, "sona_ulaşır": False}
                      for i, ad in enumerate(işlevler)}
        # Hiç dönmeyen işlevler: gövdesi hiçbir yoldan sona ulaşmayan ve hiç 'döndür'
        # içermeyen işlevler (her yolu programı bitirir). Birbirlerini çağırabildikleri
        # için küme, değişmeyene dek yeniden hesaplanır.
        self.dönmeyenler = set()
        değişti = True
        while değişti:
            değişti = False
            for ad, (_, gövde, _) in işlevler.items():
                if ad not in self.dönmeyenler and not self.içerir_mi(gövde, "döndür") \
                        and not self.tamamlanır(gövde):
                    self.dönmeyenler.add(ad)
                    değişti = True
        # Değişken kayıtları: [yer, tür|None, ilk atamanın konumu, okundu mu]
        self.küreseller = {}      # ad -> kayıt (yer = etiket)
        self.değer_işlevler = []  # değer olarak kullanılan, henüz derlenmemiş işlevler
        self.ortaklar = set()     # işlevlerin de atayabildiği (`ortak` ile tanımlanmış) küreseller
        self.okunan_küreseller = {}   # derlenen işlevde okunan küreseller: ad -> ilk okunduğu yer
        self.metinler = []        # bayt dizileri
        self.ondalıklar = []      # ondalık sayıların yazımları (assembler ikiliye çevirir)
        self.tür_etiketleri = {}  # yapısal tür anahtarı -> tanımın etiketi
        self.tür_tanımları = []   # rodata satırları
        self.etiket_no = 0
        self.çıktı = []
        self.işlev_kodu = []      # derlenmiş işlevlerin satırları
        self.uyarılar = []
        # geçerli işlev bağlamı (en üst düzeyde geçerli None'dır)
        self.geçerli = None
        self.yereller = None      # ad -> kayıt (yer = rbp'ye göre konum)
        self.yerel_sayısı = 0
        self.döngüler = []        # iç içe döngüler: (devam etiketi, son etiketi, çatal derinliği)
        self.çatal_derinliği = 0  # o anda yığında bekleyen çatal değerlerinin sayısı

    # ── akış çözümlemesi ──
    # Sözdizimine bakarak denetimin nereye ulaşabileceğini bulur. Temkinlidir:
    # emin olamadığı her yerde "ulaşabilir" der.

    @staticmethod
    def alt_bloklar(hedefler):
        """Hedeflerin içindeki bloklar: (blok, döngü gövdesi mi?)"""
        for h in hedefler:
            if h[0] == "eğer":
                yield h[1], False
                if h[2] is not None:
                    yield h[2], False
            elif h[0] == "iken":
                yield h[1], True
            elif h[0] == "her":
                yield h[2], True
            elif h[0] == "çatal":
                for dal in h[1]:
                    yield from KodÜretici.alt_bloklar(dal)

    def içerir_mi(self, deyimler, aranan, döngülere_gir=True):
        """Blokta (iç içe bloklar dahil) 'döndür' hedefi ya da 'dur' deyimi var mı?
        'dur' aranırken iç döngülere girilmez: oradaki 'dur' o döngüye aittir."""
        for d in deyimler:
            if d[0] == aranan:
                return True
            if d[0] != "akış":
                continue

            def hedefte(hedefler):
                return any(h[0] == aranan or (h[0] == "çatal" and any(hedefte(dal) for dal in h[1]))
                           for h in hedefler)
            if hedefte(d[2]):
                return True
            if any(self.içerir_mi(blok, aranan, döngülere_gir)
                   for blok, döngü in self.alt_bloklar(d[2]) if döngülere_gir or not döngü):
                return True
        return False

    def dönmez(self, ad):
        """Bu adın çağrısı hiç geri dönmez mi?"""
        if ad in self.işlevler:
            return ad in self.dönmeyenler
        return ad in ÇIKIŞ_ADLARI and ad not in self.kayıtlar

    def tamamlanır(self, deyimler):
        """Denetim bu bloğun sonuna ulaşabilir mi?"""
        return all(self.deyim_tamamlanır(d) for d in deyimler)

    def deyim_tamamlanır(self, d):
        if d[0] != "akış":
            return False            # dur, devam
        _, kaynak, hedefler, _ = d
        if kaynak[0] == "çağrı" and self.dönmez(kaynak[1]):
            return False
        return self.hedefler_tamamlanır(hedefler, kaynak)

    def hedefler_tamamlanır(self, hedefler, kaynak=None):
        for h in hedefler:
            if h[0] == "döndür":
                return False
            if h[0] == "ad" and self.dönmez(h[1]):
                return False
            if h[0] == "eğer" and h[2] is not None \
                    and not self.tamamlanır(h[1]) and not self.tamamlanır(h[2]):
                return False
            if h[0] == "iken":
                # `doğru -> iken { }` yalnızca içindeki bir 'dur' ile biter.
                sonsuz = kaynak is not None and kaynak[0] == "sayı" and kaynak[1] != 0 \
                    and len(hedefler) == 1
                if sonsuz and not self.içerir_mi(h[1], "dur", döngülere_gir=False):
                    return False
            if h[0] == "çatal" and not all(self.hedefler_tamamlanır(dal) for dal in h[1]):
                return False
        return True

    def tür_çöz(self, t):
        """Kayıt tanımındaki tür ifadesini türe çevirir."""
        if t[0] == "liste":
            return Liste(self.tür_çöz(t[1]))
        if t[0] == "sözlük":
            anahtar = self.tür_çöz(t[1])
            if anahtar not in ("sayı", "metin"):
                raise NehirHatası(f"sözlük anahtarı sayı ya da metin olmalı, {anahtar} bulundu", t[1][-1])
            return Sözlük(anahtar, self.tür_çöz(t[2]))
        ad = t[1]
        if ad in ("sayı", "sayi", "number"):
            return "sayı"
        if ad in ("metin", "text"):
            return "metin"
        if ad in ("ondalık", "ondalik", "float"):
            return "ondalık"
        if ad in self.kayıtlar:
            return self.kayıtlar[ad]
        raise NehirHatası(f"'{ad}' adında bir tür yok", t[-1],
                          benzerler(ad, ["sayı", "metin", "ondalık"] + list(self.kayıtlar)))

    def metin_etiketi(self, metin):
        veri = metin.encode("utf-8")
        if veri not in self.metinler:
            self.metinler.append(veri)
        return f"m{self.metinler.index(veri)}"

    def alan_bul(self, tür, alan, satır):
        """(alanın sırası, alanın türü)"""
        if isinstance(tür, TürDeğişkeni):
            raise NehirHatası(f"'.{alan}' alanına erişilen değerin türü henüz belli değil", satır,
                              "kayıt tanımında alanın türünü yazmak bunu çözer:  kayıt Ad { alan: Tür }")
        if not isinstance(tür, Kayıt):
            raise NehirHatası(f"'.{alan}': alanlara yalnızca kayıtlarda erişilir, {tür} bulundu", satır)
        if alan not in tür.alanlar:
            raise NehirHatası(f"'{tür.ad}' kaydında '{alan}' adında bir alan yok", satır,
                              benzerler(alan, tür.alanlar) or f"alanları: {', '.join(tür.alanlar)}")
        sıra = tür.alanlar.index(alan)
        return sıra, tür.türler[sıra]

    def yaz(self, satır):
        if satır in RİSKLİ:
            self.çıktı.append(f"    mov r15, {getattr(self.konum, 'dosya', 0) << 32 | int(self.konum)}")
        self.çıktı.append("    " + satır)

    def etiket_koy(self, etiket):
        self.çıktı.append(etiket + ":")

    def yeni_etiket(self):
        self.etiket_no += 1
        return f".L{self.etiket_no}"

    # ── genel akış ──
    def üret(self):
        self.küreselleri_topla(self.deyimler)

        self.çıktı.append("nehir_ana:")
        self.yaz("push rbp")
        self.yaz("mov rbp, rsp")
        for d in self.deyimler:
            self.deyim(d)
        self.yaz("leave")
        self.yaz("ret")

        # Değer olarak kullanılıp hiç doğrudan çağrılmamış işlevler en son derlenir;
        # parametre türleri o zamana dek işlev değişkenleri üzerinden yapılan
        # çağrılardan öğrenilmiş olur. Derlenen işlevler yenilerini ekleyebilir.
        while self.değer_işlevler:
            ad = self.değer_işlevler.pop(0)
            if not self.bilgi[ad]["başladı"]:
                try:
                    self.işlevi_derle(ad)
                except NehirHatası as hata:
                    if hata.ilgili is None:     # türler, değer olarak verildiği yerden gelir
                        hata.ilgili = self.bilgi[ad]["değer_yeri"]
                        hata.ilgili_not = (f"'{ad}' burada değer olarak verildi; parametre türleri "
                                           f"onu tutan değişken üzerinden yapılan çağrılardan çıkarıldı")
                    raise

        self.dönüşleri_denetle()
        self.okunmayanları_bildir(self.küreseller)
        for ad, b in self.bilgi.items():
            # Modüller kitaplıktır; her işlevlerinin kullanılması beklenmez.
            if b["türler"] is None and getattr(self.işlevler[ad][2], "dosya", 0) == 0:
                self.uyarılar.append((self.işlevler[ad][2],
                                      f"'{ad}' işlevi hiç çağrılmıyor; derlenmedi", None))
        self.uyarılar.sort(key=lambda u: (getattr(u[0], "dosya", 0), int(u[0])))

        # Tür tanımları yeni metinler (kayıt ve alan adları) ekleyebildiği için
        # kod, metinler dökülmeden önce son hâline getirilir.
        kod = [f"    lea {x.yazmaç}, [rip+{self.tür_etiketi(x.tür)}]"
               if isinstance(x, TürKoduSatırı) else str(x) for x in self.çıktı + self.işlev_kodu]
        kod = gözetle(kod)

        baş = [".intel_syntax noprefix", ".global _start", ".section .text"]
        son = [çalışma_zamanı(self.hedef_sistem), "    .section .rodata", "    .balign 8",
               "__dosyalar: .quad " + ", ".join(self.metin_etiketi(ad) for ad in self.dosya_adları)]
        if self.metinler:
            son.append("    .section .rodata")
            for i, veri in enumerate(self.metinler):
                son.append("    .balign 8")
                son.append(f"    .quad {len(veri)}")
                son.append(f"m{i}:")
                son.append("    .byte " + ", ".join(str(b) for b in veri + b"\0"))
        # Küresel değişkenler çalışma zamanının .bss'inden hemen sonra gelir; çöp toplayıcı
        # __kokler_bas ile __kokler_son arasını kök sayar.
        son.append("    .section .bss")
        for ad, kayıt in self.küreseller.items():
            son.append(f"{kayıt[0]}: .skip 8    # {ad}")
        son.append("__kokler_son:")
        if self.tür_tanımları:
            son += ["    .section .rodata", "    .balign 8"] + self.tür_tanımları
        if self.ondalıklar:
            son += ["    .section .rodata", "    .balign 8"]
            son += [f"d{i}: .double {yazım}" for i, yazım in enumerate(self.ondalıklar)]
        return "\n".join(baş + kod + son) + "\n"

    def dönüşleri_denetle(self):
        """Bütün program derlendikten sonra dönüş türleri kesinleşir. Sonuna değer
        döndürmeden ulaşılabilen bir işlev 0 döndürür: bu, sayı için 0, kayıt için
        `yok` demektir; başka türlerde geçerli bir değer değildir."""
        for ad, b in self.bilgi.items():
            if not b["bitti"]:
                continue
            dönüş = çöz(b["dönüş"])
            if isinstance(dönüş, TürDeğişkeni) and not dönüş.yalnız_kayıt:
                dönüş.bağ = dönüş = "sayı"      # yalnızca kendi sonucunu döndüren özyineleme
            if b["sona_ulaşır"] and dönüş != "sayı" and not kayıtsı(dönüş):
                raise NehirHatası(
                    f"'{ad}' işlevi {dönüş} döndürüyor ama sonuna değer döndürmeden ulaşılabiliyor",
                    self.işlevler[ad][2],
                    "her yol bir değer döndürmeli ya da programı bitirmeli; yalnızca sayı ve kayıt "
                    "döndüren işlevler sona ulaşabilir (0 ya da yok döner)")

    def tür_etiketi(self, tür):
        """Türün çalışma zamanı tanımını (gerekirse üreterek) verir. Derlemenin
        sonunda hâlâ bilinmeyen bir tür yalnızca boş kaplarda olabilir; sayı sayılır."""
        tür = çöz(tür)
        if isinstance(tür, Kayıt) or kayıtsı(tür):
            # Türü hiç belli olmamış bir `yok` her zaman 0'dır; alansız bir tanım yeter.
            anahtar = tür if isinstance(tür, Kayıt) else None
            if anahtar not in self.kayıt_etiketleri:
                etiket = self.kayıt_etiketleri[anahtar] = f"kt{len(self.kayıt_etiketleri)}"   # "k0" bir yazmaç adıdır
                alanlar = [] if anahtar is None else list(zip(tür.alanlar, tür.türler))
                parçalar = ["4", self.metin_etiketi(tür.ad if anahtar else "yok"), str(len(alanlar))]
                for ad, alan_türü in alanlar:
                    parçalar += [self.metin_etiketi(ad), self.tür_etiketi(alan_türü)]
                self.tür_tanımları.append(f"{etiket}: .quad {', '.join(parçalar)}")
            return self.kayıt_etiketleri[anahtar]
        tür = bilinen(tür)
        if isinstance(tür, İşlevTürü):
            anahtar = (5,)
            if anahtar not in self.tür_etiketleri:
                self.tür_etiketleri[anahtar] = f"t{len(self.tür_etiketleri)}"
                self.tür_tanımları.append(f"{self.tür_etiketleri[anahtar]}: .quad 5, 0, 0")
            return self.tür_etiketleri[anahtar]
        if isinstance(tür, (Liste, Sözlük)):
            alt = [self.tür_etiketi(p) for p in tür.parametreler()]
            anahtar = (2 if isinstance(tür, Liste) else 3, *alt)
        else:
            anahtar = ({"metin": 1, "ondalık": 6}.get(tür, 0),)
        if anahtar not in self.tür_etiketleri:
            self.tür_etiketleri[anahtar] = f"t{len(self.tür_etiketleri)}"
            alanlar = [str(a) for a in anahtar] + ["0"] * (3 - len(anahtar))
            self.tür_tanımları.append(f"{self.tür_etiketleri[anahtar]}: .quad {', '.join(alanlar)}")
        return self.tür_etiketleri[anahtar]

    def okunmayanları_bildir(self, değişkenler):
        """Bir işlev adına çok benzeyen ve hiç okunmayan değişken büyük olasılıkla
        yazım hatasıdır: `5 -> kere` sessizce yeni bir değişken oluşturur."""
        for ad, (_, _, konum, okundu) in değişkenler.items():
            if okundu or konum is None:
                continue
            if değişkenler is not self.küreseller and ad in self.küreseller:
                self.uyarılar.append((
                    konum, f"'{ad}' burada yerel bir değişken oluşturuyor ve hiç okunmuyor; "
                           f"aynı adlı üst düzey değişken değişmez",
                    f"üst düzey değişkeni değiştirmek için onu 'ortak' ile tanımlayın:  değer -> ortak {ad}"))
                continue
            # Yanlış alarm vermemek için yalnızca çok yakın adlar sayılır:
            # 'sayılar' ile 'sayıya' benzer ama kasıtlı bir değişken adıdır.
            sınır = 1 if len(ad) < 8 else 2
            adaylar = sorted(set(self.işlevler) | set(YERLEŞİKLER) | set(ANAHTARLAR))
            yakın = [a for a in adaylar
                     if len(ad) >= 4 and len(a) >= 3 and uzaklık(ad, a) <= sınır]
            if yakın:
                self.uyarılar.append((konum, f"'{ad}' yeni bir değişken olarak tanımlandı "
                                             f"ama hiç okunmuyor",
                                      " ya da ".join(f"'{y}'" for y in yakın[:2])
                                      + " mi demek istediniz?"))

    def küreselleri_topla(self, deyimler):
        """En üst düzeyde (iç içe bloklar dahil) atanan her ad küresel değişkendir."""
        for d in deyimler:
            if d[0] == "akış":
                self.hedeflerden_topla(d[2])

    def hedeflerden_topla(self, hedefler):
        def küresel(ad):
            self.küreseller.setdefault(ad, [f"g{len(self.küreseller)}", None, None, False])

        for h in hedefler:
            if h[0] == "ad" and h[2] is None and h[1] not in self.işlevler \
                    and h[1] not in YERLEŞİKLER and h[1] not in self.kayıtlar:
                küresel(h[1])
            elif h[0] == "eğer":
                self.küreselleri_topla(h[1])
                self.küreselleri_topla(h[2] or [])
            elif h[0] == "iken":
                self.küreselleri_topla(h[1])
            elif h[0] == "ortak":
                küresel(h[1])
                self.ortaklar.add(h[1])
            elif h[0] == "her":
                küresel(h[1])
                self.küreselleri_topla(h[2])
            elif h[0] == "çatal":
                for dal in h[1]:
                    self.hedeflerden_topla(dal)

    def işlevi_derle(self, ad):
        """İşlevi, parametre türleri belli olduktan sonra ayrı bir tampona derler."""
        parametreler, gövde, satır = self.işlevler[ad]
        b = self.bilgi[ad]
        b["başladı"] = True
        n = len(parametreler)
        saklanan = (self.çıktı, self.geçerli, self.yereller, self.yerel_sayısı,
                    self.döngüler, self.çatal_derinliği, self.okunan_küreseller)
        # Argümanlar soldan sağa itilir: ilk argüman en derinde durur.
        self.yereller = {p: [16 + 8 * (n - 1 - i), b["türler"][i], None, True]
                         for i, p in enumerate(parametreler)}
        self.çıktı, self.geçerli, self.yerel_sayısı = [], ad, 0
        self.döngüler, self.çatal_derinliği, self.okunan_küreseller = [], 0, {}
        for d in gövde:
            self.deyim(d)
        gövde_kodu, yerel_sayısı = self.çıktı, self.yerel_sayısı
        self.okunmayanları_bildir(self.yereller)
        (self.çıktı, self.geçerli, self.yereller, self.yerel_sayısı,
         self.döngüler, self.çatal_derinliği, self.okunan_küreseller) = saklanan

        if b["dönüş"] is None:
            b["dönüş"] = "sayı"     # hiç 'döndür' yok: işlev 0 döndürür
        b["sona_ulaşır"] = self.tamamlanır(gövde)
        b["bitti"] = True

        k = self.işlev_kodu
        k.append(İşlevBaşlığı(ad, b))
        k.append("    push rbp")
        k.append("    mov rbp, rsp")
        if yerel_sayısı:
            k.append(f"    sub rsp, {8 * yerel_sayısı}")
        # Yığın taşmasın: sonu gelmeyen özyineleme, işlevin satırını gösteren bir hatayla durur.
        tanım = self.işlevler[ad][2]
        k.append(f"    mov r15, {getattr(tanım, 'dosya', 0) << 32 | int(tanım)}")
        k.append("    cmp rsp, [rip+__yigin_siniri]")
        k.append("    jb __yigin_tasti")
        k.extend(gövde_kodu)
        k.append("    xor eax, eax")
        k.append("    leave")
        k.append("    ret")

    # ── deyimler ──
    def deyim(self, d):
        if d[0] in ("dur", "devam"):
            if not self.döngüler:
                raise NehirHatası(f"'{d[0]}' yalnızca döngü içinde kullanılabilir", d[1])
            devam, son, derinlik = self.döngüler[-1]
            if self.çatal_derinliği > derinlik:     # çatalların yığında bıraktıklarını at
                self.yaz(f"add rsp, {8 * (self.çatal_derinliği - derinlik)}")
            self.yaz(f"jmp {son if d[0] == 'dur' else devam}")
            return
        _, kaynak, hedefler, _ = d
        döngü_başı = None
        if hedefler and hedefler[-1][0] == "iken":
            # Koşul her turda yeniden aktığı için tüm zincir döngünün içindedir.
            döngü_başı = self.yeni_etiket()
            self.etiket_koy(döngü_başı)
        tür = self.ifade(kaynak)
        for h in hedefler:
            tür = self.hedef(h, tür, döngü_başı)
        self.atılan_sonucu_bildir(hedefler)

    def atılan_sonucu_bildir(self, hedefler):
        """`16 -> taban` gibi bir satır değişkene atamaz: akan değer yerleşik işleve argüman
        olur ve sonuç atılır. Yan etkisi olmayan bir yerleşikte bu büyük olasılıkla bir yanlışlıktır."""
        if not hedefler:
            return
        h = hedefler[-1]
        if h[0] != "ad" or h[2] is not None or h[1] in self.işlevler or h[1] in self.kayıtlar \
                or YERLEŞİKLER.get(h[1]) not in SAF_YERLEŞİKLER \
                or (self.yereller is not None and h[1] in self.yereller):
            return
        ipucu = (f"'{h[1]}' yeni bir liste verir, asıl liste değişmez:  liste -> {h[1]} -> liste"
                 if YERLEŞİKLER[h[1]] in ("sırala", "ters_çevir")
                 else "bir değişkene atamak istediyseniz ona başka bir ad verin")
        self.uyarılar.append((h[-1], f"'{h[1]}' yerleşik bir işlev: akan değer ona argüman olur "
                                     f"ve sonucu kullanılmıyor", ipucu))

    def blok(self, deyimler):
        for d in deyimler:
            self.deyim(d)

    def döngü_gövdesi(self, deyimler, devam, son):
        self.döngüler.append((devam, son, self.çatal_derinliği))
        self.blok(deyimler)
        self.döngüler.pop()

    def hedef(self, h, tür, döngü_başı=None):
        önceki, self.konum = self.konum, h[-1]
        try:
            return self.hedef_üret(h, çöz(tür), döngü_başı)
        finally:
            self.konum = önceki

    def hedef_üret(self, h, tür, döngü_başı):
        tip, satır = h[0], h[-1]
        if tip == "yazdır":
            self.yaz("push rax")
            self.yaz("mov rdi, rax")
            self.çıktı.append(TürKoduSatırı(tür))
            self.yaz("call __yaz_deger")
            self.yaz("pop rax")      # değer akmaya devam eder
            return tür
        if tip == "döndür":
            if self.geçerli is None:
                raise NehirHatası("'döndür' yalnızca işlev içinde kullanılabilir", satır)
            b = self.bilgi[self.geçerli]
            if b["dönüş"] is None:
                b["dönüş"] = tür
            elif not birleştir(b["dönüş"], tür):
                raise NehirHatası(f"'{self.geçerli}' işlevi hem {b['dönüş']} hem {tür} döndürüyor", satır)
            self.yaz("leave")
            self.yaz("ret")
            return tür
        if tip == "eğer":
            self.sayı_olmalı(tür, "'eğer' koşulu", satır)
            değilse, son = self.yeni_etiket(), self.yeni_etiket()
            self.yaz("test rax, rax")
            self.yaz(f"jz {değilse}")
            self.blok(h[1])
            self.yaz(f"jmp {son}")
            self.etiket_koy(değilse)
            self.blok(h[2] or [])
            self.etiket_koy(son)
            return tür
        if tip == "iken":
            self.sayı_olmalı(tür, "'iken' koşulu", satır)
            son = self.yeni_etiket()
            self.yaz("test rax, rax")
            self.yaz(f"jz {son}")
            self.döngü_gövdesi(h[1], döngü_başı, son)
            self.yaz(f"jmp {döngü_başı}")
            self.etiket_koy(son)
            return tür
        if tip == "her":
            baş, artır, son = self.yeni_etiket(), self.yeni_etiket(), self.yeni_etiket()
            if tür == "metin":      # her karakter sırayla değişkene akar
                self.yaz("push rax")                 # [rsp+8] = metin
                self.yaz("push 0")                   # [rsp]   = sıradaki karakterin bayt konumu
                self.etiket_koy(baş)
                self.yaz("mov rsi, [rsp]")
                self.yaz("mov rdi, [rsp+8]")
                self.yaz("cmp rsi, [rdi-8]")
                self.yaz(f"jge {son}")
                self.yaz("call __metin_karakter")
                self.yaz("mov [rsp], rdx")
                self.ata(h[1], "metin", satır)
                self.döngü_gövdesi(h[2], artır, son)
                self.etiket_koy(artır)
                self.yaz(f"jmp {baş}")
                self.etiket_koy(son)
                self.yaz("add rsp, 16")
                return tür
            if isinstance(tür, Sözlük):    # anahtarların o anki listesi üzerinde dönülür
                self.yaz("mov rdi, rax")
                self.yaz("mov esi, 16")
                self.yaz("call __sozluk_liste")
                tür = Liste(tür._anahtar)
            if not isinstance(tür, Liste):
                raise NehirHatası(f"'her' içine bir liste, sözlük ya da metin akmalı, {tür} bulundu", satır)
            self.yaz("push rax")                 # [rsp+8] = liste
            self.yaz("push 0")                   # [rsp]   = dizin
            self.etiket_koy(baş)
            self.yaz("mov rsi, [rsp]")
            self.yaz("mov rdi, [rsp+8]")
            self.yaz("cmp rsi, [rdi]")
            self.yaz(f"jge {son}")
            self.yaz("call __liste_al")
            self.ata(h[1], çöz(tür._eleman), satır)     # henüz bilinmiyorsa kullanımdan öğrenilir
            self.döngü_gövdesi(h[2], artır, son)
            self.etiket_koy(artır)
            self.yaz("inc qword ptr [rsp]")
            self.yaz(f"jmp {baş}")
            self.etiket_koy(son)
            self.yaz("add rsp, 16")
            return tür
        if tip == "çatal":
            # Aynı değer her kola ayrı ayrı akar; sonra olduğu gibi yoluna devam eder.
            for dal in h[1]:
                self.yaz("push rax")
                self.çatal_derinliği += 1
                kol_türü = tür
                for alt in dal:
                    kol_türü = self.hedef(alt, kol_türü)
                self.çatal_derinliği -= 1
                self.yaz("pop rax")
            return tür
        if tip == "eleman":
            self.yaz("push rax")                    # [rsp] = yazılacak değer
            kap = self.ifade(h[1])
            if not isinstance(kap, (Liste, Sözlük)):
                raise NehirHatası(f"'[ ]' ile yalnızca liste ve sözlüklere yazılabilir, {kap} bulundu", satır)
            self.yaz("push rax")
            dizin_türü = self.ifade(h[2])
            self.yaz("mov rsi, rax")
            self.yaz("pop rdi")
            if isinstance(kap, Liste):
                self.sayı_olmalı(dizin_türü, "liste dizini", satır)
                if not birleştir(kap, Liste(tür)):
                    raise NehirHatası(f"{kap} içine {tür} akamaz", satır)
                self.yaz("mov rdx, [rsp]")
                self.yaz("call __liste_koy")
            else:
                self.anahtar_türü(kap, dizin_türü, satır)
                if not birleştir(kap._değer, tür):
                    raise NehirHatası(f"{kap} içine değer olarak {tür} akamaz", satır)
                self.yaz("mov rcx, [rsp]")
                self.yaz("call __sozluk_koy")
            self.yaz("pop rax")
            return tür
        if tip == "ortak":
            if self.geçerli is not None:
                raise NehirHatası("'ortak' yalnızca en üst düzeyde, değişken tanımlanırken yazılır", satır,
                                  f"'{h[1]}' zaten ortaksa işlev içinde doğrudan atanır:  değer -> {h[1]}")
            if self.çağrılabilir(h[1]):
                raise NehirHatası(f"'{h[1]}' bir işlev ya da kayıt adı; değişken adı olamaz", satır)
            self.ata(h[1], tür, satır)
            return tür
        if tip == "alan_yaz":
            self.yaz("push rax")                    # [rsp] = yazılacak değer
            sıra, alan_türü = self.alan_bul(self.ifade(h[1]), h[2], satır)
            if not birleştir(alan_türü, tür):
                raise NehirHatası(f"'{h[2]}' alanı {çöz(alan_türü)} türünde; {tür} atanamaz", satır)
            self.yaz("test rax, rax")
            self.yaz("jz __yok_hatasi")
            self.yaz("mov rcx, [rsp]")
            self.yaz(f"mov [rax+{8 * sıra}], rcx")
            self.yaz("pop rax")
            return tür
        if tip == "yöntem_hedef":
            self.yaz("push rax")                    # akan değer
            nesne_türü = self.ifade(h[1])
            ad = self.yöntem_adı(nesne_türü, h[2], satır)
            self.yaz("mov rcx, [rsp]")              # yığında önce nesne, sonra akan değer
            self.yaz("mov [rsp], rax")
            self.yaz("push rcx")
            return self.çağır(ad, h[3], satır, önceki=[nesne_türü, tür])
        # tip == "ad": işlevse akan değer ilk argüman olur, değilse değişkene atanır.
        # Parametreler aynı adlı işlevleri gölgeler: parametreye akan değer ona atanır.
        _, ad, argümanlar, _ = h
        yerel = self.yereller is not None and ad in self.yereller
        if argümanlar is not None or (not yerel and self.çağrılabilir(ad)):
            self.yaz("push rax")
            try:
                return self.çağır(ad, argümanlar or [], satır, akan=tür)
            except NehirHatası as hata:
                # Yan etkisiz bir yerleşik büyük olasılıkla değişken sanılmıştır (`"a" -> taban`);
                # `5 -> uyar` gibi bir çağrıda ise niyet bellidir, bu ipucu yanıltır.
                if argümanlar is None and ad in YERLEŞİKLER and ad not in self.işlevler \
                        and YERLEŞİKLER[ad] in SAF_YERLEŞİKLER and hata.ipucu is None:
                    hata.ipucu = (f"'{ad}' yerleşik bir işlevdir; akan değer ona argüman olur. "
                                  f"Değişkene başka bir ad verin")
                raise
        self.ata(ad, tür, satır)
        return tür

    def işlev_değeri(self, ad):
        """İşlevin adresini rax'e yükler ve türünü verir. Parametre türleri henüz
        belli değilse bilinmeyenlerle başlar; işlev en son derlenir."""
        b = self.bilgi[ad]
        if b["türler"] is None:
            b["türler"] = [TürDeğişkeni() for _ in self.işlevler[ad][0]]
            b["değer_yeri"] = self.konum
            self.değer_işlevler.append(ad)
        if b["dönüş"] is None:
            b["dönüş"] = TürDeğişkeni()
        self.yaz(f"lea rax, [rip+{b['etiket']}]")
        return İşlevTürü(b["türler"], b["dönüş"])

    def değerle_çağır(self, ad, kayıt, adres, türler, satır):
        """İşlev tutan bir değişken üzerinden çağrı; argümanlar yığına itilmiştir."""
        tür = çöz(kayıt[1])
        if isinstance(tür, TürDeğişkeni) and not tür.yalnız_kayıt:
            tür.bağ = İşlevTürü([TürDeğişkeni() for _ in türler], TürDeğişkeni())
            tür = çöz(tür)
        if not isinstance(tür, İşlevTürü):
            raise NehirHatası(f"'{ad}' bir değişken ({tür}), işlev değil", satır,
                              f"'{ad}' adlı değişken, aynı adlı işlevi gölgeliyor"
                              if self.çağrılabilir(ad) else None)
        beklenen = tür._parametreler
        if len(beklenen) != len(türler):
            raise NehirHatası(f"'{ad}' {len(beklenen)} argüman alan bir işlev tutuyor, "
                              f"{len(türler)} verildi", satır, f"'{ad}' türü: {tür}")
        for i, (b, v) in enumerate(zip(beklenen, türler), 1):
            if not birleştir(b, v):
                raise NehirHatası(f"'{ad}' işlevinin {i}. argümanı {çöz(b)} olmalı, {v} verildi", satır,
                                  f"'{ad}' türü: {tür}")
        kayıt[3] = True
        if self.yereller is not None and ad not in self.yereller:
            self.okunan_küreseller.setdefault(ad, satır)
        self.yaz(f"mov rax, {adres}")
        self.yaz("call rax")
        if türler:
            self.yaz(f"add rsp, {8 * len(türler)}")
        return çöz(tür._dönüş)

    def çağrılabilir(self, ad):
        return ad in self.işlevler or ad in self.kayıtlar or ad in YERLEŞİKLER

    def anahtar_türü(self, sözlük, anahtar, satır):
        """Anahtarın türünü sözlüğünkiyle eşitler ve tür kodunu edx'e yükler."""
        if anahtar not in ("sayı", "metin"):
            raise NehirHatası(f"sözlük anahtarı sayı ya da metin olmalı, {anahtar} bulundu", satır)
        if not birleştir(sözlük._anahtar, anahtar):
            raise NehirHatası(f"bu sözlüğün anahtarları {sözlük.anahtar}; {anahtar} verildi", satır)
        self.yaz(f"mov edx, {0 if anahtar == 'sayı' else 1}")

    def bilinen_değişkenler(self):
        adlar = [ad for ad, k in self.küreseller.items() if k[1] is not None]
        if self.yereller is not None:
            adlar += [ad for ad, k in self.yereller.items() if k[1] is not None]
        return adlar

    def işlev_yok(self, ad, satır):
        if self.değişken_kaydı(ad)[0] is not None:
            return NehirHatası(f"'{ad}' bir değişken, işlev değil", satır)
        return NehirHatası(f"'{ad}' adında bir işlev yok", satır,
                           benzerler(ad, list(self.işlevler) + list(YERLEŞİKLER))
                           or (ÖZEL_AD_İPUCU if ad.startswith("_") else None))

    def değişken_kaydı(self, ad):
        """(kayıt, bellek adresi metni) ya da değişken yoksa (None, None)."""
        if self.yereller is not None and ad in self.yereller:
            kayıt = self.yereller[ad]
            return kayıt, f"[rbp{kayıt[0]:+d}]"
        if ad in self.küreseller:
            kayıt = self.küreseller[ad]
            return kayıt, f"[rip+{kayıt[0]}]"
        return None, None

    def ata(self, ad, tür, satır):
        # İşlev içindeki atama yerel değişken oluşturur. Tek istisna `ortak` ile
        # tanımlanmış üst düzey değişkenlerdir: onlara işlevler de atayabilir.
        if self.yereller is not None and ad not in self.yereller and ad not in self.ortaklar:
            if ad in self.okunan_küreseller:
                raise NehirHatası(
                    f"'{ad}' bu işlevde üst düzey değişken olarak okundu; ona burada atanamaz", satır,
                    f"işlevlerin değiştirebildiği değişkenler 'ortak' ile tanımlanır:  değer -> ortak {ad}",
                    ilgili=self.küreseller[ad][2], ilgili_not=f"'{ad}' burada tanımlanmış")
            self.yerel_sayısı += 1
            self.yereller[ad] = [-8 * self.yerel_sayısı, None, None, False]
        kayıt, adres = self.değişken_kaydı(ad)
        if kayıt is None:       # (yalnızca en üst düzeyde olmaz; küreseller önceden toplanır)
            self.yerel_sayısı += 1
            self.yereller[ad] = [-8 * self.yerel_sayısı, None, None, False]
            kayıt, adres = self.değişken_kaydı(ad)
        if kayıt[1] is None:
            kayıt[1], kayıt[2] = tür, satır
        elif not birleştir(kayıt[1], tür):
            if çöz(kayıt[1]) == "sayı" and tür == "ondalık":
                raise NehirHatası(f"'{ad}' değişkeni {kayıt[1]} türünde; {tür} atanamaz", satır,
                                  "değişken ondalık olacaksa ilk değerini de ondalık yazın:  0.0")
            raise NehirHatası(f"'{ad}' değişkeni {kayıt[1]} türünde; {tür} atanamaz", satır)
        self.yaz(f"mov {adres}, rax")

    def yöntem_adı(self, nesne_türü, yöntem, satır):
        """nesne.yöntem(...) çağrısının işlev adı: Kayıt.yöntem"""
        t = çöz(nesne_türü)
        if not isinstance(t, Kayıt):
            raise NehirHatası(f"'.{yöntem}(...)': yöntemler yalnızca kayıtlarda çağrılır, {t} bulundu", satır)
        ad = f"{t.ad}.{yöntem}"
        if ad not in self.işlevler:
            yöntemler = [a.split(".", 1)[1] for a in self.işlevler if a.startswith(t.ad + ".")]
            raise NehirHatası(f"'{t.ad}' kaydının '{yöntem}' adında bir yöntemi yok", satır,
                              benzerler(yöntem, yöntemler)
                              or (f"yöntemleri: {', '.join(yöntemler)}" if yöntemler else
                                  f"yöntem tanımı:  işlev {t.ad}.{yöntem}(nesne, ...) {{ ... }}"))
        return ad

    def çağır(self, ad, argümanlar, satır, akan=None, önceki=None):
        """Argümanları yığına iter ve işlevi çağırır. `akan` verilmişse akıştan
        gelen değer çağıran tarafından zaten itilmiştir ve ilk argümandır; `önceki`
        verilmişse türleri verilen değerlerin hepsi (sırayla) itilmiştir."""
        türler = list(önceki) if önceki else [akan] if akan else []
        for a in argümanlar:
            türler.append(self.ifade(a))
            self.yaz("push rax")
        # Ad çözümleme sırası: parametre/yerel değişken, programın kendi kayıt ve
        # işlevleri, en son yerleşik işlevler. Böylece program yerleşik bir adı
        # kendi tanımıyla gölgeleyebilir.
        kayıt, adres = self.değişken_kaydı(ad)
        if kayıt is not None and kayıt[1] is not None:
            return self.değerle_çağır(ad, kayıt, adres, türler, satır)
        if ad in self.kayıtlar:
            kayıt = self.kayıtlar[ad]
            if len(türler) != len(kayıt.alanlar):
                raise NehirHatası(f"'{ad}' kaydının {len(kayıt.alanlar)} alanı var, {len(türler)} değer verildi",
                                  satır, f"tanımı: {ad}({', '.join(kayıt.alanlar)})")
            for alan, alan_türü, verilen in zip(kayıt.alanlar, kayıt.türler, türler):
                if not birleştir(alan_türü, verilen):
                    raise NehirHatası(f"'{ad}.{alan}' alanı {çöz(alan_türü)} türünde; {verilen} verildi", satır)
            self.yaz(f"mov edi, {8 * max(len(türler), 1)}")
            self.yaz("call __ayir")
            for sıra in reversed(range(len(türler))):
                self.yaz("pop rcx")
                self.yaz(f"mov [rax+{8 * sıra}], rcx")
            return kayıt
        if ad not in self.işlevler:
            if ad in YERLEŞİKLER:
                return self.yerleşik(YERLEŞİKLER[ad], ad, türler, satır)
            raise self.işlev_yok(ad, satır)

        b = self.bilgi[ad]
        beklenen = len(self.işlevler[ad][0])
        # Çağrı tutmuyorsa ve ad yerleşik bir işlevin de adıysa, çağıran büyük
        # olasılıkla yerleşik olanı kastetmiştir; gölgeleyen tanım gösterilir.
        gölge = {"ilgili": self.işlevler[ad][2],
                 "ilgili_not": f"yerleşik '{ad}' işlevini gölgeleyen tanım burada"} \
            if ad in YERLEŞİKLER else {}
        if len(türler) != beklenen:
            raise NehirHatası(f"'{ad}' işlevi {beklenen} argüman bekliyor, {len(türler)} verildi", satır,
                              f"tanımı: {ad}({', '.join(self.işlevler[ad][0])})"
                              + ("; akıştan gelen değer ilk argüman sayılır" if akan else ""), **gölge)
        if b["türler"] is None:
            b["türler"] = türler
        elif not all(birleştir(x, y) for x, y in zip(b["türler"], türler)):
            raise NehirHatası(f"'{ad}' işlevi ({', '.join(map(str, map(çöz, b['türler'])))}) ile çağrılmıştı; "
                              f"şimdi ({', '.join(map(str, türler))}) veriliyor", satır, **gölge)
        if not b["başladı"]:
            self.işlevi_derle(ad)
        self.yaz(f"call {b['etiket']}")
        if türler:
            self.yaz(f"add rsp, {8 * len(türler)}")
        if b["dönüş"] is None:
            # Özyineleme: işlev hâlâ derleniyor ve henüz bir şey döndürmedi. Dönüş türü,
            # ilk 'döndür'de ya da sonucun kullanıldığı yerde belli olacak bir bilinmeyendir.
            b["dönüş"] = TürDeğişkeni()
        return b["dönüş"]

    def yerleşik(self, asıl, ad, türler, satır):
        def yanlış(beklenen):
            raise NehirHatası(f"'{ad}' ({beklenen}) bekliyor; "
                              f"({', '.join(map(str, türler))}) verildi", satır)

        ilk_liste = bool(türler) and isinstance(türler[0], Liste)
        ilk_sözlük = bool(türler) and isinstance(türler[0], Sözlük)
        if asıl in ("var", "sil") and ilk_sözlük and len(türler) == 2:
            self.yaz("pop rsi")
            self.yaz("pop rdi")
            self.anahtar_türü(türler[0], türler[1], satır)
            if asıl == "var":
                self.yaz("call __sozluk_ara")
                self.yaz("not rax")             # dizin >= 0 ise 1, -1 ise 0
                self.yaz("shr rax, 63")
                return "sayı"
            self.yaz("call __sozluk_sil")
            return çöz(türler[0]._değer)
        if asıl == "var":
            yanlış("sözlük, anahtar")
        if asıl in ("anahtarlar", "değerler"):
            if len(türler) != 1 or not ilk_sözlük:
                yanlış("sözlük")
            self.yaz("pop rdi")
            self.yaz(f"mov esi, {16 if asıl == 'anahtarlar' else 24}")
            self.yaz("call __sozluk_liste")
            return Liste(türler[0]._anahtar if asıl == "anahtarlar" else türler[0]._değer)
        if asıl == "uzunluk":
            if len(türler) != 1 or not (ilk_liste or ilk_sözlük or türler[0] == "metin"):
                yanlış("liste, sözlük ya da metin")
            if ilk_liste or ilk_sözlük:
                self.yaz("pop rax")
                self.yaz("mov rax, [rax]")
            else:
                self.yaz("pop rdi")
                self.yaz("call __metin_uzunluk")
            return "sayı"
        if asıl == "oku":
            # Akan ya da verilen metin, satır sonu eklenmeden istem olarak yazılır.
            if türler not in ([], ["metin"]):
                yanlış("argümansız ya da istem metni")
            if türler:
                self.yaz("pop rsi")
                self.yaz("mov rdx, [rsi-8]")
                self.yaz("call __ham_yaz")
            self.yaz("call __oku")
            return "metin"
        if asıl in ("dosya_oku", "dosya_var", "dosya_sil"):
            if türler != ["metin"]:
                yanlış("dosya yolu")
            self.yaz("pop rdi")
            self.yaz("call __" + asıl)
            return "metin" if asıl == "dosya_oku" else "sayı"
        if asıl in ("dosya_yaz", "dosya_ekle"):
            if türler != ["metin", "metin"]:
                yanlış("içerik, dosya yolu")
            self.yaz("pop rsi")
            self.yaz("pop rdi")
            # O_WRONLY | O_CREAT ve üstüne yazmak için O_TRUNC, eklemek için O_APPEND
            self.yaz(f"mov edx, {0x241 if asıl == 'dosya_yaz' else 0x441}")
            self.yaz("call __dosya_yaz")
            return "metin"
        if asıl == "baytlar":
            if türler != ["metin"]:
                yanlış("metin")
            self.yaz("pop rdi")
            self.yaz("call __metin_baytlar")
            return Liste("sayı")
        if asıl == "karakter":
            if türler != ["sayı"]:
                yanlış("karakter kodu")
            self.yaz("pop rdi")
            self.yaz("call __karakter")
            return "metin"
        if asıl in ("uçbirim_mi", "ortam_var", "dosya_hatası"):
            beklenen = {"uçbirim_mi": "sayı", "ortam_var": "metin", "dosya_hatası": "metin"}[asıl]
            if türler != [beklenen]:
                yanlış({"uçbirim_mi": "dosya tanıtıcısı", "ortam_var": "ortam değişkeninin adı",
                        "dosya_hatası": "dosya yolu"}[asıl])
            self.yaz("pop rdi")
            self.yaz({"uçbirim_mi": "call __ucbirim_mi", "ortam_var": "call __ortam_var",
                      "dosya_hatası": "call __dosya_hata_kodu"}[asıl])
            return "sayı"
        if asıl == "uyar":
            if türler != ["metin"]:
                yanlış("metin")
            self.yaz("pop rdi")
            self.yaz("call __uyar")
            return "metin"
        if asıl == "argümanlar":
            if türler:
                yanlış("argümansız")
            self.yaz("call __argumanlar")
            return Liste("metin")
        if asıl == "çık":
            if türler != ["sayı"]:
                yanlış("çıkış kodu")
            self.yaz("pop rdi")
            self.yaz("call __cik")
            return "sayı"
        if asıl == "işletim_sistemi":
            if türler:
                yanlış("argümansız")
            self.yaz("lea rax, [rip+__isletim_sistemi_adi]")
            return "metin"
        if asıl == "girdi_var":
            if türler:
                yanlış("argümansız")
            self.yaz("call __girdi_var")
            return "sayı"
        if asıl in ("zaman", "tuş", "uçbirim_boyutu", "çöp_topla", "tuş_bırakma_var"):
            if türler:
                yanlış("argümansız")
            self.yaz({"zaman": "call __zaman", "tuş": "call __tus",
                      "uçbirim_boyutu": "call __ucbirim_boyutu", "çöp_topla": "call __bellek_topla",
                      "tuş_bırakma_var": "call __tus_birakma_var"}[asıl])
            return {"zaman": "sayı", "tuş": "metin", "uçbirim_boyutu": Liste("sayı"),
                    "çöp_topla": "sayı", "tuş_bırakma_var": "sayı"}[asıl]
        if asıl in ("bekle", "rastgele", "rastgele_tohum", "tuş_kipi"):
            if türler != ["sayı"]:
                yanlış({"bekle": "milisaniye", "rastgele": "üst sınır", "rastgele_tohum": "tohum",
                        "tuş_kipi": "açmak için 1 (bırakmalarla 2), kapatmak için 0"}[asıl])
            self.yaz("pop rdi")
            self.yaz({"bekle": "call __bekle", "rastgele": "call __rastgele",
                      "rastgele_tohum": "call __rastgele_tohum", "tuş_kipi": "call __tus_kipi"}[asıl])
            return "sayı"
        if asıl == "göster":
            if türler != ["metin"]:
                yanlış("metin")
            self.yaz("pop rdi")
            self.yaz("call __goster")
            return "metin"
        if asıl == "metne":
            if türler not in (["sayı"], ["metin"], ["ondalık"]):
                yanlış("sayı")
            if türler[0] == "sayı":
                self.yaz("pop rdi")
                self.yaz("call __sayidan_metin")
            elif türler[0] == "ondalık":
                self.yaz("pop rdi")
                self.yaz("call __ondalik_metin")
            else:
                self.yaz("pop rax")
            return "metin"
        if asıl == "sayıya":
            if türler not in (["sayı"], ["metin"], ["ondalık"]):
                yanlış("metin")
            if türler[0] == "metin":
                self.yaz("pop rdi")
                self.yaz("call __metinden_sayi")
            elif türler[0] == "ondalık":
                self.yaz("pop rdi")             # sıfıra doğru kesilir
                self.yaz("call __ondalik_tama")
            else:
                self.yaz("pop rax")
            return "sayı"
        if asıl == "ondalığa":
            if türler not in (["sayı"], ["metin"], ["ondalık"]):
                yanlış("sayı ya da metin")
            if türler[0] == "metin":
                self.yaz("pop rdi")
                self.yaz("call __metinden_ondalik")
            else:
                self.yaz("pop rax")
                if türler[0] == "sayı":
                    self.yaz("cvtsi2sd xmm0, rax")
                    self.yaz("movq rax, xmm0")
            return "ondalık"
        if asıl in ("yuvarla", "taban", "tavan"):
            if türler not in (["sayı"], ["ondalık"]):
                yanlış("ondalık")
            if türler[0] == "sayı":
                self.yaz("pop rax")
            else:
                self.yaz("pop rdi")
                self.yaz(f"mov esi, {['yuvarla', 'taban', 'tavan'].index(asıl)}")
                self.yaz("call __ondalik_yuvarla")
            return "sayı"
        if asıl == "mutlak":
            if türler not in (["sayı"], ["ondalık"]):
                yanlış("sayı ya da ondalık")
            self.yaz("pop rax")
            if türler[0] == "sayı":
                self.yaz("mov rcx, rax")
                self.yaz("neg rax")
                self.yaz("cmovl rax, rcx")
            else:
                self.yaz("btr rax, 63")
            return türler[0]
        if asıl in ("karekök", "sin", "cos", "atan2"):
            sayısı = 2 if asıl == "atan2" else 1
            if len(türler) != sayısı or any(t not in ("sayı", "ondalık") for t in türler):
                yanlış("y, x" if asıl == "atan2" else "sayı ya da ondalık")
            yazmaçlar = ["rdi", "rsi"][:sayısı]
            for yazmaç, tür in reversed(list(zip(yazmaçlar, türler))):
                self.yaz(f"pop {yazmaç}")
                if tür == "sayı":
                    self.yaz(f"cvtsi2sd xmm0, {yazmaç}")
                    self.yaz(f"movq {yazmaç}, xmm0")
            if asıl == "karekök":
                self.yaz("movq xmm0, rdi")
                self.yaz("sqrtsd xmm0, xmm0")
                self.yaz("movq rax, xmm0")
            else:
                self.yaz(f"call __ondalik_{asıl}")
            return "ondalık"
        if asıl in ("bit_ve", "bit_veya", "bit_yada", "sola_kaydır", "sağa_kaydır"):
            if türler != ["sayı", "sayı"]:
                yanlış("sayı, sayı")
            self.yaz("pop rcx")
            self.yaz("pop rax")
            self.yaz({"bit_ve": "and rax, rcx", "bit_veya": "or rax, rcx", "bit_yada": "xor rax, rcx",
                      "sola_kaydır": "call __sola_kaydir", "sağa_kaydır": "call __saga_kaydir"}[asıl])
            return "sayı"
        if asıl == "bit_değil":
            if türler != ["sayı"]:
                yanlış("sayı")
            self.yaz("pop rax")
            self.yaz("not rax")
            return "sayı"
        if asıl in ("en_küçük", "en_büyük") and len(türler) == 1 and isinstance(türler[0], Liste) \
                and çöz(türler[0]._eleman) in ("sayı", "ondalık"):
            ondalık = çöz(türler[0]._eleman) == "ondalık"
            self.yaz("pop rdi")
            self.yaz(f"mov esi, {(asıl == 'en_büyük') + 2 * ondalık}")
            self.yaz("call __liste_en")
            return çöz(türler[0]._eleman)
        if asıl in ("en_küçük", "en_büyük", "sınırla", "üs"):
            sayısı = 3 if asıl == "sınırla" else 2
            if len(türler) != sayısı or any(t not in ("sayı", "ondalık") for t in türler):
                yanlış({"sınırla": "değer, alt sınır, üst sınır", "üs": "taban, üs"}.get(
                    asıl, "iki sayı ya da bir sayı listesi"))
            yazmaçlar = ["rax", "rcx", "rdx"][:sayısı] if asıl != "üs" else ["rdi", "rsi"]
            for yazmaç in reversed(yazmaçlar):
                self.yaz(f"pop {yazmaç}")
            if "ondalık" not in türler:
                if asıl == "üs":
                    self.yaz("call __us_sayi")
                else:
                    self.yaz("cmp rax, rcx")
                    self.yaz({"en_küçük": "cmovg rax, rcx", "en_büyük": "cmovl rax, rcx",
                              "sınırla": "cmovl rax, rcx"}[asıl])
                    if asıl == "sınırla":
                        self.yaz("cmp rax, rdx")
                        self.yaz("cmovg rax, rdx")
                return "sayı"
            for i, (yazmaç, tür) in enumerate(zip(yazmaçlar, türler)):
                self.yaz(f"cvtsi2sd xmm{i}, {yazmaç}" if tür == "sayı" else f"movq xmm{i}, {yazmaç}")
            if asıl == "üs":
                self.yaz("movq rdi, xmm0")
                self.yaz("movq rsi, xmm1")
                self.yaz("call __ondalik_us")
                return "ondalık"
            self.yaz({"en_küçük": "minsd xmm0, xmm1", "en_büyük": "maxsd xmm0, xmm1",
                      "sınırla": "maxsd xmm0, xmm1"}[asıl])
            if asıl == "sınırla":
                self.yaz("minsd xmm0, xmm2")
            self.yaz("movq rax, xmm0")
            return "ondalık"
        if asıl == "işaret":
            if türler not in (["sayı"], ["ondalık"]):
                yanlış("sayı ya da ondalık")
            self.yaz("pop rax")
            if türler[0] == "sayı":
                self.yaz("xor ecx, ecx")
                self.yaz("test rax, rax")
                self.yaz("setg cl")
                self.yaz("sar rax, 63")
                self.yaz("or rax, rcx")
            else:
                self.yaz("movq xmm0, rax")
                self.yaz("xorpd xmm1, xmm1")
                self.yaz("ucomisd xmm0, xmm1")
                self.yaz("seta al")
                self.yaz("setb cl")
                self.yaz("movzx eax, al")
                self.yaz("movzx ecx, cl")
                self.yaz("sub rax, rcx")
            return "sayı"
        if asıl in ("tan", "atan", "üstel", "ln", "asin", "acos"):
            if türler not in (["sayı"], ["ondalık"]):
                yanlış("sayı ya da ondalık")
            self.yaz("pop rdi")
            if türler[0] == "sayı":
                self.yaz("cvtsi2sd xmm0, rdi")
                self.yaz("movq rdi, xmm0")
            self.yaz(f"mov esi, {['tan', 'atan', 'üstel', 'ln', 'asin', 'acos'].index(asıl)}")
            self.yaz("call __ondalik_fonk")
            return "ondalık"
        if asıl in EKRAN_İŞLEVLERİ:
            biçimler, açıklama, yordam = EKRAN_İŞLEVLERİ[asıl]
            if türler not in biçimler:
                yanlış(açıklama)
            eksik = len(biçimler[-1]) - len(türler)
            for _ in range(eksik):
                self.yaz("push -1")
            sayısı = len(biçimler[-1])
            if sayısı:
                self.yaz("mov rdi, rsp")
            self.yaz(f"call {yordam}")
            if sayısı:
                self.yaz(f"add rsp, {8 * sayısı}")
            return "sayı"
        if asıl == "sırala":
            eleman = çöz(türler[0]._eleman) if ilk_liste else None
            if len(türler) == 1 and eleman in ("sayı", "metin", "ondalık"):
                self.yaz("pop rdi")
                self.yaz(f"mov esi, {['sayı', 'metin', 'ondalık'].index(eleman)}")
                self.yaz("call __liste_sirala")
                return türler[0]
            if len(türler) == 2 and ilk_liste:
                if not birleştir(türler[1], İşlevTürü([türler[0]._eleman, türler[0]._eleman], "sayı")):
                    raise NehirHatası(f"'{ad}' için karşılaştırma işlevi iki eleman alıp sayı vermeli "
                                      f"(a, b'den önce gelecekse 1); {türler[1]} verildi", satır)
                self.yaz("pop rdx")
                self.yaz("pop rdi")
                self.yaz("mov esi, 3")
                self.yaz("call __liste_sirala")
                return türler[0]
            if len(türler) == 1 and eleman is not None and not isinstance(eleman, TürDeğişkeni):
                raise NehirHatası(f"'{ad}' {eleman} elemanlarını kendiliğinden sıralayamaz", satır,
                                  "bir karşılaştırma işlevi verin:  sırala(liste, önce)   "
                                  "(önce(a, b): a, b'den önce gelecekse 1)")
            yanlış("sayı, metin ya da ondalık listesi; başka listeler için bir karşılaştırma işlevi de")
        if asıl == "ters_çevir":
            if len(türler) != 1 or not ilk_liste:
                yanlış("liste")
            self.yaz("pop rdi")
            self.yaz("call __liste_ters")
            return türler[0]
        if asıl == "rgb":
            if türler != ["sayı", "sayı", "sayı"]:
                yanlış("kırmızı, yeşil, mavi (0-255)")
            self.yaz("pop rdx")
            self.yaz("pop rcx")
            self.yaz("pop rax")
            self.yaz("and eax, 255")
            self.yaz("shl eax, 16")
            self.yaz("and ecx, 255")
            self.yaz("shl ecx, 8")
            self.yaz("or eax, ecx")
            self.yaz("and edx, 255")
            self.yaz("or eax, edx")
            return "sayı"
        if asıl == "pi":
            if türler:
                yanlış("argümansız")
            self.yaz("movabs rax, 0x400921FB54442D18")
            return "ondalık"
        if asıl == "ekle":
            if len(türler) != 2 or not ilk_liste:
                yanlış("liste, eleman")
            if türler[1] is türler[0]:
                raise NehirHatası("bir liste kendi içine eklenemez", satır)
            if not birleştir(türler[0], Liste(türler[1])):
                raise NehirHatası(f"{türler[0]} içine {türler[1]} eklenemez", satır)
            self.yaz("pop rsi")
            self.yaz("pop rdi")
            self.yaz("call __liste_ekle")
            return türler[0]
        if asıl == "dilim":
            if len(türler) != 3 or türler[1:] != ["sayı", "sayı"] \
                    or not (ilk_liste or türler[0] == "metin"):
                yanlış("liste ya da metin, baş, son")
            self.yaz("pop rdx")
            self.yaz("pop rsi")
            self.yaz("pop rdi")
            self.yaz("call __liste_dilim" if ilk_liste else "call __metin_dilim")
            return türler[0] if ilk_liste else "metin"
        if asıl == "bul":
            if türler == ["metin", "metin"]:
                self.yaz("pop rsi")
                self.yaz("pop rdi")
                self.yaz("call __metin_bul")
                return "sayı"
            if len(türler) != 2 or not ilk_liste:
                yanlış("metin, aranan metin  ya da  liste, aranan eleman")
            if not birleştir(türler[0], Liste(türler[1])) or sözlük_içerir(türler[1]):
                raise NehirHatası(f"{türler[0]} içinde {türler[1]} aranamaz", satır)
            self.yaz("pop rsi")
            self.yaz("pop rdi")
            self.çıktı.append(TürKoduSatırı(türler[1], "rdx"))
            self.yaz("call __liste_bul")
            return "sayı"
        if asıl == "sil":
            if len(türler) != 2 or not ilk_liste or türler[1] != "sayı":
                yanlış("liste, dizin  ya da  sözlük, anahtar")
            self.yaz("pop rsi")
            self.yaz("pop rdi")
            self.yaz("call __liste_sil")
            return çöz(türler[0]._eleman)
        if asıl == "böl":
            if türler != ["metin", "metin"]:
                yanlış("metin, ayraç")
            self.yaz("pop rsi")
            self.yaz("pop rdi")
            self.yaz("call __metin_bol")
            return Liste("metin")
        if asıl == "birleş":
            if len(türler) != 2 or not ilk_liste or türler[1] != "metin" \
                    or not birleştir(türler[0], Liste("metin")):
                yanlış("metin listesi, ayraç")
            self.yaz("pop rsi")
            self.yaz("pop rdi")
            self.yaz("call __liste_birles")
            return "metin"
        if türler != ["sayı", "sayı"]:      # aralık
            yanlış("sayı, sayı")
        self.yaz("pop rsi")
        self.yaz("pop rdi")
        self.yaz("call __aralik")
        return Liste("sayı")

    def sayı_olmalı(self, tür, ne, satır):
        tür = çöz(tür)
        if isinstance(tür, TürDeğişkeni) and not tür.yalnız_kayıt:
            tür.bağ = "sayı"    # türü bilinmeyen değer burada sayı olarak kullanılıyor
            return
        if tür != "sayı":
            raise NehirHatası(f"{ne} sayı olmalı, {tür} bulundu", satır,
                              "bu bir işlevin kendisi; çağırmak için adının ardına (...) yazın"
                              if isinstance(tür, İşlevTürü) else None)

    # ── ifadeler ──
    def ifade(self, e):
        önceki, self.konum = self.konum, e[-1]
        try:
            return çöz(self.ifade_üret(e))
        finally:
            self.konum = önceki

    def ifade_üret(self, e):
        tip, satır = e[0], e[-1]
        if tip == "sayı":
            self.yaz(f"mov rax, {e[1]}")
            return "sayı"
        if tip == "ondalık":
            if e[1] not in self.ondalıklar:
                self.ondalıklar.append(e[1])
            self.yaz(f"mov rax, [rip+d{self.ondalıklar.index(e[1])}]")
            return "ondalık"
        if tip == "metin":
            veri = e[1].encode("utf-8")
            if veri not in self.metinler:
                self.metinler.append(veri)
            self.yaz(f"lea rax, [rip+m{self.metinler.index(veri)}]")
            return "metin"
        if tip == "değişken":
            kayıt, adres = self.değişken_kaydı(e[1])
            if kayıt is not None and kayıt[1] is None:
                raise NehirHatası(f"'{e[1]}' değişkenine henüz bir değer akmadı", satır,
                                  "değişken, programın daha aşağısında tanımlanıyor")
            if kayıt is None:
                if e[1] in self.işlevler:
                    return self.işlev_değeri(e[1])
                if e[1] in self.kayıtlar:
                    raise NehirHatası(f"'{e[1]}' bir kayıt; kayıtlar değer olarak verilemez", satır,
                                      f"kaydı kuran bir işlev tanımlayın:  işlev yeni(...) {{ {e[1]}(...) -> döndür }}")
                if e[1] in YERLEŞİKLER:
                    raise NehirHatası(f"'{e[1]}' yerleşik bir işlev; yerleşik işlevler değer olarak verilemez",
                                      satır, f"onu çağıran bir işlev tanımlayın:  işlev benim_{e[1]}(x) "
                                             f"{{ x -> {e[1]} -> döndür }}")
                raise NehirHatası(f"'{e[1]}' adında bir değişken yok", satır,
                                  benzerler(e[1], self.bilinen_değişkenler())
                                  or (ÖZEL_AD_İPUCU if e[1].startswith("_") else None))
            kayıt[3] = True
            if self.yereller is not None and e[1] not in self.yereller:
                self.okunan_küreseller.setdefault(e[1], satır)
            self.yaz(f"mov rax, {adres}")
            return kayıt[1]
        if tip == "çağrı":
            return self.çağır(e[1], e[2], satır)
        if tip == "yok":
            self.yaz("xor eax, eax")
            return TürDeğişkeni(yalnız_kayıt=True)
        if tip == "alan":
            sıra, alan_türü = self.alan_bul(self.ifade(e[1]), e[2], satır)
            self.yaz("test rax, rax")
            self.yaz("jz __yok_hatasi")
            self.yaz(f"mov rax, [rax+{8 * sıra}]")
            return alan_türü
        if tip == "liste":
            self.yaz(f"mov edi, {max(len(e[1]), 4)}")
            self.yaz("call __liste_yeni")
            self.yaz("push rax")
            tür = Liste()
            for eleman in e[1]:
                eleman_türü = self.ifade(eleman)
                if not birleştir(tür, Liste(eleman_türü)):
                    raise NehirHatası(f"listenin elemanları aynı türde olmalı: "
                                      f"{tür.eleman} ve {eleman_türü} karışmış", satır)
                self.yaz("mov rsi, rax")
                self.yaz("mov rdi, [rsp]")
                self.yaz("call __liste_ekle")
            self.yaz("pop rax")
            return tür
        if tip == "yöntem":
            nesne_türü = self.ifade(e[1])
            ad = self.yöntem_adı(nesne_türü, e[2], satır)
            self.yaz("push rax")
            return self.çağır(ad, e[3], satır, önceki=[nesne_türü])
        if tip == "dizin":
            kap = self.ifade(e[1])
            if kap == "sayı":
                raise NehirHatası("'[ ]' ile yalnızca liste, sözlük ve metinlere erişilebilir", satır)
            self.yaz("push rax")
            dizin_türü = self.ifade(e[2])
            self.yaz("mov rsi, rax")
            self.yaz("pop rdi")
            if isinstance(kap, Sözlük):
                self.anahtar_türü(kap, dizin_türü, satır)
                self.yaz("call __sozluk_al")
                return kap._değer       # henüz bilinmiyorsa kullanıldığı yerden anlaşılır
            if not isinstance(kap, Liste) and kap != "metin":
                raise NehirHatası(f"'[ ]' ile yalnızca liste, sözlük ve metinlere erişilebilir, "
                                  f"{kap} bulundu", satır)
            self.sayı_olmalı(dizin_türü, "dizin", satır)
            self.yaz("call __metin_al" if kap == "metin" else "call __liste_al")
            return "metin" if kap == "metin" else kap._eleman
        if tip == "sözlük":
            self.yaz("call __sozluk_yeni")
            self.yaz("push rax")
            tür = Sözlük()
            for anahtar, değer in e[1]:
                anahtar_türü = self.ifade(anahtar)
                self.yaz("push rax")
                değer_türü = self.ifade(değer)
                self.yaz("mov rcx, rax")
                self.yaz("pop rsi")
                self.yaz("mov rdi, [rsp]")
                self.anahtar_türü(tür, anahtar_türü, anahtar[-1])
                if not birleştir(tür._değer, değer_türü):
                    raise NehirHatası(f"sözlüğün değerleri aynı türde olmalı: "
                                      f"{tür.değer} ve {değer_türü} karışmış", değer[-1])
                self.yaz("call __sozluk_koy")
            self.yaz("pop rax")
            return tür
        if tip == "tekli":
            işlenen = self.ifade(e[2])
            if işlenen == "ondalık" and e[1] == "-":
                self.yaz("btc rax, 63")     # işaret biti
                return "ondalık"
            self.sayı_olmalı(işlenen, f"'{e[1]}' işlecinin işleneni", satır)
            if e[1] == "-":
                self.yaz("neg rax")
            else:
                self.yaz("test rax, rax")
                self.yaz("sete al")
                self.yaz("movzx eax, al")
            return "sayı"
        return self.ikili(e)

    def ondalık_ikili(self, iş, sol_türü, sağ_türü):
        """rax ve rcx'teki işlenenlerden en az biri ondalık; sayı olan ondalığa çevrilir."""
        self.yaz("cvtsi2sd xmm0, rax" if sol_türü == "sayı" else "movq xmm0, rax")
        self.yaz("cvtsi2sd xmm1, rcx" if sağ_türü == "sayı" else "movq xmm1, rcx")
        if iş in ("/", "%"):
            if sağ_türü == "sayı":
                self.yaz("test rcx, rcx")
            else:
                self.yaz("mov rdx, rcx")
                self.yaz("btr rdx, 63")         # 0.0 da -0.0 da sıfırdır
                self.yaz("test rdx, rdx")
            self.yaz("jz __sifira_bolme")
        if iş in ("+", "-", "*", "/"):
            self.yaz({"+": "addsd", "-": "subsd", "*": "mulsd", "/": "divsd"}[iş] + " xmm0, xmm1")
            self.yaz("movq rax, xmm0")
            return "ondalık"
        if iş == "%":
            self.yaz("movq rdi, xmm0")
            self.yaz("movq rsi, xmm1")
            self.yaz("call __ondalik_kalan")
            return "ondalık"
        # Karşılaştırmalar: nan hiçbir şeye eşit, küçük ya da büyük değildir.
        self.yaz("ucomisd xmm1, xmm0" if iş in ("<", "<=") else "ucomisd xmm0, xmm1")
        if iş == "==":
            self.yaz("sete al")
            self.yaz("setnp cl")
            self.yaz("and al, cl")
        elif iş == "!=":
            self.yaz("setne al")
            self.yaz("setp cl")
            self.yaz("or al, cl")
        else:
            self.yaz(("seta" if iş in ("<", ">") else "setae") + " al")
        self.yaz("movzx eax, al")
        return "sayı"

    def ikili(self, e):
        _, iş, sol, sağ, satır = e
        if iş in ("ve", "veya"):
            # Kısa devre: sonuç her zaman 0 veya 1.
            son = self.yeni_etiket()
            self.sayı_olmalı(self.ifade(sol), f"'{iş}' işlecinin sol tarafı", satır)
            self.yaz("test rax, rax")
            self.yaz("setne al")
            self.yaz("movzx eax, al")
            self.yaz(f"{'jz' if iş == 've' else 'jnz'} {son}")
            self.sayı_olmalı(self.ifade(sağ), f"'{iş}' işlecinin sağ tarafı", satır)
            self.yaz("test rax, rax")
            self.yaz("setne al")
            self.yaz("movzx eax, al")
            self.etiket_koy(son)
            return "sayı"
        sol_türü = self.ifade(sol)
        self.yaz("push rax")
        sağ_türü = self.ifade(sağ)
        self.yaz("mov rcx, rax")
        self.yaz("pop rax")
        # Türü henüz bilinmeyen bir işlenen (boş sözlükten okunan değer gibi)
        # türünü öbür işlenenden ya da işleçten alır.
        sol_türü, sağ_türü = çöz(sol_türü), çöz(sağ_türü)
        if iş in ("==", "!=") and (kayıtsı(sol_türü) or kayıtsı(sağ_türü)
                                   or isinstance(sol_türü, İşlevTürü)):
            # Kayıtlar kimlikleriyle karşılaştırılır: aynı kayıt mı (ya da ikisi de yok mu)?
            if not birleştir(sol_türü, sağ_türü):
                raise NehirHatası(f"{sol_türü} ile {sağ_türü} karşılaştırılamaz", satır)
            self.yaz("cmp rax, rcx")
            self.yaz(f"{KARŞILAŞTIRMA[iş]} al")
            self.yaz("movzx eax, al")
            return "sayı"
        if isinstance(sol_türü, TürDeğişkeni) or isinstance(sağ_türü, TürDeğişkeni):
            if iş == "+" or iş in KARŞILAŞTIRMA:
                if isinstance(sol_türü, TürDeğişkeni) and isinstance(sağ_türü, TürDeğişkeni):
                    raise NehirHatası(f"'{iş}' işlecinin iki tarafının da türü henüz belli değil", satır,
                                      "kabın içine önce bir değer akmalı")
                birleştir(sol_türü, sağ_türü)
                sol_türü, sağ_türü = çöz(sol_türü), çöz(sağ_türü)
        if sol_türü == sağ_türü == "metin" and (iş == "+" or iş in KARŞILAŞTIRMA):
            self.yaz("mov rdi, rax")
            self.yaz("mov rsi, rcx")
            if iş == "+":
                self.yaz("call __metin_birlestir")
                return "metin"
            self.yaz("call __metin_karsilastir")
            self.yaz("test rax, rax")       # işaretli sonuç 0 ile karşılaştırılır
            self.yaz(f"{KARŞILAŞTIRMA[iş]} al")
            self.yaz("movzx eax, al")
            return "sayı"
        if isinstance(sol_türü, Liste) and isinstance(sağ_türü, Liste) and iş in ("+", "==", "!="):
            if not birleştir(sol_türü, sağ_türü) or (iş != "+" and sözlük_içerir(sol_türü)):
                raise NehirHatası(f"{sol_türü} ile {sağ_türü} "
                                  + ("birleştirilemez" if iş == "+" else "karşılaştırılamaz"), satır)
            self.yaz("mov rdi, rax")
            self.yaz("mov rsi, rcx")
            if iş == "+":
                self.yaz("call __liste_birlestir")
                return sol_türü
            self.çıktı.append(TürKoduSatırı(sol_türü, "rdx"))
            self.yaz("call __deger_esit")
            if iş == "!=":
                self.yaz("xor eax, 1")
            return "sayı"
        if isinstance(sol_türü, Sözlük) and isinstance(sağ_türü, Sözlük) and iş in ("==", "!="):
            raise NehirHatası("sözlükler '==' ve '!=' ile karşılaştırılamaz", satır)
        if isinstance(sol_türü, Liste) and iş == "+":
            raise NehirHatası(f"listeye '+' ile eleman eklenemez", satır,
                              "eleman eklemek için:  liste -> ekle(eleman)")
        if "metin" in (sol_türü, sağ_türü) and iş == "+" \
                and ("sayı" in (sol_türü, sağ_türü) or "ondalık" in (sol_türü, sağ_türü)):
            raise NehirHatası("metin ile sayı doğrudan toplanamaz", satır,
                              "sayıyı önce metne çevirin:  \"a\" + metne(5)")
        if "ondalık" in (sol_türü, sağ_türü):
            # Türü bilinmeyen işlenen ondalıktır; sayı ile ondalık karışırsa sayı ondalığa çevrilir.
            for t in (sol_türü, sağ_türü):
                if isinstance(t, TürDeğişkeni) and not t.yalnız_kayıt:
                    t.bağ = "ondalık"
            sol_türü, sağ_türü = çöz(sol_türü), çöz(sağ_türü)
            if sol_türü in ("sayı", "ondalık") and sağ_türü in ("sayı", "ondalık"):
                return self.ondalık_ikili(iş, sol_türü, sağ_türü)
        self.sayı_olmalı(sol_türü, f"'{iş}' işlecinin sol tarafı", satır)
        self.sayı_olmalı(sağ_türü, f"'{iş}' işlecinin sağ tarafı", satır)
        if iş == "+":
            self.yaz("add rax, rcx")
        elif iş == "-":
            self.yaz("sub rax, rcx")
        elif iş == "*":
            self.yaz("imul rax, rcx")
        elif iş in ("/", "%"):
            self.yaz("call __sayi_bol" if iş == "/" else "call __sayi_kalan")
        else:
            self.yaz("cmp rax, rcx")
            self.yaz(f"{KARŞILAŞTIRMA[iş]} al")
            self.yaz("movzx eax, al")
        return "sayı"


# ───────────────────────────── Sürücü ─────────────────────────────

def okuma_hatası(h):
    """Dosya okuma hatasının Türkçe nedeni."""
    if isinstance(h, UnicodeDecodeError):
        return "geçerli UTF-8 değil"
    return {errno.ENOENT: "dosya bulunamadı", errno.EACCES: "erişim izni yok",
            errno.EISDIR: "bu bir dizin, dosya değil"}.get(h.errno, h.strerror)


def derle(yol, dosyalar, hedef=VARSAYILAN_HEDEF):
    """Ana dosyayı ve `kullan` ile istediği modülleri derler; (assembly metni, uyarılar)
    verir. `dosyalar` listesi (görünen yol, kaynak metni) çiftleriyle doldurulur;
    konumlardaki dosya numarası bu listedeki sıradır."""
    işlevler, kayıtlar, yüklenen = {}, {}, set()

    def yükle(görünen, isteyen=None):
        gerçek = os.path.realpath(görünen)
        if gerçek in yüklenen:      # her modül bir kez yüklenir; döngüsel kullanım sorun olmaz
            return []
        yüklenen.add(gerçek)
        try:
            with open(görünen, encoding="utf-8") as f:
                kaynak = f.read()
        except (OSError, UnicodeDecodeError) as h:
            if isteyen is None:
                raise
            raise NehirHatası(f"'{görünen}' modülü okunamadı: {okuma_hatası(h)}", isteyen,
                              "yol, 'kullan' yazan dosyanın bulunduğu dizine göredir")
        no = len(dosyalar)
        dosyalar.append((görünen, kaynak))

        def içe_aktar(ad, konum):
            hedef = os.path.normpath(os.path.join(os.path.dirname(görünen), ad))
            return yükle(hedef.replace(os.sep, "/"), konum)

        return Ayrıştırıcı(sözcükle(kaynak, no), işlevler, kayıtlar, içe_aktar).program()

    deyimler = yükle(yol)
    üretici = KodÜretici(deyimler, işlevler, [d[0] for d in dosyalar], kayıtlar, hedef)
    return üretici.üret(), üretici.uyarılar


def sözcük_dökümü(kaynak):
    """Sözcükleri satır satır metne döker. Nehir ile yazılmış sözcükleyicinin
    (kendi/sozcukleyici.nehir) çıktısı bununla bire bir aynı olmalıdır."""
    satırlar = []
    for s in sözcükle(kaynak):
        satır = f"{int(s.satır)}:{s.satır.sütun}:{s.satır.uzunluk} {int(s.yeni_satır)} {s.tür}"
        if s.tür != "SON":
            değer = str(s.değer)
            for ham, kaçış in (("\\", "\\\\"), ("\n", "\\n"), ("\t", "\\t"), ("\r", "\\r")):
                değer = değer.replace(ham, kaçış)
            satır += " " + değer
        satırlar.append(satır)
    return "\n".join(satırlar) + "\n"


def ağaç_dökümü(kaynak):
    """Sözdizimi ağacını girintili satırlara döker:  tür "ad" sayı @satır:sütun:uzunluk
    Nehir ile yazılmış ayrıştırıcının (kendi/ayristirici.nehir) çıktısı bununla bire bir
    aynı olmalıdır. Modüller yüklenmez; `kullan` bir düğüm olarak görünür."""
    ayrıştırıcı = Ayrıştırıcı(sözcükle(kaynak), içe_aktar=lambda yol, konum: [("kullan", yol, konum)])
    deyimler = ayrıştırıcı.program()

    # Her düğüm ortak bir biçime çevrilir: (tür, ad, sayı, çocuklar, konum)
    def blok(deyimler, k):
        return ("blok", "", 0, [ifade(d) for d in deyimler], k)

    def ifade(n):       # ifadeler ve deyimler
        t, k = n[0], n[-1]
        if t == "sayı":
            return (t, "", n[1], [], k)
        if t in ("metin", "ondalık", "değişken", "kullan"):
            return (t, n[1], 0, [], k)
        if t == "çağrı":
            return (t, n[1], 0, [ifade(a) for a in n[2]], k)
        if t == "liste":
            return (t, "", 0, [ifade(a) for a in n[1]], k)
        if t == "sözlük":
            return (t, "", 0, [ifade(x) for çift in n[1] for x in çift], k)
        if t == "dizin":
            return (t, "", 0, [ifade(n[1]), ifade(n[2])], k)
        if t == "alan":
            return (t, n[2], 0, [ifade(n[1])], k)
        if t == "yöntem":
            return (t, n[2], 0, [ifade(n[1])] + [ifade(a) for a in n[3]], k)
        if t == "tekli":
            return (t, n[1], 0, [ifade(n[2])], k)
        if t == "ikili":
            return (t, n[1], 0, [ifade(n[2]), ifade(n[3])], k)
        if t == "akış":
            return (t, "", 0, [ifade(n[1])] + [hedef(h) for h in n[2]], k)
        return (t, "", 0, [], k)        # yok, dur, devam

    def hedef(h):
        t, k = h[0], h[-1]
        if t == "ad":
            argümanlar = [] if h[2] is None else [("argümanlar", "", 0, [ifade(a) for a in h[2]], k)]
            return ("hedef_ad", h[1], 0, argümanlar, k)
        if t == "eleman":
            return (t, "", 0, [ifade(h[1]), ifade(h[2])], k)
        if t == "alan_yaz":
            return (t, h[2], 0, [ifade(h[1])], k)
        if t == "yöntem_hedef":
            return (t, h[2], 0, [ifade(h[1]), ("argümanlar", "", 0, [ifade(a) for a in h[3]], k)], k)
        if t == "ortak":
            return (t, h[1], 0, [], k)
        if t == "eğer":
            return (t, "", 0, [blok(h[1], k)] + ([] if h[2] is None else [blok(h[2], k)]), k)
        if t == "iken":
            return (t, "", 0, [blok(h[1], k)], k)
        if t == "her":
            return (t, h[1], 0, [blok(h[2], k)], k)
        if t == "çatal":
            return (t, "", 0, [("dal", "", 0, [hedef(x) for x in dal], k) for dal in h[1]], k)
        return (t, "", 0, [], k)        # yazdır, döndür

    def tür(t):
        if t[0] == "ad":
            return ("tür_adı", t[1], 0, [], t[-1])
        return ("tür_" + t[0], "", 0, [tür(x) for x in t[1:-1]], t[-1])

    çocuklar = []
    for ad, (alanlar, k) in ayrıştırıcı.kayıtlar.items():
        çocuklar.append(("kayıt", ad, 0, [("alan_tanımı", a, 0, [] if t is None else [tür(t)], ak)
                                          for a, t, ak in alanlar], k))
    for ad, (parametreler, gövde, k) in ayrıştırıcı.işlevler.items():
        çocuklar.append(("işlev", ad, 0, [("param", p, 0, [], k) for p in parametreler] + [blok(gövde, k)], k))
    çocuklar += [ifade(d) for d in deyimler]

    satırlar = []

    def dök(d, girinti):
        t, ad, sayı, alt, k = d
        for ham, kaçış in (("\\", "\\\\"), ("\n", "\\n"), ("\t", "\\t"), ("\r", "\\r")):
            ad = ad.replace(ham, kaçış)
        satırlar.append(f'{girinti}{t} "{ad}" {sayı} @{int(k)}:{k.sütun}:{k.uzunluk}')
        for ç in alt:
            dök(ç, girinti + "  ")

    dök(("program", "", 0, çocuklar, Konum(0, 0, 0)), "")
    return "\n".join(satırlar) + "\n"


def windows_renklerini_aç():
    """Windows konsolunda renk kodlarının (sanal uçbirim kipi) yorumlanmasını açar; Nehir'in
    Windows çalışma zamanı da programlar için aynısını yapar."""
    import ctypes
    kernel32 = ctypes.windll.kernel32
    tutamaç = kernel32.GetStdHandle(-12)
    kip = ctypes.c_uint32()
    if kernel32.GetConsoleMode(tutamaç, ctypes.byref(kip)):
        kernel32.SetConsoleMode(tutamaç, kip.value | 4)    # ENABLE_VIRTUAL_TERMINAL_PROCESSING


def bildir(dosya, kaynak, düzey, mesaj, konum=None, ipucu=None):
    """Hata ya da uyarıyı, kaynak satırı ve altı çizili yeriyle stderr'e yazar:

        dosya:3:5: hata: 'x' adında bir değişken yok
            3 | y + x -> yazdır
              |     ^
              = ipucu: 'xs' mi demek istediniz?
    """
    renkli = sys.stderr.isatty() and "NO_COLOR" not in os.environ
    if renkli and sys.platform == "win32":
        windows_renklerini_aç()
    def boya(metin, kod):
        return f"\033[{kod}m{metin}\033[0m" if renkli else metin

    renk = {"hata": "1;31", "uyarı": "1;33"}.get(düzey, "1;36")
    yer = dosya
    if konum is not None:
        yer += f":{int(konum)}"
        if isinstance(konum, Konum):
            yer += f":{konum.sütun}"
    çıktı = [f"{boya(yer + ':', '1')} {boya(düzey + ':', renk)} {boya(mesaj, '1')}"]

    satırlar = kaynak.split("\n") if kaynak is not None else []
    kenar = " " * 6 + boya("|", "34")
    if isinstance(konum, Konum) and 1 <= konum <= len(satırlar):
        satır = satırlar[konum - 1]
        önce = satır[:konum.sütun - 1]
        # Sekmeler korunur ki işaret, kaynak satırındaki yerle aynı hizaya gelsin.
        boşluk = "".join("\t" if k == "\t" else " " for k in önce)
        uzunluk = max(1, min(konum.uzunluk, len(satır) - len(önce)))
        çıktı.append(f"{boya(f'{int(konum):5} |', '34')} {satır}")
        çıktı.append(f"{kenar} {boşluk}{boya('^' * uzunluk, renk)}")
    if ipucu:
        çıktı.append(f"{' ' * 6}{boya('=', '34')} {boya('ipucu:', '1')} {ipucu}")
    sys.stderr.write("\n".join(çıktı) + "\n")


KULLANIM = """kullanım: nehir.py <dosya.nehir> [seçenekler]

  -o <ad>            çıktı dosyasının adı (varsayılan: kaynak dosya adı, uzantısız;
                     Windows için .exe)
  --hedef <sistem>   linux ya da windows (varsayılan: derleyicinin çalıştığı sistem)
  --asm              yalnızca assembly (.s) üret, derlemeyi orada bırak
  --çalıştır, --run  derledikten sonra programı çalıştır
  --sözcükler        derlemeden yalnızca sözcükleri dök
  --ağaç             derlemeden yalnızca sözdizimi ağacını dök
  -- <argümanlar>    --çalıştır ile birlikte: sonrası programa argüman olarak verilir
"""


def ana(argv):
    girdi, çıktı, yalnız_asm, çalıştır, yalnız_sözcükler = None, None, False, False, False
    yalnız_ağaç = False
    hedef = VARSAYILAN_HEDEF
    program_argümanları = []
    if "--" in argv:
        ayraç = argv.index("--")
        argv, program_argümanları = argv[:ayraç], argv[ayraç + 1:]
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "-o" and i + 1 < len(argv):
            i += 1
            çıktı = argv[i]
        elif a == "--asm":
            yalnız_asm = True
        elif a == "--hedef" and i + 1 < len(argv) and argv[i + 1] in HEDEFLER:
            i += 1
            hedef = argv[i]
        elif a in ("--sözcükler", "--sozcukler", "--tokens"):
            yalnız_sözcükler = True
        elif a in ("--ağaç", "--agac", "--ast"):
            yalnız_ağaç = True
        elif a in ("--çalıştır", "--calistir", "--run"):
            çalıştır = True
        elif a.startswith("-") or girdi is not None:
            sys.stderr.write(KULLANIM)
            return 2
        else:
            girdi = a
        i += 1
    if girdi is None:
        sys.stderr.write(KULLANIM)
        return 2

    dosyalar = []

    def bildir_konumla(düzey, mesaj, konum, ipucu=None):
        no = getattr(konum, "dosya", 0)
        yol, kaynak = dosyalar[no] if no < len(dosyalar) else (girdi, None)
        bildir(yol, kaynak, düzey, mesaj, konum, ipucu)

    try:
        if yalnız_sözcükler or yalnız_ağaç:
            with open(girdi, encoding="utf-8") as f:
                kaynak = f.read()
            dosyalar.append((girdi, kaynak))
            sys.stdout.write(sözcük_dökümü(kaynak) if yalnız_sözcükler else ağaç_dökümü(kaynak))
            return 0
        asm, uyarılar = derle(girdi, dosyalar, hedef)
    except (OSError, UnicodeDecodeError) as h:
        bildir(girdi, None, "hata", f"dosya okunamadı: {okuma_hatası(h)}")
        return 1
    except NehirHatası as h:
        bildir_konumla("hata", h.mesaj, h.satır, h.ipucu)
        if h.ilgili is not None:
            bildir_konumla("not", h.ilgili_not, h.ilgili)
        return 1
    for satır, mesaj, ipucu in uyarılar:
        bildir_konumla("uyarı", mesaj, satır, ipucu)

    kök = çıktı or os.path.splitext(girdi)[0]
    if yalnız_asm:
        # Windows'ta da satır sonları "\n" kalsın: iki derleyicinin çıktısı bayt bayt aynı olmalı.
        with open(çıktı or kök + ".s", "w", encoding="utf-8", newline="\n") as f:
            f.write(asm)
        return 0

    if hedef == "windows":
        # MinGW-w64'ün gcc'si yalnızca birleştirici ve bağlayıcı olarak kullanılır; C kitaplığı
        # bağlanmaz, program yalnızca kernel32.dll ve shell32.dll'i kullanır.
        program = çıktı or kök + ".exe"
        gcc = "gcc" if sys.platform == "win32" else "x86_64-w64-mingw32-gcc"
        komutlar = [[gcc, "-nostdlib", "-x", "assembler", "-", "-o", program, "-lkernel32", "-lshell32",
                     "-Wl,-e,_start", "-Wl,--subsystem,console", "-Wl,--stack,67108864"]]
        nesne = None
    else:
        program = kök
        nesne = kök + ".o"
        komutlar = [["as", "-o", nesne, "-"], ["ld", "-o", program, nesne]]
    try:
        for komut in komutlar:
            subprocess.run(komut, input=asm.encode("utf-8") if "-" in komut else None, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as h:
        sys.stderr.write(f"hata: birleştirme/bağlama başarısız: {h}\n")
        if isinstance(h, FileNotFoundError) and hedef == "windows":
            sys.stderr.write("ipucu: Windows programları için MinGW-w64 gerekir (gcc)\n")
        return 1
    finally:
        if nesne and os.path.exists(nesne):
            os.remove(nesne)

    if çalıştır:
        if hedef != VARSAYILAN_HEDEF:
            sys.stderr.write(f"hata: {hedef} programı bu sistemde çalıştırılamaz; {program} üretildi\n")
            return 1
        return subprocess.run([os.path.abspath(program)] + program_argümanları).returncode
    return 0


def büyük_yığında(iş):
    """Derleyici özyinelemelidir; çok iç içe ya da çok uzun ifadeler Python'un varsayılan
    sınırlarını aşmasın diye iş, büyük yığınlı bir iş parçacığında çalıştırılır."""
    import threading
    sonuç = []
    sys.setrecursionlimit(1_000_000)
    threading.stack_size(512 * 1024 * 1024)
    t = threading.Thread(target=lambda: sonuç.append(iş()))
    t.start()
    t.join()
    return sonuç[0] if sonuç else 1


if __name__ == "__main__":
    sys.exit(büyük_yığında(lambda: ana(sys.argv[1:])))
