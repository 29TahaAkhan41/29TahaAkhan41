#!/usr/bin/env python3
"""Çınarköy haritasını oyunun kendi karolarıyla üretir.

Kullanım:
    python3 tools/harita_uret.py "<oyun klasörü>/Content (unpacked)/Maps"

Oyunun açılmış (StardewXnbHack) Maps klasörünü okur: evleri, ağaçları, vagonu
ve tabelayı Town.tmx / BusStop.tmx içinden kopyalar, zemini (çimen + toprak yol)
oyunun kenar karolarıyla döşer. Oyunun görselleri moda KOPYALANMAZ; harita
karo setlerine yalnızca adlarıyla başvurur.

Çıktılar:
    [CP] Cinarkoy/assets/Cinarkoy.tmx   köy haritası
    [CP] Cinarkoy/assets/Tabela.tmx     otobüs durağına bindirilen tabela yaması
    [CP] Cinarkoy/assets/<mevsim>_cinarkoy_evler.png   yeniden boyanmış ev karoları
    onizleme.png                         haritanın önizlemesi

Haritayı Tiled ile elle düzenlemeye başladıktan sonra bu betiği tekrar
çalıştırma: Cinarkoy.tmx dosyasının üzerine yazar.
"""
import colorsys
import copy
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

KOK = Path(__file__).resolve().parent.parent
ASSETS = KOK / "[CP] Cinarkoy" / "assets"
G, Y = 60, 50                     # harita boyutu (karo)
rng = random.Random(2941)

# content.json ile aynı olmalı
VAGON = (6, 18)                   # ray parçasının üst karosu
TABELA = (10, 21)                 # tabela direği (Buildings)
VARIS_VAGON = (6, 22)
VARIS_TABELA = (10, 22)


# ------------------------------------------------------------ TMX okuma ---
class Harita:
    def __init__(self, yol):
        self.kok = ET.parse(yol).getroot()
        self.g = int(self.kok.get("width"))
        self.y = int(self.kok.get("height"))
        self.setler = {ts.find("image").get("source"): ts for ts in self.kok.findall("tileset")}
        self.katman = {}
        for l in self.kok.findall("layer"):
            v = [int(x) for x in l.find("data").text.replace("\n", "").split(",") if x.strip()]
            self.katman[l.get("name")] = [v[i * self.g:(i + 1) * self.g] for i in range(self.y)]

    def ilk(self, kaynak):
        return int(self.setler[kaynak].get("firstgid"))


if len(sys.argv) != 2:
    sys.exit(__doc__)
MAPS = Path(sys.argv[1])
town = Harita(MAPS / "Town.tmx")
bus = Harita(MAPS / "BusStop.tmx")

# Town.tmx'teki karo seti sırası ve numaraları aynen kullanılır
KATMANLAR = ["Back", "Back2", "Back3", "Buildings", "Buildings2", "Paths", "Front", "AlwaysFront"]
SETLER = ["spring_outdoorsTileSheet", "paths", "spring_town", "spring_Shadows"]
assert town.ilk("spring_outdoorsTileSheet") == 1 and bus.ilk("spring_outdoorsTileSheet") == 1
KASABA0 = town.ilk("spring_town")
KASABA1 = KASABA0 + int(town.setler["spring_town"].get("tilecount"))
GOLGE0 = town.ilk("spring_Shadows")
GOLGE1 = GOLGE0 + int(town.setler["spring_Shadows"].get("tilecount"))

harita = {ad: [[0] * G for _ in range(Y)] for ad in KATMANLAR}


def dolu(x, y, katmanlar=("Buildings", "Buildings2", "Front", "AlwaysFront")):
    return any(harita[k][y][x] for k in katmanlar)


# ---------------------------------------------------------------- zemin ---
# Köşe tabanlı döşeme: her karonun 4 köşesi (sol üst, sağ üst, sol alt, sağ alt)
# toprak (d) ya da çimen (g). Karo numaraları spring_outdoorsTileSheet içinden.
KENAR = {
    "dddg": 179, "ddgd": 253, "ddgg": 252, "dgdd": 178, "dgdg": 229, "dggg": 254,
    "gddd": 203, "gdgd": 226, "gdgg": 251, "ggdd": 202, "ggdg": 204, "gggd": 201,
}
CIMEN = [176] * 46 + [327, 327, 353, 152, 153]
TOPRAK = [228] * 40 + [227] * 6 + [561, 590, 208, 154]

