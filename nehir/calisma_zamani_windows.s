
# ── çalışma zamanı: Windows (x86-64) ──
# Ortak kısmın (calisma_zamani.s) kullandığı işletim sistemi yordamları, kernel32.dll ve
# shell32.dll işlevleriyle. Program MinGW-w64'ün gcc'siyle C kitaplığı olmadan bağlanır:
#   gcc -nostdlib -o program.exe program.s -lkernel32 -lshell32 -Wl,-e,_start -Wl,--subsystem,console
#       -Wl,--stack,67108864
#
# Ortak kısım bu yordamları Linux sistem çağrısı gibi kullanır: yalnızca rax, rcx ve r11
# değişir, hata -errno olarak döner. Win64 çağrı düzeninde ise rdx ve r8-r10 de değişir,
# yığın 16 bayta hizalı olmalı ve 32 baytlık gölge alan ayrılmalıdır. WIN_GIRIS ve
# WIN_CIKIS bu farkı kapatır. Aradaki yerel alan:
#   [rsp+32..63]  Win64 işlevlerinin 5.-8. argümanları
#   [rsp+64]      tutamaç         [rsp+72]  uzunluk      [rsp+80]  sayaç
#   [rsp+88]      toplam          [rsp+96]  konsol kipi  [rsp+104] yedek
.macro WIN_GIRIS
    push rbp
    mov rbp, rsp
    push rdx
    push rsi
    push rdi
    push r8
    push r9
    push r10
    and rsp, -16
    sub rsp, 112
.endm

.macro WIN_CIKIS
    lea rsp, [rbp-48]
    pop r10
    pop r9
    pop r8
    pop rdi
    pop rsi
    pop rdx
    pop rbp
    ret
.endm

# rdi'deki dosya tanıtıcısını (0 girdi, 1 çıktı, 2 hata ya da açılmış dosyanın tutamacı)
# Windows tutamacına çevirip rcx'e koyar.
.macro TUTAMAC
    mov rcx, rdi
    cmp rdi, 3
    jae 99f
    lea rcx, [rip+__std_tutamac]
    mov rcx, [rcx+rdi*8]
99:
.endm

    .section .text
_start:
    mov [rip+__cagri_tepe], rsp
    lea rax, [rsp-66846720]     # yığın 64 MB ayrılarak bağlanır (-Wl,--stack,67108864); 256 KB pay
    mov [rip+__yigin_siniri], rax
    and rsp, -16
    sub rsp, 32
    mov ecx, -10                # STD_INPUT_HANDLE
    call GetStdHandle
    mov [rip+__std_tutamac], rax
    mov ecx, -11                # STD_OUTPUT_HANDLE
    call GetStdHandle
    mov [rip+__std_tutamac+8], rax
    mov ecx, -12                # STD_ERROR_HANDLE
    call GetStdHandle
    mov [rip+__std_tutamac+16], rax
    mov rcx, [rip+__std_tutamac+8]
    call __vt_ac
    mov rcx, [rip+__std_tutamac+16]
    call __vt_ac
    call nehir_ana
    xor edi, edi
    jmp __cik

__vt_ac:                        # rcx = tutamaç; konsolsa renk kodlarını (sanal uçbirim) açar
    push rbx
    sub rsp, 48
    mov rbx, rcx
    lea rdx, [rsp+40]
    call GetConsoleMode
    test eax, eax
    jz 1f
    mov edx, [rsp+40]
    or edx, 4                   # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    mov rcx, rbx
    call SetConsoleMode
1:  add rsp, 48
    pop rbx
    ret

__cik:                          # rdi = çıkış kodu
    and rsp, -16
    sub rsp, 32
    call __cikti_bosalt
    call __ekran_kapat          # ekran tamponu açık kaldıysa ayrı ekrandan çıkılır (rdi korunur)
    call __tk_geri              # tuş kipi açık kaldıysa konsol eski hâline döner
    mov ecx, edi
    call ExitProcess

# rdi'deki UTF-8 (sıfırla biten) metni __genis_tampon'a UTF-16 olarak çevirir.
__genis_yol:
    sub rsp, 56
    mov ecx, 65001              # CP_UTF8
    xor edx, edx
    mov r8, rdi
    mov r9d, -1                 # sondaki sıfır dahil
    lea rax, [rip+__genis_tampon]
    mov [rsp+32], rax
    mov qword ptr [rsp+40], 32768
    call MultiByteToWideChar
    add rsp, 56
    ret

