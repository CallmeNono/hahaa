# coding: utf-8

import re
import copy
import redis
'''
input: orca结果需要是一个list 例如[{"车系":"宝马3系"},{"车系":"奔驰C级"}]
定义逻辑and和逻辑or
逻辑and即链条的并列项，每个并列项需要被独立地检验是否存在
定义存在检验机制（三种类型的cell(小集合，每个集合下可以多个实体)，一种是布尔型（可以是一个函数，一个判断），一种是range型（{"价格":{"=":"","<":"",">":""}}），一种是枚举型）
还需要定义最内层的数据结构，range型默认是等于小于大于，而其他的可以选择str（冲突式）或者list（叠加） {"价格":{"=":"","<":"",">":""}和{"国别":[]}和{have_怎么样:""}平行
chain实际上也是一个dict，里面包含is_dict,not_dict和range_dict
成链条件(precondition)-成槽条件(percentage 即rank字段中的比例)-完成填槽条件（对自判断集合设定且逻辑，是为了表达要吗1要吗0的概念，而不是可1可2可0）
is_dict和not_dict代表一个总dict，里面的元素只要存在于一个dict中即可成槽
自判断和is_dict not_dict range_dict一定程度上是分开的，暂时不设定index

condition_dict库：

###################函数和模块库##############################
def make_warehouse 承接来自前端的格式化数据，解析成划分子意图用的树存储形式，最终是链库的形式，顺带把precondition的条件也补充进去
def make_index 对上面产生的链库创造索引
def get_qulifier 将给定的orca实体结果转换成所需的term模式，并且解析出修饰词
def fill_slot 对于入参(intent,orca_result,origin_sentence)进行填槽
def fill_local_dict(name,value,logic,slot_dict) 具体的填槽行为
def fill_condition(line,origin_sentence) 对于条件项进行填槽
def parse_slot 解析slot 匹配正确的小意图和组织正确的查询语句


###################函数和模块库##############################


warehouse图数据结构：：：：
逻辑判断分调用接口和存不存在某个词两种
index是索引
chains是各个链条，包括slot
self_judgement是各个链条下函数判断的索引，数据格式为key:chian名字,value:各个条件(list)
rank，key是各个chain的名字，value是一个dict，dict的第一个key是是否合法，第二个key是总长度，第三个key是完成度，第四个key是完成比
precondition是每个链条成链的前提条件key是chain名，value是一个list，是条件集合，基本逻辑为and逻辑，即有一个不符合就把rank中的dict的第一个key改为不合法

注意：chain名字（例如chain1）之下的key不一定就直接是实体key（国别等），还有可能是集合，所以要加判断，就像


执行次序为：
0，先初始化warehouse
1，根据进来的意图选择warehouse的某一个大意图类
2，根据原句和实体list执行precondition中的条件
3，根据普通索引填槽
4，根据函数判断索引和rank的第一个True or False填槽

模块应该分三步走：

信息表述方法：
意图-》通过链条数量确定chains下的空dict（chain1等）-》通过chains数量定义rank的dict-》读取每个chains中的数据结构，翻译为每个具体的chain  顺便补充precondition链-》制作index字段
self_judgement里的元素全部变成布尔类型判断，其他的分别有list和str
槽位类型有：is_dict,not_dict,self_judgement,range_dict,and_set,or_set,]
'''
all_canshu = [("结构","logic","list"),("用途选车","logic","list"),("城市","logic","list"),("国别","logic","list"),("品牌","logic","list"),("口碑参数","logic","list"),("论坛用词","logic","list"),("资讯关键词","logic","list"),("动作指令","logic","list"),("保养项目","logic","list"),("保养次数","logic","list"),("问时间","logic","list"),("问价格","logic","list"),("生产厂商","logic","list"),("指定拆词","logic","list"),("外观描述","logic","list"),("动力描述","logic","list"),("配置描述","logic","list"),("价格描述","logic","list"),("排量描述","logic","list"),("车身配置","logic","list"),("车身参数","logic","list"),("驱动电机数","logic","list"),("发动机型号","logic","list"),("进气形式","logic","list"),("配气机构","logic","list"),("发动机特有技术","logic","list"),("供油方式","logic","list"),("变速箱类型","logic","list"),("驱动方式","logic","list"),("助力类型","logic","list"),("车体结构","logic","list"),("驻车制动类型","logic","list"),("备胎规格","logic","list"),("四驱形式","logic","list"),("中央差速器结构","logic","list"),("电池类型","logic","list"),("后排车门开启方式","logic","list"),("电机布局","logic","list"),("变速箱和简称","logic","list"),("变速箱","logic","list"),("简称","logic","list"),("能源类型","logic","list"),("缸盖材料和缸体材料","logic","list"),("缸盖材料","logic","list"),("缸体材料","logic","list"),("前悬架类型和后悬架类型","logic","list"),("前悬架类型","logic","list"),("后悬架类型","logic","list"),("前制动器类型和后制动器类型","logic","list"),("前制动器类型","logic","list"),("后制动器类型","logic","list"),("级别","logic","list"),("版型","logic","list"),("颜色","logic","list"),("环保标准","logic","list"),("厂商","logic","list"),("询价用词","logic","list"),("热门","logic","list"),("省","logic","list"),("侧滑门","logic","list"),("车窗一键升降","logic","list"),("多天窗","logic","list"),("方向盘调节","logic","list"),("后排座椅放倒方式","logic","list"),("近光灯","logic","list"),("近光灯和远光灯","logic","list"),("可变悬架","logic","list"),("外接音源接口","logic","list"),("扬声器品牌","logic","list"),("远光灯","logic","list"),("座椅材质","logic","list"),("颜色类型","logic","list"),("CD/DVD","logic","list"),("可加热/制冷杯架","logic","list"),("前桥限滑差速器/差速锁和后桥限滑差速器/差速锁","logic","list"),("前桥限滑差速器/差速锁","logic","list"),("后桥限滑差速器/差速锁","logic","list"),("加速度描述","logic","list"),("发动机","logic","list"),("问公里","logic","list")]
all_nums = [("价格","range"),("百公里耗电量(kWh/100km)","range"),("车门数(个)","range"),("充电桩价格","range"),("纯电续航里程","range"),("挡位个数","range"),("第三排座椅","range"),("电池容量(kWh)","range"),("电池组质保公里","range"),("电池组质保年限","range"),("电动机总功率(kW)","range"),("电动机总扭矩(N·m)","range"),("缸径(mm)","range"),("高度(mm)","range"),("工信部续航里程(km)","range"),("工信部综合油耗(L/100km)","range"),("官方0-100km/h加速(s)","range"),("行程(mm)","range"),("行李厢容积(L)","range"),("后电动机最大功率(kW)","range"),("后电动机最大扭矩(N·m)","range"),("后轮距(mm)","range"),("后轮胎规格","range"),("货箱尺寸(mm)","range"),("快充电量(%)","range"),("快充时间(小时)","range"),("宽度(mm)","range"),("慢充时间(小时)","range"),("每缸气门数(个)","range"),("排量(L)","range"),("排量(mL)","range"),("气缸数(个)","range"),("前电动机最大功率(kW)","range"),("前电动机最大扭矩(N·m)","range"),("前轮距(mm)","range"),("前轮胎规格","range"),("上市时间","range"),("实测0-100km/h加速(s)","range"),("实测100-0km/h制动(m)","range"),("实测快充时间(小时)","range"),("实测离地间隙(mm)","range"),("实测慢充时间(小时)","range"),("实测续航里程(km)","range"),("实测油耗(L/100km)","range"),("系统综合功率(kW)","range"),("系统综合扭矩(N·m)","range"),("压缩比","range"),("扬声器数量","range"),("油箱容积(L)","range"),("长度(mm)","range"),("整备质量(kg)","range"),("整车质保公里","range"),("整车质保年限","range"),("中控台彩色大屏尺寸","range"),("轴距(mm)","range"),("最大功率(kW)","range"),("最大功率转速(rpm)","range"),("最大马力(Ps)","range"),("最大扭矩(N·m)","range"),("最大扭矩转速(rpm)","range"),("最大载重质量(kg)","range"),("最高车速(km/h)","range"),("最小离地间隙(mm)","range"),("座位数(个)","range")]
all_canshu_nums = [("油耗描述","logic","list"),("结构","logic","list"),("用途选车","logic","list"),("城市","logic","list"),("国别","logic","list"),("品牌","logic","list"),("口碑参数","logic","list"),("论坛用词","logic","list"),("资讯关键词","logic","list"),("动作指令","logic","list"),("保养项目","logic","list"),("保养次数","logic","list"),("问时间","logic","list"),("问价格","logic","list"),("生产厂商","logic","list"),("指定拆词","logic","list"),("外观描述","logic","list"),("动力描述","logic","list"),("配置描述","logic","list"),("价格描述","logic","list"),("排量描述","logic","list"),("车身配置","logic","list"),("车身参数","logic","list"),("驱动电机数","logic","list"),("发动机型号","logic","list"),("进气形式","logic","list"),("配气机构","logic","list"),("发动机特有技术","logic","list"),("供油方式","logic","list"),("变速箱类型","logic","list"),("驱动方式","logic","list"),("助力类型","logic","list"),("车体结构","logic","list"),("驻车制动类型","logic","list"),("备胎规格","logic","list"),("四驱形式","logic","list"),("中央差速器结构","logic","list"),("电池类型","logic","list"),("后排车门开启方式","logic","list"),("电机布局","logic","list"),("变速箱和简称","logic","list"),("变速箱","logic","list"),("简称","logic","list"),("能源类型","logic","list"),("缸盖材料和缸体材料","logic","list"),("缸盖材料","logic","list"),("缸体材料","logic","list"),("前悬架类型和后悬架类型","logic","list"),("前悬架类型","logic","list"),("后悬架类型","logic","list"),("前制动器类型和后制动器类型","logic","list"),("前制动器类型","logic","list"),("后制动器类型","logic","list"),("级别","logic","list"),("版型","logic","list"),("颜色","logic","list"),("环保标准","logic","list"),("厂商","logic","list"),("询价用词","logic","list"),("热门","logic","list"),("省","logic","list"),("侧滑门","logic","list"),("车窗一键升降","logic","list"),("多天窗","logic","list"),("方向盘调节","logic","list"),("后排座椅放倒方式","logic","list"),("近光灯","logic","list"),("近光灯和远光灯","logic","list"),("可变悬架","logic","list"),("外接音源接口","logic","list"),("扬声器品牌","logic","list"),("远光灯","logic","list"),("座椅材质","logic","list"),("颜色类型","logic","list"),("CD/DVD","logic","list"),("可加热/制冷杯架","logic","list"),("前桥限滑差速器/差速锁和后桥限滑差速器/差速锁","logic","list"),("前桥限滑差速器/差速锁","logic","list"),("后桥限滑差速器/差速锁","logic","list"),("加速度描述","logic","list"),("发动机","logic","list"),("问公里","logic","list"),("价格","range"),("百公里耗电量(kWh/100km)","range"),("车门数(个)","range"),("充电桩价格","range"),("纯电续航里程","range"),("挡位个数","range"),("第三排座椅","range"),("电池容量(kWh)","range"),("电池组质保公里","range"),("电池组质保年限","range"),("电动机总功率(kW)","range"),("电动机总扭矩(N·m)","range"),("缸径(mm)","range"),("高度(mm)","range"),("工信部续航里程(km)","range"),("工信部综合油耗(L/100km)","range"),("官方0-100km/h加速(s)","range"),("行程(mm)","range"),("行李厢容积(L)","range"),("后电动机最大功率(kW)","range"),("后电动机最大扭矩(N·m)","range"),("后轮距(mm)","range"),("后轮胎规格","range"),("货箱尺寸(mm)","range"),("快充电量(%)","range"),("快充时间(小时)","range"),("宽度(mm)","range"),("慢充时间(小时)","range"),("每缸气门数(个)","range"),("排量(L)","range"),("排量(mL)","range"),("气缸数(个)","range"),("前电动机最大功率(kW)","range"),("前电动机最大扭矩(N·m)","range"),("前轮距(mm)","range"),("前轮胎规格","range"),("上市时间","range"),("实测0-100km/h加速(s)","range"),("实测100-0km/h制动(m)","range"),("实测快充时间(小时)","range"),("实测离地间隙(mm)","range"),("实测慢充时间(小时)","range"),("实测续航里程(km)","range"),("实测油耗(L/100km)","range"),("系统综合功率(kW)","range"),("系统综合扭矩(N·m)","range"),("压缩比","range"),("扬声器数量","range"),("油箱容积(L)","range"),("长度(mm)","range"),("整备质量(kg)","range"),("整车质保公里","range"),("整车质保年限","range"),("中控台彩色大屏尺寸","range"),("轴距(mm)","range"),("最大功率(kW)","range"),("最大功率转速(rpm)","range"),("最大马力(Ps)","range"),("最大扭矩(N·m)","range"),("最大扭矩转速(rpm)","range"),("最大载重质量(kg)","range"),("最高车速(km/h)","range"),("最小离地间隙(mm)","range"),("座位数(个)","range")]
# a = {"选车":[{"chain1":[("have_是不是","precondition",""),("set_1","or",[("国别","logic","list"),("价格","range",""),("配置参数","logic","list")]),("have_有没有","judgement","")]},{"chain2":[("车系","plain","str"),("have_有没有","judgement","")]}],"配置":[{"chain0":[("车系","plain","str"),("车身配置","plain","str")]}]}
# ind = 0
a = {"选车":[{"chain0":[("条件选车","chain_name"),("set_1","or",all_canshu_nums)]},
           {"chain1":[("车系选车","chain_name"),("车系","logic","list")]},
           {"chain2":[("价格选车","chain_name"),("价格","range"),("价格_1","range")]}],
     "配置":[{"chain0":[("问配置","chain_name"),("车系","plain","str"),("车身配置","plain","str")]}],
     "保养":[{"chain0":[("保养通用","chain_name"),("车系","plain","str")]},
           {"chain1":[("保养项目","chain_name"),("车系","plain","str"),("保养次数","plain","str")]},
           {"chain2":[("保养费用","chain_name"),("车系","plain","str"),("保养次数","plain","str"),("set_1","or",[("have_钱","judgement"),("have_多","judgement")])]},
           {"chain3":[("保养咨询","chain_name"),("车系","plain","str"),("set_1","or",[("have_哪种","judgement"),("have_好","judgement")])]},
           {"chain4":[("保养费用","chain_name"),("问价格","plain","str")]},
           {"chain5":[("保养费用","chain_name"),("车系","plain","str"),("set_1","or",[("问价格","plain","str"),("have_保养费","judgement"),("have_费用","judgement"),("have_费用","judgement"),("have_贵","judgement"),("have_成本","judgement"),("have_花费","judgement")])]},
           {"chain6":[("保养通用","chain_name"),("set_1","and",[("have_保养","judgement"),("nothaveE_车系","judgement"),("nothaveE_品牌","judgement"),("nothaveE_问价格","judgement"),("nothaveE_问时间","judgement"),("nothaveE_问公里","judgement"),("nothaveE_保养次数","judgement"),("nothaveE_问价格","judgement"),("nothaveE_公里数","judgement")])]},
           {"chain7":[("保养项目","chain_name"),("车系","plain","str"),("保养项目","plain","str"),("问公里","plain","str")]},
           {"chain8": [("保养项目", "chain_name"), ("车系", "plain", "str"), ("保养项目", "plain", "str")]},
           {"chain9":[("保养费用","chain_name"),("have_保养","judgement"),("have_价","judgement")]},
           {"chain10":[("保养周期","chain_name"),("问时间","plain","str"),("set_1","or",[("have_次","judgement"),("保养次数","plain","str")])]},
           {"chain11":[("保养费用","chain_name"),("车系","plain","str"),("have_保养","judgement"),("have_钱","judgement")]},
           {"chain12":[("保养项目","chain_name"),("车系","plain","str"),("公里数","plain","str")]},
           {"chain13":[("保养费用","chain_name"),("车系","plain","str"),("公里数","plain","str"),("问价格","plain","str")]},
           {"chain14": [("保养费用", "chain_name"), ("品牌", "plain", "str"), ("set_1", "or", [("have_贵","judgement"),("问价格", "plain", "str"), ("have_保养费", "judgement"),("have_费用", "judgement"),("have_费用", "judgement"),("have_成本","judgement"),("have_花费","judgement")])]},
           {"chain15":[("保养咨询","chain_name"),("set_1","and",[("nothaveE_车系","judgement"),("nothaveE_品牌","judgement"),("nothaveE_问价格","judgement"),("nothaveE_问时间","judgement"),("nothaveE_问公里","judgement"),("nothaveE_保养次数","judgement"),("nothaveE_问价格","judgement"),("nothaveE_公里数","judgement")]),
                       ("set_2", "and", [("nothave_贵", "judgement"), ("nothave_保养费", "judgement"),("nothave_费用", "judgement"), ("nothave_费用", "judgement"), ("nothave_成本", "judgement"),("nothave_花费", "judgement"),("nothave_怎么处理","judgement"),("nothave_怎样处理","judgement"),("nothave_价位","judgement")])]},
           {"chain16": [("保养项目", "chain_name"), ("车系", "plain", "str"), ("公里数", "plain", "str"),("set_1","or",[("have_项目","judgement"),("have_保养","judgement"),("have_哪些","judgement")]),("nothaveE_问价格","judgement")]},
           {"chain17": [("保养费用", "chain_name"), ("set_1","or",[("问价格", "plain", "str"),("have_费用","judgement"),("have_钱","judgement")]),("车系","plain","str"),("保养项目","plain","str")]},
           {"chain18":[("保养周期","chain_name"),("问时间","plain","str"),("保养项目","plain","str"),("车系","plain","str")]},
           {"chain19":[("保养周期","chain_name"),("问时间","plain","str"),("车系","plain","str")]},
           {"chain20":[("保养周期","chain_name"),("问时间","plain","str"),("保养次数","plain","str"),("车系","plain","str")]},
           {"chain21":[("保养项目","chain_name"),("车系","plain","str"),("set_1","or",[("have_更换","judgement"),("have_哪些","judgement")])]},
           {"chain22":[("保养项目","chain_name"),("车系","plain","str"),("set_1","and",[("have_保养","judgement"),("have_什么","judgement"),("nothaveE_问时间","judgement")])]},
           {"chain23":[("保养费用","chain_name"),("车系","plain","str"),("问价格","plain","str"),("have_保养","judgement"),("have_公里","judgement"),("set_1","or",[("have_几","judgement"),("have_多少","judgement")])]},
           {"chain24":[("保养通用","chain_name"),("保养次数","plain","str"),("问价格","plain","str"),("车系","plain","str"),("问时间","plain","str")]},
           {"chain25":[("保养咨询","chain_name"),("车系","plain","str"),("have_怎样","judgement")]},
           {"chain26":[("维修百科","chain_name"),("set_1","or",[("have_怎么处理","judgement"),("have_怎样处理","judgement")])]},
           {"chain27":[("保养周期","chain_name"),("保养项目","plain","str"),("车系","plain","str"),("set_1","or",[("have_几时","judgement"),("have_何时","judgement"),("have_时候","judgement")])]},
           {"chain28":[("保养周期", "chain_name"), ("车系", "plain", "str"), ("保养次数", "plain", "str"),("set_1", "or", [("have_钱", "judgement"), ("have_多", "judgement")]),("set_2","or",[("have_公里","judgement"),("问公里","plain","str")])]},
           {"chain29":[("保养咨询","chain_name"),("车系","plain","str"),("set_1","or",[("have_免保养","judgement"),("have_免费保养","judgement")])]},
           {"chain30":[("保养周期", "chain_name"), ("have_周期", "judgement"), ("车系", "plain", "str")]},
           {"chain31":[("保养费用", "chain_name"),("set_1", "or", [("问价格", "plain", "str"), ("have_费用", "judgement"), ("have_多少", "judgement")]),("车系", "plain", "str"), ("车身参数", "plain", "str")]},
           {"chain32":[("保养周期", "chain_name"),("set_1", "or", [("have_换", "judgement"), ("have_多少距离", "judgement")]),("问公里", "plain", "str"), ("保养项目", "plain", "str")]},
           {"chain33": [("保养咨询", "chain_name"), ("车系", "plain", "str"), ("have_吗", "judgement"),("have_可以","judgement"),("保养项目","plain","str")]},
           {"chain34": [("保养周期", "chain_name"), ("车系", "plain", "str"),("set_1", "and", [("have_钱", "judgement"), ("have_多", "judgement")]),("set_2", "or", [("have_公里", "judgement"), ("问公里", "plain", "str")])]},
           {"chain35": [("保养项目", "chain_name"), ("车系", "plain", "str"), ("公里数", "plain", "str"),("问价格", "plain", "str"),("保养项目","plain","str")]},
           {"chain36": [("保养咨询", "chain_name"), ("车系", "plain", "str"), ("have_什么", "judgement"),("have_用", "judgement"), ("保养项目", "plain", "str")]},
           {"chain37": [("保养周期", "chain_name"), ("have_月份", "judgement"),("have_用", "judgement"), ("公里数", "plain", "str")]},
           {"chain38": [("保养咨询", "chain_name"), ("车系", "plain", "str"), ("保养项目", "plain", "str"),("have_感觉","judgement"),("have_后","judgement"),("have_换","judgement")]},
           {"chain39": [("保养周期", "chain_name"), ("车系", "plain", "str"), ("公里数", "plain", "str"),("问价格", "plain", "str"), ("保养项目", "plain", "str"),("have_要","judgement"),("have_吗","judgement")]},
           {"chain40": [("保养项目", "chain_name"), ("车系", "plain", "str"),("问时间","plain","str"),("set_1", "or", [("have_更换", "judgement"), ("have_哪些", "judgement")])]},

           ]}


