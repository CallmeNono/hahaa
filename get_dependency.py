# coding: utf-8

import re
import requests


sentence = "宝马3系2.0T舒适版和奔驰C级2.0t对比怎么样"
#orca_result = requests.get("http://api.orca.corpautohome.com/cognitive?q={}".format(sentence)).json()["entities"]
orca_result = [{'str': '宝马3系', 'score': 1.0, 'endIndex': 3, 'entity': '宝马3系', 'type': '车系', 'startIndex': 0}, {'str': '2.0T', 'score': 1.0, 'endIndex': 7, 'entity': '2.0t', 'type': '排量(L)', 'startIndex': 4}, {'str': '舒适版', 'score': 1.0, 'endIndex': 10, 'entity': '舒适版', 'type': '版型', 'startIndex': 8}, {'str': '奔驰C级', 'score': 1.0, 'endIndex': 15, 'entity': '奔驰C级', 'type': '车系', 'startIndex': 12}, {'str': '2.0T', 'score': 1.0, 'endIndex': 19, 'entity': '2.0t', 'type': '排量(L)', 'startIndex': 16}]


flag_entity = ["车系","品牌"]
modifier = {"车系":[]}

def reorganize_entity(entity_list):
    remember_dict = {}
    for item in entity_list:
        if item["type"] in remember_dict.keys():
            remember_dict[item["type"]]+=1
            item["type"] = item["type"]+"_"+str(remember_dict[item["type"]])
        else:
            remember_dict[item["type"]]=0
    return entity_list

a = reorganize_entity(orca_result)
print(a)