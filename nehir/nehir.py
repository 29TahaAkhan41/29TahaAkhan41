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
    "oku": "oku", "read": "oku",
    "girdi_var": "girdi_var", "has_input": "girdi_var",
}

İŞLEÇLER = ["->", "→", "==", "!=", "<=", ">=",
            "+", "-", "*", "/", "%", "<", ">", "(", ")", "{", "}", "[", "]", ",", "|"]

KAÇIŞLAR = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


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
                                          "geçerli olanlar: \\n  \\t  \\\"  \\\\")
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
#   ("tekli", işleç, ifade, satır)    ("ikili", işleç, sol, sağ, satır)
#   ("akış", kaynak_ifade, [hedefler], satır)
#   ("dur", satır)  ("devam", satır)              döngüden çık / sonraki tura geç
#
# Hedefler:
#   ("yazdır", satır)  ("döndür", satır)  ("ad", ad, argümanlar|None, satır)
#   ("eleman", ad, dizin_ifadesi, satır)          değer -> liste[dizin]
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
                self.al("İŞLEÇ")
                dizin = self.ifade()
                self.bekle("İŞLEÇ", "]")
                return ("eleman", s.değer, dizin, s.satır)
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
#   metin  baytların adresi (uzunluk 8 bayt öncesinde durur)
#   liste  {uzunluk, kapasite, veri adresi} başlığının adresi; elemanlar da 64 bitlik
#          değerlerdir (sayı, metin ya da başka listeler)
# Türler derleme anında izlenir. İşlevlerin parametre türleri ilk çağrıdan
# çıkarılır; bu yüzden işlevler ilk çağrıldıkları anda derlenir.

class Liste:
    """Liste türü. Eleman türü baştan bilinmeyebilir (`[]`); sonradan öğrenilince
    aynı listeye bakan her yer birlikte güncellensin diye türler birbirine bağlanır."""

    def __init__(self, eleman=None):
        self._eleman = eleman
        self.bağ = None

    def kök(self):
        t = self
        while t.bağ is not None:
            t = t.bağ
        return t

    @property
    def eleman(self):
        return self.kök()._eleman

    def __str__(self):
        return "boş liste" if self.eleman is None else f"{self.eleman} listesi"


def içerir(tür, hedef):
    if not isinstance(tür, Liste):
        return False
    tür = tür.kök()
    return tür is hedef or içerir(tür._eleman, hedef)


def birleştir(a, b):
    """İki türü eşitlemeye çalışır; bilinmeyen eleman türlerini doldurur."""
    if isinstance(a, Liste) != isinstance(b, Liste):
        return False
    if not isinstance(a, Liste):
        return a == b
    a, b = a.kök(), b.kök()
    if a is b:
        return True
    if a._eleman is None or b._eleman is None:
        if a._eleman is not None:
            a, b = b, a
        if içerir(b, a):        # bir liste kendi elemanı olamaz
            return False
        a.bağ = b
        return True
    if birleştir(a._eleman, b._eleman):
        a.bağ = b
        return True
    return False


def tür_kodu(tür):
    """Çalışma zamanındaki yazdırma kodu: 0 sayı, 1 metin, k+2 = k kodlu elemanların listesi."""
    if tür == "metin":
        return 1
    if isinstance(tür, Liste):
        return 2 + tür_kodu(tür.eleman)
    return 0


class TürKoduSatırı:
    """Yazdırılan listenin eleman türü sonradan belli olabileceği için
    tür kodunu yükleyen satır ancak derlemenin sonunda metne çevrilir."""

    def __init__(self, tür):
        self.tür = tür

    def __str__(self):
        return f"    mov esi, {tür_kodu(self.tür)}"


KARŞILAŞTIRMA = {"==": "sete", "!=": "setne", "<": "setl", ">": "setg", "<=": "setle", ">=": "setge"}

BOŞ_LİSTE_HATASI = ("bu listenin eleman türü henüz belli değil; "
                    "önce içine bir eleman akmalı")

# Hata verebilen çalışma zamanı işlemleri; öncesinde r15'e kaynak satırı yüklenir.
RİSKLİ = {"jz __sifira_bolme"} | {"call " + ad for ad in (
    "__liste_al", "__liste_koy", "__metin_al", "__metinden_sayi", "__liste_yeni",
    "__liste_ekle", "__aralik", "__metin_birlestir", "__sayidan_metin", "__oku")}

YIĞIN_BOYUTU = 256 * 1024 * 1024    # bss'te ayrılır; dokunulmadıkça bellek harcamaz