# Son Windows hatasını errno'ya çevirir -> eax (artı).
__win_errno:
    sub rsp, 40
    call GetLastError
    add rsp, 40
    cmp eax, 2                  # ERROR_FILE_NOT_FOUND
    je 2f
    cmp eax, 3                  # ERROR_PATH_NOT_FOUND
    je 2f
    cmp eax, 15                 # ERROR_INVALID_DRIVE
    je 2f
    cmp eax, 53                 # ERROR_BAD_NETPATH
    je 2f
    cmp eax, 161                # ERROR_BAD_PATHNAME
    je 2f
    cmp eax, 5                  # ERROR_ACCESS_DENIED
    je 13f
    cmp eax, 32                 # ERROR_SHARING_VIOLATION
    je 13f
    cmp eax, 33                 # ERROR_LOCK_VIOLATION
    je 13f
    cmp eax, 267                # ERROR_DIRECTORY
    je 20f
    cmp eax, 112                # ERROR_DISK_FULL
    je 28f
    mov eax, 22                 # EINVAL
    ret
2:  mov eax, 2                  # ENOENT
    ret
13: mov eax, 13                 # EACCES
    ret
20: mov eax, 20                 # ENOTDIR
    ret
28: mov eax, 28                 # ENOSPC
    ret

# __genis_tampon'daki yol bir dizin mi? -> eax = 1 ya da 0
__genis_dizin_mi:
    sub rsp, 40
    lea rcx, [rip+__genis_tampon]
    call GetFileAttributesW
    add rsp, 40
    cmp eax, -1
    je 1f
    and eax, 16                 # FILE_ATTRIBUTE_DIRECTORY
    shr eax, 4
    ret
1:  xor eax, eax
    ret

__sis_yaz:                      # rdi = fd, rsi = adres, rdx = uzunluk -> rax = yazılan ya da -errno
    WIN_GIRIS
    TUTAMAC
    mov [rsp+64], rcx
    mov [rsp+72], rdx
    lea rdx, [rsp+96]
    call GetConsoleMode
    test eax, eax
    jnz 5f
    mov rcx, [rsp+64]           # dosya ya da boru: baytlar olduğu gibi yazılır
    mov rdx, rsi
    mov r8, [rsp+72]
    lea r9, [rsp+80]
    mov qword ptr [rsp+32], 0
    call WriteFile
    test eax, eax
    jz 9f
    mov eax, [rsp+80]
    WIN_CIKIS
9:  mov rax, -5                 # EIO
    WIN_CIKIS
5:  mov rax, [rsp+72]           # konsol: UTF-8 parça parça UTF-16'ya çevrilip yazılır
    mov [rsp+88], rax
6:  mov r8, [rsp+72]
    test r8, r8
    jz 8f
    cmp r8, 8192
    jbe 7f
    mov r8, 8192
1:  movzx eax, byte ptr [rsi+r8]    # parça bir karakterin ortasında bitmesin
    and eax, 0xC0
    cmp eax, 0x80
    jne 7f
    dec r8
    jnz 1b
    mov r8, 8192
7:  mov [rsp+80], r8
    mov r9, r8
    mov r8, rsi
    mov ecx, 65001
    xor edx, edx
    lea rax, [rip+__genis_tampon]
    mov [rsp+32], rax
    mov qword ptr [rsp+40], 16384
    call MultiByteToWideChar
    mov rcx, [rsp+64]
    lea rdx, [rip+__genis_tampon]
    mov r8d, eax
    lea r9, [rsp+104]
    mov qword ptr [rsp+32], 0
    call WriteConsoleW
    mov rax, [rsp+80]
    add rsi, rax
    sub [rsp+72], rax
    jmp 6b
8:  mov rax, [rsp+88]
    WIN_CIKIS

