

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

# ── standart çıktı tamponu ──
# Standart çıktıya yazılanlar 64 KB'lık bir tamponda toplanır ve topluca yazılır. Tampon;
# dolunca, girdi okunmadan, beklenmeden, standart hataya yazılmadan, ekran çizilince ve program
# biterken boşaltılır. Çıktı bir uçbirimse her satır sonunda da boşaltılır. Bir yazma hiçbir
# zaman bölünmez (Windows konsolunda UTF-8 karakterleri parçalanmasın diye).

__ham_yaz:                      # rsi = adres, rdx = uzunluk (rsi ve rdx korunur; rax, rcx, rdi, r11 değişir)
    mov rax, [rip+__ct_dolu]
    lea rcx, [rax+rdx]
    cmp rcx, 65536
    ja 1f
    push rsi
    lea rdi, [rip+__ct_tampon]
    add rdi, rax
    mov rcx, rdx
    rep movsb
    pop rsi
    add [rip+__ct_dolu], rdx
    mov rax, rdx
    ret
1:  call __cikti_bosalt         # sığmıyor: önce tampon boşaltılır
    cmp rdx, 65536
    jbe __ham_yaz
    mov edi, 1                  # tampondan büyük: doğrudan yazılır
    jmp __sis_yaz

__cikti_bosalt:                 # tampondakileri standart çıktıya yazar (rax, rcx, r11 dışı korunur)
    mov rax, [rip+__ct_dolu]
    test rax, rax
    jz 2f
    push rdi
    push rsi
    push rdx
    lea rsi, [rip+__ct_tampon]
    mov rdx, rax
1:  mov edi, 1
    call __sis_yaz
    test rax, rax
    jle 3f                      # yazılamıyor (kapanmış boru gibi): tampon atılır
    add rsi, rax
    sub rdx, rax
    jnz 1b
3:  mov qword ptr [rip+__ct_dolu], 0
    pop rdx
    pop rsi
    pop rdi
2:  ret

__satir_sonu:                   # satır sonu; çıktı bir uçbirimse satır hemen yazılır
    lea rsi, [rip+__yeni_satir]
    mov edx, 1
    call __ham_yaz
    mov al, [rip+__ct_ucbirim]  # 0: henüz bakılmadı, 1: uçbirim, 2: değil
    test al, al
    jnz 1f
    push rdi
    push rsi
    push rdx
    mov edi, 1
    call __ucbirim_mi
    pop rdx
    pop rsi
    pop rdi
    mov cl, 2
    sub cl, al
    mov [rip+__ct_ucbirim], cl
    mov al, cl
1:  cmp al, 1
    je __cikti_bosalt
    ret

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
# taşınmaz. Son toplamadan bu yana ayrılan bellek, toplamadan sağ çıkan kadarı (en az 32 MB)
# olunca yeniden toplanır.

__ayir:                         # rdi = bayt sayısı -> rax = sıfırlanmış bellek (yalnızca rax, rcx, rdx değişir)
    cmp rdi, YIGIN_BOYUTU       # yığından büyük (ya da taşmış) istek
    ja __bellek_bitti
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
    mov rcx, [rax]              # blok sonu; yalnızca daha önce kullanılmış kısmı sıfırlanır:
    add rcx, rax                # hiç dokunulmamış bellek (__yigin_tavan'ın üstü) zaten sıfırdır
    mov rdx, [rip+__yigin_tavan]
    cmp rcx, rdx
    jbe 4f
    mov [rip+__yigin_tavan], rcx
    mov rcx, rdx
4:  sub rcx, r8
    jbe 5f
    shr rcx, 3
    mov rdi, r8
    xor eax, eax
    rep stosq
5:  mov rax, r8
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
    jz 2f
    mov rcx, [rax+8]
    mov [rdx+rdi], rcx
    mov [rax], rdi
    ret
2:  lea rsi, [rip+__gc_buyuk]   # listesi boş küçük blok: büyük listenin ilk bloğu her zaman yeter,
    mov rax, [rsi]              # aramadan bölünür; büyük boş blok yoksa yığının ucundan
    test rax, rax
    jz 6f
    mov rcx, [rax]
    and rcx, -8
    jmp 5f
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
    cmp rax, [rip+__yigin_tavan]    # metin, hiç kullanılmamış belleğe yazıldıysa tavan yükselir
    jbe 1f
    mov [rip+__yigin_tavan], rax
1:  lea rcx, [rdi-8]
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
    cmp rax, 33554432
    jae 7f
    mov eax, 33554432
7:  mov [rip+__gc_esik], rax
    mov qword ptr [rip+__gc_ayrilan], 0
    ret

__liste_yeni:                   # rdi = kapasite (>= 1) -> rax = boş liste
    cmp rdi, YIGIN_BOYUTU / 8   # kapasite * 8 taşmasın
    ja __bellek_bitti
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
    xor eax, eax
    cmp rdi, rsi                # aynı metin
    je 9f
    mov rcx, [rdi-8]
    mov rdx, [rsi-8]
    xor r8, r8
    mov r10, rcx                # r10 = kısa olanın uzunluğu
    cmp rdx, r10
    cmovb r10, rdx
6:  lea r9, [r8+8]              # 8'er bayt karşılaştırılır
    cmp r9, r10
    ja 1f
    mov rax, [rdi+r8]
    mov r9, [rsi+r8]
    cmp rax, r9
    jne 7f
    add r8, 8
    jmp 6b
7:  bswap rax                   # ilk farklı bayt en anlamlı olur
    bswap r9
    cmp rax, r9
    jb 3f
    jmp 4f
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
9:  ret

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
    call __cikti_bosalt         # sıra korunsun: önce standart çıktıdakiler
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

__metinden_sayi:                # rdi = metin -> rax = sayı; sığmıyorsa hata
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
    imul rax, rax, 10           # negatif sayılar eksi yönde biriktirilir: -9223372036854775808 sığar
    jo __buyuk_sayi_hatasi
    test r9, r9
    jnz 2f
    add rax, rdx
    jo __buyuk_sayi_hatasi
    jmp 3f
2:  sub rax, rdx
    jo __buyuk_sayi_hatasi
3:  inc r8
    cmp r8, rcx
    jb 1b
    ret

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
    movabs rcx, 0x8000000000000000  # sığmayan ya da nan: x87 bu değeri verir
    cmp rax, rcx
    jne 4f
    movabs rcx, 0xC3E0000000000000
    cmp rdi, rcx
    jne __tama_hatasi
4:  ret

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

__iki_kuvvet:                   # st0 = t -> st0 = 2^t
    fld st(0)
    frndint                     # n, t
    fld st(1)
    fsub st, st(1)              # t - n, n, t
    f2xm1
    fld1
    faddp st(1), st             # 2^(t-n), n, t
    fscale
    fstp st(1)
    fstp st(1)
    ret

__ondalik_fonk:                 # rdi = x, rsi = 0 tan, 1 atan, 2 üstel, 3 ln, 4 asin, 5 acos -> rax
    sub rsp, 24
    mov [rsp], rdi
    fnstcw [rsp+8]
    mov word ptr [rsp+10], 0x037F
    fldcw [rsp+10]
    cmp rsi, 3
    jne 1f
    fldln2                      # ln x = ln 2 * log2 x
    fld qword ptr [rsp]
    fyl2x
    jmp 9f
1:  fld qword ptr [rsp]
    test rsi, rsi
    jnz 2f
    fptan
    fstp st(0)
    jmp 9f
2:  cmp rsi, 1
    jne 3f
    fld1
    fpatan
    jmp 9f
3:  cmp rsi, 2
    jne 4f
    fldl2e                      # e^x = 2^(x * log2 e)
    fmulp st(1), st
    call __iki_kuvvet
    jmp 9f
4:  fld st(0)                   # asin x = atan2(x, s), acos x = atan2(s, x); s = karekök(1 - x²)
    fmul st, st(0)
    fld1
    fsub st, st(1)
    fsqrt
    fstp st(1)                  # s, x
    cmp rsi, 4
    je 5f
    fxch
5:  fpatan
9:  fstp qword ptr [rsp]
    fldcw [rsp+8]
    mov rax, [rsp]
    add rsp, 24
    ret

__ondalik_us:                   # rdi = taban, rsi = üs (ondalıklar) -> rax = taban^üs
    sub rsp, 40
    mov [rsp], rdi
    mov [rsp+16], rsi
    fnstcw [rsp+8]
    mov word ptr [rsp+10], 0x037F
    fldcw [rsp+10]
    movabs rax, 0x3FF0000000000000  # x^0 = 1
    mov rcx, rsi
    btr rcx, 63
    test rcx, rcx
    jz 9f
    mov rcx, rdi
    btr rcx, 63
    test rcx, rcx
    jnz 1f
    xor eax, eax                # 0^b: b > 0 ise 0, b < 0 ise sonsuz
    test rsi, rsi
    jns 9f
    movabs rax, 0x7FF0000000000000
    jmp 9f
