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

{"elma": 3} -> stok                     # sözlük
7 -> stok["kiraz"]                      # 7, "kiraz" anahtarına akar
stok["elma"] + 1 -> stok["elma"]

"günlük.txt" -> dosya_oku -> böl("\n") -> satırlar     # dosya okuma
satırlar -> birleş("\n") -> dosya_yaz("kopya.txt")     # içerik dosyaya akar

kayıt Nokta { x, y }                    # kayıt
Nokta(3, 4) -> n
n.x + 1 -> n.x                          # alan okuma ve alana yazma

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
| `--sözcükler` | derlemeden yalnızca sözcükleri dök |
| `--çalıştır`, `--run` | derledikten sonra çalıştır |
| `-- <argümanlar>` | `--çalıştır` ile birlikte: sonrası programa argüman olarak verilir |

Gereksinimler: Python 3.8+, GNU binutils (`as`, `ld`), x86-64 Linux.

## Hata mesajları

Derleyici hatanın yerini kaynak satırında gösterir ve yapabildiğinde bir ipucu verir:

```
program.nehir:2:1: hata: 'toplm' adında bir değişken yok
    2 | toplm + 1 -> yazdır
      | ^^^^^
      = ipucu: 'toplam' mi demek istediniz?
```

```
program.nehir:1:3: hata: Nehir'de '=' ile atama yok
    1 | x = 5
      |   ^
      = ipucu: değer soldan sağa akar: 5 -> x   (eşitlik sınaması için ==)
```

Nehir'de bilinmeyen bir ada akan değer yeni bir değişken oluşturduğu için, işlev adındaki
yazım hatası (`5 -> kere`) hata değildir. Derleyici, bir işlev ya da anahtar kelimeye çok
benzeyen ve hiç okunmayan değişkenler için uyarı verir. Uyarılar derlemeyi durdurmaz.

Çalışma zamanı hataları (sıfıra bölme, sınır dışı dizin, olmayan anahtar, `yok`'un alanına erişme, sayıya çevrilemeyen metin,
açılamayan dosya, biten bellek)
programı 1 çıkış koduyla durdurur ve hatanın olduğu kaynak satırını bildirir:

```
program.nehir:4: çalışma hatası: sıfıra bölme
```

Terminalde mesajlar renklidir; `NO_COLOR` ortam değişkeni renkleri kapatır.

## Dil

**Akış hedefleri** (`->` işaretinin sağına gelebilenler):

| Hedef | Ne yapar |
| --- | --- |
| değişken adı | değeri değişkene yazar, değer akmaya devam eder |
| işlev adı | değer işlevin ilk argümanı olur: `3 -> topla(4)` = `topla(3, 4)` |
| `yazdır` | değeri yazdırır, değer akmaya devam eder |
| `eğer { } değilse { }` | değer sıfır değilse ilk blok, sıfırsa ikinci blok çalışır |
| `iken { }` | akış sıfır olmayan değer ürettiği sürece bloğu tekrarlar |
| `her (x) { }` | akan listenin her elemanı (metnin her karakteri, sözlüğün her anahtarı) sırayla `x`'e akar ve blok çalışır |
| `liste[i]` | değeri listenin `i`. gözüne yazar (ilk göz 0) |
| `sözlük[a]` | değeri sözlükte `a` anahtarına yazar; anahtar yoksa eklenir |
| `kayıt.alan` | değeri kaydın alanına yazar |
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
| `kayıt` | `kayit` | `record` |
| `yok` | | `none` |
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
liste `[1, 2, 3]`, sözlük `{"a": 1, "b": 2}`, eleman erişimi `l[i]` ve `s[anahtar]`.
Metinlerde `+` birleştirir, karşılaştırma işleçleri sözlük sırasına göre çalışır ve `m[i]` `i`. karakteri verir.
Listelerde `+` iki listeyi yeni bir listede birleştirir; `==` ve `!=` içerikleri (iç içe listeler dahil) karşılaştırır.
`->` yerine `→` da yazılabilir. Yorumlar `#` ile başlar.

**Yerleşik işlevler:**