__sis_oku:                      # rdi = fd, rsi = adres, rdx = uzunluk -> rax = okunan (0: son) ya da -errno
    WIN_GIRIS
    TUTAMAC
    mov [rsp+64], rcx
    mov [rsp+72], rdx
    lea rdx, [rsp+96]
    call GetConsoleMode
    test eax, eax
    jnz 5f
    mov rcx, [rsp+64]
    mov rdx, rsi
    mov r8, [rsp+72]
    lea r9, [rsp+80]
    mov qword ptr [rsp+32], 0
    call ReadFile
    test eax, eax
    jz 9f
    mov eax, [rsp+80]
    WIN_CIKIS
9:  call GetLastError
    cmp eax, 109                # ERROR_BROKEN_PIPE: borunun yazan ucu kapandı, girdi bitti
    je 0f
    cmp eax, 38                 # ERROR_HANDLE_EOF
    je 0f
    mov rax, -5
    WIN_CIKIS
5:  mov rax, [rsp+72]           # konsol: UTF-16 okunup UTF-8'e çevrilir (karakter başına en çok 3 bayt)
    xor edx, edx
    mov ecx, 3
    div rcx
    cmp rax, 16384
    jbe 6f
    mov eax, 16384
6:  test rax, rax
    jz 0f
    mov rcx, [rsp+64]
    lea rdx, [rip+__genis_tampon]
    mov r8, rax
    lea r9, [rsp+80]
    mov qword ptr [rsp+32], 0
    call ReadConsoleW
    test eax, eax
    jz 0f
    mov r9d, [rsp+80]
    test r9d, r9d
    jz 0f
    movzx eax, word ptr [rip+__genis_tampon]
    cmp eax, 26                 # Ctrl+Z: girdinin sonu
    je 0f
    mov ecx, 65001
    xor edx, edx
    lea r8, [rip+__genis_tampon]
    mov [rsp+32], rsi
    mov rax, [rsp+72]
    mov [rsp+40], rax
    mov qword ptr [rsp+48], 0
    mov qword ptr [rsp+56], 0
    call WideCharToMultiByte
    WIN_CIKIS
0:  xor eax, eax
    WIN_CIKIS

__sis_ac:                       # rdi = yol, rsi = bayraklar (0 oku, 0x241 üstüne yaz, 0x441 ekle) -> rax = tutamaç ya da -errno
    WIN_GIRIS
    call __genis_yol
    mov edx, 0x80000000         # GENERIC_READ
    mov eax, 3                  # OPEN_EXISTING
    cmp rsi, 0x241
    jne 1f
    mov edx, 0x40000000         # GENERIC_WRITE
    mov eax, 2                  # CREATE_ALWAYS
1:  cmp rsi, 0x441
    jne 2f
    mov edx, 4                  # FILE_APPEND_DATA: her yazma dosyanın sonuna
    mov eax, 4                  # OPEN_ALWAYS
2:  lea rcx, [rip+__genis_tampon]
    mov r8d, 3                  # FILE_SHARE_READ | FILE_SHARE_WRITE
    xor r9d, r9d
    mov [rsp+32], rax
    mov qword ptr [rsp+40], 0x80    # FILE_ATTRIBUTE_NORMAL
    mov qword ptr [rsp+48], 0
    call CreateFileW
    cmp rax, -1
    je 9f
    WIN_CIKIS
9:  call __win_errno
    cmp eax, 13                 # bir dizini açmaya çalışmak Linux'taki gibi EISDIR olsun
    jne 3f
    call __genis_dizin_mi
    test eax, eax
    mov eax, 13
    jz 3f
    mov eax, 21
3:  neg rax
    WIN_CIKIS

__sis_kapat:                    # rdi = tutamaç
    WIN_GIRIS
    mov rcx, rdi
    call CloseHandle
    xor eax, eax
    WIN_CIKIS

__sis_sil:                      # rdi = yol -> rax = 0 ya da -errno
    WIN_GIRIS
    call __genis_yol
    lea rcx, [rip+__genis_tampon]
    call DeleteFileW
    test eax, eax
    jz 9f
    xor eax, eax
    WIN_CIKIS
9:  call __win_errno
    neg rax
    WIN_CIKIS

__sis_erisim:                   # rdi = yol -> rax = dosya varsa 0, yoksa -errno
    WIN_GIRIS
    call __genis_yol
    lea rcx, [rip+__genis_tampon]
    call GetFileAttributesW
    cmp eax, -1
    je 9f
    xor eax, eax
    WIN_CIKIS