1:  mov [rsp+24], rcx           # |taban|^üs = 2^(üs * log2 |taban|)
    fld qword ptr [rsp+16]
    fld qword ptr [rsp+24]
    fyl2x
    call __iki_kuvvet
    fstp qword ptr [rsp+24]
    mov rax, [rsp+24]
    test rdi, rdi
    jns 9f
    movq xmm0, rsi              # negatif taban: üs tam sayı olmalı; tekse sonuç negatif
    cvttsd2si rcx, xmm0
    cvtsi2sd xmm1, rcx
    ucomisd xmm0, xmm1
    jne 2f
    jp 2f
    test cl, 1
    jz 9f
    bts rax, 63
    jmp 9f
2:  movabs rax, 0x7FF8000000000000  # nan
9:  fldcw [rsp+8]
    add rsp, 40
    ret

__us_sayi:                      # rdi = taban, rsi = üs (>= 0) -> rax = taban^üs
    test rsi, rsi
    js __us_hatasi
    mov eax, 1
1:  test rsi, rsi
    jz 3f
    test sil, 1
    jz 2f
    imul rax, rdi
2:  imul rdi, rdi
    shr rsi, 1
    jmp 1b
3:  ret

__liste_en:                     # rdi = liste, rsi = 0 en küçük, 1 en büyük (sayı); 2, 3 (ondalık) -> rax
    mov rcx, [rdi]
    test rcx, rcx
    jz __bos_liste_hatasi
    mov rdx, [rdi+16]
    mov rax, [rdx]
    cmp rsi, 2
    jae 5f
1:  dec rcx
    jz 9f
    add rdx, 8
    mov r8, [rdx]
    test rsi, rsi
    jnz 2f
    cmp r8, rax
    cmovl rax, r8
    jmp 1b
2:  cmp r8, rax
    cmovg rax, r8
    jmp 1b
5:  movq xmm0, rax
6:  dec rcx
    jz 8f
    add rdx, 8
    movq xmm1, [rdx]
    cmp rsi, 2
    jne 7f
    minsd xmm0, xmm1
    jmp 6b
7:  maxsd xmm0, xmm1
    jmp 6b
8:  movq rax, xmm0
9:  ret

# ── ekran tamponu ──
# ekran_aç ile bir hücre ızgarası kurulur. Program arka tampona yazar (ekran_yaz, ekran_doldur,
# ekran_temizle); ekran_çiz arka tamponu en son çizilenle (ön tampon) karşılaştırır ve yalnızca
# değişen hücreleri, en az imleç ve renk kaçış dizisiyle, tek seferde uçbirime yazar. Hücre
# 16 bayttır: karakterin kod noktası ve renkler (alt 32 bit yazı, üst 32 bit arka plan rengi;
# 0xRRGGBB ya da -1: uçbirimin kendi rengi). Ekran işlevlerinin argümanları yığındadır:
# rdi, son argümanı gösterir (ilk argüman en yüksek adreste).

__ekran_ac:                     # [genişlik, yükseklik] -> rax = 0
    push rbx
    push r12
    push r13
    mov r12, [rdi+8]            # genişlik
    mov r13, [rdi]              # yükseklik
    test r12, r12
    jle __ekran_hatasi
    test r13, r13
    jle __ekran_hatasi
    mov rax, r12
    imul rax, r13
    cmp rax, 200000
    ja __ekran_hatasi
    mov rbx, rax                # hücre sayısı
    mov [rip+__ek_gen], r12
    mov [rip+__ek_yuk], r13
    mov [rip+__ek_hucre], rbx
    mov rdi, rbx
    shl rdi, 4
    call __ayir
    or qword ptr [rax-8], 2     # düz bloklar: içlerinde adres yok
    mov [rip+__ek_arka], rax
    mov rdi, rbx
    shl rdi, 4
    call __ayir
    or qword ptr [rax-8], 2
    mov [rip+__ek_on], rax
    mov rdi, rbx
    shl rdi, 6
    add rdi, 256
    call __ayir
    or qword ptr [rax-8], 2
    mov [rip+__ek_cikti], rax
    mov rdi, [rip+__ek_arka]    # arka: boşluk ve uçbirimin renkleri; ön: geçersiz, ilk çizim her şeyi yazar
    mov rsi, [rip+__ek_on]
    mov rcx, rbx
1:  mov qword ptr [rdi], 32
    mov qword ptr [rdi+8], -1
    mov qword ptr [rsi], -1
    mov qword ptr [rsi+8], -1
    add rdi, 16
    add rsi, 16
    dec rcx
    jnz 1b
    lea rsi, [rip+__ek_ac_dizi]     # ilk açılışta ayrı ekran ve gizli imleç
    mov edx, __ek_ac_dizi_son - __ek_ac_dizi
    cmp byte ptr [rip+__ek_acik], 0
    je 2f
    lea rsi, [rip+__ek_sil_dizi]    # yeniden açılış (boyut değişti): yalnızca silinir
    mov edx, __ek_sil_dizi_son - __ek_sil_dizi
2:  call __ham_yaz
    call __cikti_bosalt
    mov byte ptr [rip+__ek_acik], 1
    xor eax, eax
    pop r13
    pop r12
    pop rbx
    ret

__ekran_kapat:                  # açıksa uçbirimi eski hâline döndürür (yazmaçlar korunur) -> rax = 0
    cmp byte ptr [rip+__ek_acik], 0
    je 1f
    push rsi
    push rdx
    push rdi
    push rcx
    push r11
    mov byte ptr [rip+__ek_acik], 0
    lea rsi, [rip+__ek_kapa_dizi]
    mov edx, __ek_kapa_dizi_son - __ek_kapa_dizi
    call __ham_yaz
    call __cikti_bosalt
    pop r11
    pop rcx
    pop rdi
    pop rdx
    pop rsi
1:  xor eax, eax
    ret

__ekran_temizle:                # [arka plan rengi] -> rax = 0
    cmp byte ptr [rip+__ek_acik], 0
    je __ekran_kapali_hatasi
    mov rax, [rdi]
    shl rax, 32
    mov ecx, -1
    or rax, rcx                 # yazı rengi -1, arka plan verilen
    mov rdi, [rip+__ek_arka]
    mov rcx, [rip+__ek_hucre]
1:  mov qword ptr [rdi], 32
    mov [rdi+8], rax
    add rdi, 16
    dec rcx
    jnz 1b
    xor eax, eax
    ret

__ek_hucre_koy:                 # rdx = hücre, r8 = kod noktası (-2: değiştirme), r9 = yazı, r10 = arka rengi (-1: değiştirme)
    cmp r8, -2
    je 1f
    mov [rdx], r8
1:  cmp r9, -1
    je 2f
    mov [rdx+8], r9d
2:  cmp r10, -1
    je 3f
    mov [rdx+12], r10d
3:  ret

__ek_kod_noktasi:               # rsi = UTF-8 baytları -> r8 = kod noktası, rsi ilerler (rax, rcx değişir)
    movzx r8d, byte ptr [rsi]
    inc rsi
    cmp r8d, 0x80
    jb 9f
    mov ecx, 1
    and r8d, 0x1F
    cmp byte ptr [rsi-1], 0xE0
    jb 1f
    mov ecx, 2
    and r8d, 0x0F
    cmp byte ptr [rsi-1], 0xF0
    jb 1f
    mov ecx, 3
    and r8d, 0x07
1:  shl r8d, 6
    movzx eax, byte ptr [rsi]
    and eax, 0x3F
    or r8d, eax
    inc rsi
    dec ecx
    jnz 1b
9:  ret

__ekran_yaz:                    # [x, y, metin, yazı rengi, arka rengi] -> rax = 0; "\n" alt satıra geçer
    cmp byte ptr [rip+__ek_acik], 0
    je __ekran_kapali_hatasi
    push rbx
    push r12
    push r13
    push r14
    push r15
    mov r12, [rdi+32]           # r12 = x, r13 = y, r14 = satır başı x
    mov r13, [rdi+24]
    mov r14, r12
    mov rsi, [rdi+16]
    mov r15, rsi
    add r15, [rsi-8]            # r15 = metnin sonu
    mov r9, [rdi+8]
    mov r10, [rdi]
1:  cmp rsi, r15
    jae 9f
    call __ek_kod_noktasi
    cmp r8, 10
    jne 2f
    inc r13
    mov r12, r14
    jmp 1b
2:  mov rdi, r8                 # karakterin genişliği: 0 (birleşen işaret) atlanır, 2 iki hücre kaplar
    call __ek_genislik
    test rax, rax
    jz 1b
    mov rbx, rax
    mov rdi, r12
    push rsi
    mov rsi, r13
    mov rdx, rbx
    call __ek_yerlestir
    pop rsi
    add r12, rbx
    jmp 1b
9:  pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    xor eax, eax
    ret

