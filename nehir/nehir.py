#!/usr/bin/env python3
"""Nehir derleyicisi.

Nehir kaynak kodunu (.nehir) doğrudan x86-64 Linux assembly'sine çevirir,
ardından `as` ve `ld` ile libc'siz, bağımsız bir çalıştırılabilir dosya üretir.

Aşamalar:  kaynak -> Sözcükleyici -> Ayrıştırıcı (AST) -> Kod üretici -> .s -> as/ld
"""
import os
import subprocess
import sys


class NehirHatası(Exception):
    def __init__(self, mesaj, satır=None):
        super().__init__(mesaj)
        self.mesaj = mesaj
        self.satır = satır


# ───────────────────────────── Sözcükleyici ─────────────────────────────

# Her anahtar kelimenin Türkçe, ASCII-Türkçe ve İngilizce yazımı aynı şeye çıkar.
ANAHTARLAR = {
    "eğer": "eğer", "eger": "eğer", "if": "eğer",
    "değilse": "değilse", "degilse": "değilse", "else": "değilse",
    "iken": "iken", "while": "iken",
    "işlev": "işlev", "islev": "işlev", "fonksiyon": "işlev", "fn": "işlev",
    "döndür": "döndür", "dondur": "döndür", "return": "döndür",
    "yazdır": "yazdır", "yazdir": "yazdır", "print": "yazdır",
    "doğru": "doğru", "dogru": "doğru", "true": "doğru",
    "yanlış": "yanlış", "yanlis": "yanlış", "false": "yanlış",
    "ve": "ve", "and": "ve",
    "veya": "veya", "or": "veya",
    "değil": "değil", "degil": "değil", "not": "değil",
}

İŞLEÇLER = ["->", "→", "==", "!=", "<=", ">=",
            "+", "-", "*", "/", "%", "<", ">", "(", ")", "{", "}", ","]

KAÇIŞLAR = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


class Sözcük:
    def __init__(self, tür, değer, satır):
        self.tür, self.değer, self.satır = tür, değer, satır

    def __repr__(self):
        return f"{self.tür}:{self.değer!r}"


def sözcükle(kaynak):
    sözcükler, i, satır, n = [], 0, 1, len(kaynak)
    while i < n:
        c = kaynak[i]
        if c == "\n":
            satır += 1
            i += 1
        elif c.isspace() or c == ";":
            i += 1
        elif c == "#":
            while i < n and kaynak[i] != "\n":
                i += 1
        elif c.isdigit():
            j = i
            while j < n and (kaynak[j].isdigit() or kaynak[j] == "_"):
                j += 1
            sözcükler.append(Sözcük("SAYI", int(kaynak[i:j].replace("_", "")), satır))
            i = j
        elif c == '"':
            j, parçalar = i + 1, []
            while True:
                if j >= n or kaynak[j] == "\n":
                    raise NehirHatası("metin kapatılmamış (\" eksik)", satır)
                if kaynak[j] == '"':
                    break
                if kaynak[j] == "\\":
                    j += 1
                    if j >= n or kaynak[j] not in KAÇIŞLAR:
                        raise NehirHatası("geçersiz kaçış dizisi", satır)
                    parçalar.append(KAÇIŞLAR[kaynak[j]])
                else:
                    parçalar.append(kaynak[j])
                j += 1
            sözcükler.append(Sözcük("METİN", "".join(parçalar), satır))
            i = j + 1
        elif c.isalpha() or c == "_":
            j = i
            while j < n and (kaynak[j].isalnum() or kaynak[j] == "_"):
                j += 1
            ad = kaynak[i:j]
            if ad in ANAHTARLAR:
                sözcükler.append(Sözcük("ANAHTAR", ANAHTARLAR[ad], satır))
            else:
                sözcükler.append(Sözcük("AD", ad, satır))
            i = j
        else:
            for iş in İŞLEÇLER:
                if kaynak.startswith(iş, i):
                    sözcükler.append(Sözcük("İŞLEÇ", "->" if iş == "→" else iş, satır))
                    i += len(iş)
                    break
            else:
                raise NehirHatası(f"tanınmayan karakter: {c!r}", satır)
    sözcükler.append(Sözcük("SON", None, satır))
    return sözcükler