print(a)

def make_index_recur(path,__warehouse,_warehouse):   ####__warehouse是一直改变的正主  _warehouse只是个复制参照品
    length_of_path = len(path)
    if length_of_path > 0:
        get_value = '_warehouse["chains"]["' + path[0] + '"]'
        flag = 1  ##==1
        while flag < length_of_path:
            get_value += '[path[' + str(flag) + ']]'
            flag += 1
        tmp_warehouse = eval(get_value)
        for dict_name in tmp_warehouse:
            for item_key in tmp_warehouse[dict_name]:
                if dict_name == "is_dict":
                    if tmp_warehouse[dict_name][item_key] == "":
                        # print("hahaha",item_key,__warehouse["index"]["str_index"])
                        # print(path)

                        if item_key in __warehouse["index"]["str_index"]:
                            __warehouse["index"]["str_index"][item_key].append(path)  ####item_key是不变的实体名字 [chain]是会变化的
                        else:
                            __warehouse["index"]["str_index"][item_key] = []
                            __warehouse["index"]["str_index"][item_key].append(path)
                    else:
                        if item_key in __warehouse["index"]["list_index"]:
                            __warehouse["index"]["list_index"][item_key].append(path)
                        else:
                            __warehouse["index"]["list_index"][item_key] = []
                            __warehouse["index"]["list_index"][item_key].append(path)
                if dict_name == "range_dict":
                    if item_key in __warehouse["index"]["range_index"]:
                        __warehouse["index"]["range_index"][item_key].append(path)
                    else:
                        __warehouse["index"]["range_index"][item_key]=[]
                        __warehouse["index"]["range_index"][item_key].append(path)

                if dict_name == "self_judgement":
                    if path[0] in __warehouse["index"]["boolean_index"]:
                        tmp_path = copy.deepcopy(path)
                        tmp_path.append(item_key)
                        __warehouse["index"]["boolean_index"][path[0]].append(tmp_path[1:])
                    else:
                        tmp_path = copy.deepcopy(path)
                        tmp_path.append(item_key)
                        # print("aaa",[(path.append(item_key))[1:]])
                        __warehouse["index"]["boolean_index"][path[0]] = []
                        __warehouse["index"]["boolean_index"][path[0]].append(tmp_path[1:])

                if dict_name == "set_dict":
                    for set_dict_name in tmp_warehouse[dict_name]:
                        the_path = copy.deepcopy(path)
                        the_path.append("set_dict")
                        the_path.append(set_dict_name)
                       # print(the_path)
                        make_index_recur(the_path,__warehouse,_warehouse)
                        # for set_dict_name_detail in tmp_warehouse[dict_name][set_dict_name]:
                        #     print(set_dict_name_detail)


        #print(__warehouse["index"])
    return __warehouse