__ekran_doldur:                 # [x, y, genişlik, yükseklik, karakter, yazı rengi, arka rengi] -> rax = 0
    cmp byte ptr [rip+__ek_acik], 0
    je __ekran_kapali_hatasi
    push rbx
    push r12
    push r13
    push r14
    push r15
    mov r12, [rdi+48]           # x1 = en_büyük(x, 0), x2 = en_küçük(x + g, genişlik)
    mov r14, r12
    add r14, [rdi+32]
    mov r13, [rdi+40]           # y1, y2
    mov r15, r13
    add r15, [rdi+24]
    xor eax, eax
    test r12, r12
    cmovs r12, rax
    test r13, r13
    cmovs r13, rax
    mov rax, [rip+__ek_gen]
    cmp r14, rax
    cmovg r14, rax
    mov rax, [rip+__ek_yuk]
    cmp r15, rax
    cmovg r15, rax
    mov r8, -2                  # boş metin: karakter değişmez
    mov rsi, [rdi+16]
    cmp qword ptr [rsi-8], 0
    je 1f
    call __ek_kod_noktasi
1:  mov r9, [rdi+8]
    mov r10, [rdi]
    mov r11d, 1                 # r11 = karakterin genişliği (en az 1)
    cmp r8, -2
    je 2f
    mov rdi, r8
    call __ek_genislik
    cmp rax, 2
    jne 2f
    mov r11d, 2
2:  cmp r13, r15                # satırlar
    jge 9f
    mov rbx, r12
3:  cmp rbx, r14
    jge 4f
    mov rdx, r11
    lea rax, [rbx+r11]          # dikdörtgene sığmayan geniş karakter yerine boşluk
    cmp rax, r14
    jle 31f
    push r8
    mov r8d, 32
    mov edx, 1
    mov rdi, rbx
    mov rsi, r13
    push r11
    call __ek_yerlestir
    pop r11
    pop r8
    jmp 4f
31: mov rdi, rbx
    mov rsi, r13
    push r11
    call __ek_yerlestir
    pop r11
    add rbx, r11
    jmp 3b
4:  inc r13
    jmp 2b
9:  pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    xor eax, eax
    ret

__ek_genislik:                  # rdi = kod noktası -> rax = uçbirimdeki genişliği: 0, 1 ya da 2 (yalnızca rax değişir)
    mov eax, 1
    cmp rdi, 0x300
    jb 9f
    push rsi
    push rcx
    lea rsi, [rip+__gen_sifir]
    mov rcx, [rip+__gen_sifir_sayi]
    call __aralikta
    test rax, rax
    jz 1f
    xor eax, eax
    jmp 8f
1:  lea rsi, [rip+__gen_iki]
    mov rcx, [rip+__gen_iki_sayi]
    call __aralikta
    inc rax                     # içindeyse 2, değilse 1
8:  pop rcx
    pop rsi
9:  ret

__aralikta:                     # rdi = kod noktası, rsi = (baş, son) çiftleri, rcx = çift sayısı -> rax = içindeyse 1
    push r8                     # ikili arama; yalnızca rax değişir
    push r9
    push r10
    push r11
    xor r8d, r8d
    mov r9, rcx
1:  cmp r8, r9
    jae 0f
    lea r10, [r8+r9]
    shr r10, 1
    mov r11d, [rsi+r10*8]
    cmp rdi, r11
    jb 2f
    mov r11d, [rsi+r10*8+4]
    cmp rdi, r11
    jbe 3f
    lea r8, [r10+1]
    jmp 1b
2:  mov r9, r10
    jmp 1b
3:  mov eax, 1
    jmp 4f
0:  xor eax, eax
4:  pop r11
    pop r10
    pop r9
    pop r8
    ret

# (rdi, rsi) hücresine r8 kod noktalı, rdx genişlikli karakteri koyar (r9, r10 renkler; r8 -2 ise
# yalnızca renkler). Geniş karakterin sağ yarısı -3 ("devam") hücresidir; bölünen eski geniş
# karakterlerin kalan yarısı boşluk olur. Satır sonuna sığmayan geniş karakter yerine boşluk konur.
__ek_yerlestir:                 # r8, r9, r10, rsi korunur
    test rsi, rsi
    js 9f
    cmp rsi, [rip+__ek_yuk]
    jge 9f
    test rdi, rdi
    js 9f
    cmp rdi, [rip+__ek_gen]
    jge 9f
    push r8
    push r11
    mov r11, rdx
    cmp r11, 2
    jne 1f
    lea rax, [rdi+1]
    cmp rax, [rip+__ek_gen]
    jl 1f
    mov r8d, 32
    mov r11d, 1
1:  mov rdx, rsi
    imul rdx, [rip+__ek_gen]
    add rdx, rdi
    shl rdx, 4
    add rdx, [rip+__ek_arka]
    cmp r8, -2
    je 5f
    cmp qword ptr [rdx], -3     # geniş bir karakterin sağ yarısının üstüne: sol yarısı boşluk olur
    jne 2f
    mov qword ptr [rdx-16], 32
2:  lea rax, [rdi+1]            # geniş bir karakterin sol yarısının üstüne: sağ yarısı boşluk olur
    cmp rax, [rip+__ek_gen]
    jge 3f
    cmp qword ptr [rdx+16], -3
    jne 3f
    mov qword ptr [rdx+16], 32
3:  call __ek_hucre_koy
    cmp r11, 2
    jne 8f
    lea rax, [rdi+2]            # sağ yarının sağındaki eski devam hücresi boşluk olur
    cmp rax, [rip+__ek_gen]
    jge 4f
    cmp qword ptr [rdx+32], -3
    jne 4f
    mov qword ptr [rdx+32], 32
4:  mov qword ptr [rdx+16], -3  # sağ yarı: devam hücresi, aynı renkler
    mov rax, [rdx+8]
    mov [rdx+24], rax
    jmp 8f
5:  call __ek_hucre_koy
8:  pop r11
    pop r8
9:  ret

__metin_genisligi:              # rdi = metin -> rax = uçbirimde kapladığı sütun sayısı
    push rbx
    push r12
    mov rsi, rdi
    mov r12, rdi
    add r12, [rdi-8]
    xor ebx, ebx
1:  cmp rsi, r12
    jae 2f
    call __ek_kod_noktasi
    mov rdi, r8
    call __ek_genislik
    add rbx, rax
    jmp 1b
2:  mov rax, rbx
    pop r12
    pop rbx
    ret

__ek_sayi:                      # rax = sayı (>= 0) -> r13'e onluk yazar (rax, rcx, rdx, r8 değişir)
    xor r8d, r8d
    mov ecx, 10
1:  xor edx, edx
    div rcx
    add dl, 48
    push rdx
    inc r8
    test rax, rax
    jnz 1b
2:  pop rax
    mov [r13], al
    inc r13
    dec r8
    jnz 2b
    ret

__ek_renk:                      # eax = renk (0xRRGGBB), r9b = 38 yazı / 48 arka -> r13'e ";38;2;r;g;b"
    push rbx
    mov ebx, eax
    mov byte ptr [r13], 59
    inc r13
    movzx eax, r9b
    call __ek_sayi
    mov word ptr [r13], 0x323B  # ";2"
    add r13, 2
    mov r9d, 16
1:  mov byte ptr [r13], 59
    inc r13
    mov eax, ebx
    mov ecx, r9d
    shr eax, cl
    and eax, 0xFF
    call __ek_sayi
    sub r9d, 8
    jns 1b
    pop rbx
    ret

__ekran_ciz:                    # -> rax = uçbirime yazılan bayt sayısı
    cmp byte ptr [rip+__ek_acik], 0
    je __ekran_kapali_hatasi
    push rbx
    push r12
    push r13
    push r14
    push r15
    push rbp
    sub rsp, 24                 # [rsp] imlecin bulunduğu hücre (-1: bilinmiyor), [rsp+8] geçerli renkler
    mov qword ptr [rsp], -1
    movabs rax, 0x7FFFFFFE7FFFFFFE
    mov [rsp+8], rax
    mov r12, [rip+__ek_cikti]
    mov r13, r12
    mov r14, [rip+__ek_arka]
    mov r15, [rip+__ek_on]
    xor ebx, ebx                # hücre dizini
1:  cmp rbx, [rip+__ek_hucre]
    jae 8f
    mov rbp, rbx
    shl rbp, 4
    mov rax, [r14+rbp]
    mov rdx, [r14+rbp+8]
    cmp rax, [r15+rbp]
    jne 2f
    cmp rdx, [r15+rbp+8]
    je 7f
2:  mov [r15+rbp], rax          # ön tampon güncellenir
    mov [r15+rbp+8], rdx
    cmp rax, -3                 # geniş karakterin sağ yarısı: soldaki karakterle zaten yazıldı
    je 7f
    cmp rbx, [rsp]
    je 3f
    mov word ptr [r13], 0x5B1B  # ESC [ satır ; sütun H
    add r13, 2
    mov rax, rbx
    xor edx, edx
    div qword ptr [rip+__ek_gen]
    push rdx
    inc rax
    call __ek_sayi
    mov byte ptr [r13], 59
    inc r13
    pop rax
    inc rax
    call __ek_sayi
    mov byte ptr [r13], 72
    inc r13