# ───────────────────────────── Ayrıştırıcı ─────────────────────────────
# AST düğümleri basit demetlerdir; ilk eleman düğüm türü, son eleman satır no.
#
#   ("sayı", değer, satır)            ("metin", değer, satır)
#   ("değişken", ad, satır)           ("çağrı", ad, [argümanlar], satır)
#   ("tekli", işleç, ifade, satır)    ("ikili", işleç, sol, sağ, satır)
#   ("akış", kaynak_ifade, [hedefler], satır)
#
# Hedefler:
#   ("yazdır", satır)  ("döndür", satır)  ("ad", ad, argümanlar|None, satır)
#   ("eğer", blok, değilse_blok|None, satır)  ("iken", blok, satır)

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

    def al(self, tür, değer=None):
        if self.bak(tür, değer):
            self.k += 1
            return self.s[self.k - 1]
        return None

    def bekle(self, tür, değer=None):
        s = self.al(tür, değer)
        if s is None:
            beklenen = değer if değer is not None else tür
            bulunan = "dosya sonu" if self.şimdiki.tür == "SON" else repr(self.şimdiki.değer)
            raise NehirHatası(f"'{beklenen}' bekleniyordu, {bulunan} bulundu", self.şimdiki.satır)
        return s

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
        self.bekle("İŞLEÇ", "{")
        deyimler = []
        while not self.bak("İŞLEÇ", "}"):
            if self.bak("ANAHTAR", "işlev"):
                raise NehirHatası("işlevler yalnızca en üst düzeyde tanımlanabilir", self.şimdiki.satır)
            if self.bak("SON"):
                raise NehirHatası("blok kapatılmamış ('}' eksik)", self.şimdiki.satır)
            deyimler.append(self.deyim())
        self.bekle("İŞLEÇ", "}")
        return deyimler

    def deyim(self):
        satır = self.şimdiki.satır
        kaynak = self.ifade()
        hedefler = []
        while self.al("İŞLEÇ", "->"):
            h = self.hedef()
            hedefler.append(h)
            if h[0] in ("eğer", "iken", "döndür"):
                break   # bu hedefler akışı sonlandırır
        return ("akış", kaynak, hedefler, satır)

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
        if self.al("AD"):
            argümanlar = self.argümanlar() if self.bak("İŞLEÇ", "(") else None
            return ("ad", s.değer, argümanlar, s.satır)
        raise NehirHatası("'->' sonrasında bir hedef bekleniyordu "
                          "(değişken, işlev, yazdır, döndür, eğer, iken)", s.satır)

    def argümanlar(self):
        self.bekle("İŞLEÇ", "(")
        liste = []
        if not self.bak("İŞLEÇ", ")"):
            liste.append(self.ifade())
            while self.al("İŞLEÇ", ","):
                liste.append(self.ifade())
        self.bekle("İŞLEÇ", ")")
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
        return self.birincil()

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
            if self.bak("İŞLEÇ", "("):
                return ("çağrı", s.değer, self.argümanlar(), s.satır)
            return ("değişken", s.değer, s.satır)
        if self.al("İŞLEÇ", "("):
            iç = self.ifade()
            self.bekle("İŞLEÇ", ")")
            return iç
        bulunan = "dosya sonu" if s.tür == "SON" else repr(s.değer)
        raise NehirHatası(f"bir ifade bekleniyordu, {bulunan} bulundu", s.satır)


# ───────────────────────────── Kod üretici ─────────────────────────────
# Basit bir strateji: her ifadenin sonucu rax'te kalır. İkili işlemlerde sol
# taraf yığına itilir, sağ taraf hesaplanır, sonra ikisi birleştirilir.
# Değerler 64 bitlik tam sayıdır; metinler, uzunluğu 8 bayt öncesinde duran
# verinin adresidir. Türler derleme anında izlenir ("sayı" / "metin").

KARŞILAŞTIRMA = {"==": "sete", "!=": "setne", "<": "setl", ">": "setg", "<=": "setle", ">=": "setge"}

ÇALIŞMA_ZAMANI = r"""
# ── çalışma zamanı ──
_start:
    call nehir_ana
    xor edi, edi
    mov eax, 60
    syscall

__yaz_sayi:                     # rdi = yazılacak sayı
    push rbp
    mov rbp, rsp
    sub rsp, 32
    mov rax, rdi
    lea rsi, [rbp-1]
    mov byte ptr [rsi], 10
    mov r8, 1
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
3:  mov eax, 1
    mov edi, 1
    mov rdx, r8
    syscall
    leave
    ret

__yaz_metin:                    # rdi = metin adresi (uzunluk [rdi-8]'de)
    mov rsi, rdi
    mov rdx, [rdi-8]
    mov eax, 1
    mov edi, 1
    syscall
    mov eax, 1
    mov edi, 1
    lea rsi, [rip+__yeni_satir]
    mov edx, 1
    syscall
    ret

__sifira_bolme:
    mov eax, 1
    mov edi, 2
    lea rsi, [rip+__sifir_mesaj]
    mov edx, __sifir_mesaj_son - __sifir_mesaj
    syscall
    mov edi, 1
    mov eax, 60
    syscall

    .section .rodata
__yeni_satir: .byte 10
__sifir_mesaj: .ascii "Nehir \303\247al\304\261\305\237ma hatas\304\261: s\304\261f\304\261ra b\303\266lme\n"
__sifir_mesaj_son:
"""