9:  mov rax, -2
    WIN_CIKIS

__dosya_hata_kodu:              # rdi = yol -> rax = okumak için açılabiliyorsa 0, değilse errno
    WIN_GIRIS                   # (dizinler için EISDIR, 21)
    call __genis_yol
    call __genis_dizin_mi
    test eax, eax
    jz 1f
    mov eax, 21
    WIN_CIKIS
1:  xor esi, esi
    call __sis_ac
    test rax, rax
    jns 2f
    neg rax
    WIN_CIKIS
2:  mov rdi, rax
    call __sis_kapat
    xor eax, eax
    WIN_CIKIS

__ucbirim_mi:                   # rdi = dosya tanıtıcısı -> rax = uçbirime (konsola) bağlıysa 1
    WIN_GIRIS
    xor eax, eax
    cmp rdi, 3
    jae 1f
    TUTAMAC
    lea rdx, [rsp+96]
    call GetConsoleMode
    test eax, eax
    setne al
    movzx eax, al
1:  WIN_CIKIS

__ortam_var:                    # rdi = ad -> rax = ortam değişkeni tanımlıysa (boş olsa da) 1
    WIN_GIRIS
    call __genis_yol
    lea rcx, [rip+__genis_tampon]
    xor edx, edx
    xor r8d, r8d
    call GetEnvironmentVariableW    # tanımlıysa gereken boyutu (en az 1) verir
    test eax, eax
    setne al
    movzx eax, al
    WIN_CIKIS

__argumanlar:                   # -> rax = komut satırı argümanlarının listesi (program adı hariç)
    push rbp
    mov rbp, rsp
    push rbx
    push r12
    push r13
    push r14
    and rsp, -16
    sub rsp, 80
    call GetCommandLineW
    mov rcx, rax
    lea rdx, [rsp+64]
    call CommandLineToArgvW     # Windows'un tırnak ve ters bölü kuralları
    mov r12, rax
    movsxd r13, dword ptr [rsp+64]
    mov edi, 4
    call __liste_yeni
    mov r14, rax
    mov ebx, 1
1:  cmp rbx, r13
    jae 2f
    mov ecx, 65001
    xor edx, edx
    mov r8, [r12+rbx*8]
    mov r9d, -1
    lea rax, [rip+__dar_tampon]
    mov [rsp+32], rax
    mov qword ptr [rsp+40], 131072
    mov qword ptr [rsp+48], 0
    mov qword ptr [rsp+56], 0
    call WideCharToMultiByte    # sondaki sıfır dahil bayt sayısı
    lea rdi, [rax-1]
    call __metin_yeni
    mov rdi, rax
    lea rsi, [rip+__dar_tampon]
    mov rcx, [rax-8]
    push rax
    rep movsb
    pop rsi
    mov rdi, r14
    call __liste_ekle
    inc rbx
    jmp 1b
2:  mov rcx, r12
    call LocalFree
    mov rax, r14
    lea rsp, [rbp-32]
    pop r14
    pop r13
    pop r12
    pop rbx
    pop rbp
    ret

__sis_zaman:                    # -> rax = tekdüze saatin milisaniyesi
    WIN_GIRIS
    lea rcx, [rsp+64]
    call QueryPerformanceFrequency
    lea rcx, [rsp+72]
    call QueryPerformanceCounter
    mov rax, [rsp+72]
    mov ecx, 1000
    mul rcx
    div qword ptr [rsp+64]
    WIN_CIKIS

__sis_bekle:                    # rdi = milisaniye; varsa yüksek çözünürlüklü zamanlayıcıyla
    WIN_GIRIS
    mov rcx, [rip+__w_zamanlayici]
    test rcx, rcx
    jnz 1f
    xor ecx, ecx
    xor edx, edx
    mov r8d, 2                  # CREATE_WAITABLE_TIMER_HIGH_RESOLUTION
    mov r9d, 0x1F0003           # TIMER_ALL_ACCESS
    call CreateWaitableTimerExW
    test rax, rax
    jz 5f
    mov [rip+__w_zamanlayici], rax
    mov rcx, rax