3:  mov rdx, [r14+rbp+8]
    cmp rdx, [rsp+8]
    je 5f
    mov [rsp+8], rdx            # ESC [ 0 ; 38;2;r;g;b ; 48;2;r;g;b m
    mov dword ptr [r13], 0x305B1B
    add r13, 3
    cmp edx, -1
    je 4f
    mov eax, edx
    mov r9d, 38
    call __ek_renk
    mov rdx, [rsp+8]
4:  shr rdx, 32
    cmp edx, -1
    je 41f
    mov eax, edx
    mov r9d, 48
    call __ek_renk
41: mov byte ptr [r13], 109
    inc r13
5:  mov rax, [r14+rbp]          # karakter, UTF-8 olarak
    cmp rax, 0x80
    jae 51f
    mov [r13], al
    inc r13
    jmp 6f
51: cmp rax, 0x800
    jae 52f
    mov rcx, rax
    shr rcx, 6
    or cl, 0xC0
    mov [r13], cl
    and al, 0x3F
    or al, 0x80
    mov [r13+1], al
    add r13, 2
    jmp 6f
52: cmp rax, 0x10000
    jae 53f
    mov rcx, rax
    shr rcx, 12
    or cl, 0xE0
    mov [r13], cl
    mov rcx, rax
    shr rcx, 6
    and cl, 0x3F
    or cl, 0x80
    mov [r13+1], cl
    and al, 0x3F
    or al, 0x80
    mov [r13+2], al
    add r13, 3
    jmp 6f
53: mov rcx, rax
    shr rcx, 18
    or cl, 0xF0
    mov [r13], cl
    mov rcx, rax
    shr rcx, 12
    and cl, 0x3F
    or cl, 0x80
    mov [r13+1], cl
    mov rcx, rax
    shr rcx, 6
    and cl, 0x3F
    or cl, 0x80
    mov [r13+2], cl
    and al, 0x3F
    or al, 0x80
    mov [r13+3], al
    add r13, 4
6:  lea rax, [rbx+1]            # imleç bir sağa (geniş karakterde iki sağa) geçti; satır sonunda
    cmp rax, [rip+__ek_hucre]   # nerede olduğu belirsizdir
    jae 62f
    cmp qword ptr [r14+rbp+16], -3
    jne 62f
    inc rax
62: push rax
    xor edx, edx
    div qword ptr [rip+__ek_gen]
    pop rax
    test rdx, rdx
    jnz 61f
    mov rax, -1
61: mov [rsp], rax
7:  inc rbx
    jmp 1b
8:  cmp r13, r12
    je 9f
    mov dword ptr [r13], 0x6D305B1B # ESC [ 0 m
    add r13, 4
    mov rsi, r12
    mov rdx, r13
    sub rdx, r12
    call __ham_yaz
    call __cikti_bosalt
9:  mov rax, r13
    sub rax, r12
    add rsp, 24
    pop rbp
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

# ── sıralama ──
# Kararlı, alttan yukarı birleştirmeli sıralama. Karşılaştırma işlevi Nehir'de yazılmış
# olabildiği için (ve çağrısı yazmaçları bozabildiği için) bütün durum çerçevededir:
#   [rbp-8] kaynak liste  [rbp-16] kip  [rbp-24] işlev  [rbp-32] n  [rbp-40] sonuç listesi
#   [rbp-48] geçici liste [rbp-56] okunan dizi  [rbp-64] yazılan dizi  [rbp-72] genişlik
#   [rbp-80] i  [rbp-88] a  [rbp-96] a sonu  [rbp-104] b  [rbp-112] b sonu  [rbp-120] k

__sr_once:                      # rdi = x, rsi = y -> rax = x, y'den önce gelmeliyse 1
    mov rax, [rbp-16]
    test rax, rax
    jnz 1f
    cmp rdi, rsi                # 0: sayı
    setl al
    movzx eax, al
    ret
1:  cmp rax, 1
    jne 2f
    call __metin_karsilastir    # 1: metin
    shr rax, 63
    ret
2:  cmp rax, 2
    jne 3f
    movq xmm0, rdi              # 2: ondalık
    movq xmm1, rsi
    ucomisd xmm1, xmm0
    seta al
    movzx eax, al
    ret
3:  push rdi                    # 3: programın işlevi önce(x, y)
    push rsi
    call qword ptr [rbp-24]
    add rsp, 16
    test rax, rax
    setne al
    movzx eax, al
    ret

__liste_sirala:                 # rdi = liste, rsi = kip (0 sayı, 1 metin, 2 ondalık, 3 işlevle), rdx = işlev
    push rbp                    #  -> rax = sıralanmış yeni liste
    mov rbp, rsp
    sub rsp, 128
    mov [rbp-8], rdi
    mov [rbp-16], rsi
    mov [rbp-24], rdx
    mov rax, [rdi]
    mov [rbp-32], rax
    mov rdi, rax
    cmp rdi, 1
    jae 1f
    mov edi, 1
1:  push rdi
    call __liste_yeni
    mov [rbp-40], rax
    pop rdi
    call __liste_yeni
    mov [rbp-48], rax
    mov rcx, [rbp-32]           # kaynak sonuca kopyalanır
    mov rax, [rbp-40]
    mov [rax], rcx
    mov rdi, [rax+16]
    mov rsi, [rbp-8]
    mov rsi, [rsi+16]
    rep movsq
    mov rax, [rbp-40]
    mov rax, [rax+16]
    mov [rbp-56], rax
    mov rax, [rbp-48]
    mov rax, [rax+16]
    mov [rbp-64], rax
    mov qword ptr [rbp-72], 1
2:  mov rax, [rbp-72]           # genişlik döngüsü
    cmp rax, [rbp-32]
    jae 9f
    mov qword ptr [rbp-80], 0
3:  mov rax, [rbp-80]           # her çift parça
    cmp rax, [rbp-32]
    jae 8f
    mov [rbp-88], rax
    mov [rbp-120], rax
    add rax, [rbp-72]
    cmp rax, [rbp-32]
    jbe 31f
    mov rax, [rbp-32]
31: mov [rbp-96], rax
    mov [rbp-104], rax
    add rax, [rbp-72]
    cmp rax, [rbp-32]
    jbe 32f
    mov rax, [rbp-32]
32: mov [rbp-112], rax
4:  mov rax, [rbp-88]
    cmp rax, [rbp-96]
    jae 6f
    mov rax, [rbp-104]
    cmp rax, [rbp-112]
    jae 6f
    mov rcx, [rbp-56]
    mov rdx, [rbp-104]
    mov rdi, [rcx+rdx*8]        # y = b'deki
    mov rdx, [rbp-88]
    mov rsi, [rcx+rdx*8]        # x = a'daki
    call __sr_once              # önce(y, x) ise y alınır (kararlı)
    mov rcx, [rbp-56]
    mov r8, [rbp-64]
    mov r9, [rbp-120]
    test rax, rax
    jz 5f
    mov rdx, [rbp-104]
    mov rax, [rcx+rdx*8]
    mov [r8+r9*8], rax
    inc qword ptr [rbp-104]
    inc qword ptr [rbp-120]
    jmp 4b
5:  mov rdx, [rbp-88]
    mov rax, [rcx+rdx*8]
    mov [r8+r9*8], rax
    inc qword ptr [rbp-88]
    inc qword ptr [rbp-120]
    jmp 4b
6:  mov rcx, [rbp-56]           # kalanlar
    mov r8, [rbp-64]
    mov r9, [rbp-120]
    mov rdx, [rbp-88]
61: cmp rdx, [rbp-96]
    jae 62f
    mov rax, [rcx+rdx*8]
    mov [r8+r9*8], rax
    inc rdx
    inc r9
    jmp 61b
62: mov rdx, [rbp-104]
63: cmp rdx, [rbp-112]
    jae 64f
    mov rax, [rcx+rdx*8]
    mov [r8+r9*8], rax
    inc rdx
    inc r9
    jmp 63b
64: mov rax, [rbp-72]
    shl rax, 1
    add [rbp-80], rax
    jmp 3b
8:  mov rax, [rbp-56]           # okunan ve yazılan diziler yer değiştirir
    mov rcx, [rbp-64]
    mov [rbp-56], rcx
    mov [rbp-64], rax
    shl qword ptr [rbp-72], 1
    jmp 2b
9:  mov rax, [rbp-40]           # sonuç geçici dizide kaldıysa sonuca kopyalanır
    mov rdi, [rax+16]
    mov rsi, [rbp-56]
    cmp rdi, rsi
    je 10f
    mov rcx, [rbp-32]
    rep movsq
10: mov rax, [rbp-40]
    leave
    ret

__liste_ters:                   # rdi = liste -> rax = elemanları ters sırada yeni liste
    push rbx
    push rdi
    mov rdi, [rdi]
    cmp rdi, 1
    jae 1f
    mov edi, 1
1:  call __liste_yeni
    pop rsi
    mov rcx, [rsi]
    mov [rax], rcx
    mov rsi, [rsi+16]
    mov rdi, [rax+16]
    lea rdx, [rcx-1]