class KodÜretici:
    def __init__(self, deyimler, işlevler):
        self.deyimler = deyimler
        self.işlevler = işlevler
        self.işlev_etiketi = {ad: f"f{i}" for i, ad in enumerate(işlevler)}
        self.küreseller = {}      # ad -> [etiket, tür|None]
        self.metinler = []        # bayt dizileri
        self.etiket_no = 0
        self.çıktı = []
        # geçerli işlev bağlamı (None ise en üst düzeydeyiz)
        self.yereller = None      # ad -> [rbp'ye göre konum, tür]
        self.yerel_sayısı = 0

    def yaz(self, satır):
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

        for ad, (parametreler, gövde, _) in self.işlevler.items():
            self.işlev(ad, parametreler, gövde)

        baş = [".intel_syntax noprefix", ".global _start", ".section .text"]
        son = [ÇALIŞMA_ZAMANI]
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
            for ad, (etiket, _) in self.küreseller.items():
                son.append(f"{etiket}: .skip 8    # {ad}")
        return "\n".join(baş + self.çıktı + son) + "\n"

    def küreselleri_topla(self, deyimler):
        """En üst düzeyde (iç içe bloklar dahil) atanan her ad küresel değişkendir."""
        for _, _, hedefler, _ in deyimler:
            for h in hedefler:
                if h[0] == "ad" and h[2] is None and h[1] not in self.işlevler:
                    self.küreseller.setdefault(h[1], [f"g{len(self.küreseller)}", None])
                elif h[0] == "eğer":
                    self.küreselleri_topla(h[1])
                    if h[2]:
                        self.küreselleri_topla(h[2])
                elif h[0] == "iken":
                    self.küreselleri_topla(h[1])

    def işlev(self, ad, parametreler, gövde):
        n = len(parametreler)
        # Argümanlar soldan sağa itilir: ilk argüman en derinde durur.
        self.yereller = {p: [16 + 8 * (n - 1 - i), "sayı"] for i, p in enumerate(parametreler)}
        self.yerel_sayısı = 0
        dış, self.çıktı = self.çıktı, []
        for d in gövde:
            self.deyim(d)
        gövde_kodu, self.çıktı = self.çıktı, dış

        self.çıktı.append(f"{self.işlev_etiketi[ad]}:    # işlev {ad}")
        self.yaz("push rbp")
        self.yaz("mov rbp, rsp")
        if self.yerel_sayısı:
            self.yaz(f"sub rsp, {8 * self.yerel_sayısı}")
        self.çıktı.extend(gövde_kodu)
        self.yaz("xor eax, eax")     # döndür yoksa 0 döner
        self.yaz("leave")
        self.yaz("ret")
        self.yereller = None

    # ── deyimler ──
    def deyim(self, d):
        _, kaynak, hedefler, _ = d
        döngü_başı = None
        if hedefler and hedefler[-1][0] == "iken":
            # Koşul her turda yeniden aktığı için tüm zincir döngünün içindedir.
            döngü_başı = self.yeni_etiket()
            self.etiket_koy(döngü_başı)
        tür = self.ifade(kaynak)
        for h in hedefler:
            tür = self.hedef(h, tür, döngü_başı)

    def hedef(self, h, tür, döngü_başı):
        tip, satır = h[0], h[-1]
        if tip == "yazdır":
            self.yaz("push rax")
            self.yaz("mov rdi, rax")
            self.yaz("call __yaz_sayi" if tür == "sayı" else "call __yaz_metin")
            self.yaz("pop rax")      # değer akmaya devam eder
            return tür
        if tip == "döndür":
            if self.yereller is None:
                raise NehirHatası("'döndür' yalnızca işlev içinde kullanılabilir", satır)
            self.sayı_olmalı(tür, "döndürülen değer", satır)
            self.yaz("leave")
            self.yaz("ret")
            return tür
        if tip == "eğer":
            self.sayı_olmalı(tür, "'eğer' koşulu", satır)
            değilse, son = self.yeni_etiket(), self.yeni_etiket()
            self.yaz("test rax, rax")
            self.yaz(f"jz {değilse}")
            for d in h[1]:
                self.deyim(d)
            self.yaz(f"jmp {son}")
            self.etiket_koy(değilse)
            for d in h[2] or []:
                self.deyim(d)
            self.etiket_koy(son)
            return tür
        if tip == "iken":
            self.sayı_olmalı(tür, "'iken' koşulu", satır)
            son = self.yeni_etiket()
            self.yaz("test rax, rax")
            self.yaz(f"jz {son}")
            for d in h[1]:
                self.deyim(d)
            self.yaz(f"jmp {döngü_başı}")
            self.etiket_koy(son)
            return tür
        # tip == "ad": işlevse akan değer ilk argüman olur, değilse değişkene atanır
        _, ad, argümanlar, _ = h
        if ad in self.işlevler:
            self.sayı_olmalı(tür, f"'{ad}' işlevine akan değer", satır)
            self.yaz("push rax")
            return self.çağır(ad, argümanlar or [], satır, itilmiş=1)
        if argümanlar is not None:
            raise NehirHatası(f"'{ad}' adında bir işlev yok", satır)
        self.ata(ad, tür, satır)
        return tür

    def ata(self, ad, tür, satır):
        if self.yereller is not None and ad not in self.yereller and ad not in self.küreseller:
            self.yerel_sayısı += 1
            self.yereller[ad] = [-8 * self.yerel_sayısı, None]
        if self.yereller is not None and ad in self.yereller:
            kayıt = self.yereller[ad]
            hedef = f"[rbp{kayıt[0]:+d}]"
        else:
            kayıt = self.küreseller[ad]
            hedef = f"[rip+{kayıt[0]}]"
        if kayıt[1] not in (None, tür):
            raise NehirHatası(f"'{ad}' değişkeni {kayıt[1]} türünde; {tür} atanamaz", satır)
        kayıt[1] = tür
        self.yaz(f"mov {hedef}, rax")

    def çağır(self, ad, argümanlar, satır, itilmiş=0):
        beklenen = len(self.işlevler[ad][0])
        verilen = itilmiş + len(argümanlar)
        if verilen != beklenen:
            raise NehirHatası(f"'{ad}' işlevi {beklenen} argüman bekliyor, {verilen} verildi", satır)
        for a in argümanlar:
            self.sayı_olmalı(self.ifade(a), f"'{ad}' işlevinin argümanı", satır)
            self.yaz("push rax")
        self.yaz(f"call {self.işlev_etiketi[ad]}")
        if verilen:
            self.yaz(f"add rsp, {8 * verilen}")
        return "sayı"

    def sayı_olmalı(self, tür, ne, satır):
        if tür != "sayı":
            raise NehirHatası(f"{ne} sayı olmalı, {tür} bulundu", satır)

    # ── ifadeler ──
    def ifade(self, e):
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
            ad = e[1]
            if self.yereller is not None and ad in self.yereller:
                kayıt = self.yereller[ad]
                kaynak = f"[rbp{kayıt[0]:+d}]"
            elif ad in self.küreseller:
                kayıt = self.küreseller[ad]
                kaynak = f"[rip+{kayıt[0]}]"
            else:
                kayıt = None
            if kayıt is None or kayıt[1] is None:
                raise NehirHatası(f"'{ad}' değişkenine henüz bir değer akmadı", satır)
            self.yaz(f"mov rax, {kaynak}")
            return kayıt[1]
        if tip == "çağrı":
            if e[1] not in self.işlevler:
                raise NehirHatası(f"'{e[1]}' adında bir işlev yok", satır)
            return self.çağır(e[1], e[2], satır)
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
        self.sayı_olmalı(self.ifade(sol), f"'{iş}' işlecinin sol tarafı", satır)
        self.yaz("push rax")
        self.sayı_olmalı(self.ifade(sağ), f"'{iş}' işlecinin sağ tarafı", satır)
        self.yaz("mov rcx, rax")
        self.yaz("pop rax")
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

def derle(kaynak):
    """Nehir kaynak metnini assembly metnine çevirir."""
    ayrıştırıcı = Ayrıştırıcı(sözcükle(kaynak))
    deyimler = ayrıştırıcı.program()
    return KodÜretici(deyimler, ayrıştırıcı.işlevler).üret()


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

    try:
        with open(girdi, encoding="utf-8") as f:
            asm = derle(f.read())
    except OSError as h:
        sys.stderr.write(f"hata: {girdi} okunamadı: {h.strerror}\n")
        return 1
    except NehirHatası as h:
        yer = f"{girdi}:{h.satır}" if h.satır else girdi
        sys.stderr.write(f"{yer}: hata: {h.mesaj}\n")
        return 1

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
