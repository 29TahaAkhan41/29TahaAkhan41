# Nehir

Her şeyin **soldan sağa aktığı** deneysel bir programlama dili ve onun derleyicisi.

Nehir'de atama, yazdırma, koşul, döngü ve işlev çağrısı için ayrı sözdizimleri yoktur.
Tek bir kural vardır: bir değer üretilir ve `->` ile bir hedefe akar.

```nehir
5 -> x                      # 5, x'e akar
x * 2 -> yazdır             # 10
40 + 2 -> cevap -> yazdır   # değer her duraktan geçip yoluna devam eder

işlev kare(n) { n * n -> döndür }
3 -> kare -> yazdır         # 9

x > 3 -> eğer { "büyük" -> yazdır } değilse { "küçük" -> yazdır }

0 -> i
i < 5 -> iken {             # koşul her turda yeniden akar
    i -> yazdır
    i + 1 -> i
}
```

## Derleyici

`nehir.py`, kaynak kodu doğrudan x86-64 Linux assembly'sine çevirir; `as` ve `ld`
ile libc kullanmayan, bağımsız bir çalıştırılabilir dosya üretir.

```bash
python3 nehir.py ornekler/fibonacci.nehir --çalıştır
```

```bash
python3 nehir.py ornekler/merhaba.nehir --asm
```

| Seçenek | Anlamı |
| --- | --- |
| `-o <ad>` | çıktı dosyasının adı |
| `--asm` | yalnızca assembly (`.s`) üret |
| `--çalıştır`, `--run` | derledikten sonra çalıştır |

Gereksinimler: Python 3.8+, GNU binutils (`as`, `ld`), x86-64 Linux.

## Dil

**Akış hedefleri** (`->` işaretinin sağına gelebilenler):

| Hedef | Ne yapar |
| --- | --- |
| değişken adı | değeri değişkene yazar, değer akmaya devam eder |
| işlev adı | değer işlevin ilk argümanı olur: `3 -> topla(4)` = `topla(3, 4)` |
| `yazdır` | değeri yazdırır, değer akmaya devam eder |
| `eğer { } değilse { }` | değer sıfır değilse ilk blok, sıfırsa ikinci blok çalışır |
| `iken { }` | akış sıfır olmayan değer ürettiği sürece bloğu tekrarlar |
| `döndür` | değeri işlevden döndürür |

**Anahtar kelimeler** Türkçe, ASCII-Türkçe ya da İngilizce yazılabilir ve karıştırılabilir:

| Türkçe | ASCII | İngilizce |
| --- | --- | --- |
| `eğer` | `eger` | `if` |
| `değilse` | `degilse` | `else` |
| `iken` | | `while` |
| `işlev`, `fonksiyon` | `islev` | `fn` |
| `döndür` | `dondur` | `return` |
| `yazdır` | `yazdir` | `print` |
| `doğru` / `yanlış` | `dogru` / `yanlis` | `true` / `false` |
| `ve` / `veya` / `değil` | `degil` | `and` / `or` / `not` |

**İfadeler:** `+ - * / %`, `== != < > <= >=`, `ve veya değil`, parantez, işlev çağrısı `f(a, b)`.
`->` yerine `→` da yazılabilir. Yorumlar `#` ile başlar.

**Türler:** 64 bit tam sayılar ve metinler. Tür derleme anında denetlenir; bir değişkenin türü değişemez.

**Kapsam:** En üst düzeyde atanan değişkenler küreseldir. İşlev içinde ilk kez atanan adlar yereldir.

## Şimdilik olmayanlar

- Metinler yalnızca yazdırılabilir ve değişkende tutulabilir (birleştirme, karşılaştırma yok)
- İşlevler yalnızca sayı alır ve döndürür
- Liste, kullanıcıdan girdi alma, ondalıklı sayı yok
