#!/usr/bin/env python3
"""Nehir derleyicisi.

Nehir kaynak kodunu (.nehir) doğrudan x86-64 Linux assembly'sine çevirir,
ardından `as` ve `ld` ile libc'siz, bağımsız bir çalıştırılabilir dosya üretir.

Aşamalar:  kaynak -> Sözcükleyici -> Ayrıştırıcı (AST) -> Kod üretici -> .s -> as/ld
"""
import difflib
import os
import subprocess
import sys


class Konum(int):
    """Bir satır numarası gibi davranır ama sütunu ve uzunluğu da taşır;
    hata mesajları kaynak satırında tam yeri gösterebilsin diye."""

    def __new__(cls, satır, sütun=1, uzunluk=1):
        k = super().__new__(cls, satır)
        k.sütun, k.uzunluk = sütun, uzunluk
        return k


class NehirHatası(Exception):
    def __init__(self, mesaj, satır=None, ipucu=None):
        super().__init__(mesaj)
        self.mesaj = mesaj
        self.satır = satır
        self.ipucu = ipucu


def benzerler(ad, adaylar):
    """Yazım hatası için 'şunu mu demek istediniz' ipucu; benzer ad yoksa None."""
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
    "oku": "oku", "read": "oku",
    "girdi_var": "girdi_var", "has_input": "girdi_var",
}

İŞLEÇLER = ["->", "→", "==", "!=", "<=", ">=",
            "+", "-", "*", "/", "%", "<", ">", "(", ")", "{", "}", "[", "]", ",", "|", ":"]

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


def sözcükle(kaynak):
    sözcükler, i, satır, n = [], 0, 1, len(kaynak)
    satır_başı = 0
    son_satır = 0

    def konum(baş, son):
        return Konum(satır, baş - satır_başı + 1, max(son - baş, 1))

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
        elif c.isdigit():
            j = i
            while j < n and (kaynak[j].isdigit() or kaynak[j] == "_"):
                j += 1
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
    ekle("SON", None, n, n)
    return sözcükler


# ───────────────────────────── Ayrıştırıcı ─────────────────────────────
# AST düğümleri basit demetlerdir; ilk eleman düğüm türü, son eleman satır no.
#
#   ("sayı", değer, satır)            ("metin", değer, satır)
#   ("değişken", ad, satır)           ("çağrı", ad, [argümanlar], satır)
#   ("liste", [elemanlar], satır)     ("dizin", ifade, dizin_ifadesi, satır)
#   ("sözlük", [(anahtar, değer), ...], satır)
#   ("tekli", işleç, ifade, satır)    ("ikili", işleç, sol, sağ, satır)
#   ("akış", kaynak_ifade, [hedefler], satır)
#   ("dur", satır)  ("devam", satır)              döngüden çık / sonraki tura geç
#
# Hedefler:
#   ("yazdır", satır)  ("döndür", satır)  ("ad", ad, argümanlar|None, satır)
#   ("eleman", kap_ifadesi, dizin_ifadesi, satır) değer -> liste[dizin], değer -> sözlük[anahtar]
#   ("eğer", blok, değilse_blok|None, satır)  ("iken", blok, satır)
#   ("her", değişken, blok, satır)                liste -> her (x) { ... }
#   ("çatal", [[hedefler], [hedefler], ...], satır)   değer -> (a | b -> c)

SONLANDIRAN = ("eğer", "iken", "her", "döndür")   # bu hedeflerden sonra akış devam etmez


class Ayrıştırıcı:
    def __init__(self, sözcükler):
        self.s = sözcükler
        self.k = 0
        self.işlevler = {}   # ad -> (parametreler, gövde, satır)

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
            else:
                deyimler.append(self.deyim())
        return deyimler

    def işlev_tanımı(self):
        satır = self.bekle("ANAHTAR", "işlev").satır
        ad = self.bekle("AD").değer
        if ad in self.işlevler:
            raise NehirHatası(f"'{ad}' işlevi zaten tanımlı", satır)
        if ad in YERLEŞİKLER:
            raise NehirHatası(f"'{ad}' yerleşik bir işlevdir, yeniden tanımlanamaz", satır)
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
            if self.aynı_satırda("["):
                # a[i][j] hedefinde son dizin yazılacak gözdür; öncekiler okunur.
                kap = ("değişken", s.değer, s.satır)
                while True:
                    köşe = self.al("İŞLEÇ")
                    dizin = self.ifade()
                    self.bekle("İŞLEÇ", "]")
                    if not self.aynı_satırda("["):
                        return ("eleman", kap, dizin, s.satır)
                    kap = ("dizin", kap, dizin, köşe.satır)
            return ("ad", s.değer, None, s.satır)
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
        while self.aynı_satırda("["):
            s = self.al("İŞLEÇ")
            dizin = self.ifade()
            self.bekle("İŞLEÇ", "]")
            e = ("dizin", e, dizin, s.satır)
        return e

    def birincil(self):
        s = self.şimdiki
        if self.al("SAYI"):
            return ("sayı", s.değer, s.satır)
        if self.al("METİN"):
            return ("metin", s.değer, s.satır)
        if self.al("ANAHTAR", "doğru"):
            return ("sayı", 1, s.satır)
        if self.al("ANAHTAR", "yanlış"):
            return ("sayı", 0, s.satır)
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
# Yazdırma ve eşitlik gibi türe bağlı işlemler için derleyici her türün bir
# tanımını üretir: {tür kodu, 1. parametre tanımı, 2. parametre tanımı};
# tür kodu 0 sayı, 1 metin, 2 liste, 3 sözlük.
# Türler derleme anında izlenir. İşlevlerin parametre türleri ilk çağrıdan
# çıkarılır; bu yüzden işlevler ilk çağrıldıkları anda derlenir.

class TürDeğişkeni:
    """Henüz bilinmeyen bir tür (`[]` listesinin eleman türü gibi). Öğrenildiğinde
    `bağ` ile gerçek türe bağlanır; aynı değişkeni paylaşan her yer birlikte güncellenir."""

    def __init__(self):
        self.bağ = None

    def __str__(self):
        return "henüz bilinmeyen tür"


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


def içerir(tür, hedef):
    tür = çöz(tür)
    if tür is hedef:
        return True
    return isinstance(tür, (Liste, Sözlük)) and any(içerir(p, hedef) for p in tür.parametreler())


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
        if içerir(b, a):        # bir liste kendi elemanı olamaz
            return False
        a.bağ = b
        return True
    if type(a) is not type(b):
        return False
    if isinstance(a, str):
        return a == b
    return all(birleştir(x, y) for x, y in zip(a.parametreler(), b.parametreler()))


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

# Hata verebilen çalışma zamanı işlemleri; öncesinde r15'e kaynak satırı yüklenir.
RİSKLİ = {"jz __sifira_bolme"} | {"call " + ad for ad in (
    "__liste_al", "__liste_koy", "__metin_al", "__metinden_sayi", "__liste_yeni",
    "__liste_ekle", "__aralik", "__metin_birlestir", "__sayidan_metin", "__oku",
    "__metin_dilim", "__liste_dilim", "__liste_birlestir", "__liste_sil",
    "__metin_bol", "__liste_birles", "__sozluk_yeni", "__sozluk_koy", "__sozluk_al",
    "__sozluk_sil", "__sozluk_liste", "__dosya_oku", "__dosya_yaz", "__dosya_sil",
    "__argumanlar", "__metin_karakter")}

YIĞIN_BOYUTU = 256 * 1024 * 1024    # bss'te ayrılır; dokunulmadıkça bellek harcamaz

