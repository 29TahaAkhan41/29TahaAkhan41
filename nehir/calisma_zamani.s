

# ── çalışma zamanı: işletim sisteminden bağımsız kısım ──
# İşletim sistemiyle yalnızca calisma_zamani_<sistem>.s'deki şu yordamlar konuşur; hepsi
# Linux sistem çağrısı gibi davranır (yalnızca rax, rcx ve r11 değişir, hata -errno döner):
#   __sis_yaz(fd, adres, uzunluk)  __sis_oku(fd, adres, uzunluk)  __sis_ac(yol, bayraklar)
#   __sis_kapat(fd)  __sis_sil(yol)  __sis_erisim(yol)  __cik(kod)
# Oyun temelleri için ayrıca:
#   __sis_zaman() -> tekdüze saatin milisaniyesi     __sis_bekle(milisaniye)
#   __sis_tus_kipi(1 aç / 0 kapat) -> ham kip açıksa 1
#   __sis_tus_doldur() -> beklemeden: girdi hazırsa __g_tampon'a doldurup 1, değilse 0
#   __sis_boyut() -> (yükseklik << 32) | genişlik; uçbirim değilse 0
    .section .text

__ham_yaz:                      # rsi = adres, rdx = uzunluk
    mov edi, 1
    jmp __sis_yaz

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
    cmp rax, 6                  # 6: ondalık
    je __ondalik_ham
    cmp rax, 4                  # 4: kayıt
    je __kayit_ham
    cmp rax, 5                  # 5: işlev
    je __islev_ham
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

__kayit_ham:                    # rdi = kayıt ya da 0, rsi = tür tanımı;  Ad(alan: değer, ...)
    test rdi, rdi
    jnz 1f
    lea rsi, [rip+__yok_metni]
    mov edx, 3
    jmp __ham_yaz
1:  push rbx
    push r12
    push r13
    push r14
    mov r12, rdi
    mov r13, rsi
    mov rsi, [r13+8]
    mov rdx, [rsi-8]
    call __ham_yaz
    lea rsi, [rip+__par_ac]
    mov edx, 1
    call __ham_yaz
    xor ebx, ebx
    lea r14, [r13+24]
2:  cmp rbx, [r13+16]
    jae 4f
    test rbx, rbx
    jz 3f
    lea rsi, [rip+__virgul]
    mov edx, 2
    call __ham_yaz
3:  mov rsi, [r14]
    mov rdx, [rsi-8]
    call __ham_yaz
    lea rsi, [rip+__iki_nokta]
    mov edx, 2
    call __ham_yaz
    mov rdi, [r12+rbx*8]
    mov rsi, [r14+8]
    call __deger_tirnakli
    inc rbx
    add r14, 16
    jmp 2b
4:  lea rsi, [rip+__par_kapa]
    mov edx, 1
    call __ham_yaz
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__islev_ham:
    lea rsi, [rip+__islev_metni]
    mov edx, __islev_metni_son - __islev_metni
    jmp __ham_yaz

__yaz_deger:                    # rdi = değer, rsi = tür tanımı
    call __deger_ham
    jmp __satir_sonu

# ── bellek: ayırma ve çöp toplama ──
# Yığın (__yigin ... __yigin_uc) art arda bloklardan oluşur. Her bloğun önünde 8 baytlık bir
# başlık vardır: bloğun başlıkla birlikte bayt sayısı (8'in katı) ve alt üç bitte bayraklar
# (1 işaretli, 2 düz: içinde adres yok (metin), 4 boş). __ayir'in verdiği adres başlıktan hemen
# sonradır ve __gc_baslar bit haritasında (8 bayta bir bit) işaretlidir.
#
# Çöp toplayıcı işaretle-süpür türündedir ve muhafazakârdır: kökler (çağrı yığını, yazmaçlar,
# programın küresel değişkenleri ve çalışma zamanının değişkenleri) ile ulaşılan blokların
# içindeki her sözcük, bir bloğun adresi (ya da metinlerde olduğu gibi adresi + 8) olabilir
# diye denenir. Ulaşılamayan bloklar süpürülür: komşu boş bloklar birleşir, sondakiler
# yığının ucunu geri çeker, diğerleri boyutlarına göre boş listelerine girer. Bloklar
# taşınmaz. Son toplamadan bu yana ayrılan bellek, toplamadan sağ çıkan kadarı (en az 8 MB)
# olunca yeniden toplanır.

__ayir:                         # rdi = bayt sayısı -> rax = sıfırlanmış bellek (yalnızca rax, rcx, rdx değişir)
    push rdi
    push rsi
    push r8
    lea rdi, [rdi+15]           # başlıkla birlikte, 8'in katına yuvarlanmış; en az 16
    and rdi, -8
    cmp rdi, 16
    jae 1f
    mov edi, 16
1:  mov rax, [rip+__gc_ayrilan]
    cmp rax, [rip+__gc_esik]
    jb 2f
    call __cop_topla
2:  call __blok_bul
    test rax, rax
    jnz 3f
    call __cop_topla
    call __blok_bul
    test rax, rax
    jz __bellek_bitti
3:  add [rip+__gc_ayrilan], rdi
    lea r8, [rax+8]
    mov rcx, r8
    lea rdx, [rip+__yigin]
    sub rcx, rdx
    shr rcx, 3
    lea rdx, [rip+__gc_baslar]
    bts qword ptr [rdx], rcx
    mov rcx, [rax]
    shr rcx, 3
    dec rcx
    mov rdi, r8
    xor eax, eax
    rep stosq
    mov rax, r8
    pop r8
    pop rsi
    pop rdi
    ret