toprak = [[False] * (G + 1) for _ in range(Y + 1)]     # köşe ızgarası


def yol(x0, y0, x1, y1):
    """(x0,y0)-(x1,y1) karolarını (dahil) toprak yap."""
    for y in range(y0, y1 + 2):
        for x in range(x0, x1 + 2):
            toprak[y][x] = True


def zemini_dose():
    # Çapraz köşe karosu yok: öyle hücreleri tamamen toprak yap
    degisti = True
    while degisti:
        degisti = False
        for y in range(Y):
            for x in range(G):
                k = (toprak[y][x], toprak[y][x + 1], toprak[y + 1][x], toprak[y + 1][x + 1])
                if k in ((True, False, False, True), (False, True, True, False)):
                    toprak[y][x] = toprak[y][x + 1] = toprak[y + 1][x] = toprak[y + 1][x + 1] = True
                    degisti = True
    for y in range(Y):
        for x in range(G):
            k = "".join("d" if t else "g" for t in
                        (toprak[y][x], toprak[y][x + 1], toprak[y + 1][x], toprak[y + 1][x + 1]))
            harita["Back"][y][x] = (rng.choice(TOPRAK) if k == "dddd"
                                    else rng.choice(CIMEN) if k == "gggg" else KENAR[k])


# ---------------------------------------------------------------- damga ---
def damga(kaynak, kx0, ky0, kx1, ky1, hx, hy, filtre):
    """Kaynak haritanın (kx0,ky0)-(kx1,ky1) bölgesini (hx,hy)'ye kopyalar.
    filtre(katman, gid) True dönen karolar alınır."""
    for ad in KATMANLAR:
        if ad not in kaynak.katman:
            continue
        for y in range(ky0, ky1 + 1):
            for x in range(kx0, kx1 + 1):
                gid = kaynak.katman[ad][y][x]
                if gid and filtre(ad, gid):
                    harita[ad][hy + y - ky0][hx + x - kx0] = gid


# Evlerin yanındaki tahta çitin karoları: Town'da yalnızca çit olan hücrelerden öğrenilir
CIT_ORNEK = [(52, 55), (52, 56), (53, 55), (53, 56), (5, 76), (5, 77), (16, 76), (16, 77),
             (6, 87), (6, 88), (7, 87), (7, 88), (55, 74), (55, 75), (67, 74), (67, 75),
             (55, 77), (55, 78), (55, 79)]
CIT = {town.katman[ad][y][x] for x, y in CIT_ORNEK
       for ad in ("Buildings", "Buildings2", "Front", "AlwaysFront")} - {0}


def ev_filtresi(ad, gid):
    if ad in ("Back", "Paths") or gid in CIT:
        return False
    return KASABA0 <= gid < KASABA1 or (ad.startswith("Back") and GOLGE0 <= gid < GOLGE1)


def ev(kx0, ky0, kx1, ky1, hx, hy, boya=None):
    """Town'daki evi köye kopyalar. boya verilirse evin karoları yeniden boyanıp
    modun kendi karo setine (cinarkoy_evler) eklenir ve ev o karolarla kurulur."""
    if boya is None:
        return damga(town, kx0, ky0, kx1, ky1, hx, hy, ev_filtresi)
    for ad in KATMANLAR:
        for y in range(ky0, ky1 + 1):
            for x in range(kx0, kx1 + 1):
                gid = town.katman[ad][y][x]
                if not gid or not ev_filtresi(ad, gid):
                    continue
                if KASABA0 <= gid < KASABA1:
                    anahtar = (boya, gid - KASABA0)
                    if anahtar not in OZEL:
                        OZEL[anahtar] = len(OZEL)
                    gid = OZEL0 + OZEL[anahtar]
                harita[ad][hy + y - ky0][hx + x - kx0] = gid


# ------------------------------------------------------- yeniden boyama ---
OZEL = {}                 # (boya işlevi, kasaba karo no) -> özel karo setindeki sıra
OZEL0 = 6000              # özel karo setinin ilk numarası
OZEL_SUTUN = 16
MEVSIMLER = ["spring", "summer", "fall", "winter"]


