# İlk deneme
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)

print("Merhaba, Piton!")
for i in range(10):
    print(i, fib(i))
x = [1, 2, 3]
x.append(4)
print(x, len(x), sum(x))
d = {"a": 1, "b": 2}
d["c"] = 3
for k, v in d.items():
    print(f"{k} = {v}")
print(10 / 4, 7 // 2, -7 % 3, 2 ** 10)