1:  imul rax, rdi, -10000       # göreli süre, 100 ns birimiyle
    mov [rsp+64], rax
    lea rdx, [rsp+64]
    xor r8d, r8d
    xor r9d, r9d
    mov qword ptr [rsp+32], 0
    mov qword ptr [rsp+40], 0
    call SetWaitableTimer
    test eax, eax
    jz 5f
    mov rcx, [rip+__w_zamanlayici]
    mov edx, -1                 # INFINITE
    call WaitForSingleObject
    WIN_CIKIS
5:  mov rcx, rdi
    call Sleep
    WIN_CIKIS

__sis_tus_kipi:                 # rdi = 1 aç, 0 kapat -> rax = ham kip açıksa 1
    WIN_GIRIS
    test rdi, rdi
    jz 5f
    mov eax, 1
    cmp byte ptr [rip+__tk_acik], 0
    jne 9f
    mov rcx, [rip+__std_tutamac]
    lea rdx, [rip+__tk_eski]
    call GetConsoleMode
    test eax, eax
    jz 8f
    mov edx, [rip+__tk_eski]
    and edx, -8                 # satır, yankı ve Ctrl+C işleme kapalı
    mov rcx, [rip+__std_tutamac]
    call SetConsoleMode
    mov byte ptr [rip+__tk_acik], 1
    mov eax, 1
    WIN_CIKIS
5:  call __tk_geri
8:  xor eax, eax
9:  WIN_CIKIS

__sis_komut:                    # rdi = komut (metin) -> rax = cmd /s /c ile çalıştırılınca çıkış kodu
    WIN_GIRIS
    call __cikti_bosalt
    mov rsi, rdi                # "cmd.exe /s /c \"" + komut + "\""
    lea rdi, [rip+__cmd_on]
    call __metin_birlestir
    mov rdi, rax
    lea rsi, [rip+__cmd_son]
    call __metin_birlestir
    mov rdi, rax
    call __genis_yol
    lea rdi, [rip+__w_si]       # STARTUPINFOW sıfırlanır, boyutu yazılır
    xor eax, eax
    mov ecx, 13
    rep stosq
    mov dword ptr [rip+__w_si], 104
    xor ecx, ecx
    lea rdx, [rip+__genis_tampon]
    xor r8d, r8d
    xor r9d, r9d
    mov qword ptr [rsp+32], 1   # tutamaçlar devralınır (aynı konsol)
    mov qword ptr [rsp+40], 0
    mov qword ptr [rsp+48], 0
    mov qword ptr [rsp+56], 0
    lea rax, [rip+__w_si]
    mov [rsp+64], rax
    lea rax, [rip+__w_pi]
    mov [rsp+72], rax
    call CreateProcessW
    test eax, eax
    jz 8f
    mov rcx, [rip+__w_pi]
    mov edx, -1
    call WaitForSingleObject
    mov rcx, [rip+__w_pi]
    lea rdx, [rsp+80]
    mov dword ptr [rsp+80], -1
    call GetExitCodeProcess
    mov rcx, [rip+__w_pi]
    call CloseHandle
    mov rcx, [rip+__w_pi+8]
    call CloseHandle
    mov eax, [rsp+80]
    WIN_CIKIS
8:  mov rax, -1
    WIN_CIKIS

__sis_dizin:                    # rdi = yol -> rax = içindekilerin adları (dizinlerin sonunda "/")
    WIN_GIRIS
    mov [rsp+88], rbx           # Win64'te korunması gerekenler
    mov [rsp+96], r12
    mov [rip+__h_ek], rdi
    lea rsi, [rip+__w_yildiz]   # yol + "\*"
    call __metin_birlestir
    mov rdi, rax
    call __genis_yol
    lea rcx, [rip+__genis_tampon]
    lea rdx, [rip+__w_bul]
    call FindFirstFileW
    cmp rax, -1
    jne 1f
    call __win_errno
    neg rax
    mov rbx, [rsp+88]
    mov r12, [rsp+96]
    jmp __dosya_hatasi
1:  mov rbx, rax
    mov edi, 8
    call __liste_yeni
    mov r12, rax
2:  lea rax, [rip+__w_bul+44]   # cFileName: "." ve ".." atlanır
    cmp word ptr [rax], 46
    jne 3f
    cmp word ptr [rax+2], 0
    je 6f
    cmp word ptr [rax+2], 46
    jne 3f
    cmp word ptr [rax+4], 0
    je 6f