def _boya(kural):
    """kural(h, s, v) -> (h, s, v) ya da None. h derece (0-360), s ve v 0-1."""
    def uygula(karo):
        px = karo.load()
        for y in range(16):
            for x in range(16):
                r, g, b, a = px[x, y]
                if a == 0:
                    continue
                h, sat, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
                yeni = kural(h * 360, sat, v)
                if yeni:
                    nr, ng, nb = colorsys.hsv_to_rgb(yeni[0] / 360, min(1, yeni[1]), min(1, yeni[2]))
                    px[x, y] = (round(nr * 255), round(ng * 255), round(nb * 255), a)
        return karo
    return uygula


def _yesil(h, s, v):          # mavi duvar -> yeşil, mor çatı -> kiremit
    if 185 <= h <= 255 and s > 0.15:
        return 105, s * 0.7, v * 0.95
    if 255 < h <= 345 and s > 0.12:
        return 14, s * 1.15, v * 1.05


def _arduvaz(h, s, v):        # turuncu çatı -> mavi-gri arduvaz, duvar -> açık sarı
    if (h <= 32 or h >= 350) and s > 0.50:
        return 212, s * 0.55, v * 0.92
    if 15 <= h <= 45 and s <= 0.50 and v > 0.35:
        return 48, s * 1.1, v


def _krem(h, s, v):           # soluk mavi duvar -> krem
    if 185 <= h <= 245 and 0.06 < s < 0.34 and v > 0.40:
        return 36, s * 1.5 + 0.06, v


YESIL, ARDUVAZ, KREM = _boya(_yesil), _boya(_arduvaz), _boya(_krem)


# --------------------------------------------------------------- ağaçlar ---
def agac_ogren(govde, sutun0, genislik, tac_satir, govdeler):
    """Town.tmx'te bu ağacın en eksiksiz örneğini bulup katman düzenini öğrenir.
    Dönen: [(katman, dx, dy, gid)], (0,0) = kök karosu."""
    gidler = {r * 25 + sutun0 + c + 1 for r in range(tac_satir) for c in range(genislik)} | set(govdeler)
    yari = genislik // 2
    en_iyi = []
    for y in range(8, town.y):
        for x in range(yari, town.g - yari):
            if town.katman["Buildings"][y][x] != govde:
                continue
            bulunan = []
            for ad in ("Buildings", "Buildings2", "Front", "AlwaysFront"):
                for dy in range(-(tac_satir + 2), 1):
                    for dx in range(-yari, yari + 1):
                        gid = town.katman[ad][y + dy][x + dx]
                        if gid in gidler:
                            bulunan.append((ad, dx, dy, gid))
            if len(bulunan) > len(en_iyi):
                en_iyi = bulunan
    assert en_iyi, f"ağaç bulunamadı: {govde}"
    return en_iyi


MESE = agac_ogren(127, 0, 3, 4, [102, 127])
MESE2 = agac_ogren(130, 3, 3, 4, [105, 130])
PEMBE = agac_ogren(144, 17, 5, 4, [119, 120, 144, 145, 169, 170])


def agac(tur, x, y, zorla=False):
    """Kökü (x,y)'de olan ağaç diker; yer doluysa dikmez."""
    hucreler = [(ad, x + dx, y + dy, gid) for ad, dx, dy, gid in tur]
    if any(not (0 <= cx < G and 0 <= cy < Y) for _, cx, cy, _ in hucreler):
        return False
    if not zorla:
        if any(dolu(cx, cy) for _, cx, cy, _ in hucreler):
            return False
        if any(harita["Back"][cy][cx] not in CIMEN for ad, cx, cy, _ in hucreler if ad.startswith("Buildings")):
            return False
    for ad, cx, cy, gid in hucreler:
        harita[ad][cy][cx] = gid
    return True


# ------------------------------------------------------------- yerleşim ---
# Ana yol (doğu-batı) ve ortadaki meydan
yol(4, 22, 55, 23)
yol(26, 19, 36, 21)

# Kuzey sırası: kapılar güneye, ana yola bakar
EVLER = [
    # (Town'daki bölge)   (köydeki sol üst)  boya
    ((52, 53, 62, 63), (13, 8), None),       # gri-mavi ev (oyundaki haliyle)
    ((56, 73, 64, 88), (40, 4), None),       # büyük konak (oyundaki haliyle)
    ((7, 74, 15, 88), (18, 27), YESIL),      # yeşil ev, kiremit çatı
    ((54, 53, 62, 63), (29, 28), KREM),      # krem ev
    ((19, 79, 26, 88), (41, 28), ARDUVAZ),   # sarı ev, arduvaz çatı
]
yol(18, 19, 18, 21)                   # gri-mavi evin kapısı -> yol
yol(42, 19, 43, 21)                   # konağın kapısı -> yol
# Güney sırası: kapı güneyde, patika evin yanından dolanır
yol(27, 24, 28, 40)
yol(10, 39, 28, 40)
yol(10, 38, 11, 38)                   # kulübenin kapısı
yol(38, 24, 39, 40)
yol(38, 38, 45, 39)
yol(29, 39, 37, 40)                   # krem evin önü, iki patikayı birleştirir

