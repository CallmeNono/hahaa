import re
import requests
import time
import redis

def make_term(name,value,logic=1):
    return {"name":name,"value":value,"logic":logic}

def extract_slot_details(_terms,_target_slot):   ####获取每个slot的细节
    #print(_target_slot)
    if len(_target_slot["set_dict"])!=0:
        for set_dicts in _target_slot["set_dict"]:
            _terms = extract_slot_details(_terms,_target_slot["set_dict"][set_dicts])
    if "set_mode" in _target_slot:
        if _target_slot["rank"]["completed_per"]==1:
            for _element in _target_slot["is_dict"]:
                if type(_target_slot["is_dict"][_element])==set:
                    if len(_target_slot["is_dict"][_element])!=0:
                        for item in _target_slot["is_dict"][_element]:
                            _terms.append(make_term(name=_element,value=item))
                else:
                    if _target_slot["is_dict"][_element]!="":
                        _terms.append(make_term(name=_element,value=_target_slot["is_dict"][_element]))

            for _element in _target_slot["not_dict"]:
                if type(_target_slot["not_dict"][_element])==set:
                    if len(_target_slot["not_dict"][_element])!=0:
                        for item in _target_slot["not_dict"][_element]:
                            _terms.append(make_term(name=_element,value=item,logic=0))
                else:
                    if _target_slot["not_dict"][_element]!="":
                        _terms.append(make_term(name=_element,value=_target_slot["not_dict"][_element],logic=0))
            for _element in _target_slot["range_dict"]:
                for item in _target_slot["range_dict"][_element]:
                    if _target_slot["range_dict"][_element][item]!="":
                        _terms.append(make_term(name=_element, value=_target_slot["range_dict"][_element][item], logic=1))
    else:
        for _element in _target_slot["is_dict"]:
            if type(_target_slot["is_dict"][_element]) == set:
                if len(_target_slot["is_dict"][_element]) != 0:
                    for item in _target_slot["is_dict"][_element]:
                        _terms.append(make_term(name=_element, value=item))
            else:
                if _target_slot["is_dict"][_element] != "":
                    _terms.append(make_term(name=_element, value=_target_slot["is_dict"][_element]))

        for _element in _target_slot["not_dict"]:
            if type(_target_slot["not_dict"][_element]) == set:
                if len(_target_slot["not_dict"][_element]) != 0:
                    for item in _target_slot["not_dict"][_element]:
                        _terms.append(make_term(name=_element, value=item, logic=0))
            else:
                if _target_slot["not_dict"][_element] != "":
                    _terms.append(make_term(name=_element, value=_target_slot["not_dict"][_element], logic=0))
        for _element in _target_slot["range_dict"]:
            for item in _target_slot["range_dict"][_element]:
                if _target_slot["range_dict"][_element][item] != "":
                    _terms.append(make_term(name=_element, value=_target_slot["range_dict"][_element][item], logic=1))

    return _terms

def parse_slot(_slot_dict): ####解析slot
    terms = []
    #print(_slot_dict)

    ###对链条进行排序###
    target_chain = ""
    flag_total_len = 0
    flag_completed_per = 0
    for chain in _slot_dict["chains"]:
        if _slot_dict["chains"][chain]["rank"]["completed_per"]>flag_completed_per:
            flag_total_len = _slot_dict["chains"][chain]["rank"]["len"]
            flag_completed_per = _slot_dict["chains"][chain]["rank"]["completed_per"]
            target_chain = chain
        elif _slot_dict["chains"][chain]["rank"]["completed_per"]==flag_completed_per:
            if _slot_dict["chains"][chain]["rank"]["len"]>flag_total_len:
                flag_total_len = _slot_dict["chains"][chain]["rank"]["len"]
                flag_completed_per = _slot_dict["chains"][chain]["rank"]["completed_per"]
                target_chain = chain
    print("目标链：：：",target_chain)
    terms = extract_slot_details(terms,_slot_dict["chains"][target_chain])
    return terms

if __name__=="__main__":
    db1 = redis.Redis(host='127.0.0.1', password="123456", port=6379, db=1)
    slot_dict = db1.get("0")
    parse_slot(slot_dict)