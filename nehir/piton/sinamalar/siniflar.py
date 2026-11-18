class Hayvan:
    tür_sayısı = 0

    def __init__(self, ad, ses="..."):
        self.ad = ad
        self.ses = ses
        Hayvan.tür_sayısı += 1

    def konuş(self):
        return f"{self.ad} der ki: {self.ses}"

    def __repr__(self):
        return f"Hayvan({self.ad!r})"


class Kedi(Hayvan):
    def __init__(self, ad):
        super().__init__(ad, "miyav")
        self.can = 9

    def konuş(self):
        return super().konuş() + "!"


class Vektör:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __add__(self, o):
        return Vektör(self.x + o.x, self.y + o.y)

    def __mul__(self, k):
        return Vektör(self.x * k, self.y * k)

    def __eq__(self, o):
        return self.x == o.x and self.y == o.y

    def __str__(self):
        return f"({self.x}, {self.y})"

    def __len__(self):
        return 2

    @property
    def uzunluk(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

    @staticmethod
    def sıfır():
        return Vektör(0, 0)


hayvanlar = [Hayvan("Karabaş", "hav"), Kedi("Tekir"), Hayvan("Balık")]
for h in hayvanlar:
    print(h.konuş())
print(hayvanlar)
print(Hayvan.tür_sayısı, isinstance(hayvanlar[1], Hayvan), isinstance(hayvanlar[0], Kedi))
v = Vektör(3, 4) + Vektör(1, 2) * 2
print(v, len(v), v.uzunluk, Vektör(1, 1) == Vektör(1, 1), Vektör.sıfır())
print(str(v), repr(hayvanlar[1]), type(v).__name__)
konuşma = hayvanlar[0].konuş
print(konuşma())
