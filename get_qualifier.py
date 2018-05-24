# coding: utf-8
__author__ = 'LY'
import requests
import re
import time

########hanshu###########
chs_arabic_map = {'零':0, '一':1, '二':2,'两':2, '三':3, '四':4,
        '五':5, '六':6, '七':7, '八':8, '九':9,
        '十':10, '千':10 ** 3, '万':10 ** 4,
        '〇':0, '壹':1, '贰':2, '叁':3, '肆':4,
        '伍':5, '陆':6, '柒':7, '捌':8, '玖':9,
        '拾':10, '仟':10 ** 3, '萬':10 ** 4,
        '亿':10 ** 8, '億':10 ** 8, '幺': 1,
        '0':0, '1':1, '2':2, '3':3, '4':4,
        '5':5, '6':6, '7':7, '8':8, '9':9}

def convertChineseDigitsToArabic (chinese_digits):
    replace_list = re.findall("[0-9]{1,}[.][0-9]*[万|w|W]",chinese_digits)
    for i in replace_list:
        chinese_digits = chinese_digits.replace(i,str(int(float(i[:-1])*10**4)))

    allstr = ""
    result  = 0
    tmp     = 0
    hnd_mln = 0
    last_is_dig = False  #上个字符是否是数字
    for count in range(len(chinese_digits)):
        curr_char  = chinese_digits[count]
        curr_digit = chs_arabic_map.get(curr_char, None)
        if curr_digit is None:
            if last_is_dig:
                allstr+=str(result + tmp + hnd_mln)
            allstr+=curr_char
            last_is_dig = False
        else:
            if not last_is_dig:
                result = 0
                tmp = 0
                hnd_mln = 0
            # meet 「亿」 or 「億」
            if curr_digit == 10 ** 8:
                result  = result + tmp
                result  = result * curr_digit
                # get result before 「亿」 and store it into hnd_mln
                # reset `result`
                hnd_mln = hnd_mln * 10 ** 8 + result
                result  = 0
                tmp     = 0
            # meet 「万」 or 「萬」
            elif curr_digit == 10 ** 4:
                result = result + tmp
                result = result * curr_digit
                tmp    = 0
            # meet 「十」, 「百」, 「千」 or their traditional version
            elif curr_digit >= 10:
                tmp    = 1 if tmp == 0 else tmp
                result = result + curr_digit * tmp
                tmp    = 0
            # meet single digit
            elif curr_digit is not None:
                tmp = tmp * 10 + curr_digit

            if count == len(chinese_digits)-1:
                allstr += str(result + tmp + hnd_mln)

            last_is_dig = True

    return allstr

##########################
#'缸径(mm)'mm, '高度(mm)'mm, '行程(mm)'mm,'后轮距(mm)'mm,'宽度(mm)'mm, '前轮距(mm)'mm,'实测离地间隙(mm)'mm,'长度(mm)'mm, '轴距(mm)'mm,'最小离地间隙(mm)'mm,
legal_entity = ['价格','百公里耗电量(kWh/100km)', '车门数(个)', '充电桩价格', '纯电续航里程', '挡位个数', '第三排座椅', '电池容量(kWh)', '电池组质保公里', '电池组质保年限', '电动机总功率(kW)', '电动机总扭矩(N·m)', '缸径(mm)', '高度(mm)', '工信部续航里程(km)', '工信部综合油耗(L/100km)', '官方0-100km/h加速(s)', '行程(mm)', '行李厢容积(L)', '后电动机最大功率(kW)', '后电动机最大扭矩(N·m)', '后轮距(mm)', '后轮胎规格', '货箱尺寸(mm)', '快充电量(%)', '快充时间(小时)', '宽度(mm)', '慢充时间(小时)', '每缸气门数(个)', '排量(L)', '排量(mL)', '气缸数(个)', '前电动机最大功率(kW)', '前电动机最大扭矩(N·m)', '前轮距(mm)', '前轮胎规格', '上市时间', '实测0-100km/h加速(s)', '实测100-0km/h制动(m)', '实测快充时间(小时)', '实测离地间隙(mm)', '实测慢充时间(小时)', '实测续航里程(km)', '实测油耗(L/100km)', '系统综合功率(kW)', '系统综合扭矩(N·m)', '压缩比', '扬声器数量', '油箱容积(L)','长度(mm)', '整备质量(kg)', '整车质保公里','整车质保年限', '中控台彩色大屏尺寸', '轴距(mm)', '最大功率(kW)', '最大功率转速(rpm)', '最大马力(Ps)', '最大扭矩(N·m)', '最大扭矩转速(rpm)', '最大载重质量(kg)', '最高车速(km/h)', '最小离地间隙(mm)', '座位数(个)']
ten_percent_range_entities = ['价格']  ######当结果为等于(或者左右之类)的时候，需要上下取百分之10的实体#########
standardalization_entity = ['缸径(mm)','高度(mm)','行程(mm)', '后轮距(mm)', '货箱尺寸(mm)','宽度(mm)','前轮距(mm)','实测离地间隙(mm)','长度(mm)', '轴距(mm)','最小离地间隙(mm)']  ##需要被标准化单位的实体，即把米的数值对应到数据库中的毫米数值

