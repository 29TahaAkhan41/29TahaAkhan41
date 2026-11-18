# Piton: Nehir ile yazılmış Python derleyicisi

Piton, Python programlarını bağımsız çalıştırılabilir dosyalara (Linux'ta ELF, Windows'ta `.exe`) derler.
Kendisi tamamen Nehir ile yazılmıştır ve Python'a ihtiyaç duymaz.

```bash
python3 nehir.py piton/piton.nehir -o piton          # derleyiciyi bir kez derle
./piton program.py                                    # program.py -> program
./piton program.py --çalıştır                         # derle ve çalıştır
./piton program.py --nehir                            # üretilen Nehir kodunu gör (program.nehir)
```

Piton, `piton/pitonca.nehir` kitaplığını ve `calisma_zamani.s` dosyalarını çalışma dizininde arar.
Başka yerden çalıştırırken `--kitaplık <yol>` ve `--çalışma-zamanı <yol>` ile verilebilirler.
Linux'ta `as` ve `ld`, Windows'ta MinGW-w64'ün `gcc`'si gerekir (Nehir'deki gibi).

| Seçenek | Anlamı |
| --- | --- |
| `-o <ad>` | çıktı dosyası |
| `--hedef linux`, `--hedef windows` | hangi sistem için derleneceği |
| `--çalıştır` | derledikten sonra çalıştır; `--` sonrası programa argüman olur |
| `--nehir` | yalnızca Nehir koduna çevir |
| `--asm` | assembly dosyasını da bırak |

## Nasıl çalışır

1. Python kaynağı sözcüklere ayrılır (girintiler, f-dizgeleri, üç tırnaklı dizgeler dahil) ve
   özyinelemeli bir ayrıştırıcıyla sözdizimi ağacına dönüştürülür.
2. Ağaç Nehir koduna çevrilir. Her Python satırı aynı numaralı Nehir satırına düşer; kavramalar,
   lambda'lar ve iç işlevler dosyanın sonuna ayrı işlevler olarak taşınır.
3. Bu kod aynı süreç içinde Nehir ile yazılmış Nehir derleyicisinin (`kendi/`) aşamalarından geçip
   x86-64 assembly'sine dönüşür; ardından birleştirici ve bağlayıcı çağrılır.

Python'un dinamik türlü değerleri `pitonca.nehir`'de tek bir Nehir kaydıyla (`Değer`) temsil edilir.
İşleçler, yerleşik işlevler, yöntemler, yazdırma ve hata mesajları Python'daki gibi davranır:
`0.1 + 0.2` → `0.30000000000000004`, `round(2.5)` → `2`, `-7 // 2` → `-4`, `print([1, 'a', None])`
→ `[1, 'a', None]`. Ondalık sayılar Python'un `repr`'i gibi geri okunduğunda aynı sayıyı veren en kısa
biçimde yazılır. `try`/`except`, Nehir'in `kaçış_noktası()` / `kaçış()` yerleşikleriyle (yerel olmayan
çıkış) gerçekleştirilir.

`piton/sinamalar/` altındaki programların çıktıları CPython'unkiyle bayt bayt aynıdır (yakalanmayan
istisnaların biçimi dışında); `python3 test.py` bunları da sınar.

## Desteklenenler

- **Türler:** `int`, `float`, `str`, `bool`, `None`, `list`, `tuple`, `dict`, `set`
- **İşleçler:** `+ - * / // % **`, bit işleçleri, zincirleme karşılaştırma (`a < b < c`), `in`, `not in`,
  `is`, kısa devreli `and` / `or` (değer döndürür), `x if k else y`, artırmalı atamalar (`+=` ...)
- **Deyimler:** `if/elif/else`, `while`, `for` (`range`, liste, dizge, sözlük, `enumerate`, `zip`, ...),
  `break`, `continue`, `pass`, demet açma (`a, b = b, a`, `a, *b = l`), `del`, `assert`, `global`,
  `with open(...) as f`
- **İşlevler:** varsayılan değerler, adlı argümanlar, `*args`, yalnızca adlı parametreler, `f(*l)`,
  `f(**d)`, özyineleme, işlevler değer olarak, `lambda`, iç işlevler (kapanışlar)
- **Kavramalar:** liste, sözlük ve küme kavramaları, üreteç ifadeleri (liste olarak)
- **Dizgeler:** f-dizgeleri (`{x:>8.2f}`, `{x!r}`, `{x=}`), `%` biçimlendirme, `str.format`, bütün
  biçim belirteçleri ve yaygın yöntemler (`split`, `join`, `strip`, `replace`, `upper`, `find`, ...)
- **Sınıflar:** `__init__`, kalıtım, `super()`, sınıf öznitelikleri, `@staticmethod`, `@classmethod`,
  `@property`, işleç yükleme (`__add__`, `__eq__`, `__lt__`, ...), `__str__`, `__repr__`, `__len__`,
  `__getitem__`, `__contains__`, `__iter__`, `__call__`, `__bool__`, bağlı yöntemler, `isinstance`
- **İstisnalar:** `try/except/else/finally`, `raise`, yeniden fırlatma, `except (A, B) as e`, kendi
  istisna sınıflarınız, Python'un yerleşik istisna sıradüzeni
- **Yerleşikler:** `print`, `input`, `len`, `range`, `str`, `int`, `float`, `bool`, `list`, `tuple`,
  `dict`, `set`, `abs`, `min`, `max`, `sum`, `sorted`, `reversed`, `enumerate`, `zip`, `map`, `filter`,
  `any`, `all`, `ord`, `chr`, `round`, `divmod`, `pow`, `hex`, `bin`, `oct`, `repr`, `isinstance`,
  `type`, `format`, `callable`, `open`, `exit`
- **Modüller:** `math`, `random`, `time`, `sys` (`argv`, `exit`)

## Desteklenmeyenler

- Üreteçler (`yield`), `async`, `nonlocal`, `**kwargs` parametresi, çoklu kalıtım, `match`
- Tam sayılar 64 bitliktir; sığmayan sonuçlar `OverflowError` verir (Python'daki gibi büyümez)
- `for ... else`, `while ... else`, `:=`, dilime atama (`l[1:3] = ...`), `bytes`, karmaşık sayılar
- Başka `.py` dosyalarını `import` etmek; yalnızca yukarıdaki dört modül var
- Kapanışlar dış değişkenleri tanımlandıkları andaki değerleriyle yakalar
- `range()` bir liste döndürür; `random` CPython'dan farklı sayılar üretir
- Yakalanmayan bir istisna Python'un "Traceback" biçimi yerine Nehir'in biçimiyle bildirilir:
  `program.py:12: çalışma hatası: ZeroDivisionError: division by zero`
