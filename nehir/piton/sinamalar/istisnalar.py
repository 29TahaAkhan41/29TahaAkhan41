class BenimHatam(ValueError):
    def __init__(self, kod):
        super().__init__(f"kod {kod}")
        self.kod = kod

def böl(a, b):
    return a / b

def derin(n):
    if n == 0:
        raise BenimHatam(42)
    return derin(n - 1)

for x in ["10", "abc", "0", "5"]:
    try:
        sonuç = böl(100, int(x))
    except ValueError as e:
        print("değer hatası:", e)
    except ZeroDivisionError as e:
        print("sıfır:", e, type(e).__name__)
    else:
        print("sonuç:", sonuç)
    finally:
        print("bitti", x)

try:
    derin(30)
except BenimHatam as e:
    print("yakalandı:", e, e.kod, isinstance(e, ValueError), e.args)

d = {"a": 1}
try:
    d["b"]
except KeyError as e:
    print("anahtar yok:", e, repr(e))
try:
    [1, 2][5]
except (IndexError, KeyError) as e:
    print("dizin:", e)
try:
    None + 1
except TypeError as e:
    print("tür:", e)
try:
    try:
        raise RuntimeError("iç")
    except RuntimeError:
        print("içte yakalandı, yeniden fırlatılıyor")
        raise
except Exception as e:
    print("dışta:", e)

def f():
    try:
        return "try'dan dönüş"
    finally:
        print("finally önce çalışır")
print(f())

sayılar = []
for i in range(10):
    try:
        if i % 3 == 0:
            raise ValueError(i)
        if i == 8:
            break
        sayılar.append(i)
    except ValueError:
        continue
print(sayılar)

girdiler = iter_yok = ["x", "y", "7"]
sıra = 0
while True:
    try:
        n = int(girdiler[sıra])
        break
    except ValueError:
        print("geçersiz:", girdiler[sıra])
        sıra += 1
print("okundu:", n)

def güvenli(f, *a):
    try:
        return f(*a)
    except Exception as e:
        return f"{type(e).__name__}: {e}"
print(güvenli(int, "q"), güvenli(lambda: [][0]), güvenli(lambda: {}["k"]), güvenli(lambda: 1 // 0))
try:
    assert 1 + 1 == 3, "matematik bozuk"
except AssertionError as e:
    print("doğrulama:", e)
try:
    raise KeyError("k")
except LookupError as e:
    print("üst sınıfla yakalandı", repr(e))
x = 5
try:
    x = int("bozuk")
except:
    pass
print("x hâlâ", x)
print("son")
raise BenimHatam(7)