__blok_bul:                     # rdi = blok boyutu -> rax = başlığı yazılmış bloğun başlığı ya da 0
    cmp rdi, 512
    ja 3f
    lea rdx, [rip+__gc_listeler]    # küçük bloklar: tam bu boyuttakilerin listesi
    mov rax, [rdx+rdi]
    test rax, rax
    jz 3f
    mov rcx, [rax+8]
    mov [rdx+rdi], rcx
    mov [rax], rdi
    ret
3:  lea rsi, [rip+__gc_buyuk]   # büyük boş bloklar: ilk yeten bölünür
4:  mov rax, [rsi]
    test rax, rax
    jz 6f
    mov rcx, [rax]
    and rcx, -8
    cmp rcx, rdi
    jae 5f
    lea rsi, [rax+8]
    jmp 4b
5:  mov rdx, [rax+8]
    mov [rsi], rdx
    sub rcx, rdi
    cmp rcx, 16
    jb 7f
    push rdi
    lea rdi, [rax+rdi]
    mov rsi, rcx
    call __bos_ekle
    pop rdi
    mov [rax], rdi
    ret
7:  add rcx, rdi
    mov [rax], rcx
    ret
6:  mov rax, [rip+__yigin_uc]   # yığının ucundan
    lea rdx, [rax+rdi]
    lea rcx, [rip+__yigin_son]
    cmp rdx, rcx
    ja 8f
    mov [rip+__yigin_uc], rdx
    mov [rax], rdi
    ret
8:  xor eax, eax
    ret

__bos_ekle:                     # rdi = başlık, rsi = boyut: boş blok olarak listesine ekler (rax korunur)
    lea rcx, [rsi+4]
    mov [rdi], rcx
    lea rcx, [rip+__gc_buyuk]
    cmp rsi, 512
    ja 1f
    lea rcx, [rip+__gc_listeler]
    add rcx, rsi
1:  mov rdx, [rcx]
    mov [rdi+8], rdx
    mov [rcx], rdi
    ret

# Metin doğrudan yığının ucunda büyütülürken (__oku, __dosya_oku): önce gerekirse toplanır.
__uc_bas:                       # -> rax = metnin baytlarının yazılacağı adres (uç + 16)
    call __gc_belki
    mov rax, [rip+__yigin_uc]
    add rax, 16
    ret

__uc_bitir:                     # rdi = __uc_bas'ın verdiği adres, rsi = bayt uzunluğu -> rax = metin
    mov [rdi-8], rsi
    mov byte ptr [rdi+rsi], 0
    lea rax, [rdi+rsi+8]
    and rax, -8
    lea rcx, [rdi-16]
    mov rdx, rax
    sub rdx, rcx
    add [rip+__gc_ayrilan], rdx
    or rdx, 2                   # düz blok
    mov [rcx], rdx
    mov [rip+__yigin_uc], rax
    lea rcx, [rdi-8]
    lea rdx, [rip+__yigin]
    sub rcx, rdx
    shr rcx, 3
    lea rdx, [rip+__gc_baslar]
    bts qword ptr [rdx], rcx
    mov rax, rdi
    ret

__gc_belki:                     # son toplamadan bu yana eşik kadar ayrıldıysa toplar
    push rax
    mov rax, [rip+__gc_ayrilan]
    cmp rax, [rip+__gc_esik]
    pop rax
    jae __cop_topla
    ret

__bellek_topla:                 # çöp_topla() -> rax = toplamadan sağ çıkan bayt sayısı
    call __cop_topla
    mov rax, [rip+__gc_canli]
    ret

__cop_topla:                    # bütün yazmaçlar korunur (yığına itilir, böylece kök de olurlar)
    push rax
    push rbx
    push rcx
    push rdx
    push rsi
    push rdi
    push rbp
    push r8
    push r9
    push r10
    push r11
    push r12
    push r13
    push r14
    push r15
    mov qword ptr [rip+__ma_metin], 0   # önbellekler, süpürülüp yeniden kullanılacak metinleri göstermesin
    mov qword ptr [rip+__mu_metin], 0
    lea rbx, [rip+__gc_isaret]  # işaretlenip içi taranacak bloklar
    xor r12, r12
    mov byte ptr [rip+__gc_tasti], 0
    mov rsi, rsp
    mov rdx, [rip+__cagri_tepe]
    call __gc_aralik
    lea rsi, [rip+__kokler_bas]
    lea rdx, [rip+__kokler_son]
    call __gc_aralik
    call __gc_bosalt
1:  cmp byte ptr [rip+__gc_tasti], 0    # işaret yığını taştıysa: işaretli blokların içi yeniden taranır
    je 4f
    mov byte ptr [rip+__gc_tasti], 0
    lea r13, [rip+__yigin]
2:  cmp r13, [rip+__yigin_uc]
    jae 1b
    mov rax, [r13]
    mov r14, rax
    and r14, -8
    and eax, 7
    cmp eax, 1                  # işaretli, düz değil, boş değil
    jne 3f
    lea rsi, [r13+8]
    lea rdx, [r13+r14]
    call __gc_aralik
    call __gc_bosalt
3:  add r13, r14
    jmp 2b
4:  call __gc_supur
    pop r15
    pop r14
    pop r13
    pop r12
    pop r11
    pop r10
    pop r9
    pop r8
    pop rbp
    pop rdi
    pop rsi
    pop rdx
    pop rcx
    pop rbx
    pop rax
    ret

__gc_aralik:                    # rsi = baş, rdx = son: aradaki her sözcük aday
1:  cmp rsi, rdx
    jae 2f
    mov rdi, [rsi]
    call __gc_aday
    add rsi, 8
    jmp 1b
2:  ret