3:  mov ecx, 65001
    xor edx, edx
    lea r8, [rip+__w_bul+44]
    mov r9d, -1
    lea rax, [rip+__dar_tampon]
    mov [rsp+32], rax
    mov qword ptr [rsp+40], 131072
    mov qword ptr [rsp+48], 0
    mov qword ptr [rsp+56], 0
    call WideCharToMultiByte    # sondaki sıfır dahil bayt sayısı
    lea rdi, [rax-1]
    mov [rsp+80], rdi
    test dword ptr [rip+__w_bul], 0x10  # FILE_ATTRIBUTE_DIRECTORY: sona "/"
    jz 4f
    inc rdi
4:  call __metin_yeni
    mov rdi, rax
    lea rsi, [rip+__dar_tampon]
    mov rcx, [rsp+80]
    rep movsb
    test dword ptr [rip+__w_bul], 0x10
    jz 5f
    mov byte ptr [rdi], 47
5:  mov rsi, rax
    mov rdi, r12
    call __liste_ekle
6:  mov rcx, rbx
    lea rdx, [rip+__w_bul]
    call FindNextFileW
    test eax, eax
    jnz 2b
    mov rcx, rbx
    call FindClose
    mov qword ptr [rip+__h_ek], 0
    mov rax, r12
    mov rbx, [rsp+88]
    mov r12, [rsp+96]
    WIN_CIKIS

__sis_birakma_ac:               # konsol tuş bırakmalarını zaten bildirir
    movzx eax, byte ptr [rip+__tk_acik]
    mov [rip+__tk_birakma], al
    ret

__tk_geri:                      # tuş kipi açıksa konsolun eski kipini geri yükler (hizalı yığınla çağrılır)
    mov byte ptr [rip+__tk_genis], 0
    mov byte ptr [rip+__tk_birakma], 0
    cmp byte ptr [rip+__tk_acik], 0
    je 1f
    mov byte ptr [rip+__tk_acik], 0
    sub rsp, 40
    mov rcx, [rip+__std_tutamac]
    mov edx, [rip+__tk_eski]
    call SetConsoleMode
    add rsp, 40
1:  ret

__sis_tus_doldur:               # -> rax = girdi hazırsa tampona doldurup 1, değilse 0 (beklemez)
    WIN_GIRIS
    mov rcx, [rip+__std_tutamac]
    mov [rsp+64], rcx
    lea rdx, [rsp+96]
    call GetConsoleMode
    test eax, eax
    jnz 5f
    mov rcx, [rsp+64]           # boruda bekleyen bayt yoksa okunmaz
    call GetFileType
    cmp eax, 3                  # FILE_TYPE_PIPE
    jne 4f
    mov rcx, [rsp+64]
    xor edx, edx
    xor r8d, r8d
    xor r9d, r9d
    mov dword ptr [rsp+80], 0
    lea rax, [rsp+80]
    mov [rsp+32], rax
    mov qword ptr [rsp+40], 0
    call PeekNamedPipe
    test eax, eax
    jz 4f                       # boru kapandı: okumak girdinin bittiğini bildirir
    cmp dword ptr [rsp+80], 0
    je 0f
4:  call __girdi_doldur
    WIN_CIKIS
5:  mov qword ptr [rsp+72], 0   # konsol: tuş olayları UTF-8'e (oklar Esc [ A ... dizilerine) çevrilir
6:  cmp qword ptr [rsp+72], 65000
    jae 8f
    mov rcx, [rsp+64]
    lea rdx, [rsp+80]
    call GetNumberOfConsoleInputEvents
    test eax, eax
    jz 8f
    cmp dword ptr [rsp+80], 0
    je 8f
    mov rcx, [rsp+64]
    lea rdx, [rip+__w_kayit]
    mov r8d, 1
    lea r9, [rsp+80]
    call ReadConsoleInputW
    test eax, eax
    jz 8f
    lea rax, [rip+__w_kayit]
    cmp word ptr [rax], 1       # KEY_EVENT
    jne 6b
    cmp dword ptr [rax+4], 0    # bırakma: istendiyse kitty biçiminde (Esc [ kod ; 1:3 u) yazılır
    jne 61f
    cmp byte ptr [rip+__tk_genis], 0
    je 6b
    call __w_birakma_yaz
    jmp 6b