two_after = {'以内':'<', '以里':'<', '以下':'<', '以上':'>', '之上':'>'}
two_before = {'小于':'<', '最多':'<', '低于':'<', '超过':'>', '大于':'>', '至少':'>', '最少':'>', '高于':'>',"<":"<",">":">","=":""}

three_before = {'不超过':'<','不高于':'<','不大于':'<','不小于':'>','不低于':'>','不少于':'>'}
all_fixes = [three_before,two_before,two_after]
middle = ['至', '~', '～', '-', '到','—']
two_other_before = {'不要':2,"不想":2,"排除":2} #,"只要":1,"就要":1,"只想":1,"想要":1
three_other_before = {'不想要':2,"不希望":2,"排除掉":2,"不用于":2,"不喜欢":2,"不要带":2,"不要有":2,"不需要":2}
two_other_after = {'不要':2,"不想":2,"排除":2}

def extract(line):
    url = "http://api.orca.corpautohome.com/cognitive?q={}".format(line)
    data = requests.get(url).json()
    return data["entities"]

def make_term(name="",value="",logic=1):
    return {"name":name,"value":value,"logic":logic}

def check_contain(word,dict_or_list):
    if type(dict_or_list)==list:
        for item in dict_or_list:
            if item in word:
                return ""
        return False
    else:
        for key in dict_or_list.keys():
            if key in word:
                return dict_or_list[key]
        return False

def get_inner_relationship(entity_list):
    terms = []
    for index in range(len(entity_list)-1,-1,-1):
        wan_flag = False
        entity_str = entity_list[index]["entity"].replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').upper()
        if len(re.findall("[万]",entity_str))==1 or len(re.findall("[w]",entity_str))==1 or len(re.findall("[W]",entity_str))==1:
            wan_flag = True
        entity_str = convertChineseDigitsToArabic(entity_str)


        if check_contain(entity_str,middle)!=False:
            _entities = re.findall("[0-9.]+", entity_str)
            if len(_entities)==2:
                _type = entity_list[index]["type"]
                if wan_flag and float(_entities[0])<1000:
                    terms.append(make_term(name=_type,value=">"+str(int(_entities[0])*10**4)))
                else:
                    terms.append(make_term(name=_type, value=">" + _entities[0]))
                if wan_flag and float(_entities[1])<1000:
                    terms.append(make_term(name=_type, value="<" + str(int(_entities[1])*10**4)))
                else:
                    terms.append(make_term(name=_type,value="<"+_entities[1]))
                entity_list.pop(index)
            continue

        for fix in all_fixes:
            _symbol = check_contain(entity_str,fix)
            if _symbol!=False:
                _entities = re.findall("[0-9.]+", entity_str)
                if len(_entities)==1:
                    _type = entity_list[index]["type"]
                    terms.append(make_term(name=_type,value=_symbol+_entities[0]))
                    entity_list.pop(index)
                continue

    return entity_list,terms