__gc_aday:                      # rdi = bir blok adresi olabilecek değer: öyleyse işaretler
    test dil, 7
    jnz 9f
    lea rax, [rip+__yigin]
    cmp rdi, rax
    jbe 9f
    cmp rdi, [rip+__yigin_uc]
    jae 9f
    mov rcx, rdi
    sub rcx, rax
    shr rcx, 3
    lea r8, [rip+__gc_baslar]
    bt qword ptr [r8], rcx
    jc 1f
    dec rcx                     # metinler: adres, bloğun başı + 8'dir
    bt qword ptr [r8], rcx
    jnc 9f
    sub rdi, 8
1:  mov rax, [rdi-8]
    test al, 1
    jnz 9f
    or rax, 1
    mov [rdi-8], rax
    test al, 2
    jnz 9f
    cmp r12, 1048576
    jae 8f
    mov [rbx+r12*8], rdi
    inc r12
9:  ret
8:  mov byte ptr [rip+__gc_tasti], 1
    ret

__gc_bosalt:                    # işaret yığınındaki blokların içini tarar
1:  test r12, r12
    jz 2f
    dec r12
    mov rsi, [rbx+r12*8]
    mov rdx, [rsi-8]
    and rdx, -8
    lea rdx, [rsi+rdx-8]
    call __gc_aralik
    jmp 1b
2:  ret

__gc_supur:                     # işaretsiz blokları boşaltır, boş komşuları birleştirir
    lea rdi, [rip+__gc_listeler]
    mov ecx, 66
    xor eax, eax
    rep stosq                   # __gc_listeler ve __gc_buyuk sıfırlanır
    lea r13, [rip+__yigin]      # r13 = başlık, r14 = süren boş dizinin başı (0: yok), r15 = canlı bayt
    xor r14, r14
    xor r15, r15
    lea rbx, [rip+__gc_baslar]
1:  cmp r13, [rip+__yigin_uc]
    jae 5f
    mov rax, [r13]
    mov rcx, rax
    and rcx, -8
    test al, 1
    jz 3f
    and rax, -2
    mov [r13], rax
    add r15, rcx
    test r14, r14
    jz 4f
    push rcx
    mov rdi, r14
    mov rsi, r13
    sub rsi, r14
    call __bos_ekle
    pop rcx
    xor r14, r14
    jmp 4f
3:  lea rdx, [r13+8]
    lea rax, [rip+__yigin]
    sub rdx, rax
    shr rdx, 3
    btr qword ptr [rbx], rdx
    test r14, r14
    jnz 4f
    mov r14, r13
4:  add r13, rcx
    jmp 1b
5:  test r14, r14
    jz 6f
    mov [rip+__yigin_uc], r14
6:  mov [rip+__gc_canli], r15
    mov rax, r15
    cmp rax, 8388608
    jae 7f
    mov eax, 8388608
7:  mov [rip+__gc_esik], rax
    mov qword ptr [rip+__gc_ayrilan], 0
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
    or qword ptr [rax-8], 2     # düz blok: içinde adres yok
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
    cmp rdi, [rip+__mu_metin]   # son ölçülen metin mi? (metinler değişmez, bellek
    jne 0f                      #  geri verilmez: bir adres hep aynı metindir)
    mov rax, [rip+__mu_uzunluk]
    ret
0:  mov rcx, [rdi-8]
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
2:  mov [rip+__mu_metin], rdi
    mov [rip+__mu_uzunluk], rax
    ret

__metin_al:                     # rdi = metin, rsi = karakter dizini -> rax = o karakter (metin)
    push rbx
    push r12
    mov rcx, [rdi-8]
    xor r8, r8                  # bayt konumu
    mov r10, rsi                # istenen dizin (önbellek için)
    cmp rdi, [rip+__ma_metin]   # aynı metinde son erişilen yerden ileride mi? Öyleyse
    jne 1f                      # saymaya oradan başlanır: m[0], m[1], ... doğrusal olur.
    mov rax, [rip+__ma_dizin]
    cmp rsi, rax
    jb 1f
    sub rsi, rax
    mov r8, [rip+__ma_bayt]
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
3:  mov [rip+__ma_metin], rdi
    mov [rip+__ma_dizin], r10
    mov [rip+__ma_bayt], r8
    mov r9, r8                  # karakterin sonunu bul
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

__metin_baytlar:                # rdi = metin -> rax = UTF-8 baytlarının sayı listesi
    push rbx
    push r12
    push r13
    mov rbx, rdi
    mov rdi, [rbx-8]
    cmp rdi, 4
    jge 1f
    mov edi, 4
1:  call __liste_yeni
    mov r12, rax
    xor r13, r13
2:  cmp r13, [rbx-8]
    jae 3f
    movzx esi, byte ptr [rbx+r13]
    mov rdi, r12
    call __liste_ekle
    inc r13
    jmp 2b
3:  mov rax, r12
    pop r13
    pop r12
    pop rbx
    ret

__karakter:                     # rdi = Unicode kod noktası -> rax = o karakter (UTF-8 metin)
    push rbx
    mov rbx, rdi
    cmp rbx, 0x10FFFF           # geçersiz: eksi, 0x10FFFF'ten büyük ya da vekil (D800-DFFF)
    ja __karakter_hatasi
    mov rax, rbx
    and rax, -2048
    cmp rax, 0xD800
    je __karakter_hatasi
    mov edi, 1
    cmp rbx, 0x80
    jb 1f
    mov edi, 2
    cmp rbx, 0x800
    jb 1f
    mov edi, 3
    cmp rbx, 0x10000
    jb 1f
    mov edi, 4
1:  push rdi
    call __metin_yeni
    pop rcx
    cmp rcx, 1
    jne 2f
    mov [rax], bl
    jmp 5f
2:  mov rdx, rbx                # son bayttan geriye: 10xxxxxx
    lea r8, [rcx-1]
