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

[3, 1, 4] -> l -> ekle(1) -> yazdır     # [3, 1, 4, 1]
l -> her (e) { e * e -> yazdır }        # her eleman e'ye akar

4 -> (yazdır | kare -> a | kare -> kare -> b)   # çatal: nehir kollara ayrılır

"Cevap: " + metne(6 * 7) -> yazdır      # Cevap: 42
"nehir" -> her (k) { k -> yazdır }      # karakterler tek tek akar

["elma", "armut"] -> meyveler -> ekle("kiraz") -> yazdır   # metin listesi
meyveler -> her (m) { m == "armut" -> eğer { dur }   m -> yazdır }

"Adın ne? " -> oku -> ad                # istem oku'ya akar, yazılan satır geri akar
"Merhaba, " + ad + "!" -> yazdır
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
| `her (x) { }` | akan listenin her elemanı (ya da metnin her karakteri) sırayla `x`'e akar ve blok çalışır |
| `liste[i]` | değeri listenin `i`. gözüne yazar (ilk göz 0) |
| `(a \| b \| c)` | **çatal:** aynı değer her kola ayrı ayrı akar, sonra değişmeden yoluna devam eder |
| `döndür` | değeri işlevden döndürür |

**Anahtar kelimeler** Türkçe, ASCII-Türkçe ya da İngilizce yazılabilir ve karıştırılabilir:

| Türkçe | ASCII | İngilizce |
| --- | --- | --- |
| `eğer` | `eger` | `if` |
| `değilse` | `degilse` | `else` |
| `iken` | | `while` |
| `her` | | `each` |
| `dur` | | `break` |
| `devam` | | `continue` |
| `işlev`, `fonksiyon` | `islev` | `fn` |
| `döndür` | `dondur` | `return` |
| `yazdır` | `yazdir` | `print` |
| `doğru` / `yanlış` | `dogru` / `yanlis` | `true` / `false` |
| `ve` / `veya` / `değil` | `degil` | `and` / `or` / `not` |

**Çatal** dilin en kendine özgü parçasıdır. Her kol bir hedef zinciridir:

```nehir
4 -> (yazdır | kare -> a | küp -> b)    # 4 yazılır, a = 16, b = 64
10 -> (kare -> yazdır) -> x             # 100 yazılır, x = 10
```

Kollarda `eğer` ve `döndür` kullanılabilir; `iken` ve `her` kullanılamaz.

**Döngü denetimi:** `dur` en içteki `iken` ya da `her` döngüsünden çıkar, `devam` sonraki tura geçer.
İkisi de tek başına birer deyimdir ve genellikle bir `eğer` bloğunda durur:

```nehir
sayılar -> her (s) {
    s < 0 -> eğer { devam }
    s > 100 -> eğer { dur }
    s -> yazdır
}
```

**İfadeler:** `+ - * / %`, `== != < > <= >=`, `ve veya değil`, parantez, işlev çağrısı `f(a, b)`,
liste `[1, 2, 3]`, eleman erişimi `l[i]`.
Metinlerde `+` birleştirir, karşılaştırma işleçleri sözlük sırasına göre çalışır ve `m[i]` `i`. karakteri verir.
`->` yerine `→` da yazılabilir. Yorumlar `#` ile başlar.

**Yerleşik işlevler:**

| Türkçe | İngilizce | Ne yapar |
| --- | --- | --- |
| `uzunluk(x)` | `len` | listenin eleman sayısı ya da metnin karakter sayısı |
| `ekle(l, e)` | `push` | `e`'yi listenin sonuna ekler, listeyi döndürür |
| `aralık(a, b)` | `range` | `[a, a+1, ..., b-1]` listesini üretir |
| `metne(n)` | `str` | sayıyı metne çevirir |
| `sayıya(m)` | `num` | metni sayıya çevirir; metin geçerli bir tam sayı değilse program hatayla durur |
| `oku()` | `read` | standart girdiden bir satır okur (satır sonu olmadan); girdi bittiyse `""` verir |
| `oku(istem)` | `read` | önce `istem` metnini satır sonu eklemeden yazar, sonra bir satır okur |
| `girdi_var()` | `has_input` | okunacak girdi kaldıysa 1, bittiyse 0 verir |

Girdinin tamamını okumak için koşulu döngüye akıtmak yeter:

```nehir
girdi_var() -> iken { oku() -> sayıya -> n   toplam + n -> toplam }
```

Metinler UTF-8'dir; uzunluk ve dizinler bayt değil karakter sayar (`"çığlık"` 6 karakterdir).
Metin ile sayı doğrudan toplanamaz: `"a" + metne(5)`.

**Türler:** 64 bit tam sayılar, metinler ve listeler. Bir listenin bütün elemanları aynı türdendir:
sayı listesi, metin listesi ya da liste listesi (`[[1, 2], [3]]`). Boş listenin (`[]`) türü,
içine akan ilk elemandan anlaşılır. Türler derleme anında denetlenir; bir değişkenin türü değişemez. İşlevlerin parametre ve dönüş türleri yazılmaz, ilk çağrıdan
çıkarılır; bir işlev hep aynı türlerle çağrılmalıdır.

**Kapsam:** En üst düzeyde atanan değişkenler küreseldir. İşlev içinde ilk kez atanan adlar yereldir.

**Satırlar:** Deyimler arasında ayırıcı gerekmez. Tek kural: çağrı `f(...)` ve eleman erişimi
`l[...]` için parantez adla aynı satırda olmalıdır. Aynı satıra birden çok deyim yazarken `;` kullanılabilir.

## Sınamalar

```bash
python3 test.py
```

Her örnek derlenir, çalıştırılır ve çıktısı yanındaki `.beklenen` dosyasıyla karşılaştırılır.
Aynı adlı bir `.girdi` dosyası varsa programa standart girdi olarak verilir.

## Şimdilik olmayanlar

- Metinler değiştirilemez; alt metin alma, arama, büyük/küçük harf çevirme yok
- Listelerden eleman silinemez; listeler `+` ile birleştirilemez ve `==` ile karşılaştırılamaz
- Bir işlev hem sayı listesiyle hem metin listesiyle çağrılamaz (her işlevin tek bir tür imzası vardır)
- Bellek geri toplanmaz: program en çok 256 MB liste ve metin belleği ayırabilir
- Ondalıklı sayı, dosya okuma/yazma yok
