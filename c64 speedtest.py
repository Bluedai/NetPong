import time

maxzahl = 100000000
# zähle bis 1000000
start = time.time()
# for i in range(1000000):
#     pass
i = 0
while i < maxzahl:
    i += 1

end = time.time()
print(end - start)

print("gegenprobe:", maxzahl / (end - start), " Schleifendurchläufe pro Sekunde")
print("Das ist ", round((maxzahl / (end - start)) /500), " mal so schnell wie ein C64")
      


