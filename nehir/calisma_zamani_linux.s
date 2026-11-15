
# ── çalışma zamanı: Linux (x86-64) ──
# Ortak kısmın (calisma_zamani.s) kullandığı işletim sistemi yordamları.
    .section .text
_start:
    mov [rip+__baslangic_sp], rsp
    call nehir_ana
    xor edi, edi
    jmp __cik

__cik:                          # rdi = çıkış kodu
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

    .section .rodata
    .balign 8
    .quad 5
__isletim_sistemi_adi: .ascii "linux"
    .byte 0

    .section .bss
    .balign 8
__baslangic_sp: .skip 8         # süreç başlarken yığın: argc, argv..., 0, ortam..., 0