61:
    movzx ecx, word ptr [rax+14]
    test ecx, ecx
    jnz 7f
    movzx ecx, word ptr [rax+10]    # karaktersiz tuş
    cmp ecx, 0x41                   # Ctrl + harf karakter kodu olmadan geldiyse (bazı klavye
    jb 72f                          # düzenleri ve konsollar): denetim baytına (Ctrl+S = 0x13) çevrilir
    cmp ecx, 0x5A
    ja 72f
    test dword ptr [rax+16], 0xC    # LEFT_CTRL_PRESSED | RIGHT_CTRL_PRESSED
    jz 72f
    sub ecx, 0x40
    lea rdx, [rip+__g_tampon]
    add rdx, [rsp+72]
    mov [rdx], cl
    inc qword ptr [rsp+72]
    jmp 6b
72: sub ecx, 0x21                   # oklar, gezinme ve işlev tuşları, uçbirimlerdeki kaçış
                                    # dizilerine çevrilir
    cmp ecx, 0x5A
    ja 6b
    lea rdx, [rip+__w_vk]
    mov rdx, [rdx+rcx*8]
    test rdx, rdx
    jz 6b
    movzx ecx, byte ptr [rdx]       # dizinin uzunluğu, ardından baytları
    inc rdx
    lea r8, [rip+__g_tampon]
    add r8, [rsp+72]
    add [rsp+72], rcx
71: mov al, [rdx]
    mov [r8], al
    inc rdx
    inc r8
    dec ecx
    jnz 71b
    jmp 6b
7:  lea r8, [rax+14]
    mov ecx, 65001
    xor edx, edx
    mov r9d, 1
    lea rax, [rip+__g_tampon]
    add rax, [rsp+72]
    mov [rsp+32], rax
    mov qword ptr [rsp+40], 8
    mov qword ptr [rsp+48], 0
    mov qword ptr [rsp+56], 0
    call WideCharToMultiByte
    add [rsp+72], rax
    jmp 6b
8:  mov rax, [rsp+72]
    test rax, rax
    jz 0f
    mov [rip+__g_son], rax
    mov qword ptr [rip+__g_konum], 0
    mov eax, 1
    WIN_CIKIS
0:  xor eax, eax
    WIN_CIKIS

__w_birakma_yaz:                # [rsp+8..]: __sis_tus_doldur'un çerçevesi; __w_kayit'teki bırakmayı tampona yazar
    lea rax, [rip+__w_kayit]
    lea rdx, [rip+__g_tampon]
    add rdx, [rsp+8+72]         # çağıranın [rsp+72]'si: tampondaki bayt sayısı
    movzx ecx, word ptr [rax+14]
    test ecx, ecx
    jnz 2f
    movzx ecx, word ptr [rax+10]    # karaktersiz: yalnızca oklar, Esc [ 1 ; 1 : 3 X
    sub ecx, 0x25
    cmp ecx, 3
    ja 9f
    mov byte ptr [rdx], 27
    mov dword ptr [rdx+1], 0x3B315B     # "[1;"
    mov dword ptr [rdx+4], 0x333A31     # "1:3"
    lea r8, [rip+__w_oklar]
    movzx ecx, byte ptr [r8+rcx]
    mov [rdx+7], cl
    add qword ptr [rsp+8+72], 8
    ret
2:  mov byte ptr [rdx], 27      # Esc [ kod ; 1 : 3 u
    mov byte ptr [rdx+1], 91
    lea r8, [rdx+2]
    mov eax, ecx                # kod onluk yazılır (en çok 5 basamak)
    xor r9d, r9d
3:  xor edx, edx
    mov ecx, 10
    div ecx
    add dl, 48
    push rdx
    inc r9
    test eax, eax
    jnz 3b
4:  pop rax
    mov [r8], al
    inc r8
    dec r9
    jnz 4b
    mov dword ptr [r8], 0x333A313B      # ";1:3"
    mov byte ptr [r8+4], 117    # 'u'
    add r8, 5
    lea rax, [rip+__g_tampon]
    sub r8, rax
    mov [rsp+8+72], r8
9:  ret

