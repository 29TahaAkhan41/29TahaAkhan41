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
    "her": "her", "each": "her",
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
}

İŞLEÇLER = ["->", "→", "==", "!=", "<=", ">=",
            "+", "-", "*", "/", "%", "<", ">", "(", ")", "{", "}", "[", "]", ",", "|"]

KAÇIŞLAR = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


class Sözcük:
    def __init__(self, tür, değer, satır, yeni_satır):
        self.tür, self.değer, self.satır = tür, değer, satır
        self.yeni_satır = yeni_satır    # bu sözcük satırının ilk sözcüğü mü?

    def __repr__(self):
        return f"{self.tür}:{self.değer!r}"


def sözcükle(kaynak):
    sözcükler, i, satır, n = [], 0, 1, len(kaynak)
    son_satır = 0

    def ekle(tür, değer):
        nonlocal son_satır
        sözcükler.append(Sözcük(tür, değer, satır, satır != son_satır))
        son_satır = satır

    while i < n:
        c = kaynak[i]
        if c == "\n":
            satır += 1
            i += 1
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
            ekle("SAYI", int(kaynak[i:j].replace("_", "")))
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
            ekle("METİN", "".join(parçalar))
            i = j + 1
        elif c.isalpha() or c == "_":
            j = i
            while j < n and (kaynak[j].isalnum() or kaynak[j] == "_"):
                j += 1
            ad = kaynak[i:j]
            if ad in ANAHTARLAR:
                ekle("ANAHTAR", ANAHTARLAR[ad])
            else:
                ekle("AD", ad)
            i = j
        else:
            for iş in İŞLEÇLER:
                if kaynak.startswith(iş, i):
                    ekle("İŞLEÇ", "->" if iş == "→" else iş)
                    i += len(iş)
                    break
            else:
                raise NehirHatası(f"tanınmayan karakter: {c!r}", satır)
    ekle("SON", None)
    return sözcükler


# ───────────────────────────── Ayrıştırıcı ─────────────────────────────
# AST düğümleri basit demetlerdir; ilk eleman düğüm türü, son eleman satır no.
#
#   ("sayı", değer, satır)            ("metin", değer, satır)
#   ("değişken", ad, satır)           ("çağrı", ad, [argümanlar], satır)
#   ("liste", [elemanlar], satır)     ("dizin", ifade, dizin_ifadesi, satır)
#   ("tekli", işleç, ifade, satır)    ("ikili", işleç, sol, sağ, satır)
#   ("akış", kaynak_ifade, [hedefler], satır)
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
        raise NehirHatası("'->' sonrasında bir hedef bekleniyordu "
                          "(değişken, işlev, yazdır, döndür, eğer, iken, her, çatal)", s.satır)

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
        bulunan = "dosya sonu" if s.tür == "SON" else repr(s.değer)
        raise NehirHatası(f"bir ifade bekleniyordu, {bulunan} bulundu", s.satır)


# ───────────────────────────── Kod üretici ─────────────────────────────
# Basit bir strateji: her ifadenin sonucu rax'te kalır. İkili işlemlerde sol
# taraf yığına itilir, sağ taraf hesaplanır, sonra ikisi birleştirilir.
#
# Değerler 64 bitliktir:
#   sayı   tam sayının kendisi
#   metin  baytların adresi (uzunluk 8 bayt öncesinde durur)
#   liste  {uzunluk, kapasite, veri adresi} başlığının adresi (elemanlar sayıdır)
# Türler derleme anında izlenir. İşlevlerin parametre türleri ilk çağrıdan
# çıkarılır; bu yüzden işlevler ilk çağrıldıkları anda derlenir.

KARŞILAŞTIRMA = {"==": "sete", "!=": "setne", "<": "setl", ">": "setg", "<=": "setle", ">=": "setge"}

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

__sayi_ham:                     # rdi = sayı; satır sonu eklemeden yazar
    push rbp
    mov rbp, rsp
    sub rsp, 32
    mov rax, rdi
    mov rsi, rbp
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
    call __ham_yaz
    leave
    ret

__yaz_sayi:                     # rdi = sayı
    call __sayi_ham
    jmp __satir_sonu