ÇALIŞMA_ZAMANI = r"""
# ── çalışma zamanı ──
_start:
    mov [rip+__baslangic_sp], rsp
    call nehir_ana
    xor edi, edi
    mov eax, 60
    syscall

__ham_yaz:                      # rsi = adres, rdx = uzunluk
    mov eax, 1
    mov edi, 1
    syscall
    ret

__satir_sonu:
    lea rsi, [rip+__yeni_satir]
    mov edx, 1
    jmp __ham_yaz

__sayi_basamak:                 # rdi = sayı, rsi = tampon sonu -> rsi = baş, rdx = uzunluk
    mov rax, rdi
    xor r8, r8
    xor r9, r9
    test rax, rax
    jns 1f
    neg rax
    mov r9, 1
1:  mov rcx, 10
2:  xor edx, edx
    div rcx
    add dl, 48
    dec rsi
    mov [rsi], dl
    inc r8
    test rax, rax
    jnz 2b
    test r9, r9
    jz 3f
    dec rsi
    mov byte ptr [rsi], 45
    inc r8
3:  mov rdx, r8
    ret

__sayi_ham:                     # rdi = sayı; satır sonu eklemeden yazar
    push rbp
    mov rbp, rsp
    sub rsp, 32
    mov rsi, rbp
    call __sayi_basamak
    call __ham_yaz
    leave
    ret

__deger_tirnakli:               # rdi = değer, rsi = tür tanımı; metinse tırnak içinde yazar
    cmp qword ptr [rsi], 1
    jne __deger_ham
    push rdi
    lea rsi, [rip+__tirnak]
    mov edx, 1
    call __ham_yaz
    pop rsi
    mov rdx, [rsi-8]
    call __ham_yaz
    lea rsi, [rip+__tirnak]
    mov edx, 1
    jmp __ham_yaz

__deger_ham:                    # rdi = değer, rsi = tür tanımı; satır sonu eklemeden yazar
    mov rax, [rsi]
    test rax, rax               # 0: sayı
    jz __sayi_ham
    cmp rax, 1                  # 1: metin
    jne 1f
    mov rsi, rdi
    mov rdx, [rdi-8]
    jmp __ham_yaz
1:  push rbx
    push r12
    push r13
    mov r12, rdi
    mov r13, rsi
    xor ebx, ebx
    cmp rax, 3
    je 5f
    lea rsi, [rip+__ac]         # 2: liste
    mov edx, 1
    call __ham_yaz
2:  cmp rbx, [r12]
    jae 4f
    test rbx, rbx
    jz 3f
    lea rsi, [rip+__virgul]
    mov edx, 2
    call __ham_yaz
3:  mov rax, [r12+16]
    mov rdi, [rax+rbx*8]
    mov rsi, [r13+8]
    call __deger_tirnakli
    inc rbx
    jmp 2b
4:  lea rsi, [rip+__kapa]
    mov edx, 1
    call __ham_yaz
    jmp 9f
5:  lea rsi, [rip+__sus_ac]     # 3: sözlük
    mov edx, 1
    call __ham_yaz
6:  cmp rbx, [r12]
    jae 8f
    test rbx, rbx
    jz 7f
    lea rsi, [rip+__virgul]
    mov edx, 2
    call __ham_yaz
7:  mov rax, [r12+16]
    mov rdi, [rax+rbx*8]
    mov rsi, [r13+8]
    call __deger_tirnakli
    lea rsi, [rip+__iki_nokta]
    mov edx, 2
    call __ham_yaz
    mov rax, [r12+24]
    mov rdi, [rax+rbx*8]
    mov rsi, [r13+16]
    call __deger_tirnakli
    inc rbx
    jmp 6b
8:  lea rsi, [rip+__sus_kapa]
    mov edx, 1
    call __ham_yaz
9:  pop r13
    pop r12
    pop rbx
    ret

__yaz_deger:                    # rdi = değer, rsi = tür tanımı
    call __deger_ham
    jmp __satir_sonu

__ayir:                         # rdi = bayt sayısı -> rax = adres
    mov rax, [rip+__yigin_uc]
    lea rdx, [rax+rdi]
    lea rcx, [rip+__yigin_son]
    cmp rdx, rcx
    ja __bellek_bitti
    mov [rip+__yigin_uc], rdx
    ret

__liste_yeni:                   # rdi = kapasite (>= 1) -> rax = boş liste
    push rdi
    mov edi, 24
    call __ayir
    push rax
    mov rdi, [rsp+8]
    shl rdi, 3
    call __ayir
    mov rdx, rax
    pop rax
    pop rcx
    mov qword ptr [rax], 0
    mov [rax+8], rcx
    mov [rax+16], rdx
    ret

__liste_ekle:                   # rdi = liste, rsi = değer -> rax = liste
    mov rcx, [rdi]
    cmp rcx, [rdi+8]
    jb 3f
    push rdi                    # dolu: iki katı yer ayır ve kopyala
    push rsi
    mov rdi, [rdi+8]
    shl rdi, 4
    call __ayir
    pop rsi
    pop rdi
    mov r8, [rdi+16]
    mov rcx, [rdi]
    xor edx, edx
1:  cmp rdx, rcx
    jae 2f
    mov r9, [r8+rdx*8]
    mov [rax+rdx*8], r9
    inc rdx
    jmp 1b
2:  mov [rdi+16], rax
    shl qword ptr [rdi+8], 1
3:  mov rcx, [rdi]
    mov rdx, [rdi+16]
    mov [rdx+rcx*8], rsi
    inc qword ptr [rdi]
    mov rax, rdi
    ret

__liste_al:                     # rdi = liste, rsi = dizin -> rax = eleman
    cmp rsi, [rdi]
    jae __dizin_hatasi
    mov rax, [rdi+16]
    mov rax, [rax+rsi*8]
    ret

__liste_koy:                    # rdi = liste, rsi = dizin, rdx = değer
    cmp rsi, [rdi]
    jae __dizin_hatasi
    mov rax, [rdi+16]
    mov [rax+rsi*8], rdx
    ret

__aralik:                       # rdi = baş, rsi = son -> rax = [baş, ..., son-1]
    push rbx
    push r12
    push r13
    mov r12, rdi
    mov r13, rsi
    mov rdi, rsi
    sub rdi, r12
    cmp rdi, 4
    jge 1f
    mov edi, 4
1:  call __liste_yeni
    mov rbx, rax
2:  cmp r12, r13
    jge 3f
    mov rdi, rbx
    mov rsi, r12
    call __liste_ekle
    inc r12
    jmp 2b
3:  mov rax, rbx
    pop r13
    pop r12
    pop rbx
    ret

__metin_yeni:                   # rdi = bayt uzunluğu -> rax = metin (içeriği boş)
    push rdi
    add rdi, 16                 # başlık + baytlar + en az bir sıfır baytı (yeni bellek sıfırdır)
    and rdi, -8
    call __ayir
    pop rcx
    mov [rax], rcx
    add rax, 8
    ret

__metin_birlestir:              # rdi = a, rsi = b -> rax = a + b
    push rbx
    push r12
    push r13
    mov r12, rdi
    mov r13, rsi
    mov rdi, [r12-8]
    add rdi, [r13-8]
    call __metin_yeni
    mov rbx, rax
    mov rdi, rax
    mov rsi, r12
    mov rcx, [r12-8]
    rep movsb
    mov rsi, r13
    mov rcx, [r13-8]
    rep movsb
    mov rax, rbx
    pop r13
    pop r12
    pop rbx
    ret

__metin_karsilastir:            # rdi = a, rsi = b -> rax = -1 / 0 / 1 (sözlük sırası)
    mov rcx, [rdi-8]
    mov rdx, [rsi-8]
    xor r8, r8
1:  cmp r8, rcx
    jae 2f
    cmp r8, rdx
    jae 4f
    movzx eax, byte ptr [rdi+r8]
    movzx r9d, byte ptr [rsi+r8]
    inc r8
    cmp eax, r9d
    je 1b
    jb 3f
4:  mov eax, 1
    ret
2:  cmp rcx, rdx
    je 5f
3:  mov rax, -1
    ret
5:  xor eax, eax
    ret

__metin_uzunluk:                # rdi = metin -> rax = karakter sayısı (UTF-8)
    mov rcx, [rdi-8]
    xor eax, eax
    xor r8, r8
1:  cmp r8, rcx
    jae 2f
    movzx edx, byte ptr [rdi+r8]
    and edx, 0xC0
    cmp edx, 0x80
    setne dl
    movzx edx, dl
    add rax, rdx
    inc r8
    jmp 1b
2:  ret

__metin_al:                     # rdi = metin, rsi = karakter dizini -> rax = o karakter (metin)
    push rbx
    push r12
    mov rcx, [rdi-8]
    xor r8, r8
1:  cmp r8, rcx                 # rsi karakter atla
    jae __dizin_hatasi
    test rsi, rsi
    jz 3f
    inc r8
2:  cmp r8, rcx
    jae 4f
    movzx edx, byte ptr [rdi+r8]
    and edx, 0xC0
    cmp edx, 0x80
    jne 4f
    inc r8
    jmp 2b
4:  dec rsi
    jmp 1b
3:  mov r9, r8                  # karakterin sonunu bul
    inc r9
5:  cmp r9, rcx
    jae 6f
    movzx edx, byte ptr [rdi+r9]
    and edx, 0xC0
    cmp edx, 0x80
    jne 6f
    inc r9
    jmp 5b
6:  lea rbx, [rdi+r8]
    mov r12, r9
    sub r12, r8
    mov rdi, r12
    call __metin_yeni
    mov rdi, rax
    mov rsi, rbx
    mov rcx, r12
    rep movsb
    pop r12
    pop rbx
    ret

__metin_karakter:               # rdi = metin, rsi = bayt konumu -> rax = oradaki karakter (metin),
    push rbx                    #                                  rdx = sonraki karakterin bayt konumu
    push r12
    push r13
    mov rbx, rdi
    mov r12, rsi
    mov rcx, [rbx-8]
    lea r13, [r12+1]
1:  cmp r13, rcx
    jae 2f
    movzx eax, byte ptr [rbx+r13]
    and eax, 0xC0
    cmp eax, 0x80
    jne 2f
    inc r13
    jmp 1b
2:  mov rdi, r13
    sub rdi, r12
    call __metin_yeni
    mov rdi, rax
    lea rsi, [rbx+r12]
    mov rcx, r13
    sub rcx, r12
    rep movsb
    mov rdx, r13
    pop r13
    pop r12
    pop rbx
    ret

__uyar:                         # rdi = metin; stderr'e satır olarak yazar -> rax = metin
    push rdi
    mov rsi, rdi
    mov rdx, [rdi-8]
    call __hata_yaz
    lea rsi, [rip+__yeni_satir]
    mov edx, 1
    call __hata_yaz
    pop rax
    ret

__sayidan_metin:                # rdi = sayı -> rax = metin
    push rbp
    mov rbp, rsp
    sub rsp, 32
    mov rsi, rbp
    call __sayi_basamak
    push rsi
    push rdx
    mov rdi, rdx
    call __metin_yeni
    pop rcx
    pop rsi
    mov rdi, rax
    rep movsb
    leave
    ret

__metinden_sayi:                # rdi = metin -> rax = sayı
    mov rcx, [rdi-8]
    xor eax, eax
    xor r8, r8
    xor r9, r9
    test rcx, rcx
    jz __sayi_hatasi
    cmp byte ptr [rdi], 45
    jne 1f
    mov r9, 1
    inc r8
    cmp r8, rcx
    jae __sayi_hatasi
1:  movzx edx, byte ptr [rdi+r8]
    sub edx, 48
    cmp edx, 9
    ja __sayi_hatasi
    imul rax, rax, 10
    add rax, rdx
    inc r8
    cmp r8, rcx
    jb 1b
    test r9, r9
    jz 2f
    neg rax
2:  ret

__deger_esit:                   # rdi = a, rsi = b, rdx = tür tanımı -> rax = eşitse 1, değilse 0
    mov rax, [rdx]
    test rax, rax               # 0: sayı
    jnz 1f
    cmp rdi, rsi
    sete al
    movzx eax, al
    ret
1:  cmp rax, 1                  # 1: metin
    jne 2f
    call __metin_karsilastir
    test rax, rax
    sete al
    movzx eax, al
    ret
2:  push rbx                    # 2: liste; uzunluklar ve tüm elemanlar eşit olmalı
    push r12
    push r13
    push r14
    mov r12, rdi
    mov r13, rsi
    mov r14, [rdx+8]
    mov rax, [r12]
    cmp rax, [r13]
    jne 5f
    xor ebx, ebx
3:  cmp rbx, [r12]
    jae 4f
    mov rax, [r12+16]
    mov rdi, [rax+rbx*8]
    mov rax, [r13+16]
    mov rsi, [rax+rbx*8]
    mov rdx, r14
    call __deger_esit
    test rax, rax
    jz 5f
    inc rbx
    jmp 3b
4:  mov eax, 1
    jmp 6f
5:  xor eax, eax
6:  pop r14
    pop r13
    pop r12
    pop rbx
    ret

__liste_bul:                    # rdi = liste, rsi = aranan, rdx = eleman tür tanımı -> rax = dizin ya da -1
    push rbx
    push r12
    push r13
    push r14
    mov r12, rdi
    mov r13, rsi
    mov r14, rdx
    xor ebx, ebx
1:  cmp rbx, [r12]
    jae 2f
    mov rax, [r12+16]
    mov rdi, [rax+rbx*8]
    mov rsi, r13
    mov rdx, r14
    call __deger_esit
    test rax, rax
    jnz 3f
    inc rbx
    jmp 1b
2:  mov rbx, -1
3:  mov rax, rbx
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__liste_sil:                    # rdi = liste, rsi = dizin -> rax = silinen eleman
    cmp rsi, [rdi]
    jae __dizin_hatasi
    mov rdx, [rdi+16]
    mov rax, [rdx+rsi*8]
    mov rcx, [rdi]
    dec rcx
    mov [rdi], rcx
1:  cmp rsi, rcx                # sonrakileri bir göz geri kaydır
    jae 2f
    mov r8, [rdx+rsi*8+8]
    mov [rdx+rsi*8], r8
    inc rsi
    jmp 1b
2:  ret

__liste_dilim:                  # rdi = liste, rsi = baş, rdx = son -> rax = [baş, son) elemanlarının yeni listesi
    push rbx
    push r12
    push r13
    push r14
    mov rbx, rdi
    mov r12, rsi
    mov r13, rdx
    test r12, r12               # sınırlar listeye sığdırılır
    jns 1f
    xor r12, r12
1:  cmp r13, [rbx]
    jle 2f
    mov r13, [rbx]
2:  mov rdi, r13
    sub rdi, r12
    cmp rdi, 4
    jge 3f
    mov edi, 4
3:  call __liste_yeni
    mov r14, rax
4:  cmp r12, r13
    jge 5f
    mov rax, [rbx+16]
    mov rsi, [rax+r12*8]
    mov rdi, r14
    call __liste_ekle
    inc r12
    jmp 4b
5:  mov rax, r14
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__liste_birlestir:              # rdi = a, rsi = b -> rax = a + b (yeni liste)
    push rbx
    push r12
    push r13
    push r14
    mov r12, rdi
    mov r13, rsi
    mov rdi, [r12]
    add rdi, [r13]
    cmp rdi, 4
    jge 1f
    mov edi, 4
1:  call __liste_yeni
    mov r14, rax
    xor ebx, ebx
2:  cmp rbx, [r12]
    jae 3f
    mov rax, [r12+16]
    mov rsi, [rax+rbx*8]
    mov rdi, r14
    call __liste_ekle
    inc rbx
    jmp 2b
3:  xor ebx, ebx
4:  cmp rbx, [r13]
    jae 5f
    mov rax, [r13+16]
    mov rsi, [rax+rbx*8]
    mov rdi, r14
    call __liste_ekle
    inc rbx
    jmp 4b
5:  mov rax, r14
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__metin_konum:                  # rdi = metin, rsi = karakter dizini -> rax = bayt konumu (metne sığdırılır)
    mov rcx, [rdi-8]
    xor eax, eax
    test rsi, rsi
    jle 3f
1:  cmp rax, rcx
    jae 3f
    inc rax
2:  cmp rax, rcx
    jae 4f
    movzx edx, byte ptr [rdi+rax]
    and edx, 0xC0
    cmp edx, 0x80
    jne 4f
    inc rax
    jmp 2b
4:  dec rsi
    jnz 1b
3:  ret

__metin_dilim:                  # rdi = metin, rsi = baş, rdx = son (karakter) -> rax = alt metin
    push rbx
    push r12
    push r13
    mov rbx, rdi
    mov r13, rdx
    call __metin_konum
    mov r12, rax
    mov rdi, rbx
    mov rsi, r13
    call __metin_konum
    mov r13, rax
    cmp r13, r12
    jae 1f
    mov r13, r12
1:  sub r13, r12
    mov rdi, r13
    call __metin_yeni
    mov rdi, rax
    lea rsi, [rbx+r12]
    mov rcx, r13
    rep movsb
    pop r13
    pop r12
    pop rbx
    ret

__metin_bul:                    # rdi = metin, rsi = aranan -> rax = ilk geçtiği karakter dizini ya da -1
    push rbx
    mov rcx, [rdi-8]
    mov rdx, [rsi-8]
    xor r8, r8                  # bayt konumu
    xor eax, eax                # karakter dizini
1:  lea r9, [r8+rdx]
    cmp r9, rcx
    ja 5f
    xor r10, r10
2:  cmp r10, rdx
    jae 4f
    lea r9, [rdi+r8]
    movzx r11d, byte ptr [r9+r10]
    movzx ebx, byte ptr [rsi+r10]
    cmp r11d, ebx
    jne 3f
    inc r10
    jmp 2b
3:  movzx r11d, byte ptr [rdi+r8]
    and r11d, 0xC0
    cmp r11d, 0x80
    setne r11b
    movzx r11d, r11b
    add rax, r11
    inc r8
    jmp 1b
4:  pop rbx
    ret
5:  mov rax, -1
    pop rbx
    ret

__bol_parca:                    # rbx = metin, r14 = baş, rsi = son (bayt); parçayı r13 listesine ekler
    sub rsi, r14
    push rsi
    mov rdi, rsi
    call __metin_yeni
    pop rcx
    mov rdi, rax
    lea rsi, [rbx+r14]
    rep movsb
    mov rsi, rax
    mov rdi, r13
    jmp __liste_ekle

__metin_bol:                    # rdi = metin, rsi = ayraç -> rax = parçaların listesi
    push rbx
    push r12
    push r13
    push r14
    push rbp
    mov rbx, rdi
    mov r12, rsi
    mov edi, 4
    call __liste_yeni
    mov r13, rax
    xor r14, r14                # süren parçanın başı
    xor ebp, ebp                # tarama konumu
    cmp qword ptr [r12-8], 0    # boş ayraç: metin tek parça kalır
    je 5f
1:  mov rax, [r12-8]
    add rax, rbp
    cmp rax, [rbx-8]
    ja 5f
    xor ecx, ecx
2:  cmp rcx, [r12-8]
    jae 4f
    lea rax, [rbx+rbp]
    movzx edx, byte ptr [rax+rcx]
    cmp dl, [r12+rcx]
    jne 3f
    inc rcx
    jmp 2b
3:  inc rbp
    jmp 1b
4:  mov rsi, rbp
    call __bol_parca
    add rbp, [r12-8]
    mov r14, rbp
    jmp 1b
5:  mov rsi, [rbx-8]
    call __bol_parca
    mov rax, r13
    pop rbp
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__liste_birles:                 # rdi = metin listesi, rsi = ayraç -> rax = birleşik metin
    push rbx
    push r12
    push r13
    push r14
    mov r12, rdi
    mov r13, rsi
    xor edi, edi                # toplam bayt uzunluğu
    xor ebx, ebx
    mov rdx, [r12+16]
1:  cmp rbx, [r12]
    jae 3f
    mov rax, [rdx+rbx*8]
    add rdi, [rax-8]
    test rbx, rbx
    jz 2f
    add rdi, [r13-8]
2:  inc rbx
    jmp 1b
3:  call __metin_yeni
    mov r14, rax
    mov rdi, rax
    xor ebx, ebx
4:  cmp rbx, [r12]
    jae 6f
    test rbx, rbx
    jz 5f
    mov rsi, r13
    mov rcx, [r13-8]
    rep movsb
5:  mov rax, [r12+16]
    mov rsi, [rax+rbx*8]
    mov rcx, [rsi-8]
    rep movsb
    inc rbx
    jmp 4b
6:  mov rax, r14
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__sozluk_yeni:                  # -> rax = boş sözlük
    mov edi, 56
    call __ayir
    push rax
    mov edi, 64
    call __ayir
    mov rdx, [rsp]
    mov [rdx+16], rax
    mov edi, 64
    call __ayir
    mov rdx, [rsp]
    mov [rdx+24], rax
    mov edi, 128
    call __ayir                 # yeni ayrılan bellek sıfırdır: tablo boş başlar
    pop rdx
    mov [rdx+40], rax
    mov qword ptr [rdx], 0
    mov qword ptr [rdx+8], 8
    mov qword ptr [rdx+32], 16
    mov rax, rdx
    ret

__sozluk_ara:                   # rdi = sözlük, rsi = anahtar, rdx = anahtar türü (0 sayı, 1 metin)
    push rbx                    # -> rax = girdinin dizini ya da -1; r8 = bulunduğu / ilk boş tablo gözü
    push r12
    push r13
    push r14
    push rbp
    mov rbx, rdi
    mov r12, rsi
    mov r13, rdx
    test r13, r13
    jnz 1f
    mov rax, r12                # sayı: çarpımsal hash
    mov rcx, 0x9E3779B97F4A7C15
    imul rax, rcx
    mov rcx, rax
    shr rcx, 32
    xor rax, rcx
    jmp 3f
1:  mov rax, 0xCBF29CE484222325 # metin: FNV-1a
    mov rcx, [r12-8]
    xor edx, edx
    mov r8, 0x100000001B3
2:  cmp rdx, rcx
    jae 3f
    movzx r9d, byte ptr [r12+rdx]
    xor rax, r9
    imul rax, r8
    inc rdx
    jmp 2b
3:  mov r14, [rbx+32]
    dec r14                     # tablo boyu 2'nin kuvveti: maske
    and rax, r14
    mov rbp, rax
4:  mov rax, [rbx+40]
    mov rax, [rax+rbp*8]
    test rax, rax
    jz 7f
    dec rax
    mov rcx, [rbx+16]
    mov rdi, [rcx+rax*8]
    test r13, r13
    jnz 5f
    cmp rdi, r12
    je 8f
    jmp 6f
5:  push rax
    mov rsi, r12
    call __metin_karsilastir
    mov rcx, rax
    pop rax
    test rcx, rcx
    jz 8f
6:  inc rbp                     # doğrusal yoklama
    and rbp, r14
    jmp 4b
7:  mov rax, -1
8:  mov r8, rbp
    pop rbp
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__sozluk_dizinle:               # rdi = sözlük, rsi = anahtar türü; tabloyu baştan kurar
    push rbx
    push r12
    push r13
    mov rbx, rdi
    mov r13, rsi
    mov rdi, [rbx+40]
    mov rcx, [rbx+32]
    xor eax, eax
    rep stosq
    xor r12, r12
1:  cmp r12, [rbx]
    jae 2f
    mov rdi, rbx
    mov rax, [rbx+16]
    mov rsi, [rax+r12*8]
    mov rdx, r13
    call __sozluk_ara
    inc r12
    mov rax, [rbx+40]
    mov [rax+r8*8], r12
    jmp 1b
2:  pop r13
    pop r12
    pop rbx
    ret

__sozluk_koy:                   # rdi = sözlük, rsi = anahtar, rdx = anahtar türü, rcx = değer -> rax = sözlük
    push rbx
    push r12
    push r13
    push r14
    mov rbx, rdi
    mov r12, rsi
    mov r13, rdx
    mov r14, rcx
    mov rax, [rbx]              # girdi dizileri doluysa iki katına çıkar
    cmp rax, [rbx+8]
    jb 1f
    mov rdi, [rbx+8]
    shl rdi, 4
    call __ayir
    mov rdi, rax
    mov rsi, [rbx+16]
    mov rcx, [rbx]
    rep movsq
    mov [rbx+16], rax
    mov rdi, [rbx+8]
    shl rdi, 4
    call __ayir
    mov rdi, rax
    mov rsi, [rbx+24]
    mov rcx, [rbx]
    rep movsq
    mov [rbx+24], rax
    shl qword ptr [rbx+8], 1
1:  mov rax, [rbx]              # tablo yarıdan fazla dolacaksa iki katına çıkar
    inc rax
    shl rax, 1
    cmp rax, [rbx+32]
    jbe 2f
    mov rdi, [rbx+32]
    shl rdi, 4
    call __ayir
    mov [rbx+40], rax
    shl qword ptr [rbx+32], 1
    mov rdi, rbx
    mov rsi, r13
    call __sozluk_dizinle
2:  mov rdi, rbx
    mov rsi, r12
    mov rdx, r13
    call __sozluk_ara
    test rax, rax
    js 3f
    mov rcx, [rbx+24]           # anahtar var: değeri güncelle
    mov [rcx+rax*8], r14
    jmp 4f
3:  mov rax, [rbx]              # yeni girdi
    mov rcx, [rbx+16]
    mov [rcx+rax*8], r12
    mov rcx, [rbx+24]
    mov [rcx+rax*8], r14
    inc rax
    mov [rbx], rax
    mov rcx, [rbx+40]
    mov [rcx+r8*8], rax
4:  mov rax, rbx
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__sozluk_al:                    # rdi = sözlük, rsi = anahtar, rdx = anahtar türü -> rax = değer
    push rdi
    call __sozluk_ara
    pop rdi
    test rax, rax
    js __anahtar_hatasi
    mov rcx, [rdi+24]
    mov rax, [rcx+rax*8]
    ret

__sozluk_sil:                   # rdi = sözlük, rsi = anahtar, rdx = anahtar türü -> rax = silinen değer
    push rbx
    push r12
    push r13
    mov rbx, rdi
    mov r13, rdx
    call __sozluk_ara
    test rax, rax
    js __anahtar_hatasi
    mov rcx, [rbx+24]
    mov r12, [rcx+rax*8]
    mov rsi, [rbx+16]
    mov rdx, [rbx]
    dec rdx
    mov [rbx], rdx
1:  cmp rax, rdx                # sonraki girdileri bir göz geri kaydır
    jae 2f
    mov r8, [rsi+rax*8+8]
    mov [rsi+rax*8], r8
    mov r8, [rcx+rax*8+8]
    mov [rcx+rax*8], r8
    inc rax
    jmp 1b
2:  mov rdi, rbx
    mov rsi, r13
    call __sozluk_dizinle
    mov rax, r12
    pop r13
    pop r12
    pop rbx
    ret

__sozluk_liste:                 # rdi = sözlük, rsi = 16 (anahtarlar) ya da 24 (değerler) -> rax = yeni liste
    push rbx
    push r12
    push r13
    mov rbx, rdi
    mov r13, rsi
    mov rdi, [rbx]
    cmp rdi, 4
    jge 1f
    mov edi, 4
1:  call __liste_yeni
    mov r12, rax
    mov rsi, [rbx+r13]
    mov rdi, [r12+16]
    mov rcx, [rbx]
    mov [r12], rcx
    rep movsq
    mov rax, r12
    pop r13
    pop r12
    pop rbx
    ret

__dosya_oku:                    # rdi = yol -> rax = dosyanın tüm içeriği (metin)
    push rbx
    push r12
    push r13
    mov [rip+__h_ek], rdi
    mov eax, 2                  # open(yol, O_RDONLY)
    xor esi, esi
    xor edx, edx
    syscall
    test rax, rax
    js __dosya_hatasi
    mov r13, rax
    mov rbx, [rip+__yigin_uc]   # içerik doğrudan yığının ucuna okunur
    add rbx, 8
    xor r12, r12
1:  lea rsi, [rbx+r12]
    lea rdx, [rip+__yigin_son]
    sub rdx, rsi
    jbe __bellek_bitti
    mov rdi, r13
    xor eax, eax                # read
    syscall
    test rax, rax
    js __dosya_hatasi
    jz 2f
    add r12, rax
    jmp 1b
2:  mov rdi, r13
    mov eax, 3                  # close
    syscall
    mov [rbx-8], r12
    lea rax, [rbx+r12+8]
    and rax, -8
    mov [rip+__yigin_uc], rax
    mov qword ptr [rip+__h_ek], 0
    mov rax, rbx
    pop r13
    pop r12
    pop rbx
    ret

__dosya_yaz:                    # rdi = içerik, rsi = yol, rdx = open bayrakları -> rax = içerik
    push rbx
    push r12
    push r13
    mov rbx, rdi
    mov [rip+__h_ek], rsi
    mov rdi, rsi
    mov rsi, rdx
    mov edx, 420                # 0644
    mov eax, 2
    syscall
    test rax, rax
    js __dosya_hatasi
    mov r13, rax
    xor r12, r12
1:  mov rdx, [rbx-8]
    sub rdx, r12
    jz 2f
    lea rsi, [rbx+r12]
    mov rdi, r13
    mov eax, 1
    syscall
    test rax, rax
    js __dosya_hatasi
    add r12, rax
    jmp 1b
2:  mov rdi, r13
    mov eax, 3
    syscall
    mov qword ptr [rip+__h_ek], 0
    mov rax, rbx
    pop r13
    pop r12
    pop rbx
    ret

__dosya_var:                    # rdi = yol -> rax = dosya varsa 1, yoksa 0
    mov eax, 21                 # access(yol, F_OK)
    xor esi, esi
    syscall
    test rax, rax
    sete al
    movzx eax, al
    ret

__dosya_sil:                    # rdi = yol
    mov [rip+__h_ek], rdi
    mov eax, 87                 # unlink
    syscall
    test rax, rax
    js __dosya_hatasi
    mov qword ptr [rip+__h_ek], 0
    xor eax, eax
    ret

__argumanlar:                   # -> rax = komut satırı argümanlarının listesi (program adı hariç)
    push rbx
    push r12
    push r13
    push r14
    mov r12, [rip+__baslangic_sp]
    mov r13, [r12]
    mov edi, 4
    call __liste_yeni
    mov r14, rax
    mov ebx, 1
1:  cmp rbx, r13
    jae 4f
    mov rsi, [r12+8+rbx*8]
    xor ecx, ecx
2:  cmp byte ptr [rsi+rcx], 0
    je 3f
    inc rcx
    jmp 2b
3:  push rsi
    push rcx
    mov rdi, rcx
    call __metin_yeni
    pop rcx
    pop rsi
    mov rdi, rax
    rep movsb
    mov rsi, rax
    mov rdi, r14
    call __liste_ekle
    inc rbx
    jmp 1b
4:  mov rax, r14
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__girdi_doldur:                 # tamponu stdin'den doldurur -> rax = 1, girdi bittiyse 0
    xor eax, eax
    xor edi, edi
    lea rsi, [rip+__g_tampon]
    mov edx, 65536
    syscall
    test rax, rax
    jle 1f
    mov [rip+__g_son], rax
    mov qword ptr [rip+__g_konum], 0
    mov eax, 1
    ret
1:  xor eax, eax
    ret

__girdi_var:                    # -> rax = okunacak girdi kaldıysa 1, yoksa 0
    mov rax, [rip+__g_konum]
    cmp rax, [rip+__g_son]
    jae __girdi_doldur
    mov eax, 1
    ret

__oku:                          # -> rax = bir satır (satır sonu olmadan); girdi bittiyse ""
    push rbx
    push r12
    mov rbx, [rip+__yigin_uc]   # metin doğrudan yığının ucunda büyütülür
    add rbx, 8
    xor r12, r12
1:  mov rax, [rip+__g_konum]
    cmp rax, [rip+__g_son]
    jb 2f
    call __girdi_doldur
    test rax, rax
    jz 3f
    mov rax, [rip+__g_konum]
2:  lea rcx, [rip+__g_tampon]
    movzx edx, byte ptr [rcx+rax]
    inc rax
    mov [rip+__g_konum], rax
    cmp edx, 10
    je 3f
    lea rcx, [rbx+r12]
    lea rax, [rip+__yigin_son]
    cmp rcx, rax
    jae __bellek_bitti
    mov [rcx], dl
    inc r12
    jmp 1b
3:  mov [rbx-8], r12
    lea rax, [rbx+r12+8]
    and rax, -8
    mov [rip+__yigin_uc], rax
    mov rax, rbx
    pop r12
    pop rbx
    ret

__sifira_bolme:
    lea rsi, [rip+__h_sifir]
    mov edx, __h_sifir_son - __h_sifir
    jmp __hata
__dizin_hatasi:
    lea rsi, [rip+__h_dizin]
    mov edx, __h_dizin_son - __h_dizin
    jmp __hata
__dosya_hatasi:                 # rax = -errno; yol __h_ek'te
    lea rsi, [rip+__h_yok]
    mov edx, __h_yok_son - __h_yok
    cmp rax, -2                 # ENOENT
    je __hata
    lea rsi, [rip+__h_izin]
    mov edx, __h_izin_son - __h_izin
    cmp rax, -13                # EACCES
    je __hata
    lea rsi, [rip+__h_dizin_yol]
    mov edx, __h_dizin_yol_son - __h_dizin_yol
    cmp rax, -21                # EISDIR
    je __hata
    lea rsi, [rip+__h_dosya_genel]
    mov edx, __h_dosya_genel_son - __h_dosya_genel
    jmp __hata
__anahtar_hatasi:
    lea rsi, [rip+__h_anahtar]
    mov edx, __h_anahtar_son - __h_anahtar
    jmp __hata
__sayi_hatasi:
    lea rsi, [rip+__h_sayi]
    mov edx, __h_sayi_son - __h_sayi
    jmp __hata
__bellek_bitti:
    lea rsi, [rip+__h_bellek]
    mov edx, __h_bellek_son - __h_bellek
__hata:                         # rsi = mesaj, rdx = uzunluk, r15 = kaynak satırı
    push rdx                    # stderr'e "dosya:satır: çalışma hatası: mesaj" yazıp 1 ile çıkar
    push rsi
    lea rsi, [rip+__h_dosya]
    mov edx, __h_dosya_son - __h_dosya
    call __hata_yaz
    sub rsp, 32
    mov rdi, r15
    lea rsi, [rsp+32]
    call __sayi_basamak
    call __hata_yaz
    add rsp, 32
    lea rsi, [rip+__h_ara]
    mov edx, __h_ara_son - __h_ara
    call __hata_yaz
    pop rsi
    pop rdx
    call __hata_yaz
    mov rax, [rip+__h_ek]       # varsa ek bilgi: ": dosya yolu"
    test rax, rax
    jz 1f
    push rax
    lea rsi, [rip+__iki_nokta]
    mov edx, 2
    call __hata_yaz
    pop rsi
    mov rdx, [rsi-8]
    call __hata_yaz
1:  lea rsi, [rip+__yeni_satir]
    mov edx, 1
    call __hata_yaz
    mov edi, 1
    mov eax, 60
    syscall
__hata_yaz:
    mov eax, 1
    mov edi, 2
    syscall
    ret

    .section .rodata
__yeni_satir: .byte 10
__ac: .ascii "["
__kapa: .ascii "]"
__virgul: .ascii ", "
__tirnak: .byte 34
__sus_ac: .ascii "{"
__sus_kapa: .ascii "}"
__iki_nokta: .ascii ": "
__h_ara: .ascii ": çalışma hatası: "
__h_ara_son:
__h_sifir: .ascii "sıfıra bölme"
__h_sifir_son:
__h_dizin: .ascii "dizin sınırların dışında"
__h_dizin_son:
__h_sayi: .ascii "metin sayıya çevrilemiyor"
__h_sayi_son:
__h_anahtar: .ascii "anahtar sözlükte yok"
__h_anahtar_son:
__h_yok: .ascii "dosya bulunamadı"
__h_yok_son:
__h_izin: .ascii "dosyaya erişim izni yok"
__h_izin_son:
__h_dizin_yol: .ascii "bu bir dizin, dosya değil"
__h_dizin_yol_son:
__h_dosya_genel: .ascii "dosya işlemi başarısız"
__h_dosya_genel_son:
__h_bellek: .ascii "bellek tükendi"
__h_bellek_son:

    .section .data
__yigin_uc: .quad __yigin

    .section .bss
    .balign 16
__yigin: .skip YIGIN_BOYUTU
__yigin_son:
    .skip 64                    # __oku'nun başlık ve yuvarlama payı
__g_tampon: .skip 65536
__baslangic_sp: .skip 8         # süreç başlarken yığın: argc, argv...
__h_ek: .skip 8                 # hata mesajına eklenecek metin (dosya yolu) ya da 0
__g_konum: .skip 8
__g_son: .skip 8
""".replace("YIGIN_BOYUTU", str(YIĞIN_BOYUTU))