2:  test rcx, rcx
    jz 3f
    mov rbx, [rsi+rdx*8]
    mov [rdi], rbx
    add rdi, 8
    dec rdx
    dec rcx
    jmp 2b
3:  pop rbx
    ret

# ── tam sayı işlemleri ──
__sayi_bol:                     # rax / rcx -> rax; en küçük sayı / -1 taşar ve kendisi olur (işlemci çökmez)
    test rcx, rcx
    jz __sifira_bolme
    cmp rcx, -1
    je 1f
    cqo
    idiv rcx
    ret
1:  neg rax
    ret

__sayi_kalan:                   # rax % rcx -> rax (işareti bölünenin işaretidir)
    test rcx, rcx
    jz __sifira_bolme
    cmp rcx, -1
    je 1f
    cqo
    idiv rcx
    mov rax, rdx
    ret
1:  xor eax, eax
    ret

__sola_kaydir:                  # rax << rcx; 0-63 dışındaki kaydırmalar 0 verir
    cmp rcx, 63
    ja 1f
    shl rax, cl
    ret
1:  xor eax, eax
    ret

__saga_kaydir:                  # rax >> rcx (işaret korunur); 0-63 dışında 0 ya da -1
    cmp rcx, 63
    jbe 1f
    sar rax, 63
    ret
1:  sar rax, cl
    ret

__ondalik_tama:                 # rdi = ondalık -> rax = sıfıra doğru kesilmiş tam sayı; sığmıyorsa hata
    movq xmm0, rdi
    cvttsd2si rax, xmm0
    movabs rcx, 0x8000000000000000
    cmp rax, rcx
    jne 1f
    movabs rcx, 0xC3E0000000000000  # tam olarak -2^63 ise geçerli
    cmp rdi, rcx
    jne __tama_hatasi
1:  ret

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
    cmp qword ptr [r12-8], 0    # boş ayraç: metin karakterlerine bölünür
    je 6f
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
7:  mov rax, r13
    pop rbp
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

__metin_karakterleri:           # __metin_bol'un boş ayraçlı kolu (oradan atlanır)
6:  cmp rbp, [rbx-8]
    jae 7b
    mov r14, rbp
    movzx eax, byte ptr [rbx+rbp]
    mov ecx, 1
    cmp eax, 0xC0
    jb 8f
    inc ecx
    cmp eax, 0xE0
    jb 8f
    inc ecx
    cmp eax, 0xF0
    jb 8f
    inc ecx
8:  add rbp, rcx
    mov rsi, rbp
    call __bol_parca
    jmp 6b

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
    mov edi, 64
    call __ayir
    mov rdx, [rsp]
    mov [rdx+48], rax           # her girdinin tablodaki gözü (silmeyi hızlandırır)
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
    call __sozluk_ozet
    mov r14, [rbx+32]
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

__sozluk_ozet:                  # rsi = anahtar, rdx = anahtar türü -> rax = özet (rcx, rdx, r8, r9 değişir)
    test rdx, rdx
    jnz 1f
    mov rax, rsi                # sayı: çarpımsal özet
    mov rcx, 0x9E3779B97F4A7C15
    imul rax, rcx
    mov rcx, rax
    shr rcx, 32
    xor rax, rcx
    ret
1:  mov rax, 0xCBF29CE484222325 # metin: FNV-1a
    mov rcx, [rsi-8]
    xor edx, edx
    mov r8, 0x100000001B3
2:  cmp rdx, rcx
    jae 3f
    movzx r9d, byte ptr [rsi+rdx]
    xor rax, r9
    imul rax, r8
    inc rdx
    jmp 2b
3:  ret

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
    mov rax, [rbx+48]
    mov [rax+r12*8], r8
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
    mov rdi, [rbx+8]
    shl rdi, 4
    call __ayir
    mov rdi, rax
    mov rsi, [rbx+48]
    mov rcx, [rbx]
    rep movsq
    mov [rbx+48], rax
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
    mov rcx, [rbx+48]
    mov [rcx+rax*8], r8
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
    push rbx                    # Tablo baştan kurulmaz: silinen gözün ardındaki küme geriye kaydırılır
    push r12                    # (doğrusal yoklamada silme), sonraki girdilerin dizinleri bir azaltılır.
    push r13
    push r14
    push r15
    push rbp
    mov rbx, rdi
    mov r13, rdx
    call __sozluk_ara           # rax = girdi dizini, r8 = tablo gözü
    test rax, rax
    js __anahtar_hatasi
    mov r15, rax
    mov rcx, [rbx+24]
    mov r12, [rcx+rax*8]        # silinen değer
    mov r14, [rbx+32]
    dec r14                     # maske
    mov rbp, r8                 # delik
    mov rax, [rbx+40]
    mov qword ptr [rax+rbp*8], 0
    sub rsp, 8
    mov [rsp], rbp              # j
1:  mov rax, [rsp]
    inc rax
    and rax, r14
    mov [rsp], rax
    mov rcx, [rbx+40]
    mov rdx, [rcx+rax*8]
    test rdx, rdx
    jz 5f                       # boş göz: küme bitti
    dec rdx
    mov rcx, [rbx+16]
    mov rsi, [rcx+rdx*8]
    mov rdx, r13
    call __sozluk_ozet
    and rax, r14                # ev gözü
    mov rcx, [rsp]
    mov rdx, rcx
    sub rdx, rax
    and rdx, r14                # evden j'ye uzaklık
    mov r8, rcx
    sub r8, rbp
    and r8, r14                 # delikten j'ye uzaklık
    cmp rdx, r8
    jb 1b                       # ev gözü (delik, j] arasında: girdi yerinde kalır
    mov rax, [rbx+40]
    mov rdx, [rax+rcx*8]
    mov [rax+rbp*8], rdx
    mov qword ptr [rax+rcx*8], 0
    mov rax, [rbx+48]           # taşınan girdinin gözü
    mov [rax+rdx*8-8], rbp
    mov rbp, rcx
    jmp 1b
5:  add rsp, 8
    mov rdi, [rbx+40]           # silinenden sonraki girdilerin tablodaki dizinleri (dizin + 1) bir azalır
    mov rsi, [rbx+48]
    lea rcx, [r15+1]
6:  cmp rcx, [rbx]
    jae 7f
    mov rax, [rsi+rcx*8]
    dec qword ptr [rdi+rax*8]
    inc rcx
    jmp 6b
7:  mov rcx, [rbx]              # girdi dizileri bir göz geri kaydırılır (sıra korunur)
    dec rcx
    mov [rbx], rcx
    sub rcx, r15
    mov rdi, [rbx+16]
    lea rdi, [rdi+r15*8]
    lea rsi, [rdi+8]
    push rcx
    rep movsq
    mov rcx, [rsp]
    mov rdi, [rbx+24]
    lea rdi, [rdi+r15*8]
    lea rsi, [rdi+8]
    rep movsq
    pop rcx
    mov rdi, [rbx+48]
    lea rdi, [rdi+r15*8]
    lea rsi, [rdi+8]
    rep movsq
    mov rax, r12
    pop rbp
    pop r15
    pop r14
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
    call __cikti_bosalt         # soru ekranda görünsün
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
    call __cikti_bosalt
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

__goster:                       # rdi = metin; satır sonu eklemeden yazar ve hemen gösterir -> rax = metin
    push rdi
    mov rsi, rdi
    mov rdx, [rdi-8]
    call __ham_yaz
    call __cikti_bosalt
    pop rax
    ret

__tus_kipi:                     # rdi = 1 aç, 2 aç ve bırakmaları da iste, 0 kapat -> rax = ham kip açıksa 1
    push rdi
    test rdi, rdi
    jz 1f
    mov edi, 1
1:  call __sis_tus_kipi
    pop rdi
    cmp rdi, 2
    jne 2f
    test rax, rax
    jz 2f
    mov byte ptr [rip+__tk_genis], 1
    push rax
    call __sis_birakma_ac       # işletim sistemine özgü: kitty protokolünü ister ya da konsoldan alır
    pop rax
2:  ret

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
    call __cikti_bosalt
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
13: cmp byte ptr [rbx+1], 91    # Esc [ parametreler son: kitty klavye protokolü ya da tanınmayan dizi
    jne 12f
    call __tus_csi
    jmp 21f
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

# Esc [ ile başlayan diziyi çözer (rbx = dizinin başı, r12 = tamponda kalan bayt).
# kitty klavye protokolü:  Esc [ tuş[:kaydırılmış] ; değiştiriciler[:olay] u   (olay 1 bas, 2 tekrar, 3 bırak)
# ve oklar için Esc [ 1 ; değiştiriciler[:olay] A/B/C/D. Bırakmalar "-" ile başlar: "-a", "-sol".
# Uçbirimin bayrak yanıtı (Esc [ ? bayraklar u), bırakmaların bildirildiğini gösterir.
__tus_csi:                      # -> rax = tuş metni ya da ""
    push rbp
    mov rbp, rsp
    sub rsp, 48                 # [rbp-40..-16]: 4 alan (tuş, kaydırılmış, değiştiriciler, olay); [rbp-8] özel
    xor eax, eax
    mov [rbp-40], rax
    mov [rbp-32], rax
    mov [rbp-24], rax
    mov [rbp-16], rax
    mov [rbp-8], rax
    mov ecx, 2                  # rcx = konum, r8 = alan sırası (alan * 2 + alt alan)
    xor r8d, r8d
