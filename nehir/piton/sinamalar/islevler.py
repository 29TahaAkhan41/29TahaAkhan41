def topla(*sayılar, başlangıç=0):
    toplam = başlangıç
    for s in sayılar:
        toplam += s
    return toplam

def sayaç_yap():
    sayı = [0]
    def artır(adım=1):
        sayı[0] += adım
        return sayı[0]
    return artır

def uygula(f, l):
    return [f(x) for x in l]

print(topla(1, 2, 3), topla(), topla(1, başlangıç=10))
s = sayaç_yap()
s(); s(); print(s(5))
kareler = uygula(lambda x: x * x, range(6))
print(kareler)
print(sorted(["armut", "elma", "kiraz", "ayva"], key=len))
print(sorted([3, 1, 2], reverse=True), list(map(str, [1, 2, 3])), list(filter(None, [0, 1, "", "a"])))
çiftler = {x: x * x for x in range(5) if x % 2 == 0}
print(çiftler, {c for c in "nehir"} == set("nehir"))
print([(i, j) for i in range(3) for j in range(i)])
print(max([3, 7, 2]), min("zeytin"), max(["a", "bb", "c"], key=len), sum(x for x in range(101)))
a, *b, c = [1, 2, 3, 4, 5]
print(a, b, c)
x = 5
y = "büyük" if x > 3 else "küçük"
print(y, x > 3 and "evet" or "hayır", [] or "boş")
def faktöriyel(n):
    return 1 if n <= 1 else n * faktöriyel(n - 1)
print(faktöriyel(20))
toplam = 0
def ekle(n):
    global toplam
    toplam += n
for i in range(1, 11):
    ekle(i)
print(toplam)
print(list(enumerate("abc", 1)), list(zip([1, 2], "xy")), dict(zip("ab", [1, 2])))
print(any(x > 4 for x in [1, 5]), all([]), divmod(17, 5), pow(3, 4, 5), abs(-3.5), round(3.14159, 2))