ÇALIŞMA_ZAMANI = r"""
# ── çalışma zamanı ──
_start:
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

__deger_ham:                    # rdi = değer, rsi = tür kodu; satır sonu eklemeden yazar
    test rsi, rsi               # 0: sayı
    jz __sayi_ham
    cmp rsi, 1                  # 1: metin
    jne 1f
    mov rsi, rdi
    mov rdx, [rdi-8]
    jmp __ham_yaz
1:  push rbx                    # k+2: k kodlu elemanların listesi
    push r12
    push r13
    push r14
    mov r12, [rdi]
    mov r13, [rdi+16]
    lea r14, [rsi-2]
    xor ebx, ebx
    lea rsi, [rip+__ac]
    mov edx, 1
    call __ham_yaz
2:  cmp rbx, r12
    jge 6f
    test rbx, rbx
    jz 3f
    lea rsi, [rip+__virgul]
    mov edx, 2
    call __ham_yaz
3:  cmp r14, 1
    jne 4f
    lea rsi, [rip+__tirnak]     # liste içindeki metinler tırnakla yazılır
    mov edx, 1
    call __ham_yaz
4:  mov rdi, [r13+rbx*8]
    mov rsi, r14
    call __deger_ham
    cmp r14, 1
    jne 5f
    lea rsi, [rip+__tirnak]
    mov edx, 1
    call __ham_yaz
5:  inc rbx
    jmp 2b
6:  lea rsi, [rip+__kapa]
    mov edx, 1
    call __ham_yaz
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__yaz_deger:                    # rdi = değer, rsi = tür kodu
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
    add rdi, 15
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
    lea rax, [rbx+r12+7]
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
__h_ara: .ascii ": çalışma hatası: "
__h_ara_son:
__h_sifir: .ascii "sıfıra bölme\n"
__h_sifir_son:
__h_dizin: .ascii "dizin sınırların dışında\n"
__h_dizin_son:
__h_sayi: .ascii "metin sayıya çevrilemiyor\n"
__h_sayi_son:
__h_bellek: .ascii "bellek tükendi\n"
__h_bellek_son:

    .section .data
__yigin_uc: .quad __yigin

    .section .bss
    .balign 16
__yigin: .skip YIGIN_BOYUTU
__yigin_son:
    .skip 64                    # __oku'nun başlık ve yuvarlama payı
__g_tampon: .skip 65536
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
                if veri:
                    son.append("    .byte " + ", ".join(str(b) for b in veri))
        if self.küreseller:
            son.append("    .section .bss")
            for ad, kayıt in self.küreseller.items():
                son.append(f"{kayıt[0]}: .skip 8    # {ad}")
        return "\n".join(map(str, baş + self.çıktı + self.işlev_kodu + son)) + "\n"

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
                     if len(ad) >= 3 and len(a) >= 3 and uzaklık(ad, a) <= sınır]
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
            return self.hedef_üret(h, tür, döngü_başı)
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
                self.yaz("push rax")                 # [rsp+16] = metin
                self.yaz("mov rdi, rax")
                self.yaz("call __metin_uzunluk")
                self.yaz("push rax")                 # [rsp+8]  = karakter sayısı
                self.yaz("push 0")                   # [rsp]    = dizin
                self.etiket_koy(baş)
                self.yaz("mov rsi, [rsp]")
                self.yaz("cmp rsi, [rsp+8]")
                self.yaz(f"jge {son}")
                self.yaz("mov rdi, [rsp+16]")
                self.yaz("call __metin_al")
                self.ata(h[1], "metin", satır)
                self.döngü_gövdesi(h[2], artır, son)
                self.etiket_koy(artır)
                self.yaz("inc qword ptr [rsp]")
                self.yaz(f"jmp {baş}")
                self.etiket_koy(son)
                self.yaz("add rsp, 24")
                return tür
            if not isinstance(tür, Liste):
                raise NehirHatası(f"'her' içine bir liste ya da metin akmalı, {tür} bulundu", satır)
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
            self.yaz("push rax")
            liste_türü = self.ifade(("değişken", h[1], satır))
            if not isinstance(liste_türü, Liste):
                raise NehirHatası(f"'{h[1]}' bir liste değil", satır)
            if not birleştir(liste_türü, Liste(tür)):
                raise NehirHatası(f"'{h[1]}' bir {liste_türü}; içine {tür} akamaz", satır)
            self.yaz("push rax")
            self.sayı_olmalı(self.ifade(h[2]), "liste dizini", satır)
            self.yaz("mov rsi, rax")
            self.yaz("pop rdi")
            self.yaz("mov rdx, [rsp]")
            self.yaz("call __liste_koy")
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
        if asıl == "uzunluk":
            if len(türler) != 1 or not (ilk_liste or türler[0] == "metin"):
                yanlış("liste ya da metin")
            if ilk_liste:
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
            if içerir(türler[1], türler[0].kök()):
                raise NehirHatası("bir liste kendi içine eklenemez", satır)
            if not birleştir(türler[0], Liste(türler[1])):
                raise NehirHatası(f"{türler[0]} içine {türler[1]} eklenemez", satır)
            self.yaz("pop rsi")
            self.yaz("pop rdi")
            self.yaz("call __liste_ekle")
            return türler[0]
        if türler != ["sayı", "sayı"]:      # aralık
            yanlış("sayı, sayı")
        self.yaz("pop rsi")
        self.yaz("pop rdi")
        self.yaz("call __aralik")
        return Liste("sayı")

    def sayı_olmalı(self, tür, ne, satır):
        if tür != "sayı":
            raise NehirHatası(f"{ne} sayı olmalı, {tür} bulundu", satır)

    # ── ifadeler ──
    def ifade(self, e):
        önceki, self.konum = self.konum, e[-1]
        try:
            return self.ifade_üret(e)
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
                raise NehirHatası("'[ ]' ile yalnızca liste ve metinlere erişilebilir", satır)
            if isinstance(kap, Liste) and kap.eleman is None:
                raise NehirHatası(BOŞ_LİSTE_HATASI, satır)
            self.yaz("push rax")
            self.sayı_olmalı(self.ifade(e[2]), "dizin", satır)
            self.yaz("mov rsi, rax")
            self.yaz("pop rdi")
            self.yaz("call __metin_al" if kap == "metin" else "call __liste_al")
            return "metin" if kap == "metin" else kap.eleman
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
"""


def ana(argv):
    girdi, çıktı, yalnız_asm, çalıştır = None, None, False, False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "-o" and i + 1 < len(argv):
            i += 1
            çıktı = argv[i]
        elif a == "--asm":
            yalnız_asm = True
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
        return subprocess.run([os.path.abspath(kök)]).returncode
    return 0


if __name__ == "__main__":
    sys.exit(ana(sys.argv[1:]))
