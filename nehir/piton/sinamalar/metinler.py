s = "  Nehir, Python'u derliyor!  "
print(s.strip().upper(), s.lower().strip(), s.strip().split(", "))
print("-".join(["a", "b", "c"]), "a,b,,c".split(","), "bir  iki üç".split())
print("merhaba".replace("a", "4"), "nehir".startswith("ne"), "nehir".endswith("ir"), "nehir".find("hi"))
print("abc"[::-1], "abcdef"[1:4], "abcdef"[::2], "abcdef"[-2:], len("çiçek"))
print(f"{3.14159:.2f} {42:>6} {42:<6}| {'orta':^10}| {1234567:,} {0.256:.1%} {255:x} {255:#b}")
ad = "Ayşe"
yaş = 30
print(f"{ad} {yaş} yaşında; gelecek yıl {yaş + 1}.", f"{ad=}", f"{yaş * 2 = }")
print("%s %d %.3f %5s|%-5s|" % ("x", 42, 3.14159, "sağ", "sol"))
print("{} + {} = {}".format(1, 2, 3), "{0}{1}{0}".format("a", "b"), "{ad}".format(ad="Can"))
print(repr("tırnak'lı"), repr('çift"tırnak'), str(1.0), str(1e20), str(1.5e-7), 1/3)
print("x".center(7, "*"), "42".zfill(5), "Başlık bu".title(), "a b c".count(" "), "ABC".isupper(), "123".isdigit())
print(ord("A"), chr(231), "ılık".upper(), "İSTANBUL".lower(), "ß".upper())
print("satır1\nsatır2".splitlines(), "a=b=c".partition("="), "a=b=c".rsplit("=", 1))
for i, k in enumerate("çay"):
    print(i, k, end=" ")
print()
print(*[1, 2, 3], sep=" | ")
print(int("42") + 1, int("ff", 16), int(" -7 "), float("2.5") * 2, int(3.99), int(-3.99), bool(""), bool("a"))
print(0.1 + 0.2, 1e16, 1e-5, 123456789012345678, 2 ** 62, -2 ** 2, (-2) ** 2, 7 % -3, -7 // 2)
print(round(2.5), round(3.5), round(-0.5), round(1234.5678, -2), 10 // 3.0, 10 % 3.5)
print([1, [2, 3]] == [1, [2, 3]], (1, 2) < (1, 3), "a" < "b", None is None, 3 in [1, 2, 3], "z" not in "abc")
