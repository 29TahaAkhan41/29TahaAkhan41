ad = input("Adın ne? ")
print(f"Merhaba {ad}!")
n = int(input("Kaç sayı? "))
sayılar = []
for i in range(n):
    sayılar.append(float(input()))
print("toplam:", sum(sayılar), "ortalama:", sum(sayılar) / len(sayılar))
satırlar = []
while True:
    s = input()
    if s == "son":
        break
    satırlar.append(s.upper())
print(satırlar)
