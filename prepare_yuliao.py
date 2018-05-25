# coding: utf-8
a = open("errorsss","r",encoding="utf8")
w = open("baiyang_badcase.txt","w",encoding="utf8")
for i in a:
    jump = i.strip().split("\t")
    o = jump[3].split("  ")
    jump.pop(3)
    jump.append(o[0])
    jump.append(o[1])
    iii = "\t".join(jump)
    w.write(iii)
    w.write("\n")
print(jump)