def make_rank(_warehouse):
    the_len = 0
    for dict_name in _warehouse:
        if dict_name=="is_dict":
            the_len+=len(_warehouse[dict_name])
        elif dict_name=="range_dict":
            the_len+=len(_warehouse[dict_name])
        elif dict_name=="self_judgement":
            the_len+=len(_warehouse[dict_name])
        elif dict_name=="set_dict":
            the_len+=len(_warehouse[dict_name])
            for items in _warehouse[dict_name]:
                make_rank(_warehouse[dict_name][items])
    _warehouse["rank"]["len"] = the_len
    _warehouse["rank"]["completed_len"] = 0
    _warehouse["rank"]["completed_per"] = 0
    return


def make_index(_warehouse):
    for intent_warehouse in _warehouse.values():
        for chain in intent_warehouse["chains"]:
            path = [chain]
            tmp_ware = copy.deepcopy(intent_warehouse)
            make_index_recur(path,intent_warehouse,tmp_ware)
            make_rank(intent_warehouse["chains"][chain])
    return _warehouse

def put_elements(_warehouse,element):

    pattern = re.compile("__\d+")
    print(element[0])

    compliered_element_name = re.sub(pattern,"",element[0])
    if element[1]=="logic":
        if element[2] == "list":
            _warehouse["is_dict"][element[0]] = set()
            _warehouse["not_dict"][element[0]] = set()
        elif element[2] == "str":
            _warehouse["is_dict"][element[0]] = ""
            _warehouse["not_dict"][element[0]] = ""
    elif element[1] == "plain":
        if element[2] == "list":
            _warehouse["is_dict"][element[0]] = set()
        elif element[2] == "str":
            _warehouse["is_dict"][element[0]] = ""
    elif element[1]=="range":
        _warehouse["range_dict"][element[0]] = {"=":"","<":"",">":""}
    elif element[1]=="judgement":
        _warehouse["self_judgement"][element[0]] = ""
    elif compliered_element_name.startswith("set"):
        _warehouse["set_dict"][element[0]] = {"is_dict":{},"not_dict":{},"range_dict":{},"self_judgement":{},"rank":{},"set_dict":{},"set_mode":element[1]}
        for _element in element[2]:
            put_elements(_warehouse["set_dict"][element[0]], _element)