__sis_boyut:                    # -> rax = (yükseklik << 32) | genişlik; konsol değilse 0
    WIN_GIRIS
    mov rcx, [rip+__std_tutamac+8]
    lea rdx, [rsp+64]
    call GetConsoleScreenBufferInfo
    test eax, eax
    jz 1f
    movsx rax, word ptr [rsp+80]    # srWindow.Bottom - Top + 1
    movsx rcx, word ptr [rsp+76]
    sub rax, rcx
    inc rax
    shl rax, 32
    movsx rdx, word ptr [rsp+78]    # srWindow.Right - Left + 1
    movsx rcx, word ptr [rsp+74]
    sub rdx, rcx
    inc rdx
    or rax, rdx
    WIN_CIKIS
1:  xor eax, eax
    WIN_CIKIS

    .section .rodata
    .balign 8
    .quad 7
__isletim_sistemi_adi: .ascii "windows"
    .byte 0
    .balign 8
    .quad 15
__cmd_on: .ascii "cmd.exe /s /c \""
    .byte 0
    .balign 8
    .quad 1
__cmd_son: .ascii "\""
    .byte 0
    .balign 8
    .quad 2
__w_yildiz: .ascii "\\*"
    .byte 0
__w_oklar: .ascii "DACB"        # sol, yukarı, sağ, aşağı -> Esc [ D/A/C/B
__w_vk_21: .byte 4
    .ascii "\033[5~"
__w_vk_22: .byte 4
    .ascii "\033[6~"
__w_vk_23: .byte 3
    .ascii "\033[F"
__w_vk_24: .byte 3
    .ascii "\033[H"
__w_vk_25: .byte 3
    .ascii "\033[D"
__w_vk_26: .byte 3
    .ascii "\033[A"
__w_vk_27: .byte 3
    .ascii "\033[C"
__w_vk_28: .byte 3
    .ascii "\033[B"
__w_vk_2D: .byte 4
    .ascii "\033[2~"
__w_vk_2E: .byte 4
    .ascii "\033[3~"
__w_vk_70: .byte 3
    .ascii "\033OP"
__w_vk_71: .byte 3
    .ascii "\033OQ"
__w_vk_72: .byte 3
    .ascii "\033OR"
__w_vk_73: .byte 3
    .ascii "\033OS"
__w_vk_74: .byte 5
    .ascii "\033[15~"
__w_vk_75: .byte 5
    .ascii "\033[17~"
__w_vk_76: .byte 5
    .ascii "\033[18~"
__w_vk_77: .byte 5
    .ascii "\033[19~"
__w_vk_78: .byte 5
    .ascii "\033[20~"
__w_vk_79: .byte 5
    .ascii "\033[21~"
__w_vk_7A: .byte 5
    .ascii "\033[23~"
__w_vk_7B: .byte 5
    .ascii "\033[24~"
    .balign 8
__w_vk:     # sanal tuş kodu 0x21 + i -> kaçış dizisi (uzunluk baytı + baytlar) ya da 0
    .quad __w_vk_21, __w_vk_22, __w_vk_23, __w_vk_24, __w_vk_25, __w_vk_26, __w_vk_27, __w_vk_28, 0, 0, 0, 0, __w_vk_2D, __w_vk_2E, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, __w_vk_70, __w_vk_71, __w_vk_72, __w_vk_73, __w_vk_74, __w_vk_75, __w_vk_76, __w_vk_77, __w_vk_78, __w_vk_79, __w_vk_7A, __w_vk_7B

    .section .bss
    .balign 16
__std_tutamac: .skip 24         # girdi, çıktı ve hata tutamaçları
__tk_eski: .skip 8              # tuş kipinden önceki konsol kipi
__tk_acik: .skip 8
__w_zamanlayici: .skip 8        # bekle() için yüksek çözünürlüklü zamanlayıcı
__w_kayit: .skip 24             # konsoldan okunan bir INPUT_RECORD
__w_si: .skip 104               # komut_çalıştır: STARTUPINFOW
__w_pi: .skip 24                # PROCESS_INFORMATION
__w_bul: .skip 600              # dizin_listele: WIN32_FIND_DATAW
__genis_tampon: .skip 65536     # UTF-16 yollar ve konsol metni
__dar_tampon: .skip 131072      # UTF-8'e çevrilen argümanlar
