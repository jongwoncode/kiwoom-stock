# "이"의 index 모두 출력.
a = "이종영, 이종원, 이종투, 이종삼, 이종포, 이종오, 이종육, 이종칠, 이종팔, 이종구"
output = []
idx = 0
while True:
    output.append(a.find("이", idx))
    idx += a.find("이", idx)

    if idx == -1:
        beak
print(output)