__yaz_metin:                    # rdi = metin
    mov rsi, rdi
    mov rdx, [rdi-8]
    call __ham_yaz
    jmp __satir_sonu

__yaz_liste:                    # rdi = liste
    push rbx
    push r12
    push r13
    mov r12, [rdi]
    mov r13, [rdi+16]
    xor ebx, ebx
    lea rsi, [rip+__ac]
    mov edx, 1
    call __ham_yaz
1:  cmp rbx, r12
    jge 3f
    test rbx, rbx
    jz 2f
    lea rsi, [rip+__virgul]
    mov edx, 2
    call __ham_yaz
2:  mov rdi, [r13+rbx*8]
    call __sayi_ham
    inc rbx
    jmp 1b
3:  lea rsi, [rip+__kapa]
    mov edx, 1
    call __ham_yaz
    pop r13
    pop r12
    pop rbx
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

__sifira_bolme:
    lea rsi, [rip+__h_sifir]
    mov edx, __h_sifir_son - __h_sifir
    jmp __hata
__dizin_hatasi:
    lea rsi, [rip+__h_dizin]
    mov edx, __h_dizin_son - __h_dizin
    jmp __hata
__bellek_bitti:
    lea rsi, [rip+__h_bellek]
    mov edx, __h_bellek_son - __h_bellek
__hata:                         # rsi = mesaj, rdx = uzunluk; stderr'e yazıp 1 ile çıkar
    mov eax, 1
    mov edi, 2
    syscall
    mov edi, 1
    mov eax, 60
    syscall

    .section .rodata
__yeni_satir: .byte 10
__ac: .ascii "["
__kapa: .ascii "]"
__virgul: .ascii ", "
__h_sifir: .ascii "Nehir çalışma hatası: sıfıra bölme\n"
__h_sifir_son:
__h_dizin: .ascii "Nehir çalışma hatası: liste dizini sınırların dışında\n"
__h_dizin_son:
__h_bellek: .ascii "Nehir çalışma hatası: bellek tükendi\n"
__h_bellek_son:

    .section .data
__yigin_uc: .quad __yigin

    .section .bss
    .balign 16