def get_external_relationship(sentence,entity_list):
    _continue_flag = False
    list_length = len(entity_list)
    terms = []
    pop_list = []


    if list_length<=1 and list_length!=0:
        _type1 = entity_list[0]["type"]
        start_index = entity_list[0]["startIndex"]
        end_index = entity_list[0]["endIndex"]
        target_section = (sentence[:start_index]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','')
        if len(target_section) >= 3:
            _symbol = check_contain(target_section[-3:], three_before)
            if _symbol != False:
                value_0 = convertChineseDigitsToArabic(entity_list[0]["str"])
                terms.append(make_term(name=_type1, value=value_0))
                entity_list.pop(0)
                return
        if len(target_section) >= 2:
            _symbol = check_contain(target_section[-2:], two_before)
            if _symbol != False:
                value_0 = convertChineseDigitsToArabic(entity_list[0]["str"])
                terms.append(make_term(name=_type1, value=value_0))
                entity_list.pop(0)
                return
        target_section = (sentence[end_index:entity_list[0]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','')
        if len(target_section) >= 2:
            _symbol = check_contain(target_section[:2], two_after)
            if _symbol != False:
                value_0 = convertChineseDigitsToArabic(entity_list[0]["str"])
                terms.append(make_term(name=_type1, value=value_0))
                entity_list.pop(0)


        return entity_list,terms

    else: ###数组不为1或0

        for index in range(list_length-1, -1, -1):

            if _continue_flag:
                entity_list.pop(index)
                _continue_flag = False
                continue

            if index-1>=0: ##如果不是第一个

                _type1 = entity_list[index]["type"]
                end_index = entity_list[index-1]["endIndex"]
                if _type1==entity_list[index-1]["type"]:
                    target_section = (sentence[end_index:entity_list[index]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                    if len(target_section)<=2 and check_contain(target_section,middle):
                        value_0 = convertChineseDigitsToArabic(entity_list[index-1]["str"])
                        value_1 = convertChineseDigitsToArabic(entity_list[index]["str"])
                        terms.append(make_term(name=_type1,value=">"+value_0))
                        terms.append(make_term(name=_type1,value="<"+value_1))
                        pop_list.append(index)
                        _continue_flag = True
                        continue

                if index==list_length-1:#如果是最后一个

                    target_section = (sentence[entity_list[index]["endIndex"]:]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                    if len(target_section)>=2:
                        _symbol = check_contain(target_section[:2],two_after)
                        if _symbol!=False:
                            value_0 = convertChineseDigitsToArabic(entity_list[index]["str"])
                            terms.append(make_term(name=_type1,value=_symbol+value_0))
                            pop_list.append(index)
                            continue

                    target_section = (sentence[end_index:entity_list[index]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                    if len(target_section)>=3:
                        _symbol = check_contain(target_section[-3:],three_before)
                        if _symbol!=False:
                            value_0 = convertChineseDigitsToArabic(entity_list[index]["str"])
                            terms.append(make_term(name=_type1,value=_symbol+value_0))
                            pop_list.append(index)
                            continue

                    if len(target_section)>=2:
                        _symbol = check_contain(target_section[-2:],two_before)
                        if _symbol!=False:
                            value_0 = convertChineseDigitsToArabic(entity_list[index]["str"])
                            terms.append(make_term(name=_type1,value=_symbol+value_0))
                            pop_list.append(index)
                            continue

                else:####非最后一个

                    end_index =entity_list[index]["endIndex"]
                    target_section = (sentence[end_index:entity_list[index+1]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                    if len(target_section)>=2:
                        _symbol = check_contain(target_section[:2],two_after)
                        if _symbol!=False:
                            value_0 = convertChineseDigitsToArabic(entity_list[index]["str"])
                            terms.append(make_term(name=_type1,value=_symbol+value_0))
                            pop_list.append(index)
                            continue

                    target_section = (sentence[entity_list[index-1]["endIndex"]:entity_list[index]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                    if len(target_section)>=3:
                        _symbol = check_contain(target_section[-3:],three_before)
                        if _symbol!=False:
                            value_0 = convertChineseDigitsToArabic(entity_list[index]["str"])
                            terms.append(make_term(name=_type1,value=_symbol+value_0))
                            pop_list.append(index)
                            continue

                    if len(target_section)>=2:
                        _symbol = check_contain(target_section[-2:],two_before)
                        if _symbol!=False:
                            value_0 = convertChineseDigitsToArabic(entity_list[index]["str"])
                            terms.append(make_term(name=_type1,value=_symbol+value_0))
                            pop_list.append(index)
                            continue

            else: #是第一个

                _type1 = entity_list[index]["type"]
                start_index = entity_list[index]["startIndex"]
                end_index = entity_list[index]["endIndex"]
                target_section = (sentence[:start_index]).replace('\n', '').replace('\r', '').replace('\t','').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                if len(target_section) >= 3:
                    _symbol = check_contain(target_section[-3:], three_before)
                    if _symbol != False:
                        value_0 = convertChineseDigitsToArabic(entity_list[index]["str"])
                        terms.append(make_term(name=_type1, value=_symbol+value_0))
                        pop_list.append(index)
                        continue
                if len(target_section)>=2:
                    _symbol = check_contain(target_section[-2:], two_before)
                    if _symbol != False:
                        value_0 = convertChineseDigitsToArabic(entity_list[index]["str"])
                        terms.append(make_term(name=_type1, value=_symbol+value_0))
                        pop_list.append(index)
                        continue

                target_section = (sentence[end_index:entity_list[index+1]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                if len(target_section)>=2:
                    _symbol = check_contain(target_section[:2], two_after)
                    if _symbol != False:
                        value_0 = convertChineseDigitsToArabic(entity_list[index]["str"])
                        terms.append(make_term(name=_type1, value=_symbol+value_0))
                        pop_list.append(index)
                        continue

    for index in range(list_length - 1, -1, -1):
        if index in pop_list:
            entity_list.pop(index)
    return entity_list,terms

def get_other_external_relationship(sentence,entity_list):
    _continue_flag = False
    list_length = len(entity_list)
    terms = []
    pop_list = []

    if list_length<=1 and list_length!=0:
        _type1 = entity_list[0]["type"]
        start_index = entity_list[0]["startIndex"]
        end_index = entity_list[0]["endIndex"]
        target_section = (sentence[:start_index]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','')

        if len(target_section) >= 3:
            _symbol = check_contain(target_section[-3:], three_other_before)
            if _symbol != False:
                terms.append(make_term(name=_type1, value=entity_list[0]["entity"],logic=0))
                return terms
        if len(target_section) >= 2:
            _symbol = check_contain(target_section[-2:], two_other_before)
            if _symbol != False:
                terms.append(make_term(name=_type1, value=entity_list[0]["entity"],logic=0))
                return terms

        target_section = (sentence[end_index:entity_list[0]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','')
        if len(target_section) >= 2:
            _symbol = check_contain(target_section[:2], two_other_after)
            if _symbol != False:
                terms.append(make_term(name=_type1, value=entity_list[0]["entity"],logic=0))
                return terms

        terms.append(make_term(name=_type1, value=entity_list[0]["entity"], logic=1))
        return terms

    else: ###数组不为1或0

        for index in range(list_length-1, -1, -1):

            if _continue_flag:
                entity_list.pop(index)
                _continue_flag = False
                continue

            if index-1>=0: ##如果不是第一个
                _type1 = entity_list[index]["type"]
                end_index = entity_list[index-1]["endIndex"]
                # if _type1==entity_list[index-1]["type"]:
                #     target_section = (sentence[end_index:entity_list[index]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                #     if len(target_section)<=2 and check_contain(target_section,middle):
                #         value_0 = convertChineseDigitsToArabic(entity_list[index-1]["str"])
                #         value_1 = convertChineseDigitsToArabic(entity_list[index]["str"])
                #         terms.append(make_term(name=_type1,value=">"+value_0))
                #         terms.append(make_term(name=_type1,value="<"+value_1))
                #         pop_list.append(index)
                #         _continue_flag = True
                #         continue

                if index==list_length-1:#如果是最后一个

                    target_section = (sentence[entity_list[index]["endIndex"]:]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                    if len(target_section)>=2:
                        _symbol = check_contain(target_section[:2],two_other_after)
                        if _symbol != False:
                            terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=0))
                            continue

                    target_section = (sentence[end_index:entity_list[index]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                    if len(target_section)>=3:
                        _symbol = check_contain(target_section[-3:],three_other_before)
                        if _symbol != False:
                            terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=0))
                            continue

                    if len(target_section)>=2:
                        _symbol = check_contain(target_section[-2:],two_other_before)
                        if _symbol != False:
                            terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=0))
                            continue
                    terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=1))

                    continue

                else:####非最后一个

                    end_index =entity_list[index]["endIndex"]
                    target_section = (sentence[end_index:entity_list[index+1]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                    if len(target_section)>=2:
                        _symbol = check_contain(target_section[:2],two_other_after)
                        if _symbol!=False:
                            terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=0))
                            continue

                    target_section = (sentence[entity_list[index-1]["endIndex"]:entity_list[index]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                    if len(target_section)>=3:
                        _symbol = check_contain(target_section[-3:],three_other_before)
                        if _symbol!=False:
                            value_0 = convertChineseDigitsToArabic(entity_list[index]["str"])
                            terms.append(make_term(name=_type1,value=_symbol+value_0))
                            pop_list.append(index)
                            continue

                    if len(target_section)>=2:
                        _symbol = check_contain(target_section[-2:],two_other_before)
                        if _symbol!=False:
                            terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=0))
                            continue
                    terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=1))
                    print("gggggg", terms)

                    continue

            else: #是第一个

                _type1 = entity_list[index]["type"]
                start_index = entity_list[index]["startIndex"]
                end_index = entity_list[index]["endIndex"]
                target_section = (sentence[:start_index]).replace('\n', '').replace('\r', '').replace('\t','').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                if len(target_section) >= 3:
                    _symbol = check_contain(target_section[-3:], three_other_before)
                    if _symbol != False:
                        terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=0))

                        continue
                if len(target_section)>=2:
                    _symbol = check_contain(target_section[-2:], two_other_before)
                    if _symbol != False:
                        terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=0))
                        continue

                target_section = (sentence[end_index:entity_list[index+1]["startIndex"]]).replace('\n', '').replace('\r', '').replace('\t', '').replace(' ', '').replace('万','').replace('W','').replace('w','').upper()
                if len(target_section)>=2:
                    _symbol = check_contain(target_section[:2], two_other_after)
                    if _symbol != False:
                        terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=0))
                        continue
                terms.append(make_term(name=_type1, value=entity_list[index]["entity"], logic=1))
                continue

    # for index in range(list_length - 1, -1, -1):
    #     if index in pop_list:
    #         entity_list.pop(index)

    return terms

def get_qualifier(sentence):   #######主函数#########
    '''

    :param entity_list: 未处理的term
    :return: 处理剩下的实体list和已经处理成功的terms
    '''
    #####filter######
    #return [{'value': '油耗低', 'name': '排量描述', 'logic': 1}, {'value': '宝马3系', 'name': '车系1', 'logic': 1}, {'value': '>720000', 'name': '价格', 'logic': 1}, {'value': '<880000', 'name': '价格', 'logic': 1}]
    haha = time.time()
    orca_result = requests.get("http://api.orca.corpautohome.com/cognitive?q={}".format(sentence)).json()
    print("orca原结果",orca_result)
    entity_list = orca_result["entities"]
    the_intent = orca_result["topScoringIntent"]["intent"]
    # entity_list = {'query': '我要一个不要排量好的50万-100万,80万左右,30万以内，最多20万,轴距5m以内排量2.0t以内第三排座位', 'intents': [{'intent': 'None', 'score': 0.00017077346274163574}, {'intent': '保值率', 'score': 1.1366290547654145e-10}, {'intent': '保 养', 'score': 2.2508478636495965e-08}, {'intent': '口碑', 'score': 2.0310471882112324e-06}, {'intent': '品牌百科', 'score': 2.327756298825534e-08}, {'intent': '待定', 'score': 3.578276563942495e-10}, {'intent': '搜索', 'score': 0.0009961813921108842}, {'intent': '新闻', 'score': 6.68408395299025e-09}, {'intent': '经销商', 'score': 8.731705491982211e-08}, {'intent': '论坛', 'score': 1.1347928108307315e-07}, {'intent': '询价', 'score': 4.783480108017102e-06}, {'intent': '车型对比', 'score': 0.0014305261429399252}, {'intent': '车系图片', 'score': 8.182605704121215e-10}, {'intent': '选车', 'score': 0.9973706007003784}, {'intent': '配置', 'score': 2.4541512175346725e-05}, {'intent': '配置百科', 'score': 1.8894237996391894e-07}, {'intent': '重新选车', 'score': 2.3609342036934322e-08}, {'intent': '金融', 'score': 1.272395593332476e-07}], 'entities': [{'endIndex': 7, 'score': 1.0, 'type': '车身参数', 'startIndex': 6, 'str': '排量', 'entity': '排量(L)'}, {'endIndex': 17, 'score': 1.0, 'type': '价格', 'startIndex': 10, 'str': '50万-100万', 'entity': '50万-100万'}, {'endIndex': 23, 'score': 1.0, 'type': '价格', 'startIndex': 19, 'str': '80万左右', 'entity': '80万左右'}, {'endIndex': 29, 'score': 1.0, 'type': '价格', 'startIndex': 25, 'str': '30万以内', 'entity': '30万以内'}, {'endIndex': 35, 'score': 1.0, 'type': '价格', 'startIndex': 31, 'str': '最多20万', 'entity': '最多20万'}, {'endIndex': 42, 'score': 1.0, 'type': '轴距(mm)', 'startIndex': 37, 'str': '轴距5M以内', 'entity': '轴距5m以内'}, {'endIndex': 50, 'score': 1.0, 'type': '排量(L)', 'startIndex': 43, 'str': '排量2.0T以内', 'entity': '排量2.0t以内'}], 'message': '成功', 'topScoringIntent': {'intent': '选 车', 'score': 0.9973706007003784}, 'code': 0}
    # entity_list = entity_list["entities"]
    remember_dict = {}
    for item in entity_list:
        if item["type"] in remember_dict.keys():
            remember_dict[item["type"]]+=1
            item["type"] = item["type"]+"_"+str(remember_dict[item["type"]])
        else:
            remember_dict[item["type"]]=0

    dd = time.time()-haha
    print("orca接口时间：：：：：",dd)
    for entity in entity_list:
        if entity["type"] in standardalization_entity:
            values = re.findall("[0-9.]+",entity["entity"])
            for value in values:
                if float(value)<50:     ##汽车轴距不可能超过50000毫米，也就是50米
                    entity["entity"] = entity["entity"].replace(value,str(int(float(value)*10**3)))
    legal_entities = []
    for i in range(len(entity_list)-1,-1,-1):
        if entity_list[i]["type"].split("_")[0] in legal_entity:

            legal_entities.append(entity_list[i])
            entity_list.pop(i)
    entity_list = get_other_external_relationship(sentence,entity_list)
    # entity_list.append({'name': '车系1', 'logic': 1, 'value': '宝马3系'})
    #################
    terms = []

    rest_entity_list,terms1 = get_inner_relationship(legal_entities)
    rest_entity_list,terms2 = get_external_relationship(sentence,rest_entity_list)
    for i in range(len(rest_entity_list)-1,-1,-1):
        entity_str = rest_entity_list[i]["entity"].replace('\n', '').replace('\r', '').replace('\t', '').replace(' ','').upper()
        entity_str = convertChineseDigitsToArabic(entity_str)
        _entities = re.findall("[0-9.]+", entity_str)
        if len(_entities) == 1:
            _type = rest_entity_list[i]["type"]
            _type_str_flag = _type.split("_")[0]
            if _type_str_flag in ten_percent_range_entities:
                terms.append(make_term(name=_type, value=">"+str(int(int(_entities[0])*0.9))))
                terms.append(make_term(name=_type, value="<"+str(int(int(_entities[0])*1.1))))
            else:
                terms.append(make_term(name=_type, value=_entities[0]))
            rest_entity_list.pop(i)
    terms+=terms1
    ###返回处理剩下的实体list和已经处理成功的term
    full_list = entity_list+rest_entity_list+terms+terms2
    ##########整理一下list###############

    print("取实体关系时间：：：：：",time.time()-dd-haha)

    return full_list,the_intent


if __name__ == '__main__':

    test_sents = "我要一个不要排量好的50万-100万,80万左右,30万以内，最多20万"
    #,轴距5m以内排量2.0t以内第三排座位
    #test_sents = "我要一个油耗"
    # test_sents = [
    #     {"name": "快充时间(小时)", "value": "<2小时", "logic": 1},
    #     {"name": "整车质保公里","value": "20~30","logic": 1},
    #     {"name":"官方0-100km/h加速(s)","value":"百公里加速6~8秒","logic":1},
    #     {"name": "官方0-100km/h加速(s)", "value": "百公里加速最多6秒", "logic": 1},
    #     {"name": "车门数(个)", "value": "两门", "logic": 1}
    #
    # ]
    #test_sents = {'query': '给我来一个车门数少于5个的车', 'intents': [{'score': 0.011849227361381054, 'intent': 'None'}, {'score': 2.723278385019512e-07, 'intent': '保值率'}, {'score': 1.3072253750578966e-05, 'intent': '保养'}, {'score': 0.0020225225016474724, 'intent': '口碑'}, {'score': 5.655079075950198e-05, 'intent': '品牌百科'}, {'score': 1.3517504839910544e-06, 'intent': '待定'}, {'score': 0.15814904868602753, 'intent': '搜索'}, {'score': 5.244945441518212e-06, 'intent': '新闻'}, {'score': 0.00010697939433157444, 'intent': '经销商'}, {'score': 1.610483741387725e-05, 'intent': '论坛'}, {'score': 0.00010591611498966813, 'intent': '询价'}, {'score': 0.0007017640164121985, 'intent': '车型对比'}, {'score': 4.1174743614647014e-07, 'intent': '车系图片'}, {'score': 0.8258548378944397, 'intent': '选车'}, {'score': 0.0009416777174919844, 'intent': '配置'}, {'score': 0.0001618348906049505, 'intent': '配置百科'}, {'score': 3.5159141589247156e-06, 'intent': '重新选车'}, {'score': 9.690823389973957e-06, 'intent': '金融'}], 'message': '成功', 'topScoringIntent': {'score': 0.8258548378944397, 'intent': '选车'}, 'code': 0, 'entities': [{'endIndex': 6, 'entity': '一个车门', 'score': 1.0, 'type': '车门数(个)', 'str': '一个车门', 'startIndex': 3}]}

#{'entity': '缸径小于600', 'type': '缸径(mm)', 'startIndex': 0, 'endIndex': 6, 'score': 1.0, 'str': '缸径小于600'}
        #results = extract(sentence)
    aa = time.time()
    terms = get_qualifier(test_sents)
    print("原term剩余::::",test_sents)
    print("解析出的结果::",terms)
    print("耗时",time.time() - aa)

#, {"name": "排量(L)", "value": "2.0", "logic": 1},
#{"name": "气缸数(个)", "value": "气缸数(个)6缸", "logic": 1},
#{"name": "轴距(mm)", "value": "4到5", "logic": 1},
#{"name": "价格", "value": "100~200万", "logic": 1}, {"name": "缸径(mm)", "value": "缸径不小于600", "logic": 1}



