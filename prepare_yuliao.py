# coding: utf-8
a = open("for_baoyang","r",encoding="utf8")
w = open("nums","w",encoding="utf8")
for i in a:
    jump = i.strip().split("\t")
    w.write(jump[0]+"\t"+jump[2]+"\t"+jump[3])
    w.write("\n")
print(jump)