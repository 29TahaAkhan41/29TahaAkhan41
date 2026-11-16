
# ── çalışma zamanı: Linux (x86-64) ──
# Ortak kısmın (calisma_zamani.s) kullandığı işletim sistemi yordamları.
    .section .text
_start:
    mov [rip+__baslangic_sp], rsp
    lea rsp, [rip+__cagri_yigini_son]   # program kendi 64 MB'lık çağrı yığınında çalışır
    mov [rip+__cagri_tepe], rsp
    lea rax, [rip+__cagri_yigini+65536] # altta hata mesajı için pay
    mov [rip+__yigin_siniri], rax
    call nehir_ana
    xor edi, edi
    jmp __cik

__cik:                          # rdi = çıkış kodu
    call __cikti_bosalt
    push rdi
    call __ekran_kapat          # ekran tamponu açık kaldıysa ayrı ekrandan çıkılır
    call __tk_geri              # tuş kipi açık kaldıysa uçbirim eski hâline döner
    pop rdi
    mov eax, 60
    syscall

__sis_yaz:                      # rdi = fd, rsi = adres, rdx = uzunluk -> rax = yazılan ya da -errno
    mov eax, 1
    syscall
    ret

__sis_oku:                      # rdi = fd, rsi = adres, rdx = uzunluk -> rax = okunan (0: son) ya da -errno
    xor eax, eax
    syscall
    ret

__sis_ac:                       # rdi = yol, rsi = bayraklar (0 oku, 0x241 üstüne yaz, 0x441 ekle) -> rax = fd ya da -errno
    push rdx
    mov edx, 420                # 0644
    mov eax, 2
    syscall
    pop rdx
    ret

__sis_kapat:                    # rdi = fd
    mov eax, 3
    syscall
    ret

__sis_sil:                      # rdi = yol -> rax = 0 ya da -errno
    mov eax, 87                 # unlink
    syscall
    ret

__sis_erisim:                   # rdi = yol -> rax = dosya varsa 0, yoksa -errno
    push rsi
    mov eax, 21                 # access(yol, F_OK)
    xor esi, esi
    syscall
    pop rsi
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

__sis_zaman:                    # -> rax = tekdüze saatin milisaniyesi
    push rdi
    push rsi
    push rdx
    sub rsp, 16
    mov eax, 228                # clock_gettime(CLOCK_MONOTONIC, &ts)
    mov edi, 1
    mov rsi, rsp
    syscall
    mov rax, [rsp+8]
    xor edx, edx
    mov ecx, 1000000
    div rcx
    imul rdx, [rsp], 1000
    add rax, rdx
    add rsp, 16
    pop rdx
    pop rsi
    pop rdi
    ret

__sis_bekle:                    # rdi = milisaniye
    push rdi
    push rsi
    push rdx
    sub rsp, 16
    mov rax, rdi
    xor edx, edx
    mov ecx, 1000
    div rcx
    mov [rsp], rax
    imul rdx, rdx, 1000000
    mov [rsp+8], rdx
    mov eax, 35                 # nanosleep(&ts, 0)
    mov rdi, rsp
    xor esi, esi
    syscall
    add rsp, 16
    pop rdx
    pop rsi
    pop rdi
    ret

__sis_tus_doldur:               # -> rax = girdi hazırsa tampona doldurup 1, değilse 0 (beklemez)
    push rdi
    push rsi
    push rdx
    sub rsp, 16
    mov dword ptr [rsp], 0      # poll({fd 0, POLLIN}, 1, 0)
    mov dword ptr [rsp+4], 1
    mov eax, 7
    mov rdi, rsp
    mov esi, 1
    xor edx, edx
    syscall
    add rsp, 16
    test rax, rax
    jle 1f
    call __girdi_doldur
    jmp 2f
1:  xor eax, eax
2:  pop rdx
    pop rsi
    pop rdi
    ret