3:  test r8, r8
    jz 4f
    mov r9, rdx
    and r9, 0x3F
    or r9, 0x80
    mov [rax+r8], r9b
    shr rdx, 6
    dec r8
    jmp 3b
4:  mov r9, 0xF0                # ilk bayt: 110xxxxx, 1110xxxx ya da 11110xxx
    cmp rcx, 4
    je 6f
    mov r9, 0xE0
    cmp rcx, 3
    je 6f
    mov r9, 0xC0
6:  or r9, rdx
    mov [rax], r9b
5:  pop rbx
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

# ── ondalık sayılar (IEEE 754 çift duyarlık) ──
# Değer, sayılar gibi 64 bitlik bir yazmaçta (ham bitleriyle) taşınır. Metne çevirme,
# metinden okuma ve matematik işlevleri x87 ile 80 bitlik duyarlıkla hesaplanır; denetim
# sözcüğü her seferinde açıkça kurulur, böylece Linux ve Windows aynı sonucu verir.

__on_kuvvet:                    # rdi = k -> st0 = 10^k (80 bit)
    mov rax, rdi
    test rax, rax
    jns 1f
    neg rax
1:  fld1
    fld qword ptr [rip+__od_on]
2:  test rax, rax
    jz 4f
    test al, 1
    jz 3f
    fmul st(1), st
3:  fmul st, st
    shr rax, 1
    jmp 2b
4:  fstp st(0)
    test rdi, rdi
    jns 5f
    fdivr qword ptr [rip+__od_bir]
5:  ret

__ondalik_metin:                # rdi = ondalık -> rax = metin (15 anlamlı basamak, Python'un repr'i gibi)
    push rbp
    mov rbp, rsp
    push rbx
    push r12
    push r13
    push r14
    sub rsp, 128                # [rbp-40] x, [rbp-48] denetim sözcükleri, [rbp-56] geçici,
    lea r12, [rbp-160]          # [rbp-72..-58] basamaklar, [rbp-160..] çıktı
    mov rax, rdi
    btr rax, 63
    jnc 1f
    mov byte ptr [r12], 45
    inc r12
1:  movabs rcx, 0x7FF0000000000000
    mov rdx, rax
    and rdx, rcx
    cmp rdx, rcx
    jne 2f
    cmp rax, rcx
    jne 3f
    mov dword ptr [r12], 0x666E69   # "inf"
    add r12, 3
    jmp 90f
3:  lea r12, [rbp-160]
    mov dword ptr [r12], 0x6E616E   # "nan"
    add r12, 3
    jmp 90f
2:  test rax, rax
    jnz 4f
    mov dword ptr [r12], 0x302E30   # "0.0"
    add r12, 3
    jmp 90f
4:  mov [rbp-40], rax
    fnstcw [rbp-48]
    mov word ptr [rbp-46], 0x037F   # 64 bit duyarlık, en yakına yuvarla
    mov word ptr [rbp-44], 0x077F   # 64 bit duyarlık, aşağı yuvarla
    fldcw [rbp-44]
    fldlg2
    fld qword ptr [rbp-40]
    fyl2x                       # log10(x)
    fistp qword ptr [rbp-56]
    fldcw [rbp-46]
    mov r13, [rbp-56]           # r13 = onluk üs
5:  mov edi, 14
    sub rdi, r13
    call __on_kuvvet
    fmul qword ptr [rbp-40]
    fistp qword ptr [rbp-56]    # m = x * 10^(14-üs), 15 basamaklı olmalı
    mov rax, [rbp-56]
    movabs rcx, 1000000000000000
    cmp rax, rcx
    jl 6f
    inc r13
    jmp 5b
6:  movabs rcx, 100000000000000
    cmp rax, rcx
    jge 7f
    dec r13
    jmp 5b
7:  fldcw [rbp-48]
    mov ebx, 10
    mov r8d, 14
8:  xor edx, edx
    div rbx
    add dl, 48
    mov [rbp+r8-72], dl
    dec r8
    jns 8b
    mov r14d, 15                # r14 = sondaki sıfırlar atılınca basamak sayısı
9:  cmp r14, 1
    jbe 10f
    cmp byte ptr [rbp+r14-73], 48
    jne 10f
    dec r14
    jmp 9b
10: cmp r13, -4
    jl 30f
    cmp r13, 16
    jge 30f
    test r13, r13
    js 20f
    xor ecx, ecx                # tam kısım
11: cmp rcx, r13
    jg 12f
    mov al, 48
    cmp rcx, r14
    jae 111f
    mov al, [rbp+rcx-72]
111: mov [r12], al
    inc r12
    inc rcx
    jmp 11b
12: mov byte ptr [r12], 46
    inc r12
    cmp rcx, r14
    jb 13f
    mov byte ptr [r12], 48
    inc r12
    jmp 90f
13: cmp rcx, r14
    jae 90f
    mov al, [rbp+rcx-72]
    mov [r12], al
    inc r12
    inc rcx
    jmp 13b
20: mov word ptr [r12], 0x2E30  # "0." ve sıfırlar
    add r12, 2
    mov rcx, r13
    neg rcx
    dec rcx
21: test rcx, rcx
    jz 22f
    mov byte ptr [r12], 48
    inc r12
    dec rcx
    jmp 21b
22: xor ecx, ecx
23: cmp rcx, r14
    jae 90f
    mov al, [rbp+rcx-72]
    mov [r12], al
    inc r12
    inc rcx
    jmp 23b
30: mov al, [rbp-72]            # üslü yazım: 1.5e-07, 1e+16
    mov [r12], al
    inc r12
    cmp r14, 1
    jbe 32f
    mov byte ptr [r12], 46
    inc r12
    mov ecx, 1
31: cmp rcx, r14
    jae 32f
    mov al, [rbp+rcx-72]
    mov [r12], al
    inc r12
    inc rcx
    jmp 31b
