# Teknik Mod

Minecraft **1.21.1** / **NeoForge 21.1** icin teknik mod. Enerji birimi FE'dir (NeoForge `IEnergyStorage`),
bu yuzden diger modlarin makineleri ve kablolariyla uyumludur.

## Icerik

Her cihazin uc kademesi vardir: Temel, Gelismis (`advanced_`) ve Elit (`elite_`).

| Cihaz | Temel | Gelismis | Elit |
|---|---|---|---|
| Komur Jeneratoru: uretim | 40 FE/t | 120 FE/t | 360 FE/t |
| Komur Jeneratoru: depo | 20.000 FE | 60.000 FE | 180.000 FE |
| Gunes Paneli: uretim (yagmurda yarisi) | 8 FE/t | 32 FE/t | 128 FE/t |
| Batarya: depo | 200.000 FE | 1.000.000 FE | 5.000.000 FE |
| Batarya: giris/cikis | 500 FE/t | 2.000 FE/t | 8.000 FE/t |
| Elektrikli Firin / Ogutucu: hiz | 2x | 4x | 8x |
| Elektrikli Firin / Ogutucu: tuketim | 40 FE/t | 80 FE/t | 160 FE/t |

| Kablo | Aktarim |
|---|---|
| Bakir | 250 FE/t |
| Altin | 1.000 FE/t |
| Elmas | 4.000 FE/t |

Yukseltme tarifi: onceki kademenin dort yanina altin kulce (Gelismis) veya elmas (Elit).

### Yaratici kademe (`creative_`)

Her cihazin ve kablonun bir de Yaratici kademesi vardir. Tarifleri [Extended Crafting](https://www.curseforge.com/minecraft/mc-mods/extended-crafting)
modunun 9x9 Ultimate masasindadir ve yalnizca o mod yukluyken etkinlesir (mod zorunlu degildir; yoksa yaratici
moddan veya `/give` ile alinir). Tarifler `tools/gen_resources.py` icindeki `ec_table` cagrilariyla uretilir.

- Jenerator ve gunes paneli: yakit/gunes gerektirmez, 10.000.000 FE/t'ye kadar verir.
- Batarya: hic bosalmaz, enerji kabul etmez, her yuzunden enerji verir.
- Elektrikli firin ve ogutucu: enerji harcamaz, her islem 1 tick surer.
- Kablo: aktarim siniri yoktur.

`Tier.java` icine yeni bir cihaz eklenince dort kademe de kendiliginden olusur.

- Komur jeneratoru yalnizca komur, odun komuru ve komur blogu yakar (`teknikmod:coal_generator_fuel` etiketi); yakit ayni surede yanar, ust kademe ayni yakittan daha cok enerji cikarir.
- Gunes paneli gunduz ve gokyuzunu goruyorsa calisir; ustunden kablo baglanmaz.
- Batarya on yuzunden enerji verir, diger yuzlerinden alir.
- Elektrikli firin tum normal firin tariflerini pisirir (esya basina 4.000 FE). Hiz, normal firina goredir.
- Ogutucu `teknikmod:crushing` tariflerini isler: ham maden -> 2 toz, cevher blogu -> 3 toz, tas -> kirik tas -> cakil -> kum vb.
  Tozlar firinda kulceye doner. Yeni tarif eklemek icin `data/<ad>/recipe/` altina su bicimde JSON koymak yeterli:
  `{"type": "teknikmod:crushing", "ingredient": {"item": "..."}, "result": {"id": "...", "count": 2}, "time": 200}`
- Iki makinede de huni/borular esyayi giris yuvasina koyar, cikis yuvasindan alir.
- Kablolar enerji depolamaz; bir kabloya giren enerji agdaki tum alicilara esit paylastirilir.
  Hiz siniri, enerjinin aga girdigi kabloya gore uygulanir.

Denge degerleri `Tier.java` icindedir. Dokular ve JSON dosyalari `tools/gen_resources.py` ile uretilir.

## Diger modlarla uyum

Tum bloklar NeoForge'un standart enerji yetenegini (`Capabilities.EnergyStorage.BLOCK`, FE) sunar ve komsulara
ayni yetenek uzerinden enerji iter. Bu yuzden FE kullanan modlarin makineleri bizim jenerator/kablolarimizdan
beslenir, onlarin jenerator ve kablolari da bizim batarya ve kablolarimiza enerji verebilir.

## Derleme

```bash
./gradlew build        # build/libs/teknikmod-0.6.1.jar
./gradlew runClient    # oyunu modla ac
./gradlew runServer    # test sunucusu
```
