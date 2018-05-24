# print("aaa".split(" "))
# c = {"车系":[["chain1","set"],"chain2"]}
# cx = [{"车系":"宝马5系"}]
# chain = {"chain":{"chain1":{"车系":{"宝马5系":""}},"chain2":{"车系":{"宝马5系":""}}}}
#
#
# import time
# a = time.time()
# for i in cx:   #i 是一个dict{"车系":"宝马5系"}
#     the_key = list(i.keys())[0]
#     if the_key in c.keys():
#         for slot_cells in c[the_key]:
#             if type(slot_cells)!=list:
#                 print(chain["chain"][slot_cells][the_key])
#                 chain["chain"][slot_cells][the_key][i[the_key]] = "1"
#                 print(chain)

# print(time.time()-a)
# a = 0.95
#
# if a:
#     print(int(a))
# import re
# aa = "车系__1512"
# pattern = re.compile("__\d+")
# aa = re.sub(pattern,"",aa)
# print(aa)
# print(1==1.0)
import requests
d = ["a"]
c= exec("def f(x): return x")
a1 = "ab"
a2 = "aa"
param_list = ["a","aa"]
print(c)
strs ='requests.get("http://api.orca.corpautohome.com/v0.2/cognitive?q=[$arg0]").json()'.format(["宝马5系","l"])
ggg = "'{}' in '{}'".format(a1,a2)
ttt = "'[$arg0]' in '[$arg1]'"
for i in range(len(param_list)):
    if '[$arg'+str(i)+']' in ttt:
        ttt = ttt.replace('[$arg'+str(i)+']',param_list[i])


print(ttt)
def abc(*g,**kwargs):
    print(kwargs)
abc("a","a","ccc","aaaaaa")
data = eval(ttt)
print(data)
print(len("".split("_")))
print({"code": 0, "message": "\u6210\u529f", "topScoringIntent": {"intent": "\u9009\u8f66", "score": 0.8258548378944397}, "intents": [{"intent": "None", "score": 0.011849227361381054}, {"intent": "\u4fdd\u503c\u7387", "score": 2.723278385019512e-07}, {"intent": "\u4fdd\u517b", "score": 1.3072253750578966e-05}, {"intent": "\u53e3\u7891", "score": 0.0020225225016474724}, {"intent": "\u54c1\u724c\u767e\u79d1", "score": 5.655079075950198e-05}, {"intent": "\u5f85\u5b9a", "score": 1.3517504839910544e-06}, {"intent": "\u641c\u7d22", "score": 0.15814904868602753}, {"intent": "\u65b0\u95fb", "score": 5.244945441518212e-06}, {"intent": "\u7ecf\u9500\u5546", "score": 0.00010697939433157444}, {"intent": "\u8bba\u575b", "score": 1.610483741387725e-05}, {"intent": "\u8be2\u4ef7", "score": 0.00010591611498966813}, {"intent": "\u8f66\u578b\u5bf9\u6bd4", "score": 0.0007017640164121985}, {"intent": "\u8f66\u7cfb\u56fe\u7247", "score": 4.1174743614647014e-07}, {"intent": "\u9009\u8f66", "score": 0.8258548378944397}, {"intent": "\u914d\u7f6e", "score": 0.0009416777174919844}, {"intent": "\u914d\u7f6e\u767e\u79d1", "score": 0.0001618348906049505}, {"intent": "\u91cd\u65b0\u9009\u8f66", "score": 3.5159141589247156e-06}, {"intent": "\u91d1\u878d", "score": 9.690823389973957e-06}], "entities": [{"entity": "\u4e00\u4e2a\u8f66\u95e8", "type": "\u8f66\u95e8\u6570(\u4e2a)", "startIndex": 3, "endIndex": 6, "score": 1.0, "str": "\u4e00\u4e2a\u8f66\u95e8"}], "query": "\u7ed9\u6211\u6765\u4e00\u4e2a\u8f66\u95e8\u6570\u5c11\u4e8e5\u4e2a\u7684\u8f66"})