class KodÜretici:
    def __init__(self, deyimler, işlevler, dosya_adı="<girdi>"):
        self.dosya_adı = dosya_adı
        self.konum = 0            # o anda derlenen düğümün satırı
        self.deyimler = deyimler
        self.işlevler = işlevler
        # Her işlev için: etiket, parametre türleri (ilk çağrıda belirlenir),
        # dönüş türü, ve özyineleme sırasında dönüş türü varsayıldı mı.
        self.bilgi = {ad: {"etiket": f"f{i}", "türler": None, "dönüş": None,
                           "varsayım": False, "bitti": False}
                      for i, ad in enumerate(işlevler)}
        # Değişken kayıtları: [yer, tür|None, ilk atamanın konumu, okundu mu]
        self.küreseller = {}      # ad -> kayıt (yer = etiket)
        self.metinler = []        # bayt dizileri
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

    def yaz(self, satır):
        if satır in RİSKLİ:
            self.çıktı.append(f"    mov r15d, {int(self.konum)}")
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

        self.okunmayanları_bildir(self.küreseller)
        for ad, b in self.bilgi.items():
            if b["türler"] is None:
                self.uyarılar.append((self.işlevler[ad][2],
                                      f"'{ad}' işlevi hiç çağrılmıyor; derlenmedi", None))
        self.uyarılar.sort(key=lambda u: int(u[0]))

        baş = [".intel_syntax noprefix", ".global _start", ".section .text"]
        son = [ÇALIŞMA_ZAMANI, "    .section .rodata",
               "__h_dosya: .byte " + ", ".join(str(b) for b in (self.dosya_adı + ":").encode("utf-8")),
               "__h_dosya_son:"]
        if self.metinler:
            son.append("    .section .rodata")
            for i, veri in enumerate(self.metinler):
                son.append("    .balign 8")
                son.append(f"    .quad {len(veri)}")
                son.append(f"m{i}:")
                son.append("    .byte " + ", ".join(str(b) for b in veri + b"\0"))
        if self.küreseller:
            son.append("    .section .bss")
            for ad, kayıt in self.küreseller.items():
                son.append(f"{kayıt[0]}: .skip 8    # {ad}")
        kod = [f"    lea {x.yazmaç}, [rip+{self.tür_etiketi(x.tür)}]"
               if isinstance(x, TürKoduSatırı) else x for x in self.çıktı + self.işlev_kodu]
        if self.tür_tanımları:
            son += ["    .section .rodata", "    .balign 8"] + self.tür_tanımları
        return "\n".join(baş + kod + son) + "\n"

    def tür_etiketi(self, tür):
        """Türün çalışma zamanı tanımını (gerekirse üreterek) verir. Derlemenin
        sonunda hâlâ bilinmeyen bir tür yalnızca boş kaplarda olabilir; sayı sayılır."""
        tür = bilinen(tür)
        if isinstance(tür, (Liste, Sözlük)):
            alt = [self.tür_etiketi(p) for p in tür.parametreler()]
            anahtar = (2 if isinstance(tür, Liste) else 3, *alt)
        else:
            anahtar = (1 if tür == "metin" else 0,)
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
                    and h[1] not in YERLEŞİKLER:
                küresel(h[1])
            elif h[0] == "eğer":
                self.küreselleri_topla(h[1])
                self.küreselleri_topla(h[2] or [])
            elif h[0] == "iken":
                self.küreselleri_topla(h[1])
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
        n = len(parametreler)
        saklanan = (self.çıktı, self.geçerli, self.yereller, self.yerel_sayısı,
                    self.döngüler, self.çatal_derinliği)
        # Argümanlar soldan sağa itilir: ilk argüman en derinde durur.
        self.yereller = {p: [16 + 8 * (n - 1 - i), b["türler"][i], None, True]
                         for i, p in enumerate(parametreler)}
        self.çıktı, self.geçerli, self.yerel_sayısı = [], ad, 0
        self.döngüler, self.çatal_derinliği = [], 0
        for d in gövde:
            self.deyim(d)
        gövde_kodu, yerel_sayısı = self.çıktı, self.yerel_sayısı
        self.okunmayanları_bildir(self.yereller)
        (self.çıktı, self.geçerli, self.yereller, self.yerel_sayısı,
         self.döngüler, self.çatal_derinliği) = saklanan

        if b["dönüş"] is None:
            b["dönüş"] = "sayı"      # hiç döndür yok: işlev 0 döndürür
        if b["varsayım"] and b["dönüş"] != "sayı":
            raise NehirHatası(f"özyinelemeli '{ad}' işlevinin dönüş türü ilk kullanımda "
                              f"sayı varsayıldı ama {b['dönüş']} döndürüyor", satır)
        b["bitti"] = True

        k = self.işlev_kodu
        k.append(f"{b['etiket']}:    # işlev {ad}({', '.join(map(str, b['türler']))}) -> {b['dönüş']}")
        k.append("    push rbp")
        k.append("    mov rbp, rsp")
        if yerel_sayısı:
            k.append(f"    sub rsp, {8 * yerel_sayısı}")
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
                if tür.anahtar is None:
                    raise NehirHatası(BOŞ_SÖZLÜK_HATASI, satır)
                self.yaz("mov rdi, rax")
                self.yaz("mov esi, 16")
                self.yaz("call __sozluk_liste")
                tür = Liste(tür.anahtar)
            if not isinstance(tür, Liste):
                raise NehirHatası(f"'her' içine bir liste, sözlük ya da metin akmalı, {tür} bulundu", satır)
            if tür.eleman is None:
                raise NehirHatası(BOŞ_LİSTE_HATASI, satır)
            self.yaz("push rax")                 # [rsp+8] = liste
            self.yaz("push 0")                   # [rsp]   = dizin
            self.etiket_koy(baş)
            self.yaz("mov rsi, [rsp]")
            self.yaz("mov rdi, [rsp+8]")
            self.yaz("cmp rsi, [rdi]")
            self.yaz(f"jge {son}")
            self.yaz("call __liste_al")
            self.ata(h[1], tür.eleman, satır)
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
        # tip == "ad": işlevse akan değer ilk argüman olur, değilse değişkene atanır
        _, ad, argümanlar, _ = h
        if ad in self.işlevler or ad in YERLEŞİKLER:
            self.yaz("push rax")
            return self.çağır(ad, argümanlar or [], satır, akan=tür)
        if argümanlar is not None:
            raise self.işlev_yok(ad, satır)
        self.ata(ad, tür, satır)
        return tür

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
                           benzerler(ad, list(self.işlevler) + list(YERLEŞİKLER)))

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
        kayıt, adres = self.değişken_kaydı(ad)
        if kayıt is None:       # işlev içinde ilk kez atanan ad: yeni yerel
            self.yerel_sayısı += 1
            self.yereller[ad] = [-8 * self.yerel_sayısı, None, None, False]
            kayıt, adres = self.değişken_kaydı(ad)
        if kayıt[1] is None:
            kayıt[1], kayıt[2] = tür, satır
        elif not birleştir(kayıt[1], tür):
            raise NehirHatası(f"'{ad}' değişkeni {kayıt[1]} türünde; {tür} atanamaz", satır)
        self.yaz(f"mov {adres}, rax")

    def çağır(self, ad, argümanlar, satır, akan=None):
        """Argümanları yığına iter ve işlevi çağırır. `akan` verilmişse akıştan
        gelen değer çağıran tarafından zaten itilmiştir ve ilk argümandır."""
        türler = [akan] if akan else []
        for a in argümanlar:
            türler.append(self.ifade(a))
            self.yaz("push rax")
        if ad in YERLEŞİKLER:
            return self.yerleşik(YERLEŞİKLER[ad], ad, türler, satır)
        if ad not in self.işlevler:
            raise self.işlev_yok(ad, satır)

        b = self.bilgi[ad]
        beklenen = len(self.işlevler[ad][0])
        if len(türler) != beklenen:
            raise NehirHatası(f"'{ad}' işlevi {beklenen} argüman bekliyor, {len(türler)} verildi", satır,
                              f"tanımı: {ad}({', '.join(self.işlevler[ad][0])})"
                              + ("; akıştan gelen değer ilk argüman sayılır" if akan else ""))
        if b["türler"] is None:
            b["türler"] = türler
            self.işlevi_derle(ad)
        elif not all(birleştir(x, y) for x, y in zip(b["türler"], türler)):
            raise NehirHatası(f"'{ad}' işlevi ({', '.join(map(str, b['türler']))}) ile çağrılmıştı; "
                              f"şimdi ({', '.join(map(str, türler))}) veriliyor", satır)
        self.yaz(f"call {b['etiket']}")
        if türler:
            self.yaz(f"add rsp, {8 * len(türler)}")
        if b["dönüş"] is None:      # özyineleme: işlev hâlâ derleniyor
            b["varsayım"] = True
            return "sayı"
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
            self.yaz("mov eax, 60")
            self.yaz("syscall")
            return "sayı"
        if asıl == "girdi_var":
            if türler:
                yanlış("argümansız")
            self.yaz("call __girdi_var")
            return "sayı"
        if asıl == "metne":
            if türler not in (["sayı"], ["metin"]):
                yanlış("sayı")
            if türler[0] == "sayı":
                self.yaz("pop rdi")
                self.yaz("call __sayidan_metin")
            else:
                self.yaz("pop rax")
            return "metin"
        if asıl == "sayıya":
            if türler not in (["sayı"], ["metin"]):
                yanlış("metin")
            if türler[0] == "metin":
                self.yaz("pop rdi")
                self.yaz("call __metinden_sayi")
            else:
                self.yaz("pop rax")
            return "sayı"
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
        if isinstance(tür, TürDeğişkeni):   # türü bilinmeyen değer burada sayı olarak kullanılıyor
            tür.bağ = "sayı"
            return
        if tür != "sayı":
            raise NehirHatası(f"{ne} sayı olmalı, {tür} bulundu", satır)

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
                if e[1] in self.işlevler or e[1] in YERLEŞİKLER:
                    raise NehirHatası(f"'{e[1]}' bir işlev; burada değer olarak kullanılmış", satır,
                                      f"çağırmak için: {e[1]}(...)   ya da   değer -> {e[1]}")
                raise NehirHatası(f"'{e[1]}' adında bir değişken yok", satır,
                                  benzerler(e[1], self.bilinen_değişkenler()))
            kayıt[3] = True
            self.yaz(f"mov rax, {adres}")
            return kayıt[1]
        if tip == "çağrı":
            return self.çağır(e[1], e[2], satır)
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
            self.sayı_olmalı(self.ifade(e[2]), f"'{e[1]}' işlecinin işleneni", satır)
            if e[1] == "-":
                self.yaz("neg rax")
            else:
                self.yaz("test rax, rax")
                self.yaz("sete al")
                self.yaz("movzx eax, al")
            return "sayı"
        return self.ikili(e)

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
        if "metin" in (sol_türü, sağ_türü) and "sayı" in (sol_türü, sağ_türü) and iş == "+":
            raise NehirHatası("metin ile sayı doğrudan toplanamaz", satır,
                              "sayıyı önce metne çevirin:  \"a\" + metne(5)")
        self.sayı_olmalı(sol_türü, f"'{iş}' işlecinin sol tarafı", satır)
        self.sayı_olmalı(sağ_türü, f"'{iş}' işlecinin sağ tarafı", satır)
        if iş == "+":
            self.yaz("add rax, rcx")
        elif iş == "-":
            self.yaz("sub rax, rcx")
        elif iş == "*":
            self.yaz("imul rax, rcx")
        elif iş in ("/", "%"):
            self.yaz("test rcx, rcx")
            self.yaz("jz __sifira_bolme")
            self.yaz("cqo")
            self.yaz("idiv rcx")
            if iş == "%":
                self.yaz("mov rax, rdx")
        else:
            self.yaz("cmp rax, rcx")
            self.yaz(f"{KARŞILAŞTIRMA[iş]} al")
            self.yaz("movzx eax, al")
        return "sayı"


