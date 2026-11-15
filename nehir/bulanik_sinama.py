# Bulanık sınama: örnek programları rastgele bozar (sözcük siler, ekler, yer değiştirir) ve
# iki derleyiciye verir. Python derleyicisi iç hata (traceback) vermemeli, Nehir ile yazılmış
# derleyici çökmemeli, ikisi aynı assembly'yi ya da aynı tanıları vermeli.
#
#   python3 bulanik_sinama.py [deneme sayısı] [tohum]
import glob, os, random, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
KÖK = os.path.dirname(os.path.abspath(__file__))
S = tempfile.mkdtemp(prefix="nehir_bulanik_")
SAYI = int(sys.argv[1]) if len(sys.argv) > 1 else 500
TOHUM = int(sys.argv[2]) if len(sys.argv) > 2 else 1
DERLE = os.path.join(S, "derle_fuzz")
subprocess.run([sys.executable, "nehir.py", "kendi/derle.nehir", "-o", DERLE], cwd=KÖK, check=True)
kaynaklar = sorted(glob.glob(KÖK + "/ornekler/**/*.nehir", recursive=True) + glob.glob(KÖK + "/kendi/sinamalar/*.nehir"))
def okunur(k):
    try: return "kullan" not in open(k, encoding="utf-8").read()
    except UnicodeDecodeError: return False
kaynaklar = [k for k in kaynaklar if okunur(k)]
SÖZ = re.compile(r'\s+|"(?:[^"\\\n]|\\.)*"|\w+|->|==|!=|<=|>=|.', re.S)
EKLER = ["(", ")", "{", "}", "[", "]", ",", "->", ".", "|", ":", "eğer", "değilse", "iken", "her", "işlev",
         "döndür", "dur", "devam", "kayıt", "yok", "ortak", "0", "1.5", "\"m\"", "x", "+", "-", "*", "/", "\n",
         "yazdır", "uzunluk", "sırala", "ekran_yaz", "0x", "0b2", "9223372036854775808", "\"", "#", "\\"]
def boz(metin, r):
    s = SÖZ.findall(metin)
    for _ in range(r.randint(1, 3)):
        if not s: break
        i = r.randrange(len(s)); k = r.random()
        if k < 0.3: del s[i]
        elif k < 0.5: s.insert(i, r.choice(EKLER))
        elif k < 0.65: s.insert(i, r.choice(s))
        elif k < 0.8 and i + 1 < len(s): s[i], s[i + 1] = s[i + 1], s[i]
        else: s[i] = r.choice(s)
    return "".join(s)
def dene(n):
    r = random.Random(TOHUM * 100000 + n)
    kaynak = r.choice(kaynaklar)
    metin = boz(open(kaynak, encoding="utf-8").read(), r)
    d = os.path.join(S, "fuzz", f"f{n}")
    os.makedirs(d, exist_ok=True)
    yol = os.path.join(d, "p.nehir")
    open(yol, "w", encoding="utf-8").write(metin)
    try:
        p = subprocess.run([sys.executable, KÖK + "/nehir.py", "p.nehir", "--asm", "-o", "py.s"], cwd=d,
                           capture_output=True, timeout=60)
        q = subprocess.run([DERLE, "p.nehir", "nh.s", KÖK + "/calisma_zamani.s"], cwd=d, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return (n, kaynak, "zaman aşımı")
    if b"Traceback" in p.stderr:
        return (n, kaynak, "python iç hata: " + p.stderr.decode(errors="replace").strip().split("\n")[-1])
    if q.returncode not in (0, 1, 2, 3) or "çalışma hatası".encode() in q.stderr:
        return (n, kaynak, f"nehir derleyicisi çöktü ({q.returncode}): " + q.stderr.decode(errors="replace")[:200])
    if q.returncode == 3:
        return None
    if p.returncode != q.returncode or p.stderr != q.stderr:
        return (n, kaynak, "farklı tanı:\n  PY: " + p.stderr.decode(errors="replace")[:300] + "\n  NH: " + q.stderr.decode(errors="replace")[:300])
    if p.returncode == 0 and open(os.path.join(d, "py.s"), "rb").read() != open(os.path.join(d, "nh.s"), "rb").read():
        return (n, kaynak, "farklı assembly")
    return None
with ThreadPoolExecutor(6) as h:
    sonuçlar = [x for x in h.map(dene, range(SAYI)) if x]
for n, k, m in sonuçlar:
    print(f"#{n} {os.path.relpath(k, KÖK)}: {m}")
print("bitti:", SAYI, "deneme,", len(sonuçlar), "sorun  (dosyalar:", S + ")")
sys.exit(1 if sonuçlar else 0)