1:  cmp rcx, r12
    jae 9f                      # yarım kalmış dizi: atılır
    movzx eax, byte ptr [rbx+rcx]
    inc rcx
    cmp eax, 64
    jae 5f                      # son bayt
    sub eax, 48
    cmp eax, 9
    ja 2f
    cmp r8, 4                   # rakam
    jae 1b
    mov rdx, [rbp+r8*8-40]
    imul rdx, rdx, 10
    add rdx, rax
    cmp rdx, 0x10FFFF
    ja 1b
    mov [rbp+r8*8-40], rdx
    jmp 1b
2:  add eax, 48
    cmp eax, 58                 # ':' alt alan
    jne 3f
    test r8, 1
    jnz 21f
    inc r8
    jmp 1b
21: mov r8d, 99
    jmp 1b
3:  cmp eax, 59                 # ';' sonraki alan
    jne 4f
    or r8, 1
    inc r8
    jmp 1b
4:  mov qword ptr [rbp-8], 1    # < = > ? : özel dizi
    jmp 1b
5:  add [rip+__g_konum], rcx    # dizinin tamamı tüketildi
    cmp qword ptr [rbp-8], 0
    je 6f
    cmp eax, 117                # Esc [ ? bayraklar u: bırakmalar bildirilecek
    jne 9f
    cmp byte ptr [rip+__tk_genis], 0
    je 9f
    mov byte ptr [rip+__tk_birakma], 1
    jmp 9f
6:  cmp qword ptr [rbp-24], 0   # varsayılanlar: değiştiriciler 1, olay 1
    jne 61f
    mov qword ptr [rbp-24], 1
61: cmp qword ptr [rbp-16], 0
    jne 62f
    mov qword ptr [rbp-16], 1
62: cmp eax, 117                # 'u'
    je 7f
    sub eax, 65                 # 'A'..'D': oklar
    cmp eax, 3
    ja 9f
    lea rcx, [rip+__t_oklar]
    mov rax, [rcx+rax*8]
    jmp 8f
7:  mov rax, [rbp-40]           # tuş kodu
    mov rcx, [rbp-24]
    dec rcx
    test cl, 4                  # Ctrl+C
    jz 71f
    cmp rax, 99
    jne 71f
    cmp qword ptr [rbp-16], 3
    je 9f
    jmp 30b
71: test cl, 1                  # Shift: kaydırılmış tuş varsa o
    jz 72f
    mov rdx, [rbp-32]
    test rdx, rdx
    jz 72f
    mov rax, rdx
72: lea rcx, [rip+__t_esc]
    cmp rax, 27
    je 74f
    lea rcx, [rip+__t_enter]
    cmp rax, 13
    je 74f
    lea rcx, [rip+__t_tab]
    cmp rax, 9
    je 74f
    lea rcx, [rip+__t_geri]
    cmp rax, 127
    je 74f
    cmp rax, 8
    je 74f
    cmp rax, 32                 # denetim karakterleri ve özel tuşlar (kitty: 57344 ve üstü) atlanır
    jb 9f
    cmp rax, 0xE000
    jae 9f
    mov rdi, rax
    call __karakter
    jmp 8f
74: mov rax, rcx
8:  cmp qword ptr [rbp-16], 3   # bırakma: başına "-"
    jne 99f
    lea rdi, [rip+__t_eksi]
    mov rsi, rax
    call __metin_birlestir
    jmp 99f
9:  lea rax, [rip+__t_bos]
99: leave
    ret

__tus_birakma_var:              # -> rax = uçbirim tuş bırakmalarını bildiriyorsa 1
    movzx eax, byte ptr [rip+__tk_birakma]
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
__ekran_hatasi:
    lea rsi, [rip+__h_ekran]
    mov edx, __h_ekran_son - __h_ekran
    jmp __hata
__ekran_kapali_hatasi:
    lea rsi, [rip+__h_ekran_kapali]
    mov edx, __h_ekran_kapali_son - __h_ekran_kapali
    jmp __hata
__tama_hatasi:
    lea rsi, [rip+__h_tama]
    mov edx, __h_tama_son - __h_tama
    jmp __hata
__buyuk_sayi_hatasi:
    lea rsi, [rip+__h_buyuk_sayi]
    mov edx, __h_buyuk_sayi_son - __h_buyuk_sayi
    jmp __hata
__yigin_tasti:
    mov rsp, [rip+__cagri_tepe]     # program bitecek: hata yazılırken yığın yetsin diye tepeye dönülür
    lea rsi, [rip+__h_yigin]
    mov edx, __h_yigin_son - __h_yigin
    jmp __hata
__us_hatasi:
    lea rsi, [rip+__h_us]
    mov edx, __h_us_son - __h_us
    jmp __hata
__bos_liste_hatasi:
    lea rsi, [rip+__h_bos_liste]
    mov edx, __h_bos_liste_son - __h_bos_liste
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
    call __ekran_kapat          # hata mesajı ayrı ekranda kaybolmasın
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
    call __cikti_bosalt
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
__h_ekran: .ascii "ekran boyutu geçersiz (genişlik ve yükseklik pozitif, çarpımları en çok 200000 olmalı)"
__h_ekran_son:
__h_ekran_kapali: .ascii "ekran açık değil; önce ekran_aç(genişlik, yükseklik)"
__h_ekran_kapali_son:
__ek_ac_dizi: .ascii "\033[?1049h\033[?25l\033[0m\033[2J"    # ayrı ekran, imleç gizli, silinmiş
__ek_ac_dizi_son:
__ek_sil_dizi: .ascii "\033[0m\033[2J"
__ek_sil_dizi_son:
__ek_kapa_dizi: .ascii "\033[0m\033[?25h\033[?1049l"
__ek_kapa_dizi_son:
__h_tama: .ascii "ondalık sayı tam sayıya sığmıyor"
__h_tama_son:
__h_buyuk_sayi: .ascii "sayı çok büyük; en fazla 9223372036854775807 olabilir"
__h_buyuk_sayi_son:
__h_yigin: .ascii "çağrı yığını taştı (sonu gelmeyen bir özyineleme mi?)"
__h_yigin_son:
__h_us: .ascii "tam sayının üssü negatif olamaz (ondalıkla deneyin: üs(2.0, -1))"
__h_us_son:
__h_bos_liste: .ascii "boş listenin en küçüğü ya da en büyüğü yok"
__h_bos_liste_son:
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
    .balign 8
    .quad 1
__t_eksi: .ascii "-"
    .byte 0
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
__gc_esik: .quad 33554432       # bu kadar ayrılınca çöp toplanır
__yigin_tavan: .quad __yigin    # yığının bugüne dek ulaşılan en yüksek ucu; üstü hiç kullanılmadı

    .section .bss
    .balign 16
__gc_listeler: .skip 520        # boş bloklar: 16, 24, ..., 512 baytlıkların listeleri (boyut / 8. göz)
__gc_buyuk: .skip 8             # daha büyük boş blokların listesi (__gc_listeler'le birlikte sıfırlanır)
__gc_ayrilan: .skip 8           # son toplamadan bu yana ayrılan bayt
__gc_canli: .skip 8             # son toplamadan sağ çıkan bayt
__gc_tasti: .skip 8             # işaret yığını taştı mı
__cagri_tepe: .skip 8           # çağrı yığınının programın başındaki tepesi
__yigin_siniri: .skip 8         # işlevler girişte yığının bunun altına inip inmediğine bakar
__gc_baslar: .skip YIGIN_BOYUTU / 64 + 64   # blok başları bit haritası
__gc_isaret: .skip 8388608      # işaret yığını (1M blok)
    .balign 16
__yigin: .skip YIGIN_BOYUTU
__yigin_son:
    .skip 64                    # __oku'nun başlık ve yuvarlama payı
__kokler_bas:                   # buradan programın küresel değişkenlerinin sonuna (__kokler_son) dek
                                # her sözcük çöp toplayıcı için köktür
__g_tampon: .skip 65536
__ct_tampon: .skip 65536        # standart çıktı tamponu
__h_ek: .skip 8
__ma_metin: .skip 8             # __metin_al önbelleği: metin, karakter dizini, bayt konumu
__ma_dizin: .skip 8
__ma_bayt: .skip 8
__mu_metin: .skip 8             # __metin_uzunluk önbelleği: metin, karakter sayısı
__mu_uzunluk: .skip 8                 # hata mesajına eklenecek metin (dosya yolu) ya da 0
__g_konum: .skip 8
__ct_dolu: .skip 8              # çıktı tamponundaki bayt sayısı
__ct_ucbirim: .skip 8
__g_son: .skip 8
__rs_durum: .skip 8             # rastgele sayı üretecinin durumu
__rs_tohumlu: .skip 8
__tk_genis: .skip 8             # tuş bırakmaları istendi mi
__tk_birakma: .skip 8           # uçbirim bırakmaları bildiriyor mu
__ek_arka: .skip 8              # ekran tamponu: arka ve ön hücreler, çıktı tamponu (kökler)
__ek_on: .skip 8
__ek_cikti: .skip 8
__ek_gen: .skip 8
__ek_yuk: .skip 8
__ek_hucre: .skip 8
__ek_acik: .skip 8

    .section .rodata