32: mov byte ptr [r12], 101
    mov byte ptr [r12+1], 43
    test r13, r13
    jns 33f
    mov byte ptr [r12+1], 45
    neg r13
33: add r12, 2
    mov rax, r13
    cmp rax, 100
    jb 34f
    xor edx, edx
    mov ecx, 100
    div rcx
    add al, 48
    mov [r12], al
    inc r12
    mov rax, rdx
34: xor edx, edx
    mov ecx, 10
    div rcx
    add al, 48
    add dl, 48
    mov [r12], al
    mov [r12+1], dl
    add r12, 2
90: lea rsi, [rbp-160]
    mov rdi, r12
    sub rdi, rsi
    call __metin_yeni
    mov rdi, rax
    lea rsi, [rbp-160]
    mov rcx, [rax-8]
    rep movsb
    lea rsp, [rbp-32]
    pop r14
    pop r13
    pop r12
    pop rbx
    pop rbp
    ret

__ondalik_ham:                  # rdi = ondalık; satır sonu eklemeden yazar
    call __ondalik_metin
    mov rsi, rax
    mov rdx, [rax-8]
    jmp __ham_yaz

__metinden_ondalik:             # rdi = metin ("-12.5", "3", "1.5e-3") -> rax = ondalık
    push rbx
    push r12
    sub rsp, 16
    mov rcx, [rdi-8]
    xor r8, r8                  # konum
    xor r9, r9                  # eksi mi
    xor eax, eax                # anlamlı basamaklar (en çok 18)
    xor r10, r10                # görülen basamak sayısı
    xor r11, r11                # onluk üs düzeltmesi
    xor r12, r12                # biriken anlamlı basamak sayısı
    xor ebx, ebx                # kesir kısmında mı
    test rcx, rcx
    jz __ondalik_hatasi
    cmp byte ptr [rdi], 45
    jne 1f
    mov r9, 1
    inc r8
1:  cmp r8, rcx
    jae 5f
    movzx edx, byte ptr [rdi+r8]
    cmp edx, 46                 # '.'
    jne 2f
    test ebx, ebx
    jnz __ondalik_hatasi
    mov ebx, 1
    inc r8
    jmp 1b
2:  sub edx, 48
    cmp edx, 9
    ja 4f
    inc r10
    inc r8
    cmp r12, 18
    jae 3f
    imul rax, rax, 10
    add rax, rdx
    sub r11, rbx                # kesirdeki her basamak üssü bir azaltır
    test rax, rax
    jz 1b
    inc r12
    jmp 1b
3:  test ebx, ebx               # sığmayan basamak: tam kısımdaysa üssü artırır
    jnz 1b
    inc r11
    jmp 1b
4:  test r10, r10               # üs: e ya da E
    jz __ondalik_hatasi
    add edx, 48
    or edx, 32
    cmp edx, 101
    jne __ondalik_hatasi
    inc r8
    xor ebx, ebx                # ebx = üssün işareti, rdx = üs
    cmp r8, rcx
    jae __ondalik_hatasi
    movzx edx, byte ptr [rdi+r8]
    cmp edx, 43
    je 41f
    cmp edx, 45
    jne 42f
    mov ebx, 1
41: inc r8
42: cmp r8, rcx
    jae __ondalik_hatasi
    push rax
    xor eax, eax
43: movzx edx, byte ptr [rdi+r8]
    sub edx, 48
    cmp edx, 9
    ja __ondalik_hatasi
    cmp rax, 100000
    jae 44f
    imul rax, rax, 10
    add rax, rdx
44: inc r8
    cmp r8, rcx
    jb 43b
    test ebx, ebx
    jz 45f
    neg rax
45: add r11, rax
    pop rax
    jmp 6f
5:  test r10, r10
    jz __ondalik_hatasi
6:  test rax, rax
    jz 7f
    mov [rsp], rax
    fnstcw [rsp+8]
    mov word ptr [rsp+10], 0x037F
    fldcw [rsp+10]
    mov rdi, r11
    call __on_kuvvet
    fild qword ptr [rsp]
    fmulp st(1), st
    fstp qword ptr [rsp]
    fldcw [rsp+8]
    mov rax, [rsp]
7:  test r9, r9
    jz 8f
    bts rax, 63
8:  add rsp, 16
    pop r12
    pop rbx
    ret

__ondalik_yuvarla:              # rdi = ondalık, rsi = 0 yuvarla (yarımlar sıfırdan uzağa), 1 taban, 2 tavan
    sub rsp, 24                 #  -> rax = sayı
    mov [rsp], rdi
    fnstcw [rsp+8]
    mov word ptr [rsp+10], 0x077F
    cmp rsi, 1
    je 1f
    mov word ptr [rsp+10], 0x0B7F
    cmp rsi, 2
    je 1f
    mov word ptr [rsp+10], 0x0F7F   # sıfıra doğru, önce ±0.5 eklenir
1:  fldcw [rsp+10]
    fld qword ptr [rsp]
    test rsi, rsi
    jnz 2f
    fld qword ptr [rip+__od_yarim]
    test rdi, rdi
    jns 3f
    fchs
3:  faddp st(1), st
2:  fistp qword ptr [rsp]
    fldcw [rsp+8]
    mov rax, [rsp]
    add rsp, 24
    ret

__ondalik_kalan:                # rdi = a, rsi = b (b != 0) -> rax = a - b * tam(a / b), işareti a'nınki
    sub rsp, 8
    mov [rsp], rsi
    fld qword ptr [rsp]
    mov [rsp], rdi
    fld qword ptr [rsp]
1:  fprem
    fnstsw ax
    test ah, 4
    jnz 1b
    fstp qword ptr [rsp]
    fstp st(0)
    mov rax, [rsp]
    add rsp, 8
    ret