| Türkçe | İngilizce | Ne yapar |
| --- | --- | --- |
| `uzunluk(x)` | `len` | listenin eleman sayısı, sözlüğün anahtar sayısı ya da metnin karakter sayısı |
| `ekle(l, e)` | `push` | `e`'yi listenin sonuna ekler, listeyi döndürür |
| `aralık(a, b)` | `range` | `[a, a+1, ..., b-1]` listesini üretir |
| `dilim(x, baş, son)` | `slice` | listenin ya da metnin `baş` ile `son` arasındaki parçası (`son` dahil değil); taşan sınırlar sığdırılır |
| `bul(x, aranan)` | `find` | elemanın listede ya da metnin metinde ilk geçtiği dizin; yoksa `-1` |
| `sil(l, i)` | `remove` | `i`. elemanı listeden çıkarır ve o elemanı verir |
| `sil(s, a)` | `remove` | `a` anahtarını sözlükten çıkarır ve değerini verir |
| `var(s, a)` | `has` | `a` anahtarı sözlükte varsa 1, yoksa 0 |
| `anahtarlar(s)` | `keys` | sözlüğün anahtarlarının listesi (eklenme sırasıyla) |
| `değerler(s)` | `values` | sözlüğün değerlerinin listesi |
| `böl(m, ayraç)` | `split` | metni ayraçtan böler, metin listesi verir |
| `birleş(l, ayraç)` | `join` | metin listesinin elemanlarını araya ayraç koyarak tek metin yapar |
| `metne(n)` | `str` | sayıyı metne çevirir |
| `sayıya(m)` | `num` | metni sayıya çevirir; metin geçerli bir tam sayı değilse program hatayla durur |
| `oku()` | `read` | standart girdiden bir satır okur (satır sonu olmadan); girdi bittiyse `""` verir |
| `oku(istem)` | `read` | önce `istem` metnini satır sonu eklemeden yazar, sonra bir satır okur |
| `girdi_var()` | `has_input` | okunacak girdi kaldıysa 1, bittiyse 0 verir |
| `dosya_oku(yol)` | `read_file` | dosyanın tüm içeriğini metin olarak verir |
| `dosya_yaz(içerik, yol)` | `write_file` | içeriği dosyaya yazar (yoksa oluşturur, varsa üstüne yazar); içeriği geri verir |
| `dosya_ekle(içerik, yol)` | `append_file` | içeriği dosyanın sonuna ekler |
| `dosya_var(yol)` | `file_exists` | dosya varsa 1, yoksa 0 |
| `dosya_sil(yol)` | `delete_file` | dosyayı siler |
| `argümanlar()` | `args` | programa verilen komut satırı argümanlarının listesi (program adı hariç) |
| `çık(kod)` | `exit` | programı verilen çıkış koduyla hemen bitirir |
| `uyar(m)` | `warn` | metni standart hataya (stderr) bir satır olarak yazar |

Yazma işlevlerinde içerik ilk argümandır, yani akışla gelir: `"merhaba\n" -> dosya_yaz("selam.txt")`.
Açılamayan, okunamayan ya da yazılamayan dosya programı hatayla durdurur:
`program.nehir:3: çalışma hatası: dosya bulunamadı: yok.txt`. Önce `dosya_var` ile sorulabilir.

Girdinin tamamını okumak için koşulu döngüye akıtmak yeter:

```nehir
girdi_var() -> iken { oku() -> sayıya -> n   toplam + n -> toplam }
```

Metinler UTF-8'dir; uzunluk ve dizinler bayt değil karakter sayar (`"çığlık"` 6 karakterdir).
Metin ile sayı doğrudan toplanamaz: `"a" + metne(5)`.

**Sözlükler** anahtarları değerlere eşler ve eklenme sırasını korur. Anahtarlar sayı ya da metin,
değerler herhangi bir tür olabilir; bir sözlüğün bütün anahtarları aynı türden, bütün değerleri aynı türdendir.
Olmayan bir anahtarı okumak çalışma zamanı hatasıdır; önce `var` ile sorulabilir:

```nehir
{} -> sayılar
"su akar su bulur" -> böl(" ") -> her (kelime) {
    sayılar -> var(kelime) -> eğer { sayılar[kelime] + 1 -> sayılar[kelime] }
    değilse { 1 -> sayılar[kelime] }
}
sayılar -> yazdır           # {"su": 2, "akar": 1, "bulur": 1}
```

**Kayıtlar** adlandırılmış alanları olan değerlerdir. Tanım en üst düzeyde yapılır; kayıt, adı
işlev gibi çağrılarak kurulur ve değerler alanlara tanımdaki sırayla verilir:

```nehir
kayıt Nokta { x, y }

Nokta(3, 4) -> n
n.x * n.x + n.y * n.y -> yazdır     # 25
10 -> n.x                           # alana yazma
n -> yazdır                         # Nokta(x: 10, y: 4)
```

Kayıtlar kopyalanmaz, paylaşılır: `n -> m` dedikten sonra `m.x`'e yazmak `n.x`'i de değiştirir.
`==` iki değerin *aynı kayıt* olup olmadığına bakar, içeriklerine değil.