zemini_dose()
for (kx0, ky0, kx1, ky1), (hx, hy), boya in EVLER:
    ev(kx0, ky0, kx1, ky1, hx, hy, boya)

# Sıfırdan çizilmiş kulübe (tools/ev_ciz.py üretir): üst 2 sıra Front, gerisi Buildings
KULUBE0, KULUBE_G, KULUBE_Y = 7000, 8, 7
KULUBE_PNG = Image.open(ASSETS / "cinarkoy_kulube.png").convert("RGBA")
KULUBE = (7, 31)
for ky in range(KULUBE_Y):
    for kx in range(KULUBE_G):
        if KULUBE_PNG.crop((kx * 16, ky * 16, kx * 16 + 16, ky * 16 + 16)).getbbox():
            harita["Front" if ky < 2 else "Buildings"][KULUBE[1] + ky][KULUBE[0] + kx] = KULUBE0 + ky * KULUBE_G + kx

# Vagon: Town'daki ray + vagon + kol
damga(town, 105, 77, 105, 80, VAGON[0], VAGON[1], lambda ad, gid: gid not in CIMEN and ad != "Paths")
damga(town, 106, 79, 107, 79, VAGON[0] + 1, VAGON[1] + 2, lambda ad, gid: ad not in ("Back", "Paths"))
VAGON_TIK = [(VAGON[0], y) for y in range(VAGON[1], VAGON[1] + 4) if harita["Buildings"][y][VAGON[0]]]

# Tabela: BusStop'taki yön tabelası
TABELA_UST = bus.katman["Front"][21][21]
TABELA_ALT = bus.katman["Buildings"][22][21]
harita["Front"][TABELA[1] - 1][TABELA[0]] = TABELA_UST
harita["Buildings"][TABELA[1]][TABELA[0]] = TABELA_ALT

# Meydanın kuzeyinde kiraz ağacı
agac(PEMBE, 31, 16)

# Kenar: haritayı çevreleyen ağaç şeridi (taçlar üst üste binmeden)
for x in range(1, G - 1, 3):
    agac(rng.choice((MESE, MESE2)), x, 5)
    agac(rng.choice((MESE, MESE2)), x, Y - 1)
for y in range(9, Y - 4, 4):
    agac(rng.choice((MESE, MESE2)), 1, y)
    agac(rng.choice((MESE, MESE2)), G - 2, y)

# İçeride serpiştirilmiş ağaçlar
dikilen, deneme = 0, 0
while dikilen < 14 and deneme < 4000:
    deneme += 1
    x, y = rng.randrange(5, G - 5), rng.randrange(12, Y - 7)
    cevre_bos = all(not dolu(cx, cy) and harita["Back"][cy][cx] in CIMEN
                    for cy in range(y - 6, y + 2) for cx in range(x - 2, x + 3))
    if cevre_bos and agac(rng.choice((MESE, MESE2)), x, y):
        dikilen += 1

for vx, vy in (VARIS_VAGON, VARIS_TABELA):
    assert not dolu(vx, vy, ("Buildings", "Buildings2")), "Varış karosu dolu!"


# ---------------------------------------------------------------- çıktı ---
def set_xml(kaynak_harita, kaynak):
    ts = copy.deepcopy(kaynak_harita.setler[kaynak])
    ts.find("image").set("source", kaynak + ".png")
    ts.tail = "\n "
    return ET.tostring(ts, encoding="unicode").rstrip()


def katman_xml(i, ad, veri, g, y):
    csv = ",\n".join(",".join(map(str, satir)) for satir in veri)
    return f' <layer id="{i}" name="{ad}" width="{g}" height="{y}">\n  <data encoding="csv">\n{csv}\n</data>\n </layer>\n'