__ondalik_sin:                  # rdi = ondalık -> rax = sin
    sub rsp, 8
    mov [rsp], rdi
    fld qword ptr [rsp]
    fsin
    fstp qword ptr [rsp]
    mov rax, [rsp]
    add rsp, 8
    ret

__ondalik_cos:                  # rdi = ondalık -> rax = cos
    sub rsp, 8
    mov [rsp], rdi
    fld qword ptr [rsp]
    fcos
    fstp qword ptr [rsp]
    mov rax, [rsp]
    add rsp, 8
    ret

__ondalik_atan2:                # rdi = y, rsi = x -> rax = atan2(y, x)
    sub rsp, 8
    mov [rsp], rdi
    fld qword ptr [rsp]
    mov [rsp], rsi
    fld qword ptr [rsp]
    fpatan
    fstp qword ptr [rsp]
    mov rax, [rsp]
    add rsp, 8
    ret

__deger_esit:                   # rdi = a, rsi = b, rdx = tür tanımı -> rax = eşitse 1, değilse 0
    mov rax, [rdx]
    cmp rax, 6                  # 6: ondalık (0.0 == -0.0; nan hiçbir şeye eşit değil)
    jne 0f
    movq xmm0, rdi
    movq xmm1, rsi
    ucomisd xmm0, xmm1
    sete al
    setnp cl
    and al, cl
    movzx eax, al
    ret
0:  test rax, rax               # 0: sayı
    jz 7f
    cmp rax, 4                  # 4 kayıt, 5 işlev: aynı değer mi diye adres karşılaştırılır
    jb 1f
7:  cmp rdi, rsi
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
    xor esi, esi                # okumak için aç
    call __sis_ac
    test rax, rax
    js __dosya_hatasi
    mov r13, rax
    call __uc_bas               # içerik doğrudan yığının ucuna okunur
    mov rbx, rax
    xor r12, r12
1:  lea rsi, [rbx+r12]
    lea rdx, [rip+__yigin_son]
    sub rdx, rsi
    jbe __bellek_bitti
    mov rdi, r13
    call __sis_oku
    test rax, rax
    js __dosya_hatasi
    jz 2f
    add r12, rax
    jmp 1b
2:  mov rdi, r13
    call __sis_kapat
    mov rdi, rbx
    mov rsi, r12
    call __uc_bitir
    mov qword ptr [rip+__h_ek], 0
    pop r13
    pop r12
    pop rbx
    ret

__dosya_yaz:                    # rdi = içerik, rsi = yol, rdx = 0x241 (üstüne yaz) ya da 0x441 (ekle)
    push rbx                    #  -> rax = içerik
    push r12
    push r13
    mov rbx, rdi
    mov [rip+__h_ek], rsi
    mov rdi, rsi
    mov rsi, rdx
    call __sis_ac
    test rax, rax
    js __dosya_hatasi
    mov r13, rax
    xor r12, r12
1:  mov rdx, [rbx-8]
    sub rdx, r12
    jz 2f
    lea rsi, [rbx+r12]
    mov rdi, r13
    call __sis_yaz
    test rax, rax
    js __dosya_hatasi
    add r12, rax
    jmp 1b
2:  mov rdi, r13
    call __sis_kapat
    mov qword ptr [rip+__h_ek], 0
    mov rax, rbx
    pop r13
    pop r12
    pop rbx
    ret

__dosya_var:                    # rdi = yol -> rax = dosya varsa 1, yoksa 0
    call __sis_erisim
    test rax, rax
    sete al
    movzx eax, al
    ret

__dosya_sil:                    # rdi = yol
    mov [rip+__h_ek], rdi
    call __sis_sil
    test rax, rax
    js __dosya_hatasi
    mov qword ptr [rip+__h_ek], 0
    xor eax, eax
    ret

__girdi_doldur:                 # tamponu stdin'den doldurur -> rax = 1, girdi bittiyse 0
    xor edi, edi
    lea rsi, [rip+__g_tampon]
    mov edx, 65536
    call __sis_oku
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
    call __uc_bas               # metin doğrudan yığının ucunda büyütülür
    mov rbx, rax
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
    je 7f
    lea rcx, [rbx+r12]
    lea rax, [rip+__yigin_son]
    cmp rcx, rax
    jae __bellek_bitti
    mov [rcx], dl
    inc r12
    jmp 1b
7:  test r12, r12               # "\r\n" ile biten satırın "\r"si de atılır
    jz 3f
    cmp byte ptr [rbx+r12-1], 13
    jne 3f
    dec r12
3:  mov rdi, rbx
    mov rsi, r12
    call __uc_bitir
    pop r12
    pop rbx
    ret

# ── oyun temelleri: zaman, rastgelelik, tuşlar, ekran ──

__zaman:                        # -> rax = milisaniye (tekdüze saat; yalnızca farkı anlamlıdır)
    jmp __sis_zaman

__bekle:                        # rdi = milisaniye -> rax = milisaniye
    test rdi, rdi
    jle 1f
    call __sis_bekle
1:  mov rax, rdi
    ret

__rastgele_tohum:               # rdi = tohum -> rax = tohum
    mov [rip+__rs_durum], rdi
    mov byte ptr [rip+__rs_tohumlu], 1
    mov rax, rdi
    ret

__rastgele:                     # rdi = n (> 0) -> rax = 0, 1, ..., n-1 (splitmix64)
    test rdi, rdi
    jle __rastgele_hatasi
    cmp byte ptr [rip+__rs_tohumlu], 0
    jne 1f
    rdtsc                       # tohum verilmediyse işlemcinin zaman sayacından
    shl rdx, 32
    or rax, rdx
    mov [rip+__rs_durum], rax
    mov byte ptr [rip+__rs_tohumlu], 1
