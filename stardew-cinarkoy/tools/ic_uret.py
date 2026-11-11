#!/usr/bin/env python3
"""Çınarköy evlerinin iç haritalarını üretir.

Her ev için ayrı bir oda haritası (assets/Ic_<Konum>.tmx) yazar. Odalar yalnızca
modun kendi karo setini (cinarkoy_ic.png, tools/ic_ciz.py üretir) kullanır.

Tek başına çalıştırılırsa önizleme için haritaları üretir; asıl kullanımda
harita_uret.py bunu içe aktarır ve her odanın çıkışını köydeki kapıya bağlar.

Koordinatlar: fx, fy = oda zemini üzerindeki karo (sol üst 0,0).
Haritadaki karşılığı: x = fx + 1, y = fy + 4 (üstte 1 kenar + 3 duvar sırası).
"""
from pathlib import Path

from PIL import Image

import ic_ciz

KOK = Path(__file__).resolve().parent.parent
ASSETS = KOK / "[CP] Cinarkoy" / "assets"
MOD = "TahaAkhan.Cinarkoy"
KOY = f"{MOD}_Koy"
DUVAR_Y = 3                                             # arka duvarın karo yüksekliği

SAYFA, YER = ic_ciz.yaz()


def gid(ad, dx=0, dy=0):
    x, y, _, _ = YER[ad]
    return 1 + (y + dy) * ic_ciz.SUTUN + x + dx


def dolu_mu(ad, dx, dy):
    x, y, _, _ = YER[ad]
    sx, sy = (x + dx) * 16, (y + dy) * 16
    return SAYFA.crop((sx, sy, sx + 16, sy + 16)).getbbox() is not None