# >>> genişlik tabloları
# Unicode 15.1.0; kendi/genislik_uret.py ile üretildi
    .balign 8
__gen_iki_sayi: .quad 120
__gen_iki:
    .long 0x1100, 0x115F, 0x231A, 0x231B, 0x2329, 0x232A, 0x23E9, 0x23EC, 0x23F0, 0x23F0, 0x23F3, 0x23F3
    .long 0x25FD, 0x25FE, 0x2614, 0x2615, 0x2648, 0x2653, 0x267F, 0x267F, 0x2693, 0x2693, 0x26A1, 0x26A1
    .long 0x26AA, 0x26AB, 0x26BD, 0x26BE, 0x26C4, 0x26C5, 0x26CE, 0x26CE, 0x26D4, 0x26D4, 0x26EA, 0x26EA
    .long 0x26F2, 0x26F3, 0x26F5, 0x26F5, 0x26FA, 0x26FA, 0x26FD, 0x26FD, 0x2705, 0x2705, 0x270A, 0x270B
    .long 0x2728, 0x2728, 0x274C, 0x274C, 0x274E, 0x274E, 0x2753, 0x2755, 0x2757, 0x2757, 0x2795, 0x2797
    .long 0x27B0, 0x27B0, 0x27BF, 0x27BF, 0x2B1B, 0x2B1C, 0x2B50, 0x2B50, 0x2B55, 0x2B55, 0x2E80, 0x2E99
    .long 0x2E9B, 0x2EF3, 0x2F00, 0x2FD5, 0x2FF0, 0x303E, 0x3041, 0x3096, 0x3099, 0x30FF, 0x3105, 0x312F
    .long 0x3131, 0x318E, 0x3190, 0x31E3, 0x31EF, 0x321E, 0x3220, 0x3247, 0x3250, 0x4DBF, 0x4E00, 0xA48C
    .long 0xA490, 0xA4C6, 0xA960, 0xA97C, 0xAC00, 0xD7A3, 0xF900, 0xFAFF, 0xFE10, 0xFE19, 0xFE30, 0xFE52
    .long 0xFE54, 0xFE66, 0xFE68, 0xFE6B, 0xFF01, 0xFF60, 0xFFE0, 0xFFE6, 0x16FE0, 0x16FE4, 0x16FF0, 0x16FF1
    .long 0x17000, 0x187F7, 0x18800, 0x18CD5, 0x18D00, 0x18D08, 0x1AFF0, 0x1AFF3, 0x1AFF5, 0x1AFFB, 0x1AFFD, 0x1AFFE
    .long 0x1B000, 0x1B122, 0x1B132, 0x1B132, 0x1B150, 0x1B152, 0x1B155, 0x1B155, 0x1B164, 0x1B167, 0x1B170, 0x1B2FB
    .long 0x1F004, 0x1F004, 0x1F0CF, 0x1F0CF, 0x1F18E, 0x1F18E, 0x1F191, 0x1F19A, 0x1F200, 0x1F202, 0x1F210, 0x1F23B
    .long 0x1F240, 0x1F248, 0x1F250, 0x1F251, 0x1F260, 0x1F265, 0x1F300, 0x1F320, 0x1F32D, 0x1F335, 0x1F337, 0x1F37C
    .long 0x1F37E, 0x1F393, 0x1F3A0, 0x1F3CA, 0x1F3CF, 0x1F3D3, 0x1F3E0, 0x1F3F0, 0x1F3F4, 0x1F3F4, 0x1F3F8, 0x1F43E
    .long 0x1F440, 0x1F440, 0x1F442, 0x1F4FC, 0x1F4FF, 0x1F53D, 0x1F54B, 0x1F54E, 0x1F550, 0x1F567, 0x1F57A, 0x1F57A
    .long 0x1F595, 0x1F596, 0x1F5A4, 0x1F5A4, 0x1F5FB, 0x1F64F, 0x1F680, 0x1F6C5, 0x1F6CC, 0x1F6CC, 0x1F6D0, 0x1F6D2
    .long 0x1F6D5, 0x1F6D7, 0x1F6DC, 0x1F6DF, 0x1F6EB, 0x1F6EC, 0x1F6F4, 0x1F6FC, 0x1F7E0, 0x1F7EB, 0x1F7F0, 0x1F7F0
    .long 0x1F90C, 0x1F93A, 0x1F93C, 0x1F945, 0x1F947, 0x1F9FF, 0x1FA70, 0x1FA7C, 0x1FA80, 0x1FA88, 0x1FA90, 0x1FABD
    .long 0x1FABF, 0x1FAC5, 0x1FACE, 0x1FADB, 0x1FAE0, 0x1FAE8, 0x1FAF0, 0x1FAF8, 0x20000, 0x2FFFD, 0x30000, 0x3FFFD
    .balign 8