1:  movabs rax, 0x9E3779B97F4A7C15
    add rax, [rip+__rs_durum]
    mov [rip+__rs_durum], rax
    mov rcx, rax
    shr rcx, 30
    xor rax, rcx
    movabs rcx, 0xBF58476D1CE4E5B9
    imul rax, rcx
    mov rcx, rax
    shr rcx, 27
    xor rax, rcx
    movabs rcx, 0x94D049BB133111EB
    imul rax, rcx
    mov rcx, rax
    shr rcx, 31
    xor rax, rcx
    xor edx, edx
    div rdi
    mov rax, rdx
    ret

__goster:                       # rdi = metin; satır sonu eklemeden yazar -> rax = metin
    push rdi
    mov rsi, rdi
    mov rdx, [rdi-8]
    call __ham_yaz
    pop rax
    ret

__tus_kipi:                     # rdi = 1 aç, 0 kapat -> rax = ham kip açıksa 1
    jmp __sis_tus_kipi

__ucbirim_boyutu:               # -> rax = [genişlik, yükseklik]; uçbirim değilse [80, 24]
    push rbx
    push r12
    call __sis_boyut
    mov ebx, eax
    mov r12, rax
    shr r12, 32
    test rbx, rbx
    jz 1f
    test r12, r12
    jnz 2f
1:  mov ebx, 80
    mov r12d, 24
2:  mov edi, 2
    call __liste_yeni
    mov rdi, rax
    mov rsi, rbx
    call __liste_ekle
    mov rdi, rax
    mov rsi, r12
    call __liste_ekle
    pop r12
    pop rbx
    ret

# Girdiden bir tuş alır; beklemez. Girdi oku() ile aynı tampondan gelir.
# Oklar "yukarı", "aşağı", "sağ", "sol"; Enter "enter", Esc "esc", Tab "tab",
# geri silme "geri"; diğer tuşlar yazdıkları karakterdir. Ctrl+C programı bitirir.
__tus:                          # -> rax = tuş (metin); basılan tuş yoksa ""
    push rbx
    push r12
    mov rax, [rip+__g_konum]
    cmp rax, [rip+__g_son]
    jb 1f
    call __sis_tus_doldur
    test rax, rax
    jz 20f
    mov rax, [rip+__g_konum]
1:  lea rbx, [rip+__g_tampon]
    add rbx, rax                # rbx = tuşun başı
    mov r12, [rip+__g_son]
    sub r12, rax                # r12 = tamponda kalan bayt
    movzx eax, byte ptr [rbx]
    cmp eax, 27
    je 10f
    lea rcx, [rip+__t_enter]
    cmp eax, 13
    je 3f
    cmp eax, 10
    je 4f
    lea rcx, [rip+__t_geri]
    cmp eax, 127
    je 4f
    cmp eax, 8
    je 4f
    lea rcx, [rip+__t_tab]
    cmp eax, 9
    je 4f
    cmp eax, 3                  # Ctrl+C
    je 30f
    mov ecx, 1                  # UTF-8 karakterinin bayt sayısı
    cmp eax, 0xC0
    jb 5f
    mov ecx, 2
    cmp eax, 0xE0
    jb 5f
    mov ecx, 3
    cmp eax, 0xF0
    jb 5f
    mov ecx, 4
5:  cmp rcx, r12
    jbe 6f
    mov rcx, r12
6:  add [rip+__g_konum], rcx
    push rcx
    mov rdi, rcx
    call __metin_yeni
    pop rcx
    mov rdi, rax
    mov rsi, rbx
    rep movsb
    jmp 21f
3:  cmp r12, 2                  # "\r\n" tek bir Enter
    jb 4f
    cmp byte ptr [rbx+1], 10
    jne 4f
    inc qword ptr [rip+__g_konum]
4:  inc qword ptr [rip+__g_konum]
    mov rax, rcx
    jmp 21f
10: cmp r12, 3                  # Esc [ A ... : ok tuşları
    jb 12f
    movzx eax, byte ptr [rbx+1]
    cmp eax, 91                 # '['
    je 11f
    cmp eax, 79                 # 'O'
    jne 12f
11: movzx eax, byte ptr [rbx+2]
    sub eax, 65                 # 'A'
    cmp eax, 3
    ja 13f
    add qword ptr [rip+__g_konum], 3
    lea rcx, [rip+__t_oklar]
    mov rax, [rcx+rax*8]
    jmp 21f
13: cmp byte ptr [rbx+1], 91    # tanınmayan dizi: sonuna dek atlanır
    jne 12f
    mov ecx, 2
14: cmp rcx, r12
    jae 15f
    movzx eax, byte ptr [rbx+rcx]
    inc rcx
    cmp eax, 64
    jb 14b
15: add [rip+__g_konum], rcx
20: lea rax, [rip+__t_bos]
    jmp 21f
12: lea rcx, [rip+__t_esc]
    jmp 4b
21: pop r12
    pop rbx
    ret
30: cmp byte ptr [rip+__tk_acik], 0   # uçbirimde: renkler sıfırlanır, imleç geri gelir
    je 31f
    lea rsi, [rip+__t_sifirla]
    mov edx, __t_sifirla_son - __t_sifirla
    call __ham_yaz
31: mov edi, 130
    jmp __cik

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
__yok_hatasi:
    lea rsi, [rip+__h_yok_alan]
    mov edx, __h_yok_alan_son - __h_yok_alan
    jmp __hata
__karakter_hatasi:
    lea rsi, [rip+__h_karakter]
    mov edx, __h_karakter_son - __h_karakter
    jmp __hata
__anahtar_hatasi:
    lea rsi, [rip+__h_anahtar]
    mov edx, __h_anahtar_son - __h_anahtar
    jmp __hata