__sis_tus_kipi:                 # rdi = 1 aç, 0 kapat -> rax = ham kip açıksa 1
    push rdi
    push rsi
    push rdx
    test rdi, rdi
    jz 5f
    mov eax, 1
    cmp byte ptr [rip+__tk_acik], 0
    jne 9f
    mov eax, 16                 # ioctl(0, TCGETS, &eski): yalnızca uçbirimde başarılı olur
    xor edi, edi
    mov esi, 0x5401
    lea rdx, [rip+__tk_eski]
    syscall
    test rax, rax
    jnz 8f
    sub rsp, 64
    lea rsi, [rip+__tk_eski]
    mov rdi, rsp
    mov ecx, 8
    rep movsq
    and dword ptr [rsp], -1281      # c_iflag: ICRNL ve IXON kapalı
    and dword ptr [rsp+12], -32780  # c_lflag: ISIG, ICANON, ECHO ve IEXTEN kapalı
    mov byte ptr [rsp+22], 0        # VTIME
    mov byte ptr [rsp+23], 1        # VMIN: oku() yine bir bayt bekler; tuş() hiç beklemez
    mov eax, 16                 # ioctl(0, TCSETS, &yeni)
    xor edi, edi
    mov esi, 0x5402
    mov rdx, rsp
    syscall
    add rsp, 64
    mov byte ptr [rip+__tk_acik], 1
    mov eax, 1
    jmp 9f
5:  call __tk_geri
8:  xor eax, eax
9:  pop rdx
    pop rsi
    pop rdi
    ret

__sis_birakma_ac:               # kitty klavye protokolü istenir (bayraklar 1|2|4|8: olay türleri, bütün
    call __cikti_bosalt         # tuşlar kaçış dizisi olarak) ve desteklenip desteklenmediği sorulur
    push rdi
    push rsi
    push rdx
    mov edi, 1
    lea rsi, [rip+__kitty_ac]
    mov edx, __kitty_ac_son - __kitty_ac
    call __sis_yaz
    pop rdx
    pop rsi
    pop rdi
    ret

__tk_geri:                      # tuş kipi açıksa uçbirimin eski ayarlarını geri yükler
    cmp byte ptr [rip+__tk_genis], 0
    je 2f
    mov byte ptr [rip+__tk_genis], 0
    mov byte ptr [rip+__tk_birakma], 0
    mov edi, 1                  # kitty protokolü kapatılır
    lea rsi, [rip+__kitty_kapa]
    mov edx, __kitty_kapa_son - __kitty_kapa
    call __sis_yaz
2:  cmp byte ptr [rip+__tk_acik], 0
    je 1f
    mov byte ptr [rip+__tk_acik], 0
    mov eax, 16                 # ioctl(0, TCSETS, &eski)
    xor edi, edi
    mov esi, 0x5402
    lea rdx, [rip+__tk_eski]
    syscall
1:  ret

__sis_boyut:                    # -> rax = (yükseklik << 32) | genişlik; uçbirim değilse 0
    push rdi
    push rsi
    push rdx
    sub rsp, 16
    mov qword ptr [rsp], 0
    mov eax, 16                 # ioctl(1, TIOCGWINSZ, &ws)
    mov edi, 1
    mov esi, 0x5413
    mov rdx, rsp
    syscall
    movzx eax, word ptr [rsp]   # satır
    shl rax, 32
    movzx ecx, word ptr [rsp+2] # sütun
    or rax, rcx
    add rsp, 16
    pop rdx
    pop rsi
    pop rdi
    ret

    .section .rodata
__kitty_ac: .ascii "\033[>15u\033[?u"
__kitty_ac_son:
__kitty_kapa: .ascii "\033[<u"
__kitty_kapa_son:
    .balign 8
    .quad 5
__isletim_sistemi_adi: .ascii "linux"
    .byte 0

    .section .bss
    .balign 8
__baslangic_sp: .skip 8         # süreç başlarken yığın: argc, argv..., 0, ortam..., 0
__tk_eski: .skip 64             # tuş kipinden önceki uçbirim ayarları (termios)
__tk_acik: .skip 8
    .balign 16
__cagri_yigini: .skip 67108864  # çağrı yığını (dokunulmadıkça bellek harcamaz)
__cagri_yigini_son:
