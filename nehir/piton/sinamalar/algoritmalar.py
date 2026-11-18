def elek(n):
    asal = [True] * (n + 1)
    asal[0] = asal[1] = False
    i = 2
    while i * i <= n:
        if asal[i]:
            for j in range(i * i, n + 1, i):
                asal[j] = False
        i += 1
    return [i for i, a in enumerate(asal) if a]

def hanoi(n, kaynak, hedef, ara, hamleler):
    if n == 0:
        return
    hanoi(n - 1, kaynak, ara, hedef, hamleler)
    hamleler.append((kaynak, hedef))
    hanoi(n - 1, ara, hedef, kaynak, hamleler)

def ikili_ara(l, x):
    alt, üst = 0, len(l) - 1
    while alt <= üst:
        orta = (alt + üst) // 2
        if l[orta] == x:
            return orta
        elif l[orta] < x:
            alt = orta + 1
        else:
            üst = orta - 1
    return -1

önbellek = {}
def fib(n):
    if n in önbellek:
        return önbellek[n]
    sonuç = n if n < 2 else fib(n - 1) + fib(n - 2)
    önbellek[n] = sonuç
    return sonuç

def matris_çarp(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))] for i in range(len(a))]

def kabarcık(l):
    l = l[:]
    for i in range(len(l)):
        for j in range(len(l) - 1 - i):
            if l[j] > l[j + 1]:
                l[j], l[j + 1] = l[j + 1], l[j]
    return l

asallar = elek(100)
print(len(asallar), asallar[-5:], sum(asallar))
h = []
hanoi(5, "A", "C", "B", h)
print(len(h), h[:3])
print(ikili_ara(asallar, 61), ikili_ara(asallar, 60), fib(90))
print(matris_çarp([[1, 2], [3, 4]], [[5, 6], [7, 8]]))
print(kabarcık([5, 2, 9, 1, 5, 6]), sorted("nehirdil"), "".join(sorted("nehirdil", reverse=True)))
yığın = []
for c in "((a)(b))":
    if c == "(":
        yığın.append(c)
    elif c == ")":
        yığın.pop()
print("dengeli" if not yığın else "dengesiz")
kuyruk = [1, 2, 3]
kuyruk.append(4)
print(kuyruk.pop(0), kuyruk, kuyruk.index(3), kuyruk.count(2))
kelimeler = "bir iki üç bir iki bir".split()
sayım = {}
for k in kelimeler:
    sayım[k] = sayım.get(k, 0) + 1
print(sayım, sorted(sayım.items(), key=lambda kv: -kv[1]), max(sayım, key=sayım.get))
ızgara = [[0] * 3 for _ in range(3)]
ızgara[1][1] = 5
print(ızgara, [satır[:] for satır in ızgara][1])
print(list(range(10, 0, -3)), list(reversed([1, 2, 3])), [x for x in range(20) if x % 3 == 0 if x % 2 == 0])