__ondalik_hatasi:
    lea rsi, [rip+__h_ondalik]
    mov edx, __h_ondalik_son - __h_ondalik
    jmp __hata
__sayi_hatasi:
    lea rsi, [rip+__h_sayi]
    mov edx, __h_sayi_son - __h_sayi
    jmp __hata
__rastgele_hatasi:
    lea rsi, [rip+__h_rastgele]
    mov edx, __h_rastgele_son - __h_rastgele
    jmp __hata
__bellek_bitti:
    lea rsi, [rip+__h_bellek]
    mov edx, __h_bellek_son - __h_bellek
__hata:                         # rsi = mesaj, rdx = uzunluk, r15 = kaynak dosyası ve satırı
    push rdx                    # stderr'e "dosya:satır: çalışma hatası: mesaj" yazıp 1 ile çıkar
    push rsi
    mov rax, r15                # r15'in üst yarısı dosya numarası, alt yarısı satır
    shr rax, 32
    lea rcx, [rip+__dosyalar]
    mov rsi, [rcx+rax*8]
    mov rdx, [rsi-8]
    call __hata_yaz
    lea rsi, [rip+__iki_nokta]
    mov edx, 1
    call __hata_yaz
    sub rsp, 32
    mov edi, r15d
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
    jmp __cik
__hata_yaz:
    mov edi, 2
    jmp __sis_yaz

    .section .rodata
__yeni_satir: .byte 10
__ac: .ascii "["
__kapa: .ascii "]"
__virgul: .ascii ", "
__tirnak: .byte 34
__sus_ac: .ascii "{"
__sus_kapa: .ascii "}"
__iki_nokta: .ascii ": "
__par_ac: .ascii "("
__par_kapa: .ascii ")"
__yok_metni: .ascii "yok"
__islev_metni: .ascii "<işlev>"
__islev_metni_son:
__h_ara: .ascii ": çalışma hatası: "
__h_ara_son:
__h_sifir: .ascii "sıfıra bölme"
__h_sifir_son:
__h_dizin: .ascii "dizin sınırların dışında"
__h_dizin_son:
__h_sayi: .ascii "metin sayıya çevrilemiyor"
__h_sayi_son:
__h_ondalik: .ascii "metin ondalık sayıya çevrilemiyor"
__h_ondalik_son:
    .balign 8
__od_on: .double 10.0
__od_bir: .double 1.0
__od_yarim: .double 0.5
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
__h_yok_alan: .ascii "yok değerinin alanına erişilemez"
__h_yok_alan_son:
__h_karakter: .ascii "geçersiz karakter kodu"
__h_karakter_son:
__h_bellek: .ascii "bellek tükendi"
__h_bellek_son:
__h_rastgele: .ascii "rastgele'nin üst sınırı pozitif olmalı"
__h_rastgele_son:
    .balign 8
__t_oklar: .quad __t_yukari, __t_asagi, __t_sag, __t_sol
    .quad 0
__t_bos: .byte 0
__t_sifirla: .ascii "\033[0m\033[?25h\n"
__t_sifirla_son:
    .balign 8
    .quad 7
__t_yukari: .ascii "yukarı"
    .byte 0
    .balign 8
    .quad 8
__t_asagi: .ascii "aşağı"
    .byte 0
    .balign 8
    .quad 4
__t_sag: .ascii "sağ"
    .byte 0
    .balign 8
    .quad 3
__t_sol: .ascii "sol"
    .byte 0
    .balign 8
    .quad 5
__t_enter: .ascii "enter"
    .byte 0
    .balign 8
    .quad 3
__t_esc: .ascii "esc"
    .byte 0
    .balign 8
    .quad 3
__t_tab: .ascii "tab"
    .byte 0
    .balign 8
    .quad 4
__t_geri: .ascii "geri"
    .byte 0

    .section .data
__yigin_uc: .quad __yigin       # yığının ucu: bir sonraki bloğun başlığı buraya yazılır
__gc_esik: .quad 8388608        # bu kadar ayrılınca çöp toplanır

    .section .bss
    .balign 16
__gc_listeler: .skip 520        # boş bloklar: 16, 24, ..., 512 baytlıkların listeleri (boyut / 8. göz)
__gc_buyuk: .skip 8             # daha büyük boş blokların listesi (__gc_listeler'le birlikte sıfırlanır)
__gc_ayrilan: .skip 8           # son toplamadan bu yana ayrılan bayt
__gc_canli: .skip 8             # son toplamadan sağ çıkan bayt
__gc_tasti: .skip 8             # işaret yığını taştı mı
__cagri_tepe: .skip 8           # çağrı yığınının programın başındaki tepesi
__gc_baslar: .skip YIGIN_BOYUTU / 64 + 64   # blok başları bit haritası
__gc_isaret: .skip 8388608      # işaret yığını (1M blok)
    .balign 16
__yigin: .skip YIGIN_BOYUTU
__yigin_son:
    .skip 64                    # __oku'nun başlık ve yuvarlama payı
__kokler_bas:                   # buradan programın küresel değişkenlerinin sonuna (__kokler_son) dek
                                # her sözcük çöp toplayıcı için köktür
__g_tampon: .skip 65536
__h_ek: .skip 8
__ma_metin: .skip 8             # __metin_al önbelleği: metin, karakter dizini, bayt konumu
__ma_dizin: .skip 8
__ma_bayt: .skip 8
__mu_metin: .skip 8             # __metin_uzunluk önbelleği: metin, karakter sayısı
__mu_uzunluk: .skip 8                 # hata mesajına eklenecek metin (dosya yolu) ya da 0
__g_konum: .skip 8
__g_son: .skip 8
__rs_durum: .skip 8             # rastgele sayı üretecinin durumu
__rs_tohumlu: .skip 8