class Oda:
    def __init__(self, konum, gk, yk, duvar, zemin, kapi):
        self.konum, self.gk, self.yk, self.kapi = konum, gk, yk, kapi
        self.G, self.Y = gk + 2, yk + DUVAR_Y + 2
        self.k = {ad: [[0] * self.G for _ in range(self.Y)] for ad in ("Back", "Buildings", "Front")}
        b, bu = self.k["Back"], self.k["Buildings"]
        for y in range(self.Y):
            for x in range(self.G):
                b[y][x] = gid("bosluk")
        for x in range(1, self.G - 1):
            for i in range(DUVAR_Y):
                bu[1 + i][x] = gid(duvar, 0, i)
            for y in range(DUVAR_Y + 1, self.Y - 1):
                b[y][x] = gid(zemin, x % 4, y % 2)
            bu[self.Y - 1][x] = gid("kenar_alt")
        for y in range(1, self.Y - 1):
            bu[y][0] = gid("kenar_sol")
            bu[y][self.G - 1] = gid("kenar_sag")
        bu[0] = [gid("bosluk")] * self.G
        bu[self.Y - 1][0] = gid("kenar_alt_sol")
        bu[self.Y - 1][self.G - 1] = gid("kenar_alt_sag")
        kx = kapi + 1                                   # kapı boşluğu
        bu[self.Y - 1][kx] = 0
        b[self.Y - 1][kx] = gid("paspas")

    # -- yerleştirme --
    def _koy(self, ad, mx, my, on):
        _, _, gk, yk = YER[ad]
        for dy in range(yk):
            for dx in range(gk):
                if dolu_mu(ad, dx, dy):
                    self.k["Front" if dy < on else "Buildings"][my + dy][mx + dx] = gid(ad, dx, dy)

    def yere(self, ad, fx, fy, on=0):
        """Zemine mobilya; üstten `on` sıra oyuncunun önünde çizilir."""
        self._koy(ad, fx + 1, fy + DUVAR_Y + 1, on)

    def arka(self, ad, fx):
        """Arka duvara dayalı mobilya: alt sırası ilk zemin sırasında, üstü duvarın önünde."""
        yk = YER[ad][3]
        self._koy(ad, fx + 1, DUVAR_Y + 1 - (yk - 1), yk - 1)

    def duvara(self, ad, fx, sira=1):
        """Duvar süsü (pencere, tablo): tamamı Front katmanında."""
        self._koy(ad, fx + 1, sira, 99)

    def zemine(self, ad, fx, fy):
        """Halı gibi üstünde yürünen parçalar: Back katmanı."""
        _, _, gk, yk = YER[ad]
        for dy in range(yk):
            for dx in range(gk):
                self.k["Back"][fy + DUVAR_Y + 1 + dy][fx + 1 + dx] = gid(ad, dx, dy)

    # -- bilgi --
    def karo(self, fx, fy):
        return fx + 1, fy + DUVAR_Y + 1

    @property
    def giris(self):
        """Dışarıdan girince oyuncunun durduğu karo."""
        return self.kapi + 1, self.Y - 2

    def bos(self, fx, fy):
        x, y = self.karo(fx, fy)
        return self.k["Buildings"][y][x] == 0

    # -- çıktı --
    def tmx(self, disari):
        """disari: köyde bu evin kapısının önündeki karo (x, y)."""
        def katman(i, ad):
            csv = ",\n".join(",".join(map(str, s)) for s in self.k[ad])
            return (f' <layer id="{i}" name="{ad}" width="{self.G}" height="{self.Y}">\n'
                    f'  <data encoding="csv">\n{csv}\n</data>\n </layer>\n')
        warp = f"{self.kapi + 1} {self.Y} {KOY} {disari[0]} {disari[1]}"
        return ('<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<map version="1.4" tiledversion="1.4.2" orientation="orthogonal" renderorder="right-down" '
                f'width="{self.G}" height="{self.Y}" tilewidth="16" tileheight="16" infinite="0" '
                'nextlayerid="4" nextobjectid="1">\n'
                ' <properties>\n'
                f'  <property name="Warp" type="string" value="{warp}"/>\n'
                ' </properties>\n'
                f' <tileset firstgid="1" name="cinarkoy_ic" tilewidth="16" tileheight="16" '
                f'tilecount="{SAYFA.width // 16 * (SAYFA.height // 16)}" columns="{ic_ciz.SUTUN}">\n'
                f'  <image source="cinarkoy_ic.png" width="{SAYFA.width}" height="{SAYFA.height}"/>\n'
                ' </tileset>\n'
                + "".join(katman(i, ad) for i, ad in enumerate(("Back", "Buildings", "Front"), 1))
                + '</map>\n')

    def onizleme(self):
        im = Image.new("RGBA", (self.G * 16, self.Y * 16), (0, 0, 0, 255))
        for ad in ("Back", "Buildings", "Front"):
            for y in range(self.Y):
                for x in range(self.G):
                    g = self.k[ad][y][x]
                    if g:
                        sx, sy = ((g - 1) % ic_ciz.SUTUN) * 16, ((g - 1) // ic_ciz.SUTUN) * 16
                        im.alpha_composite(SAYFA.crop((sx, sy, sx + 16, sy + 16)), (x * 16, y * 16))
        return im


# ------------------------------------------------------------------ odalar ---
def tas_kulube():
    o = Oda("TasKulube", 9, 6, "duvar_krem", "zemin_tahta", kapi=4)
    o.arka("saksi", 0)
    o.arka("somine", 1)
    o.duvara("pencere_mavi", 4)
    o.arka("kitaplik", 6)
    o.duvara("tablo", 8, 2)
    o.zemine("hali_mavi", 3, 1)
    o.yere("yatak_mavi", 7, 2)
    o.yere("masa_duz", 0, 3)
    o.yere("tabure", 2, 4)
    return o


def siva_kulube():
    o = Oda("SivaKulube", 9, 6, "duvar_pembe", "zemin_tahta", kapi=4)
    o.arka("dolap", 1)
    o.duvara("tablo", 0, 2)
    o.duvara("pencere_kirmizi", 4)
    o.arka("somine_tugla", 6)
    o.arka("saksi", 8)
    o.zemine("hali_kirmizi", 3, 1)
    o.yere("yatak_kirmizi", 0, 2)
    o.yere("masa", 6, 3)
    o.yere("tabure", 5, 4)
    return o


def ahsap_ev():
    o = Oda("AhsapEv", 9, 7, "duvar_tahta", "zemin_tahta", kapi=4)
    o.arka("saksi", 0)
    o.duvara("pencere_yesil", 1)
    o.arka("somine", 3)
    o.duvara("tablo", 5, 2)
    o.arka("kitaplik", 6)
    o.zemine("hali_yesil", 3, 1)
    o.yere("marangoz_tezgahi", 0, 3)
    o.yere("odun_yigini", 0, 5)
    o.yere("sandik", 2, 6)
    o.yere("yatak_yesil", 7, 3)
    return o


def iki_katli():
    o = Oda("IkiKatli", 12, 8, "duvar_mavi", "zemin_tahta", kapi=5)
    o.arka("saksi", 0)
    o.arka("kitaplik", 1)
    o.duvara("pencere_mavi", 3)
    o.arka("somine", 5)
    o.duvara("pencere_mavi", 8)
    o.arka("dolap", 9)
    o.arka("saksi", 11)
    o.zemine("hali_mor", 4, 1)
    o.yere("yatak_mor", 0, 3)
    o.yere("yatak_sari", 10, 3)
    o.yere("masa", 7, 4)
    o.yere("tabure", 6, 5)
    o.yere("tabure", 9, 5)
    return o


def dukkan():
    o = Oda("Bakkal", 12, 7, "duvar_krem", "zemin_tas", kapi=4)
    o.arka("mal_rafi_1", 0)
    o.arka("mal_rafi_2", 2)
    o.arka("mal_rafi_3", 4)
    o.arka("fici", 6)
    o.arka("fici", 7)
    o.duvara("pencere_kirmizi", 9)
    o.duvara("tablo", 11, 2)
    for i, parca in enumerate(("tezgah_sol", "tezgah_orta", "tezgah_duz", "tezgah_sag")):
        o.yere(parca, 1 + i, 2)
    o.yere("sandik", 8, 0)
    o.yere("cuval", 0, 5)
    o.yere("cuval", 1, 6)
    o.yere("sandik", 0, 6)
    o.zemine("hali_kirmizi", 6, 3)
    o.yere("yatak_kirmizi", 10, 3)
    return o


def ahir():
    o = Oda("Ahir", 12, 8, "duvar_ahir", "zemin_saman", kapi=5)
    o.duvara("pencere_yesil", 3)
    o.duvara("pencere_yesil", 9)
    o.yere("saman_balyasi", 0, 0)
    o.yere("saman_balyasi", 0, 2)
    o.yere("yalak", 4, 0)
    for fx in range(7, 12):                            # hayvan bölmesi
        o.yere("bolme", fx, 1, on=1)
    o.yere("yalak", 9, 0)
    o.arka("fici", 2)
    o.yere("cuval", 0, 6)
    o.yere("cuval", 1, 7)
    o.yere("sandik", 0, 7)
    o.yere("yatak_mavi", 10, 5)
    o.yere("sandik", 9, 7)
    return o


# bina adı (ev_ciz.BINALAR) -> oda
ODALAR = {"tas_kulube": tas_kulube(), "siva_kulube": siva_kulube(), "ahsap_ev": ahsap_ev(),
          "iki_katli": iki_katli(), "dukkan": dukkan(), "ahir": ahir()}

# Köylülerin evdeki yerleri: (bina, fx, fy, baktığı yön) — 0 yukarı, 1 sağ, 2 aşağı, 3 sol
YERLER = {
    "Halil.yatak": ("dukkan", 9, 4, 1), "Halil.tezgah": ("dukkan", 2, 1, 2),
    "Nazife.yatak": ("iki_katli", 2, 4, 3), "Nazife.somine": ("iki_katli", 5, 2, 0),
    "Elif.yatak": ("iki_katli", 9, 4, 1), "Elif.masa": ("iki_katli", 8, 6, 0),
    "Kerem.yatak": ("ahir", 9, 6, 1), "Kerem.yalak": ("ahir", 5, 1, 0),
    "Zeynep.yatak": ("ahsap_ev", 6, 4, 1), "Zeynep.tezgah": ("ahsap_ev", 3, 4, 3),
}
for anahtar, (bina, fx, fy, _) in YERLER.items():
    assert ODALAR[bina].bos(fx, fy), f"{anahtar}: karo dolu"
for bina, oda in ODALAR.items():
    assert oda.k["Buildings"][oda.giris[1]][oda.giris[0]] == 0, f"{bina}: giriş karosu dolu"


def konum(bina):
    return f"{MOD}_{ODALAR[bina].konum}"


def nokta(anahtar):
    """Program satırı parçası: '<konum> <x> <y> <yön>'."""
    bina, fx, fy, yon = YERLER[anahtar]
    x, y = ODALAR[bina].karo(fx, fy)
    return f"{konum(bina)} {x} {y} {yon}"


def yaz(disari=None):
    """disari: {bina: (x, y)} köydeki kapı önü karoları. Verilmezse (0,0) yazılır."""
    for bina, oda in ODALAR.items():
        (ASSETS / f"Ic_{oda.konum}.tmx").write_text(oda.tmx((disari or {}).get(bina, (0, 0))), encoding="utf-8")


def onizleme(yol):
    resimler = [o.onizleme() for o in ODALAR.values()]
    g = max(r.width for r in resimler) * 2 + 24
    y = sum(max(a.height, b.height) + 8 for a, b in zip(resimler[::2], resimler[1::2])) + 8
    tum = Image.new("RGBA", (g, y), (60, 60, 70, 255))
    yy = 8
    for a, b in zip(resimler[::2], resimler[1::2]):
        tum.alpha_composite(a, (8, yy))
        tum.alpha_composite(b, (g // 2 + 4, yy))
        yy += max(a.height, b.height) + 8
    tum.resize((tum.width * 3, tum.height * 3), Image.NEAREST).save(yol)


if __name__ == "__main__":
    yaz()
    onizleme(KOK / "onizleme_ic.png")
    print("Yazıldı:", ", ".join(o.konum for o in ODALAR.values()))