__yigin: .skip YIGIN_BOYUTU
__yigin_son:
""".replace("YIGIN_BOYUTU", str(YIĞIN_BOYUTU))


class KodÜretici:
    def __init__(self, deyimler, işlevler):
        self.deyimler = deyimler
        self.işlevler = işlevler
        # Her işlev için: etiket, parametre türleri (ilk çağrıda belirlenir),
        # dönüş türü, ve özyineleme sırasında dönüş türü varsayıldı mı.
        self.bilgi = {ad: {"etiket": f"f{i}", "türler": None, "dönüş": None,
                           "varsayım": False, "bitti": False}
                      for i, ad in enumerate(işlevler)}
        self.küreseller = {}      # ad -> [etiket, tür|None]
        self.metinler = []        # bayt dizileri
        self.etiket_no = 0
        self.çıktı = []
        self.işlev_kodu = []      # derlenmiş işlevlerin satırları
        self.uyarılar = []
        # geçerli işlev bağlamı (en üst düzeyde geçerli None'dır)
        self.geçerli = None
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

        for ad, b in self.bilgi.items():
            if b["türler"] is None:
                self.uyarılar.append((self.işlevler[ad][2],
                                      f"'{ad}' işlevi hiç çağrılmıyor; derlenmedi"))

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
        return "\n".join(baş + self.çıktı + self.işlev_kodu + son) + "\n"

    def küreselleri_topla(self, deyimler):
        """En üst düzeyde (iç içe bloklar dahil) atanan her ad küresel değişkendir."""
        for _, _, hedefler, _ in deyimler:
            self.hedeflerden_topla(hedefler)

    def hedeflerden_topla(self, hedefler):
        def küresel(ad):
            self.küreseller.setdefault(ad, [f"g{len(self.küreseller)}", None])

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
        saklanan = (self.çıktı, self.geçerli, self.yereller, self.yerel_sayısı)
        # Argümanlar soldan sağa itilir: ilk argüman en derinde durur.
        self.yereller = {p: [16 + 8 * (n - 1 - i), b["türler"][i]]
                         for i, p in enumerate(parametreler)}
        self.çıktı, self.geçerli, self.yerel_sayısı = [], ad, 0
        for d in gövde:
            self.deyim(d)
        gövde_kodu, yerel_sayısı = self.çıktı, self.yerel_sayısı
        self.çıktı, self.geçerli, self.yereller, self.yerel_sayısı = saklanan

        if b["dönüş"] is None:
            b["dönüş"] = "sayı"      # hiç döndür yok: işlev 0 döndürür
        if b["varsayım"] and b["dönüş"] != "sayı":
            raise NehirHatası(f"özyinelemeli '{ad}' işlevinin dönüş türü ilk kullanımda "
                              f"sayı varsayıldı ama {b['dönüş']} döndürüyor", satır)
        b["bitti"] = True

        k = self.işlev_kodu
        k.append(f"{b['etiket']}:    # işlev {ad}({', '.join(b['türler'])}) -> {b['dönüş']}")
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

    def hedef(self, h, tür, döngü_başı=None):
        tip, satır = h[0], h[-1]
        if tip == "yazdır":
            self.yaz("push rax")
            self.yaz("mov rdi, rax")
            self.yaz({"sayı": "call __yaz_sayi", "metin": "call __yaz_metin",
                      "liste": "call __yaz_liste"}[tür])
            self.yaz("pop rax")      # değer akmaya devam eder
            return tür
        if tip == "döndür":
            if self.geçerli is None:
                raise NehirHatası("'döndür' yalnızca işlev içinde kullanılabilir", satır)
            b = self.bilgi[self.geçerli]
            if b["dönüş"] not in (None, tür):
                raise NehirHatası(f"'{self.geçerli}' işlevi hem {b['dönüş']} hem {tür} döndürüyor", satır)
            b["dönüş"] = tür
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
            self.blok(h[1])
            self.yaz(f"jmp {döngü_başı}")
            self.etiket_koy(son)
            return tür
        if tip == "her":
            if tür != "liste":
                raise NehirHatası(f"'her' içine bir liste akmalı, {tür} bulundu", satır)
            baş, son = self.yeni_etiket(), self.yeni_etiket()
            self.yaz("push rax")                 # [rsp+8] = liste
            self.yaz("push 0")                   # [rsp]   = dizin
            self.etiket_koy(baş)
            self.yaz("mov rsi, [rsp]")
            self.yaz("mov rdi, [rsp+8]")
            self.yaz("cmp rsi, [rdi]")
            self.yaz(f"jge {son}")
            self.yaz("call __liste_al")
            self.ata(h[1], "sayı", satır)
            self.blok(h[2])
            self.yaz("inc qword ptr [rsp]")
            self.yaz(f"jmp {baş}")
            self.etiket_koy(son)
            self.yaz("add rsp, 16")
            return tür
        if tip == "çatal":
            # Aynı değer her kola ayrı ayrı akar; sonra olduğu gibi yoluna devam eder.
            for dal in h[1]:
                self.yaz("push rax")
                kol_türü = tür
                for alt in dal:
                    kol_türü = self.hedef(alt, kol_türü)
                self.yaz("pop rax")
            return tür
        if tip == "eleman":
            self.sayı_olmalı(tür, "listeye akan değer", satır)
            self.yaz("push rax")
            if self.ifade(("değişken", h[1], satır)) != "liste":
                raise NehirHatası(f"'{h[1]}' bir liste değil", satır)
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
            raise NehirHatası(f"'{ad}' adında bir işlev yok", satır)
        self.ata(ad, tür, satır)
        return tür

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
            self.yereller[ad] = [-8 * self.yerel_sayısı, None]
            kayıt, adres = self.değişken_kaydı(ad)
        if kayıt[1] not in (None, tür):
            raise NehirHatası(f"'{ad}' değişkeni {kayıt[1]} türünde; {tür} atanamaz", satır)
        kayıt[1] = tür
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
            raise NehirHatası(f"'{ad}' adında bir işlev yok", satır)

        b = self.bilgi[ad]
        beklenen = len(self.işlevler[ad][0])
        if len(türler) != beklenen:
            raise NehirHatası(f"'{ad}' işlevi {beklenen} argüman bekliyor, {len(türler)} verildi", satır)
        if b["türler"] is None:
            b["türler"] = türler
            self.işlevi_derle(ad)
        elif b["türler"] != türler:
            raise NehirHatası(f"'{ad}' işlevi ({', '.join(b['türler'])}) ile çağrılmıştı; "
                              f"şimdi ({', '.join(türler)}) veriliyor", satır)
        self.yaz(f"call {b['etiket']}")
        if türler:
            self.yaz(f"add rsp, {8 * len(türler)}")
        if b["dönüş"] is None:      # özyineleme: işlev hâlâ derleniyor
            b["varsayım"] = True
            return "sayı"
        return b["dönüş"]

    def yerleşik(self, asıl, ad, türler, satır):
        def imza(*beklenen):
            if len(türler) != len(beklenen) or any(t not in b for t, b in zip(türler, beklenen)):
                beklenen_metin = ", ".join("/".join(b) for b in beklenen)
                raise NehirHatası(f"'{ad}' ({beklenen_metin}) bekliyor; "
                                  f"({', '.join(türler)}) verildi", satır)

        if asıl == "uzunluk":
            imza(("liste", "metin"))
            self.yaz("pop rax")
            self.yaz("mov rax, [rax]" if türler[0] == "liste" else "mov rax, [rax-8]")
            return "sayı"
        if asıl == "ekle":
            imza(("liste",), ("sayı",))
            self.yaz("pop rsi")
            self.yaz("pop rdi")
            self.yaz("call __liste_ekle")
            return "liste"
        imza(("sayı",), ("sayı",))          # aralık
        self.yaz("pop rsi")
        self.yaz("pop rdi")
        self.yaz("call __aralik")
        return "liste"

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
            kayıt, adres = self.değişken_kaydı(e[1])
            if kayıt is None or kayıt[1] is None:
                raise NehirHatası(f"'{e[1]}' değişkenine henüz bir değer akmadı", satır)
            self.yaz(f"mov rax, {adres}")
            return kayıt[1]
        if tip == "çağrı":
            return self.çağır(e[1], e[2], satır)
        if tip == "liste":
            self.yaz(f"mov edi, {max(len(e[1]), 4)}")
            self.yaz("call __liste_yeni")
            self.yaz("push rax")
            for eleman in e[1]:
                self.sayı_olmalı(self.ifade(eleman), "liste elemanı", satır)
                self.yaz("mov rsi, rax")
                self.yaz("mov rdi, [rsp]")
                self.yaz("call __liste_ekle")
            self.yaz("pop rax")
            return "liste"
        if tip == "dizin":
            if self.ifade(e[1]) != "liste":
                raise NehirHatası("yalnızca listelerin elemanına '[ ]' ile erişilebilir", satır)
            self.yaz("push rax")
            self.sayı_olmalı(self.ifade(e[2]), "liste dizini", satır)
            self.yaz("mov rsi, rax")
            self.yaz("pop rdi")
            self.yaz("call __liste_al")
            return "sayı"
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
    """Nehir kaynak metnini (assembly metni, uyarılar) ikilisine çevirir."""
    ayrıştırıcı = Ayrıştırıcı(sözcükle(kaynak))
    deyimler = ayrıştırıcı.program()
    üretici = KodÜretici(deyimler, ayrıştırıcı.işlevler)
    return üretici.üret(), üretici.uyarılar


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
            asm, uyarılar = derle(f.read())
    except OSError as h:
        sys.stderr.write(f"hata: {girdi} okunamadı: {h.strerror}\n")
        return 1
    except NehirHatası as h:
        yer = f"{girdi}:{h.satır}" if h.satır else girdi
        sys.stderr.write(f"{yer}: hata: {h.mesaj}\n")
        return 1
    for satır, mesaj in uyarılar:
        sys.stderr.write(f"{girdi}:{satır}: uyarı: {mesaj}\n")

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
