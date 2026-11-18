import sys
import random
from math import sqrt, pi

def selamla(ad, *, unvan="Sayın", ünlem=False):
    return f"{unvan} {ad}{'!' if ünlem else '.'}"

ayarlar = {"unvan": "Dr.", "ünlem": True}
print(selamla("Ece"), selamla("Ece", **ayarlar), selamla(*["Can"], unvan="Bay"))

class Izgara:
    def __init__(self, g, y):
        self.g, self.y = g, y
        self.hücreler = [[0] * g for _ in range(y)]
    def __getitem__(self, konum):
        x, y = konum
        return self.hücreler[y][x]
    def __setitem__(self, konum, değer):
        x, y = konum
        self.hücreler[y][x] = değer
    def __iter__(self):
        return iter([h for satır in self.hücreler for h in satır])
    def __contains__(self, d):
        return any(d in satır for satır in self.hücreler)
    @classmethod
    def kare(cls, n):
        return cls(n, n)

class Çarpan:
    def __init__(self, k):
        self.k = k
    def __call__(self, x):
        return x * self.k

ı = Izgara.kare(3)
ı[1, 2] = 7
print(ı[1, 2], sum(ı), 7 in ı, 8 in ı, list(ı)[:4])
üçle = Çarpan(3)
print(üçle(5), list(map(üçle, [1, 2])))

with open("piton_deneme.txt", "w") as f:
    f.write("birinci\n")
    f.write("ikinci\n")
with open("piton_deneme.txt") as f:
    for satır in f:
        print(satır.strip().upper())
print(open("piton_deneme.txt").read().split())
print(len(sys.argv), round(sqrt(2) * pi, 6))
random.seed(3)
a = [random.randint(1, 6) for _ in range(5)]
print(len(a), all(1 <= x <= 6 for x in a))
l = [5, 3, 8]
l.sort(key=lambda x: -x)
print(l, "{:>5}|{:<5}|{:^5}".format("a", "b", "c"), (lambda *s: len(s))(1, 2, 3))
