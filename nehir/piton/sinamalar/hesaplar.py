import math
from random import seed, randint

class YetersizBakiye(Exception):
    pass

class Hesap:
    sayaç = 0
    def __init__(self, sahibi, bakiye=0.0):
        Hesap.sayaç += 1
        self.no = Hesap.sayaç
        self.sahibi = sahibi
        self.bakiye = bakiye
        self.hareketler = []

    def yatır(self, miktar):
        if miktar <= 0:
            raise ValueError("miktar pozitif olmalı")
        self.bakiye += miktar
        self.hareketler.append(("yatırma", miktar))

    def çek(self, miktar):
        if miktar > self.bakiye:
            return False
        self.bakiye -= miktar
        self.hareketler.append(("çekme", miktar))
        return True

    def __str__(self):
        return f"#{self.no} {self.sahibi:<8} {self.bakiye:>10.2f} TL"

class VadeliHesap(Hesap):
    def __init__(self, sahibi, bakiye, faiz):
        super().__init__(sahibi, bakiye)
        self.faiz = faiz

    def yıl_geçir(self, yıl=1):
        self.bakiye *= (1 + self.faiz) ** yıl
        return self

hesaplar = [Hesap("Ali", 100), VadeliHesap("Zeynep", 1000, 0.05), Hesap("Mert")]
hesaplar[0].yatır(50.5)
print(hesaplar[2].çek(10), hesaplar[0].çek(20))
hesaplar[1].yıl_geçir(3)
for h in sorted(hesaplar, key=lambda h: h.bakiye, reverse=True):
    print(h)
print([type(h).__name__ for h in hesaplar], hesaplar[0].hareketler)
toplam = sum(h.bakiye for h in hesaplar)
print(f"toplam: {toplam:,.2f}", math.floor(toplam), math.sqrt(16), math.pi, round(math.e, 5))
print(isinstance(hesaplar[1], Hesap), isinstance(hesaplar[1], VadeliHesap), isinstance(YetersizBakiye("x"), Exception))