# ───────────────────────────── Sürücü ─────────────────────────────

def derle(kaynak, dosya_adı="<girdi>"):
    """Nehir kaynak metnini (assembly metni, uyarılar) ikilisine çevirir."""
    ayrıştırıcı = Ayrıştırıcı(sözcükle(kaynak))
    deyimler = ayrıştırıcı.program()
    üretici = KodÜretici(deyimler, ayrıştırıcı.işlevler, dosya_adı)
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


def bildir(dosya, kaynak, düzey, mesaj, konum=None, ipucu=None):
    """Hata ya da uyarıyı, kaynak satırı ve altı çizili yeriyle stderr'e yazar:

        dosya:3:5: hata: 'x' adında bir değişken yok
            3 | y + x -> yazdır
              |     ^
              = ipucu: 'xs' mi demek istediniz?
    """
    renkli = sys.stderr.isatty() and "NO_COLOR" not in os.environ
    def boya(metin, kod):
        return f"\033[{kod}m{metin}\033[0m" if renkli else metin

    renk = "1;31" if düzey == "hata" else "1;33"
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

  -o <ad>            çıktı dosyasının adı (varsayılan: kaynak dosya adı, uzantısız)
  --asm              yalnızca assembly (.s) üret, derlemeyi orada bırak
  --çalıştır, --run  derledikten sonra programı çalıştır
  --sözcükler        derlemeden yalnızca sözcükleri dök
  -- <argümanlar>    --çalıştır ile birlikte: sonrası programa argüman olarak verilir