def tmx(g, y, setler, katmanlar, ozellikler=""):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<map version="1.4" tiledversion="1.4.2" orientation="orthogonal" renderorder="right-down" '
            f'width="{g}" height="{y}" tilewidth="16" tileheight="16" infinite="0" '
            f'nextlayerid="{len(katmanlar) + 1}" nextobjectid="1">\n'
            + ozellikler
            + "".join(" " + s + "\n" for s in setler)
            + "".join(katman_xml(i, ad, veri, g, y) for i, (ad, veri) in enumerate(katmanlar, 1))
            + "</map>\n")


def ozel_set_yaz():
    """Yeniden boyanmış ev karolarını dört mevsim için ayrı PNG olarak yazar."""
    satir = (len(OZEL) + OZEL_SUTUN - 1) // OZEL_SUTUN
    sutun = int(town.setler["spring_town"].get("columns"))
    for mevsim in MEVSIMLER:
        kasaba = Image.open(MAPS / f"{mevsim}_town.png").convert("RGBA")
        sayfa = Image.new("RGBA", (OZEL_SUTUN * 16, satir * 16), (0, 0, 0, 0))
        for (boya, no), sira in OZEL.items():
            kx, ky = (no % sutun) * 16, (no // sutun) * 16
            sayfa.paste(boya(kasaba.crop((kx, ky, kx + 16, ky + 16))),
                        ((sira % OZEL_SUTUN) * 16, (sira // OZEL_SUTUN) * 16))
        sayfa.save(ASSETS / f"{mevsim}_cinarkoy_evler.png")
    return (f'<tileset firstgid="{OZEL0}" name="cinarkoy_evler" tilewidth="16" tileheight="16" '
            f'tilecount="{satir * OZEL_SUTUN}" columns="{OZEL_SUTUN}">\n'
            f'  <image source="spring_cinarkoy_evler.png" width="{OZEL_SUTUN * 16}" height="{satir * 16}"/>\n'
            ' </tileset>')


KULUBE_SET = (f'<tileset firstgid="{KULUBE0}" name="cinarkoy_kulube" tilewidth="16" tileheight="16" '
              f'tilecount="{KULUBE_G * KULUBE_Y}" columns="{KULUBE_G}">\n'
              f'  <image source="cinarkoy_kulube.png" width="{KULUBE_G * 16}" height="{KULUBE_Y * 16}"/>\n'
              ' </tileset>')


def yaz():
    ASSETS.mkdir(parents=True, exist_ok=True)
    koy = tmx(G, Y, [set_xml(town, s) for s in SETLER] + [ozel_set_yaz(), KULUBE_SET], [(ad, harita[ad]) for ad in KATMANLAR],
              ' <properties>\n  <property name="Outdoors" type="string" value="T"/>\n </properties>\n')
    (ASSETS / "Cinarkoy.tmx").write_text(koy, encoding="utf-8")
    # Otobüs durağı yaması: 1x2, üstte tabela levhası (Front), altta direk (Buildings)
    yama = tmx(1, 2, [set_xml(bus, "spring_outdoorsTileSheet")],
               [("Buildings", [[0], [TABELA_ALT]]), ("Front", [[TABELA_UST], [0]])])
    (ASSETS / "Tabela.tmx").write_text(yama, encoding="utf-8")


def onizleme():
    sayfalar = []
    for s in SETLER:
        ts = town.setler[s]
        sayfalar.append((int(ts.get("firstgid")), int(ts.get("columns")),
                         Image.open(MAPS / f"{s}.png").convert("RGBA")))
    sayfalar.append((OZEL0, OZEL_SUTUN, Image.open(ASSETS / "spring_cinarkoy_evler.png").convert("RGBA")))
    sayfalar.append((KULUBE0, KULUBE_G, KULUBE_PNG))
    im = Image.new("RGBA", (G * 16, Y * 16), (0, 0, 0, 255))
    for ad in KATMANLAR:
        if ad == "Paths":
            continue
        for y in range(Y):
            for x in range(G):
                gid = harita[ad][y][x]
                if not gid:
                    continue
                ilk, sutun, sayfa = [s for s in sayfalar if s[0] <= gid][-1]
                i = gid - ilk
                kx, ky = (i % sutun) * 16, (i // sutun) * 16
                im.alpha_composite(sayfa.crop((kx, ky, kx + 16, ky + 16)), (x * 16, y * 16))
    im.resize((G * 32, Y * 32), Image.NEAREST).save(KOK / "onizleme.png")


if __name__ == "__main__":
    yaz()
    onizleme()
    print(f"Tamam: {G}x{Y} harita, {dikilen} iç ağaç")
    print("Vagon tıklama karoları (Buildings):", VAGON_TIK)
