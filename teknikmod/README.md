# Teknik Mod

Minecraft **1.21.1** / **NeoForge 21.1** icin teknik mod. Enerji birimi FE'dir (NeoForge `IEnergyStorage`),
bu yuzden diger modlarin makineleri ve kablolariyla uyumludur.

## Icerik

| Blok | Islev |
|---|---|
| Komur Jeneratoru | Firin yakitlarini yakar, 40 FE/t uretir. 20.000 FE depo, arayuzu var. |
| Gunes Paneli | Gunduz ve gokyuzunu goruyorsa 8 FE/t (yagmurda 4). Ustunden kablo baglanmaz. |
| Batarya | 200.000 FE depolar. On yuzunden enerji verir, diger yuzlerinden alir (500 FE/t). |
| Bakir Kablo | 250 FE/t tasir. |
| Altin Kablo | 1.000 FE/t tasir. |

Kablolar enerji depolamaz; bir kabloya giren enerji agdaki tum alicilara esit paylastirilir.
Hiz siniri, enerjinin aga girdigi kabloya gore uygulanir. Denge degerleri `Config.java` icindedir.

## Derleme

```bash
./gradlew build        # build/libs/teknikmod-0.1.0.jar
./gradlew runClient    # oyunu modla ac
./gradlew runServer    # test sunucusu
```
