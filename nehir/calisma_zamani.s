
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

__ucbirim_mi:                   # rdi = dosya tanıtıcısı -> rax = uçbirimse 1, değilse 0
    sub rsp, 64                 # ioctl(fd, TCGETS, &termios) yalnızca uçbirimde başarılı olur
    mov eax, 16
    mov esi, 0x5401
    mov rdx, rsp
    syscall
    add rsp, 64
    test rax, rax
    sete al
    movzx eax, al
    ret

__ortam_var:                    # rdi = ad -> rax = ortamda "ad=..." varsa 1, yoksa 0
    mov r8, [rip+__baslangic_sp]
    mov rcx, [r8]               # argc; ortam, argv'den ve onun sonundaki 0'dan sonra başlar
    lea r8, [r8+rcx*8+16]
    mov r9, [rdi-8]
1:  mov rsi, [r8]
    test rsi, rsi
    jz 4f
    xor ecx, ecx
2:  cmp rcx, r9
    jae 3f
    mov al, [rdi+rcx]
    cmp al, [rsi+rcx]
    jne 5f
    inc rcx
    jmp 2b
3:  cmp byte ptr [rsi+rcx], 61  # '='
    jne 5f
    mov eax, 1
    ret
5:  add r8, 8
    jmp 1b
4:  xor eax, eax
    ret

__dosya_hata_kodu:              # rdi = yol -> rax = açılabiliyorsa 0, değilse hata kodu (errno);
    push rbx                    # dizinler için EISDIR (21), Python'un open() işlevi gibi
    mov eax, 2                  # open(yol, O_RDONLY)
    xor esi, esi
    xor edx, edx
    syscall
    test rax, rax
    jns 1f
    neg rax
    pop rbx
    ret
1:  mov rbx, rax
    sub rsp, 144                # fstat(fd, &st); st_mode 24. baytta
    mov rdi, rbx
    mov rsi, rsp
    mov eax, 5
    syscall
    mov ecx, [rsp+24]
    add rsp, 144
    and ecx, 0xF000
    mov rdi, rbx
    mov eax, 3                  # close
    push rcx
    syscall
    pop rcx
    xor eax, eax
    cmp ecx, 0x4000             # S_IFDIR
    jne 2f
    mov eax, 21
2:  pop rbx
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
__sayi_hatasi:
    lea rsi, [rip+__h_sayi]
    mov edx, __h_sayi_son - __h_sayi
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

    .section .data
__yigin_uc: .quad __yigin

    .section .bss
    .balign 16
__yigin: .skip YIGIN_BOYUTU
__yigin_son:
    .skip 64                    # __oku'nun başlık ve yuvarlama payı
__g_tampon: .skip 65536
__baslangic_sp: .skip 8         # süreç başlarken yığın: argc, argv...
__h_ek: .skip 8
__ma_metin: .skip 8             # __metin_al önbelleği: metin, karakter dizini, bayt konumu
__ma_dizin: .skip 8
__ma_bayt: .skip 8
__mu_metin: .skip 8             # __metin_uzunluk önbelleği: metin, karakter sayısı
__mu_uzunluk: .skip 8                 # hata mesajına eklenecek metin (dosya yolu) ya da 0
__g_konum: .skip 8
__g_son: .skip 8