__gen_sifir_sayi: .quad 356
__gen_sifir:
    .long 0x300, 0x36F, 0x483, 0x489, 0x591, 0x5BD, 0x5BF, 0x5BF, 0x5C1, 0x5C2, 0x5C4, 0x5C5
    .long 0x5C7, 0x5C7, 0x600, 0x605, 0x610, 0x61A, 0x61C, 0x61C, 0x64B, 0x65F, 0x670, 0x670
    .long 0x6D6, 0x6DD, 0x6DF, 0x6E4, 0x6E7, 0x6E8, 0x6EA, 0x6ED, 0x70F, 0x70F, 0x711, 0x711
    .long 0x730, 0x74A, 0x7A6, 0x7B0, 0x7EB, 0x7F3, 0x7FD, 0x7FD, 0x816, 0x819, 0x81B, 0x823
    .long 0x825, 0x827, 0x829, 0x82D, 0x859, 0x85B, 0x890, 0x891, 0x898, 0x89F, 0x8CA, 0x902
    .long 0x93A, 0x93A, 0x93C, 0x93C, 0x941, 0x948, 0x94D, 0x94D, 0x951, 0x957, 0x962, 0x963
    .long 0x981, 0x981, 0x9BC, 0x9BC, 0x9C1, 0x9C4, 0x9CD, 0x9CD, 0x9E2, 0x9E3, 0x9FE, 0x9FE
    .long 0xA01, 0xA02, 0xA3C, 0xA3C, 0xA41, 0xA42, 0xA47, 0xA48, 0xA4B, 0xA4D, 0xA51, 0xA51
    .long 0xA70, 0xA71, 0xA75, 0xA75, 0xA81, 0xA82, 0xABC, 0xABC, 0xAC1, 0xAC5, 0xAC7, 0xAC8
    .long 0xACD, 0xACD, 0xAE2, 0xAE3, 0xAFA, 0xAFF, 0xB01, 0xB01, 0xB3C, 0xB3C, 0xB3F, 0xB3F
    .long 0xB41, 0xB44, 0xB4D, 0xB4D, 0xB55, 0xB56, 0xB62, 0xB63, 0xB82, 0xB82, 0xBC0, 0xBC0
    .long 0xBCD, 0xBCD, 0xC00, 0xC00, 0xC04, 0xC04, 0xC3C, 0xC3C, 0xC3E, 0xC40, 0xC46, 0xC48
    .long 0xC4A, 0xC4D, 0xC55, 0xC56, 0xC62, 0xC63, 0xC81, 0xC81, 0xCBC, 0xCBC, 0xCBF, 0xCBF
    .long 0xCC6, 0xCC6, 0xCCC, 0xCCD, 0xCE2, 0xCE3, 0xD00, 0xD01, 0xD3B, 0xD3C, 0xD41, 0xD44
    .long 0xD4D, 0xD4D, 0xD62, 0xD63, 0xD81, 0xD81, 0xDCA, 0xDCA, 0xDD2, 0xDD4, 0xDD6, 0xDD6
    .long 0xE31, 0xE31, 0xE34, 0xE3A, 0xE47, 0xE4E, 0xEB1, 0xEB1, 0xEB4, 0xEBC, 0xEC8, 0xECE
    .long 0xF18, 0xF19, 0xF35, 0xF35, 0xF37, 0xF37, 0xF39, 0xF39, 0xF71, 0xF7E, 0xF80, 0xF84
    .long 0xF86, 0xF87, 0xF8D, 0xF97, 0xF99, 0xFBC, 0xFC6, 0xFC6, 0x102D, 0x1030, 0x1032, 0x1037
    .long 0x1039, 0x103A, 0x103D, 0x103E, 0x1058, 0x1059, 0x105E, 0x1060, 0x1071, 0x1074, 0x1082, 0x1082
    .long 0x1085, 0x1086, 0x108D, 0x108D, 0x109D, 0x109D, 0x135D, 0x135F, 0x1712, 0x1714, 0x1732, 0x1733
    .long 0x1752, 0x1753, 0x1772, 0x1773, 0x17B4, 0x17B5, 0x17B7, 0x17BD, 0x17C6, 0x17C6, 0x17C9, 0x17D3
    .long 0x17DD, 0x17DD, 0x180B, 0x180F, 0x1885, 0x1886, 0x18A9, 0x18A9, 0x1920, 0x1922, 0x1927, 0x1928
    .long 0x1932, 0x1932, 0x1939, 0x193B, 0x1A17, 0x1A18, 0x1A1B, 0x1A1B, 0x1A56, 0x1A56, 0x1A58, 0x1A5E
    .long 0x1A60, 0x1A60, 0x1A62, 0x1A62, 0x1A65, 0x1A6C, 0x1A73, 0x1A7C, 0x1A7F, 0x1A7F, 0x1AB0, 0x1ACE
    .long 0x1B00, 0x1B03, 0x1B34, 0x1B34, 0x1B36, 0x1B3A, 0x1B3C, 0x1B3C, 0x1B42, 0x1B42, 0x1B6B, 0x1B73
    .long 0x1B80, 0x1B81, 0x1BA2, 0x1BA5, 0x1BA8, 0x1BA9, 0x1BAB, 0x1BAD, 0x1BE6, 0x1BE6, 0x1BE8, 0x1BE9
    .long 0x1BED, 0x1BED, 0x1BEF, 0x1BF1, 0x1C2C, 0x1C33, 0x1C36, 0x1C37, 0x1CD0, 0x1CD2, 0x1CD4, 0x1CE0
    .long 0x1CE2, 0x1CE8, 0x1CED, 0x1CED, 0x1CF4, 0x1CF4, 0x1CF8, 0x1CF9, 0x1DC0, 0x1DFF, 0x200B, 0x200F
    .long 0x202A, 0x202E, 0x2060, 0x2064, 0x2066, 0x206F, 0x20D0, 0x20F0, 0x2CEF, 0x2CF1, 0x2D7F, 0x2D7F
    .long 0x2DE0, 0x2DFF, 0x302A, 0x302D, 0x3099, 0x309A, 0xA66F, 0xA672, 0xA674, 0xA67D, 0xA69E, 0xA69F
    .long 0xA6F0, 0xA6F1, 0xA802, 0xA802, 0xA806, 0xA806, 0xA80B, 0xA80B, 0xA825, 0xA826, 0xA82C, 0xA82C
    .long 0xA8C4, 0xA8C5, 0xA8E0, 0xA8F1, 0xA8FF, 0xA8FF, 0xA926, 0xA92D, 0xA947, 0xA951, 0xA980, 0xA982
    .long 0xA9B3, 0xA9B3, 0xA9B6, 0xA9B9, 0xA9BC, 0xA9BD, 0xA9E5, 0xA9E5, 0xAA29, 0xAA2E, 0xAA31, 0xAA32
    .long 0xAA35, 0xAA36, 0xAA43, 0xAA43, 0xAA4C, 0xAA4C, 0xAA7C, 0xAA7C, 0xAAB0, 0xAAB0, 0xAAB2, 0xAAB4
    .long 0xAAB7, 0xAAB8, 0xAABE, 0xAABF, 0xAAC1, 0xAAC1, 0xAAEC, 0xAAED, 0xAAF6, 0xAAF6, 0xABE5, 0xABE5
    .long 0xABE8, 0xABE8, 0xABED, 0xABED, 0xFB1E, 0xFB1E, 0xFE00, 0xFE0F, 0xFE20, 0xFE2F, 0xFEFF, 0xFEFF
    .long 0xFFF9, 0xFFFB, 0x101FD, 0x101FD, 0x102E0, 0x102E0, 0x10376, 0x1037A, 0x10A01, 0x10A03, 0x10A05, 0x10A06
    .long 0x10A0C, 0x10A0F, 0x10A38, 0x10A3A, 0x10A3F, 0x10A3F, 0x10AE5, 0x10AE6, 0x10D24, 0x10D27, 0x10EAB, 0x10EAC
    .long 0x10EFD, 0x10EFF, 0x10F46, 0x10F50, 0x10F82, 0x10F85, 0x11001, 0x11001, 0x11038, 0x11046, 0x11070, 0x11070
    .long 0x11073, 0x11074, 0x1107F, 0x11081, 0x110B3, 0x110B6, 0x110B9, 0x110BA, 0x110BD, 0x110BD, 0x110C2, 0x110C2
    .long 0x110CD, 0x110CD, 0x11100, 0x11102, 0x11127, 0x1112B, 0x1112D, 0x11134, 0x11173, 0x11173, 0x11180, 0x11181
    .long 0x111B6, 0x111BE, 0x111C9, 0x111CC, 0x111CF, 0x111CF, 0x1122F, 0x11231, 0x11234, 0x11234, 0x11236, 0x11237
    .long 0x1123E, 0x1123E, 0x11241, 0x11241, 0x112DF, 0x112DF, 0x112E3, 0x112EA, 0x11300, 0x11301, 0x1133B, 0x1133C
    .long 0x11340, 0x11340, 0x11366, 0x1136C, 0x11370, 0x11374, 0x11438, 0x1143F, 0x11442, 0x11444, 0x11446, 0x11446
    .long 0x1145E, 0x1145E, 0x114B3, 0x114B8, 0x114BA, 0x114BA, 0x114BF, 0x114C0, 0x114C2, 0x114C3, 0x115B2, 0x115B5
    .long 0x115BC, 0x115BD, 0x115BF, 0x115C0, 0x115DC, 0x115DD, 0x11633, 0x1163A, 0x1163D, 0x1163D, 0x1163F, 0x11640
    .long 0x116AB, 0x116AB, 0x116AD, 0x116AD, 0x116B0, 0x116B5, 0x116B7, 0x116B7, 0x1171D, 0x1171F, 0x11722, 0x11725
    .long 0x11727, 0x1172B, 0x1182F, 0x11837, 0x11839, 0x1183A, 0x1193B, 0x1193C, 0x1193E, 0x1193E, 0x11943, 0x11943
    .long 0x119D4, 0x119D7, 0x119DA, 0x119DB, 0x119E0, 0x119E0, 0x11A01, 0x11A0A, 0x11A33, 0x11A38, 0x11A3B, 0x11A3E
    .long 0x11A47, 0x11A47, 0x11A51, 0x11A56, 0x11A59, 0x11A5B, 0x11A8A, 0x11A96, 0x11A98, 0x11A99, 0x11C30, 0x11C36
    .long 0x11C38, 0x11C3D, 0x11C3F, 0x11C3F, 0x11C92, 0x11CA7, 0x11CAA, 0x11CB0, 0x11CB2, 0x11CB3, 0x11CB5, 0x11CB6
    .long 0x11D31, 0x11D36, 0x11D3A, 0x11D3A, 0x11D3C, 0x11D3D, 0x11D3F, 0x11D45, 0x11D47, 0x11D47, 0x11D90, 0x11D91
    .long 0x11D95, 0x11D95, 0x11D97, 0x11D97, 0x11EF3, 0x11EF4, 0x11F00, 0x11F01, 0x11F36, 0x11F3A, 0x11F40, 0x11F40
    .long 0x11F42, 0x11F42, 0x13430, 0x13440, 0x13447, 0x13455, 0x16AF0, 0x16AF4, 0x16B30, 0x16B36, 0x16F4F, 0x16F4F
    .long 0x16F8F, 0x16F92, 0x16FE4, 0x16FE4, 0x1BC9D, 0x1BC9E, 0x1BCA0, 0x1BCA3, 0x1CF00, 0x1CF2D, 0x1CF30, 0x1CF46
    .long 0x1D167, 0x1D169, 0x1D173, 0x1D182, 0x1D185, 0x1D18B, 0x1D1AA, 0x1D1AD, 0x1D242, 0x1D244, 0x1DA00, 0x1DA36
    .long 0x1DA3B, 0x1DA6C, 0x1DA75, 0x1DA75, 0x1DA84, 0x1DA84, 0x1DA9B, 0x1DA9F, 0x1DAA1, 0x1DAAF, 0x1E000, 0x1E006
    .long 0x1E008, 0x1E018, 0x1E01B, 0x1E021, 0x1E023, 0x1E024, 0x1E026, 0x1E02A, 0x1E08F, 0x1E08F, 0x1E130, 0x1E136
    .long 0x1E2AE, 0x1E2AE, 0x1E2EC, 0x1E2EF, 0x1E4EC, 0x1E4EF, 0x1E8D0, 0x1E8D6, 0x1E944, 0x1E94A, 0xE0001, 0xE0001
    .long 0xE0020, 0xE007F, 0xE0100, 0xE01EF
# <<< genişlik tabloları