"""


def ana(argv):
    girdi, çıktı, yalnız_asm, çalıştır, yalnız_sözcükler = None, None, False, False, False
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
        elif a in ("--sözcükler", "--sozcukler", "--tokens"):
            yalnız_sözcükler = True
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

    kaynak = None
    try:
        with open(girdi, encoding="utf-8") as f:
            kaynak = f.read()
        if yalnız_sözcükler:
            sys.stdout.write(sözcük_dökümü(kaynak))
            return 0
        asm, uyarılar = derle(kaynak, girdi)
    except OSError as h:
        bildir(girdi, None, "hata", f"dosya okunamadı: {h.strerror}")
        return 1
    except UnicodeDecodeError:
        bildir(girdi, None, "hata", "dosya geçerli UTF-8 değil")
        return 1
    except NehirHatası as h:
        bildir(girdi, kaynak, "hata", h.mesaj, h.satır, h.ipucu)
        return 1
    for satır, mesaj, ipucu in uyarılar:
        bildir(girdi, kaynak, "uyarı", mesaj, satır, ipucu)

    kök = çıktı or os.path.splitext(girdi)[0]
    if yalnız_asm:
        with open(çıktı or kök + ".s", "w", encoding="utf-8") as f:
            f.write(asm)
        return 0

    nesne = kök + ".o"
    try:
        subprocess.run(["as", "-o", nesne, "-"], input=asm.encode("utf-8"), check=True)
        subprocess.run(["ld", "-o", kök, nesne], check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as h:
        sys.stderr.write(f"hata: birleştirme/bağlama başarısız: {h}\n")
        return 1
    finally:
        if os.path.exists(nesne):
            os.remove(nesne)

    if çalıştır:
        return subprocess.run([os.path.abspath(kök)] + program_argümanları).returncode
    return 0


if __name__ == "__main__":
    sys.exit(ana(sys.argv[1:]))
