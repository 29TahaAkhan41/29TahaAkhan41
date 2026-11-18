def oku(metin):
    return [[int(c) for c in satır] for satır in metin.strip().split("\n")]

def uygun(ızgara, s, k, n):
    if n in ızgara[s]:
        return False
    if any(ızgara[i][k] == n for i in range(9)):
        return False
    bs, bk = 3 * (s // 3), 3 * (k // 3)
    for i in range(bs, bs + 3):
        for j in range(bk, bk + 3):
            if ızgara[i][j] == n:
                return False
    return True

deneme = 0

def çöz(ızgara):
    global deneme
    for s in range(9):
        for k in range(9):
            if ızgara[s][k] == 0:
                for n in range(1, 10):
                    if uygun(ızgara, s, k, n):
                        ızgara[s][k] = n
                        deneme += 1
                        if çöz(ızgara):
                            return True
                        ızgara[s][k] = 0
                return False
    return True

bulmaca = """
530070000
600195000
098000060
800060003
400803001
700020006
060000280
000419005
000080079
"""
ı = oku(bulmaca)
print("çözüldü" if çöz(ı) else "çözümsüz", "deneme:", deneme)
for satır in ı:
    print(" ".join(str(x) for x in satır))