Alan türleri çoğu zaman kullanımdan çıkarılır, ama tanımda da yazılabilir:
`sayı`, `metin`, bir kayıt adı, `[Tür]` (liste) ya da `{Tür: Tür}` (sözlük). Kendine gönderme
yapan kayıtlarda türü yazmak gerekir. `yok`, kayıt beklenen her yere konabilen "kayıt yok" değeridir;
`yok`'un alanına erişmek çalışma zamanı hatasıdır.

```nehir
kayıt Düğüm { değer: sayı, sonraki: Düğüm }

Düğüm(1, Düğüm(2, yok)) -> liste
liste -> d
d != yok -> iken {
    d.değer -> yazdır
    d.sonraki -> d
}
```

**Türler:** 64 bit tam sayılar, metinler, listeler, sözlükler ve kayıtlar. Bir listenin bütün elemanları aynı türdendir:
sayı listesi, metin listesi ya da liste listesi (`[[1, 2], [3]]`). Boş listenin (`[]`) türü,
içine akan ilk elemandan anlaşılır; boş sözlük (`{}`) için de aynısı geçerlidir. Türler derleme anında denetlenir; bir değişkenin türü değişemez. İşlevlerin parametre ve dönüş türleri yazılmaz, ilk çağrıdan
çıkarılır; bir işlev hep aynı türlerle çağrılmalıdır.

**Kapsam:** En üst düzeyde atanan değişkenler küreseldir. İşlev içinde ilk kez atanan adlar yereldir.

**Satırlar:** Deyimler arasında ayırıcı gerekmez. Tek kural: çağrı `f(...)` ve eleman erişimi
`l[...]` için parantez adla aynı satırda olmalıdır. Aynı satıra birden çok deyim yazarken `;` kullanılabilir.

## Kendi kendini derleme

Hedef, Nehir derleyicisini Nehir ile yazmak. `kendi/` dizini bu çalışmayı tutar; `nehir.py`
o zamana kadar asıl derleyici olarak kalır ve yeni parçaların doğruluğu ona karşı sınanır.

| Aşama | Dosya | Durum |
| --- | --- | --- |
| Sözcükleyici | `kendi/sozcukleyici.nehir` | tamam: bütün örneklerde ve kendi kaynağında `nehir.py` ile aynı sözcükleri üretiyor |
| Kayıtlar (sözdizimi ağacı için) | | tamam |
| Ayrıştırıcı | | sırada |
| Kod üretici | | bekliyor |

```bash
python3 nehir.py kendi/sozcukleyici.nehir -o sozcukleyici
```

```bash
./sozcukleyici ornekler/merhaba.nehir
```

Aynı dökümü Python'daki sözcükleyiciden almak için: `python3 nehir.py ornekler/merhaba.nehir --sözcükler`.
Bilinen tek fark: Nehir sürümü ASCII dışındaki her karakteri harf sayar; Python sürümü Unicode'un
harf tanımını kullanır (yalnızca adların içinde harf olmayan ASCII dışı simgeler kullanılırsa fark eder).

## Sınamalar

```bash
python3 test.py
```

Her örnek derlenir, çalıştırılır ve çıktısı yanındaki `.beklenen` dosyasıyla karşılaştırılır.
`ornekler/hatalar/` altındaki programlar bilerek hatalıdır; onların beklenen çıktısı hata mesajlarıdır.
Son olarak Nehir ile yazılmış sözcükleyici derlenir ve bütün `.nehir` dosyalarında (`kendi/sinamalar/`
altındaki zor ve hatalı girdiler dahil) Python'daki sözcükleyiciyle aynı çıktıyı verdiği doğrulanır.
Aynı adlı bir `.girdi` dosyası varsa programa standart girdi olarak verilir.

## Şimdilik olmayanlar

- Metinler değiştirilemez; büyük/küçük harf çevirme yok
- Listeler `<` ve `>` ile karşılaştırılamaz; yerleşik sıralama işlevi yok
- Sözlükler `==` ile karşılaştırılamaz; anahtar olarak liste kullanılamaz
- Yerleşik işlev adları (`bul`, `sil`, `böl`, `dilim`, `var`, ...) değişken ya da işlev adı olarak kullanılamaz
- Bir işlev hem sayı listesiyle hem metin listesiyle çağrılamaz (her işlevin tek bir tür imzası vardır)
- Bellek geri toplanmaz: program en çok 256 MB liste ve metin belleği ayırabilir
- Ondalıklı sayı yok
- Kayıtlar kurulurken değerler yalnızca sırayla verilir (`Nokta(x: 3, y: 4)` yazılamaz); kayıtların yöntemi yok
- `yok` yalnızca kayıtlar içindir; "sayı yok" ya da "metin yok" diye bir değer yok
- Dosyalar yalnızca bütün olarak okunur ve yazılır; dizin listeleme ya da oluşturma yok
- Çalışma zamanı hataları yakalanamaz