def make_warehouse(given_dict):
    warehouse = {}
    for intent in given_dict:
        warehouse[intent] = {"index":{"str_index":{},"list_index":{},"boolean_index":{},"range_index":{}},"chains":{},"precondition":{},"chain_name":""}
        chain_flag = 0
        for chain in given_dict[intent]:
            warehouse[intent]["precondition"][list(chain.keys())[0]] = []
            warehouse[intent]["chains"]["chain"+str(chain_flag)] = {"is_dict":{},"not_dict":{},"range_dict":{},"self_judgement":{},"rank":{},"set_dict":{}}
            for elements in chain.values():
                for element in elements:
                    if element[1]=="precondition":
                        warehouse[intent]["precondition"][list(chain.keys())[0]].append(element[0])
                    elif element[1]=="chain_name":
                        warehouse[intent]["chains"]["chain" + str(chain_flag)]["chain_name"] = element[0]
                    put_elements(warehouse[intent]["chains"]["chain"+str(chain_flag)],element)
                chain_flag+=1
    make_index(warehouse)
    return warehouse
# print(a)


if __name__ == "__main__":
    import time
    shijian = time.time()
    warehouse = make_warehouse(a)
    db0 = redis.Redis(host='127.0.0.1', password="", port=6379, db=0)
    db0.set("warehouse",str(warehouse))
    print("前端到存储数据库时间：：：",time.time()-shijian)
    print("final",warehouse["保养"]["chains"]["chain3"])
    print(warehouse)
