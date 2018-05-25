# -*- coding:utf-8 -*-
__zuozhe__ = "luoyi"

import copy
import re
import redis
import requests

#####先定义了一堆
logic_dict = {}    ###例如"国别":{"日本":"","中国":""}
plain_dict = {}
range_dict = {}


########维护一个映射词典############
#reflaction_dict = {"车系":"is_dict","国别":"is_dict","价格":"range_index","排量":"range_index"}
range_dict_entities = ["价格","排量"]
logic_dict_entities = ["车系","国别"]
boolean_dict_entities = ["have_给我","have_有没有","have_是不是"]
########更新之后由服务端读取##################需要制作一个make warehouse函数#####
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
槽位类型有：is_dict,not_dict,self_judgement,range_dict,and_set,or_set
'''

#warehouse = {"选车":{"index":{},"chains":{"chain1":{"国别":{"日本":"","中国":""},"have_怎么样":""},"chain2":{"国别":{"日本":"","中国":""}}},"self_judgement":{"chain1":["have_怎么样"]},"rank":{"chain1":[]}},"precondition":{"chain1":["have_好不好"]},"配置":{"index":{},"chains":{"chain1":{"国别":{"日本":"","中国":""}}},"rank":{"chain1":[]}}}
# warehouse = {"选车":{"index":{"str_index":{"车系":[["chain1"]],"车系_1":[["chain1"]],"车身颜色":[["chain2","set_dict","set_1"]]},"list_index":{"国别":[["chain1"],["chain2","set_dict","set_1"]]},"range_index":{"价格":[["chain1"],["chain2","set_dict","set_1"]],"动力":[["chain2","set_dict","set_1"]]},"boolean_index":{"chain1":[["have_给我"],["set_dict","set_1","have_有没有"],["set_dict","set_1","have_是不是"]],"chain2":[["set_dict","set_1","have_来一个"]]}},"chains":{"chain1":{"is_dict":{"国别":set(),"车系":"","车系_1":""},"not_dict":{"国别":set(),"车系":""},"range_dict":{"价格":{"=":"",">":"","<":""}},"self_judgement":{"have_给我":""},"set_dict":{"set_1":{"self_judgement":{"have_有没有":"","have_是不是":""},"is_dict":{},"not_dict":{},"range_dict":{},"set_dict":{},"rank":{"len":2,"completed_len":0,"completed_per":0},"set_mode":"and"}},"rank":{"len":6,"completed_len":0,"completed_per":0}},"chain2":{"is_dict":{},"not_dict":{},"range_dict":{},"self_judgement":{},"rank":{"len":1,"completed_len":0,"completed_per":0},"set_dict":{"set_1":{"set_dict":{},"is_dict":{"国别":set(),"车身颜色":""},"not_dict":{"国别":set(),"车身颜色":""},"range_dict":{"动力":{"=":"","<":"",">":""},"价格":{"=":"","<":"",">":""}},"self_judgement":{"have_来一个":""},"rank":{"len":5,"completed_len":0,"completed_per":0},"set_mode":"or"}}}},"precondition":{"chain1":["have_好不好"],"chain2":[]}},"配置":{"index":{"str_index":{},"list_index":{},"range_index":{},"boolean_dict":{}},"chains":{"chain1":{"is_dict":{"车系":"","参数配置":""},"not_dict":{},"range_dict":{},"self_judgement":{},"set_dict":{},"rank":{"len":0,"completed_len":0,"completed_per":0}}},"precondition":{"chain1":[]}}}
# warehouse = {'选车': {'precondition': {'chain0': []}, 'index': {'str_index': {}, 'boolean_index': {}, 'list_index': {'问价格': [['chain0', 'set_dict', 'set_1']], '外接音源接口': [['chain0', 'set_dict', 'set_1']], '油耗描述': [['chain0', 'set_dict', 'set_1']], '缸盖材料和缸体材料': [['chain0', 'set_dict', 'set_1']], '加速度描述': [['chain0', 'set_dict', 'set_1']], '颜色类型': [['chain0', 'set_dict', 'set_1']], '扬声器品牌': [['chain0', 'set_dict', 'set_1']], '前悬架类型和后悬架类型': [['chain0', 'set_dict', 'set_1']], '驻车制动类型': [['chain0', 'set_dict', 'set_1']], '城市': [['chain0', 'set_dict', 'set_1']], '近光灯和远光灯': [['chain0', 'set_dict', 'set_1']], '方向盘调节': [['chain0', 'set_dict', 'set_1']], '远光灯': [['chain0', 'set_dict', 'set_1']], '后制动器类型': [['chain0', 'set_dict', 'set_1']], '车身配置': [['chain0', 'set_dict', 'set_1']], '缸盖材料': [['chain0', 'set_dict', 'set_1']], '生产厂商': [['chain0', 'set_dict', 'set_1']], '驱动方式': [['chain0', 'set_dict', 'set_1']], '后悬架类型': [['chain0', 'set_dict', 'set_1']], '颜色': [['chain0', 'set_dict', 'set_1']], '前桥限滑差速器/差速锁和后桥限滑差速器/差速锁': [['chain0', 'set_dict', 'set_1']], '国别': [['chain0', 'set_dict', 'set_1']], '车体结构': [['chain0', 'set_dict', 'set_1']], '前悬架类型': [['chain0', 'set_dict', 'set_1']], '简称': [['chain0', 'set_dict', 'set_1']], '外观描述': [['chain0', 'set_dict', 'set_1']], '车身参数': [['chain0', 'set_dict', 'set_1']], '前制动器类型': [['chain0', 'set_dict', 'set_1']], '动力描述': [['chain0', 'set_dict', 'set_1']], '品牌': [['chain0', 'set_dict', 'set_1']], '配气机构': [['chain0', 'set_dict', 'set_1']], '问时间': [['chain0', 'set_dict', 'set_1']], '四驱形式': [['chain0', 'set_dict', 'set_1']], '询价用词': [['chain0', 'set_dict', 'set_1']], '后桥限滑差速器/差速锁': [['chain0', 'set_dict', 'set_1']], '环保标准': [['chain0', 'set_dict', 'set_1']], '变速箱类型': [['chain0', 'set_dict', 'set_1']], '后排车门开启方式': [['chain0', 'set_dict', 'set_1']], '电机布局': [['chain0', 'set_dict', 'set_1']], '多天窗': [['chain0', 'set_dict', 'set_1']], '进气形式': [['chain0', 'set_dict', 'set_1']], '近光灯': [['chain0', 'set_dict', 'set_1']], '供油方式': [['chain0', 'set_dict', 'set_1']], '侧滑门': [['chain0', 'set_dict', 'set_1']], '指定拆词': [['chain0', 'set_dict', 'set_1']], '厂商': [['chain0', 'set_dict', 'set_1']], '保养次数': [['chain0', 'set_dict', 'set_1']], '备胎规格': [['chain0', 'set_dict', 'set_1']], '资讯关键词': [['chain0', 'set_dict', 'set_1']], '变速箱': [['chain0', 'set_dict', 'set_1']], '发动机': [['chain0', 'set_dict', 'set_1']], '前桥限滑差速器/差速锁': [['chain0', 'set_dict', 'set_1']], '动作指令': [['chain0', 'set_dict', 'set_1']], '省': [['chain0', 'set_dict', 'set_1']], '能源类型': [['chain0', 'set_dict', 'set_1']], '后排座椅放倒方式': [['chain0', 'set_dict', 'set_1']], 'CD/DVD': [['chain0', 'set_dict', 'set_1']], '变速箱和简称': [['chain0', 'set_dict', 'set_1']], '保养项目': [['chain0', 'set_dict', 'set_1']], '级别': [['chain0', 'set_dict', 'set_1']], '前制动器类型和后制动器类型': [['chain0', 'set_dict', 'set_1']], '排量描述': [['chain0', 'set_dict', 'set_1']], '缸体材料': [['chain0', 'set_dict', 'set_1']], '热门': [['chain0', 'set_dict', 'set_1']], '驱动电机数': [['chain0', 'set_dict', 'set_1']], '可加热/制冷杯架': [['chain0', 'set_dict', 'set_1']], '发动机型号': [['chain0', 'set_dict', 'set_1']], '可变悬架': [['chain0', 'set_dict', 'set_1']], '问公里': [['chain0', 'set_dict', 'set_1']], '配置描述': [['chain0', 'set_dict', 'set_1']], '价格描述': [['chain0', 'set_dict', 'set_1']], '结构': [['chain0', 'set_dict', 'set_1']], '用途选车': [['chain0', 'set_dict', 'set_1']], '论坛用词': [['chain0', 'set_dict', 'set_1']], '版型': [['chain0', 'set_dict', 'set_1']], '中央差速器结构': [['chain0', 'set_dict', 'set_1']], '座椅材质': [['chain0', 'set_dict', 'set_1']], '助力类型': [['chain0', 'set_dict', 'set_1']], '口碑参数': [['chain0', 'set_dict', 'set_1']], '电池类型': [['chain0', 'set_dict', 'set_1']], '发动机特有技术': [['chain0', 'set_dict', 'set_1']], '车窗一键升降': [['chain0', 'set_dict', 'set_1']]}, 'range_index': {'实测100-0km/h制动(m)': [['chain0', 'set_dict', 'set_1']], '工信部续航里程(km)': [['chain0', 'set_dict', 'set_1']], '整车质保公里': [['chain0', 'set_dict', 'set_1']], '系统综合功率(kW)': [['chain0', 'set_dict', 'set_1']], '中控台彩色大屏尺寸': [['chain0', 'set_dict', 'set_1']], '上市时间': [['chain0', 'set_dict', 'set_1']], '每缸气门数(个)': [['chain0', 'set_dict', 'set_1']], '整备质量(kg)': [['chain0', 'set_dict', 'set_1']], '最大功率转速(rpm)': [['chain0', 'set_dict', 'set_1']], '最高车速(km/h)': [['chain0', 'set_dict', 'set_1']], '实测快充时间(小时)': [['chain0', 'set_dict', 'set_1']], '气缸数(个)': [['chain0', 'set_dict', 'set_1']], '后电动机最大扭矩(N·m)': [['chain0', 'set_dict', 'set_1']], '实测油耗(L/100km)': [['chain0', 'set_dict', 'set_1']], '最小离地间隙(mm)': [['chain0', 'set_dict', 'set_1']], '轴距(mm)': [['chain0', 'set_dict', 'set_1']], '系统综合扭矩(N·m)': [['chain0', 'set_dict', 'set_1']], '行程(mm)': [['chain0', 'set_dict', 'set_1']], '前轮距(mm)': [['chain0', 'set_dict', 'set_1']], '宽度(mm)': [['chain0', 'set_dict', 'set_1']], '整车质保年限': [['chain0', 'set_dict', 'set_1']], '纯电续航里程': [['chain0', 'set_dict', 'set_1']], '最大马力(Ps)': [['chain0', 'set_dict', 'set_1']], '压缩比': [['chain0', 'set_dict', 'set_1']], '排量(mL)': [['chain0', 'set_dict', 'set_1']], '第三排座椅': [['chain0', 'set_dict', 'set_1']], '充电桩价格': [['chain0', 'set_dict', 'set_1']], '车门数(个)': [['chain0', 'set_dict', 'set_1']], '快充电量(%)': [['chain0', 'set_dict', 'set_1']], '油箱容积(L)': [['chain0', 'set_dict', 'set_1']], '高度(mm)': [['chain0', 'set_dict', 'set_1']], '实测0-100km/h加速(s)': [['chain0', 'set_dict', 'set_1']], '排量(L)': [['chain0', 'set_dict', 'set_1']], '电池组质保公里': [['chain0', 'set_dict', 'set_1']], '前电动机最大扭矩(N·m)': [['chain0', 'set_dict', 'set_1']], '最大扭矩(N·m)': [['chain0', 'set_dict', 'set_1']], '快充时间(小时)': [['chain0', 'set_dict', 'set_1']], '实测慢充时间(小时)': [['chain0', 'set_dict', 'set_1']], '实测离地间隙(mm)': [['chain0', 'set_dict', 'set_1']], '后轮距(mm)': [['chain0', 'set_dict', 'set_1']], '后电动机最大功率(kW)': [['chain0', 'set_dict', 'set_1']], '缸径(mm)': [['chain0', 'set_dict', 'set_1']], '前电动机最大功率(kW)': [['chain0', 'set_dict', 'set_1']], '官方0-100km/h加速(s)': [['chain0', 'set_dict', 'set_1']], '扬声器数量': [['chain0', 'set_dict', 'set_1']], '后轮胎规格': [['chain0', 'set_dict', 'set_1']], '工信部综合油耗(L/100km)': [['chain0', 'set_dict', 'set_1']], '电动机总功率(kW)': [['chain0', 'set_dict', 'set_1']], '百公里耗电量(kWh/100km)': [['chain0', 'set_dict', 'set_1']], '前轮胎规格': [['chain0', 'set_dict', 'set_1']], '电池组质保年限': [['chain0', 'set_dict', 'set_1']], '挡位个数': [['chain0', 'set_dict', 'set_1']], '电动机总扭矩(N·m)': [['chain0', 'set_dict', 'set_1']], '电池容量(kWh)': [['chain0', 'set_dict', 'set_1']], '最大功率(kW)': [['chain0', 'set_dict', 'set_1']], '慢充时间(小时)': [['chain0', 'set_dict', 'set_1']], '座位数(个)': [['chain0', 'set_dict', 'set_1']], '行李厢容积(L)': [['chain0', 'set_dict', 'set_1']], '最大载重质量(kg)': [['chain0', 'set_dict', 'set_1']], '最大扭矩转速(rpm)': [['chain0', 'set_dict', 'set_1']], '实测续航里程(km)': [['chain0', 'set_dict', 'set_1']], '价格': [['chain0', 'set_dict', 'set_1']], '货箱尺寸(mm)': [['chain0', 'set_dict', 'set_1']], '长度(mm)': [['chain0', 'set_dict', 'set_1']]}}, 'chains': {'chain0': {'is_dict': {}, 'rank': {'completed_len': 0, 'completed_per': 0, 'len': 1}, 'self_judgement': {}, 'not_dict': {}, 'range_dict': {}, 'set_dict': {'set_1': {'set_mode': 'or', 'is_dict': {'问价格': set(), '外接音源接口': set(), '油耗描述': set(), '后桥限滑差速器/差速锁': set(), '颜色类型': set(), '加速度描述': set(), '可变悬架': set(), '远光灯': set(), '扬声器品牌': set(), '前悬架类型和后悬架类型': set(), '驻车制动类型': set(), '近光灯和远光灯': set(), '方向盘调节': set(), '用途选车': set(), '后制动器类型': set(), '车身配置': set(), '缸盖材料': set(), '生产厂商': set(), '驱动方式': set(), '后悬架类型': set(), '颜色': set(), '前桥限滑差速器/差速锁和后桥限滑差速器/差速锁': set(), '国别': set(), '车体结构': set(), '前悬架类型': set(), '简称': set(), '外观描述': set(), '车身参数': set(), '前制动器类型': set(), '近光灯': set(), '动力描述': set(), '品牌': set(), '配气机构': set(), '问时间': set(), '资讯关键词': set(), '询价用词': set(), '四驱形式': set(), 'CD/DVD': set(), '变速箱类型': set(), '后排车门开启方式': set(), '多天窗': set(), '进气形式': set(), '供油方式': set(), '侧滑门': set(), '指定拆词': set(), '驱动电机数': set(), '保养次数': set(), '备胎规格': set(), '发动机': set(), '变速箱': set(), '环保标准': set(), '动作指令': set(), '电机布局': set(), '能源类型': set(), '后排座椅放倒方式': set(), '城市': set(), '车窗一键升降': set(), '变速箱和简称': set(), '保养项目': set(), '级别': set(), '前制动器类型和后制动器类型': set(), '排量描述': set(), '缸体材料': set(), '热门': set(), '前桥限滑差速器/差速锁': set(), '价格描述': set(), '可加热/制冷杯架': set(), '发动机型号': set(), '厂商': set(), '问公里': set(), '配置描述': set(), '缸盖材料和缸体材料': set(), '结构': set(), '论坛用词': set(), '版型': set(), '中央差速器结构': set(), '座椅材质': set(), '助力类型': set(), '口碑参数': set(), '电池类型': set(), '发动机特有技术': set(), '省': set()}, 'rank': {'completed_len': 0, 'completed_per': 0, 'len': 146}, 'self_judgement': {}, 'not_dict': {'问价格': set(), '外接音源接口': set(), '油耗描述': set(), '后桥限滑差速器/差速锁': set(), '颜色类型': set(), '加速度描述': set(), '可变悬架': set(), '远光灯': set(), '扬声器品牌': set(), '前悬架类型和后悬架类型': set(), '驻车制动类型': set(), '近光灯和远光灯': set(), '方向盘调节': set(), '用途选车': set(), '后制动器类型': set(), '车身配置': set(), '缸盖材料': set(), '生产厂商': set(), '驱动方式': set(), '后悬架类型': set(), '颜色': set(), '前桥限滑差速器/差速锁和后桥限滑差速器/差速锁': set(), '国别': set(), '车体结构': set(), '前悬架类型': set(), '简称': set(), '外观描述': set(), '车身参数': set(), '前制动器类型': set(), '近光灯': set(), '动力描述': set(), '品牌': set(), '配气机构': set(), '问时间': set(), '资讯关键词': set(), '询价用词': set(), '四驱形式': set(), 'CD/DVD': set(), '变速箱类型': set(), '后排车门开启方式': set(), '多天窗': set(), '进气形式': set(), '供油方式': set(), '侧滑门': set(), '指定拆词': set(), '驱动电机数': set(), '保养次数': set(), '备胎规格': set(), '发动机': set(), '变速箱': set(), '环保标准': set(), '动作指令': set(), '电机布局': set(), '能源类型': set(), '后排座椅放倒方式': set(), '城市': set(), '车窗一键升降': set(), '变速箱和简称': set(), '保养项目': set(), '级别': set(), '前制动器类型和后制动器类型': set(), '排量描述': set(), '缸体材料': set(), '热门': set(), '前桥限滑差速器/差速锁': set(), '价格描述': set(), '可加热/制冷杯架': set(), '发动机型号': set(), '厂商': set(), '问公里': set(), '配置描述': set(), '缸盖材料和缸体材料': set(), '结构': set(), '论坛用词': set(), '版型': set(), '中央差速器结构': set(), '座椅材质': set(), '助力类型': set(), '口碑参数': set(), '电池类型': set(), '发动机特有技术': set(), '省': set()}, 'range_dict': {'实测100-0km/h制动(m)': {'<': '', '>': '', '=': ''}, '最大马力(Ps)': {'<': '', '>': '', '=': ''}, '整车质保公里': {'<': '', '>': '', '=': ''}, '系统综合功率(kW)': {'<': '', '>': '', '=': ''}, '中控台彩色大屏尺寸': {'<': '', '>': '', '=': ''}, '最小离地间隙(mm)': {'<': '', '>': '', '=': ''}, '每缸气门数(个)': {'<': '', '>': '', '=': ''}, '整备质量(kg)': {'<': '', '>': '', '=': ''}, '最大功率转速(rpm)': {'<': '', '>': '', '=': ''}, '最高车速(km/h)': {'<': '', '>': '', '=': ''}, '实测快充时间(小时)': {'<': '', '>': '', '=': ''}, '气缸数(个)': {'<': '', '>': '', '=': ''}, '后电动机最大扭矩(N·m)': {'<': '', '>': '', '=': ''}, '实测油耗(L/100km)': {'<': '', '>': '', '=': ''}, '上市时间': {'<': '', '>': '', '=': ''}, '轴距(mm)': {'<': '', '>': '', '=': ''}, '行程(mm)': {'<': '', '>': '', '=': ''}, '前轮距(mm)': {'<': '', '>': '', '=': ''}, '宽度(mm)': {'<': '', '>': '', '=': ''}, '工信部综合油耗(L/100km)': {'<': '', '>': '', '=': ''}, '纯电续航里程': {'<': '', '>': '', '=': ''}, '最大载重质量(kg)': {'<': '', '>': '', '=': ''}, '整车质保年限': {'<': '', '>': '', '=': ''}, '前电动机最大扭矩(N·m)': {'<': '', '>': '', '=': ''}, '工信部续航里程(km)': {'<': '', '>': '', '=': ''}, '压缩比': {'<': '', '>': '', '=': ''}, '排量(mL)': {'<': '', '>': '', '=': ''}, '第三排座椅': {'<': '', '>': '', '=': ''}, '充电桩价格': {'<': '', '>': '', '=': ''}, '车门数(个)': {'<': '', '>': '', '=': ''}, '快充电量(%)': {'<': '', '>': '', '=': ''}, '油箱容积(L)': {'<': '', '>': '', '=': ''}, '高度(mm)': {'<': '', '>': '', '=': ''}, '实测0-100km/h加速(s)': {'<': '', '>': '', '=': ''}, '排量(L)': {'<': '', '>': '', '=': ''}, '电池组质保公里': {'<': '', '>': '', '=': ''}, '价格': {'<': '', '>': '', '=': ''}, '最大扭矩(N·m)': {'<': '', '>': '', '=': ''}, '快充时间(小时)': {'<': '', '>': '', '=': ''}, '实测慢充时间(小时)': {'<': '', '>': '', '=': ''}, '实测离地间隙(mm)': {'<': '', '>': '', '=': ''}, '后轮距(mm)': {'<': '', '>': '', '=': ''}, '后电动机最大功率(kW)': {'<': '', '>': '', '=': ''}, '缸径(mm)': {'<': '', '>': '', '=': ''}, '前电动机最大功率(kW)': {'<': '', '>': '', '=': ''}, '官方0-100km/h加速(s)': {'<': '', '>': '', '=': ''}, '扬声器数量': {'<': '', '>': '', '=': ''}, '后轮胎规格': {'<': '', '>': '', '=': ''}, '电池组质保年限': {'<': '', '>': '', '=': ''}, '电动机总功率(kW)': {'<': '', '>': '', '=': ''}, '百公里耗电量(kWh/100km)': {'<': '', '>': '', '=': ''}, '前轮胎规格': {'<': '', '>': '', '=': ''}, '挡位个数': {'<': '', '>': '', '=': ''}, '电动机总扭矩(N·m)': {'<': '', '>': '', '=': ''}, '电池容量(kWh)': {'<': '', '>': '', '=': ''}, '最大功率(kW)': {'<': '', '>': '', '=': ''}, '慢充时间(小时)': {'<': '', '>': '', '=': ''}, '座位数(个)': {'<': '', '>': '', '=': ''}, '行李厢容积(L)': {'<': '', '>': '', '=': ''}, '系统综合扭矩(N·m)': {'<': '', '>': '', '=': ''}, '最大扭矩转速(rpm)': {'<': '', '>': '', '=': ''}, '实测续航里程(km)': {'<': '', '>': '', '=': ''}, '货箱尺寸(mm)': {'<': '', '>': '', '=': ''}, '长度(mm)': {'<': '', '>': '', '=': ''}}, 'set_dict': {}}}}}}}
# warehouse = {'选车': {'index': {'list_index': {'车系': [['chain0']]}, 'range_index': {'价格': [['chain1']], '价格_1': [['chain1']]}, 'str_index': {}, 'boolean_index': {}}, 'precondition': {'chain2': [], 'chain1': []}, 'chains': {'chain0': {'rank': {'len': 1, 'completed_per': 0, 'completed_len': 0}, 'self_judgement': {}, 'set_dict': {}, 'is_dict': {'车系': set()}, 'range_dict': {}, 'not_dict': {'车系': set()}}, 'chain1': {'rank': {'len': 2, 'completed_per': 0, 'completed_len': 0}, 'self_judgement': {}, 'set_dict': {}, 'is_dict': {}, 'range_dict': {'价格': {'=': '', '>': '', '<': ''}, '价格_1': {'=': '', '>': '', '<': ''}}, 'not_dict': {}}}}}
# warehouse = {'配置': {'chain_name': '', 'index': {'str_index': {'车系': [['chain0']], '车身配置': [['chain0']]}, 'boolean_index': {}, 'list_index': {}, 'range_index': {}}, 'precondition': {'chain0': []}, 'chains': {'chain0': {'self_judgement': {}, 'range_dict': {}, 'set_dict': {}, 'rank': {'completed_len': 0, 'len': 2, 'completed_per': 0}, 'chain_name': '问配置', 'is_dict': {'车系': '', '车身配置': ''}, 'not_dict': {}}}}, '选车': {'chain_name': '', 'index': {'str_index': {}, 'boolean_index': {}, 'list_index': {'电机布局': [['chain0', 'set_dict', 'set_1']], '后悬架类型': [['chain0', 'set_dict', 'set_1']], '前桥限滑差速器/差速锁': [['chain0', 'set_dict', 'set_1']], '电池类型': [['chain0', 'set_dict', 'set_1']], '资讯关键词': [['chain0', 'set_dict', 'set_1']], '座椅材质': [['chain0', 'set_dict', 'set_1']], '前制动器类型': [['chain0', 'set_dict', 'set_1']], '指定拆词': [['chain0', 'set_dict', 'set_1']], '口碑参数': [['chain0', 'set_dict', 'set_1']], '进气形式': [['chain0', 'set_dict', 'set_1']], '后排座椅放倒方式': [['chain0', 'set_dict', 'set_1']], '车身参数': [['chain0', 'set_dict', 'set_1']], '后排车门开启方式': [['chain0', 'set_dict', 'set_1']], '城市': [['chain0', 'set_dict', 'set_1']], '油耗描述': [['chain0', 'set_dict', 'set_1']], '问公里': [['chain0', 'set_dict', 'set_1']], '变速箱类型': [['chain0', 'set_dict', 'set_1']], '变速箱和简称': [['chain0', 'set_dict', 'set_1']], '环保标准': [['chain0', 'set_dict', 'set_1']], '供油方式': [['chain0', 'set_dict', 'set_1']], '缸体材料': [['chain0', 'set_dict', 'set_1']], '配气机构': [['chain0', 'set_dict', 'set_1']], '前悬架类型': [['chain0', 'set_dict', 'set_1']], '配置描述': [['chain0', 'set_dict', 'set_1']], '版型': [['chain0', 'set_dict', 'set_1']], '动力描述': [['chain0', 'set_dict', 'set_1']], '保养项目': [['chain0', 'set_dict', 'set_1']], '前制动器类型和后制动器类型': [['chain0', 'set_dict', 'set_1']], '国别': [['chain0', 'set_dict', 'set_1']], '近光灯': [['chain0', 'set_dict', 'set_1']], '助力类型': [['chain0', 'set_dict', 'set_1']], '可变悬架': [['chain0', 'set_dict', 'set_1']], '侧滑门': [['chain0', 'set_dict', 'set_1']], '热门': [['chain0', 'set_dict', 'set_1']], '可加热/制冷杯架': [['chain0', 'set_dict', 'set_1']], 'CD/DVD': [['chain0', 'set_dict', 'set_1']], '级别': [['chain0', 'set_dict', 'set_1']], '动作指令': [['chain0', 'set_dict', 'set_1']], '后制动器类型': [['chain0', 'set_dict', 'set_1']], '结构': [['chain0', 'set_dict', 'set_1']], '发动机特有技术': [['chain0', 'set_dict', 'set_1']], '外观描述': [['chain0', 'set_dict', 'set_1']], '排量描述': [['chain0', 'set_dict', 'set_1']], '能源类型': [['chain0', 'set_dict', 'set_1']], '变速箱': [['chain0', 'set_dict', 'set_1']], '前桥限滑差速器/差速锁和后桥限滑差速器/差速锁': [['chain0', 'set_dict', 'set_1']], '厂商': [['chain0', 'set_dict', 'set_1']], '扬声器品牌': [['chain0', 'set_dict', 'set_1']], '多天窗': [['chain0', 'set_dict', 'set_1']], '颜色': [['chain0', 'set_dict', 'set_1']], '远光灯': [['chain0', 'set_dict', 'set_1']], '价格描述': [['chain0', 'set_dict', 'set_1']], '缸盖材料': [['chain0', 'set_dict', 'set_1']], '备胎规格': [['chain0', 'set_dict', 'set_1']], '前悬架类型和后悬架类型': [['chain0', 'set_dict', 'set_1']], '中央差速器结构': [['chain0', 'set_dict', 'set_1']], '论坛用词': [['chain0', 'set_dict', 'set_1']], '发动机': [['chain0', 'set_dict', 'set_1']], '近光灯和远光灯': [['chain0', 'set_dict', 'set_1']], '问价格': [['chain0', 'set_dict', 'set_1']], '发动机型号': [['chain0', 'set_dict', 'set_1']], '生产厂商': [['chain0', 'set_dict', 'set_1']], '外接音源接口': [['chain0', 'set_dict', 'set_1']], '简称': [['chain0', 'set_dict', 'set_1']], '驱动电机数': [['chain0', 'set_dict', 'set_1']], '车系': [['chain1']], '保养次数': [['chain0', 'set_dict', 'set_1']], '用途选车': [['chain0', 'set_dict', 'set_1']], '四驱形式': [['chain0', 'set_dict', 'set_1']], '问时间': [['chain0', 'set_dict', 'set_1']], '品牌': [['chain0', 'set_dict', 'set_1']], '缸盖材料和缸体材料': [['chain0', 'set_dict', 'set_1']], '加速度描述': [['chain0', 'set_dict', 'set_1']], '询价用词': [['chain0', 'set_dict', 'set_1']], '驻车制动类型': [['chain0', 'set_dict', 'set_1']], '车体结构': [['chain0', 'set_dict', 'set_1']], '车窗一键升降': [['chain0', 'set_dict', 'set_1']], '车身配置': [['chain0', 'set_dict', 'set_1']], '后桥限滑差速器/差速锁': [['chain0', 'set_dict', 'set_1']], '方向盘调节': [['chain0', 'set_dict', 'set_1']], '省': [['chain0', 'set_dict', 'set_1']], '颜色类型': [['chain0', 'set_dict', 'set_1']], '驱动方式': [['chain0', 'set_dict', 'set_1']]}, 'range_index': {'实测快充时间(小时)': [['chain0', 'set_dict', 'set_1']], '实测100-0km/h制动(m)': [['chain0', 'set_dict', 'set_1']], '扬声器数量': [['chain0', 'set_dict', 'set_1']], '最大功率转速(rpm)': [['chain0', 'set_dict', 'set_1']], '快充时间(小时)': [['chain0', 'set_dict', 'set_1']], '后电动机最大扭矩(N·m)': [['chain0', 'set_dict', 'set_1']], '最高车速(km/h)': [['chain0', 'set_dict', 'set_1']], '电动机总扭矩(N·m)': [['chain0', 'set_dict', 'set_1']], '工信部综合油耗(L/100km)': [['chain0', 'set_dict', 'set_1']], '实测0-100km/h加速(s)': [['chain0', 'set_dict', 'set_1']], '价格': [['chain2'], [['chain0', 'set_dict', 'set_1']]], '前电动机最大功率(kW)': [['chain0', 'set_dict', 'set_1']], '百公里耗电量(kWh/100km)': [['chain0', 'set_dict', 'set_1']], '实测慢充时间(小时)': [['chain0', 'set_dict', 'set_1']], '长度(mm)': [['chain0', 'set_dict', 'set_1']], '每缸气门数(个)': [['chain0', 'set_dict', 'set_1']], '慢充时间(小时)': [['chain0', 'set_dict', 'set_1']], '纯电续航里程': [['chain0', 'set_dict', 'set_1']], '上市时间': [['chain0', 'set_dict', 'set_1']], '前轮距(mm)': [['chain0', 'set_dict', 'set_1']], '货箱尺寸(mm)': [['chain0', 'set_dict', 'set_1']], '价格_1': [['chain2']], '最小离地间隙(mm)': [['chain0', 'set_dict', 'set_1']], '快充电量(%)': [['chain0', 'set_dict', 'set_1']], '电池组质保年限': [['chain0', 'set_dict', 'set_1']], '高度(mm)': [['chain0', 'set_dict', 'set_1']], '实测续航里程(km)': [['chain0', 'set_dict', 'set_1']], '油箱容积(L)': [['chain0', 'set_dict', 'set_1']], '最大功率(kW)': [['chain0', 'set_dict', 'set_1']], '前电动机最大扭矩(N·m)': [['chain0', 'set_dict', 'set_1']], '系统综合功率(kW)': [['chain0', 'set_dict', 'set_1']], '气缸数(个)': [['chain0', 'set_dict', 'set_1']], '轴距(mm)': [['chain0', 'set_dict', 'set_1']], '后电动机最大功率(kW)': [['chain0', 'set_dict', 'set_1']], '充电桩价格': [['chain0', 'set_dict', 'set_1']], '后轮胎规格': [['chain0', 'set_dict', 'set_1']], '行程(mm)': [['chain0', 'set_dict', 'set_1']], '最大载重质量(kg)': [['chain0', 'set_dict', 'set_1']], '电池组质保公里': [['chain0', 'set_dict', 'set_1']], '中控台彩色大屏尺寸': [['chain0', 'set_dict', 'set_1']], '宽度(mm)': [['chain0', 'set_dict', 'set_1']], '挡位个数': [['chain0', 'set_dict', 'set_1']], '最大马力(Ps)': [['chain0', 'set_dict', 'set_1']], '电动机总功率(kW)': [['chain0', 'set_dict', 'set_1']], '整车质保年限': [['chain0', 'set_dict', 'set_1']], '最大扭矩转速(rpm)': [['chain0', 'set_dict', 'set_1']], '前轮胎规格': [['chain0', 'set_dict', 'set_1']], '排量(L)': [['chain0', 'set_dict', 'set_1']], '座位数(个)': [['chain0', 'set_dict', 'set_1']], '车门数(个)': [['chain0', 'set_dict', 'set_1']], '整车质保公里': [['chain0', 'set_dict', 'set_1']], '工信部续航里程(km)': [['chain0', 'set_dict', 'set_1']], '系统综合扭矩(N·m)': [['chain0', 'set_dict', 'set_1']], '最大扭矩(N·m)': [['chain0', 'set_dict', 'set_1']], '行李厢容积(L)': [['chain0', 'set_dict', 'set_1']], '后轮距(mm)': [['chain0', 'set_dict', 'set_1']], '电池容量(kWh)': [['chain0', 'set_dict', 'set_1']], '官方0-100km/h加速(s)': [['chain0', 'set_dict', 'set_1']], '排量(mL)': [['chain0', 'set_dict', 'set_1']], '压缩比': [['chain0', 'set_dict', 'set_1']], '实测离地间隙(mm)': [['chain0', 'set_dict', 'set_1']], '实测油耗(L/100km)': [['chain0', 'set_dict', 'set_1']], '整备质量(kg)': [['chain0', 'set_dict', 'set_1']], '缸径(mm)': [['chain0', 'set_dict', 'set_1']], '第三排座椅': [['chain0', 'set_dict', 'set_1']]}}, 'precondition': {'chain2': [], 'chain1': [], 'chain0': []}, 'chains': {'chain2': {'self_judgement': {}, 'range_dict': {'价格': {'>': '', '=': '', '<': ''}, '价格_1': {'>': '', '=': '', '<': ''}}, 'set_dict': {}, 'rank': {'completed_len': 0, 'len': 2, 'completed_per': 0}, 'chain_name': '价格选车', 'is_dict': {}, 'not_dict': {}}, 'chain1': {'self_judgement': {}, 'range_dict': {}, 'set_dict': {}, 'rank': {'completed_len': 0, 'len': 1, 'completed_per': 0}, 'chain_name': '车系选车', 'is_dict': {'车系': set()}, 'not_dict': {'车系': set()}}, 'chain0': {'self_judgement': {}, 'range_dict': {}, 'set_dict': {'set_1': {'self_judgement': {}, 'range_dict': {'实测快充时间(小时)': {'>': '', '=': '', '<': ''}, '实测100-0km/h制动(m)': {'>': '', '=': '', '<': ''}, '扬声器数量': {'>': '', '=': '', '<': ''}, '最大功率转速(rpm)': {'>': '', '=': '', '<': ''}, '快充时间(小时)': {'>': '', '=': '', '<': ''}, '后电动机最大扭矩(N·m)': {'>': '', '=': '', '<': ''}, '最高车速(km/h)': {'>': '', '=': '', '<': ''}, '电动机总扭矩(N·m)': {'>': '', '=': '', '<': ''}, '工信部综合油耗(L/100km)': {'>': '', '=': '', '<': ''}, '实测0-100km/h加速(s)': {'>': '', '=': '', '<': ''}, '价格': {'>': '', '=': '', '<': ''}, '前电动机最大功率(kW)': {'>': '', '=': '', '<': ''}, '百公里耗电量(kWh/100km)': {'>': '', '=': '', '<': ''}, '实测慢充时间(小时)': {'>': '', '=': '', '<': ''}, '长度(mm)': {'>': '', '=': '', '<': ''}, '每缸气门数(个)': {'>': '', '=': '', '<': ''}, '慢充时间(小时)': {'>': '', '=': '', '<': ''}, '纯电续航里程': {'>': '', '=': '', '<': ''}, '上市时间': {'>': '', '=': '', '<': ''}, '前轮距(mm)': {'>': '', '=': '', '<': ''}, '最大扭矩(N·m)': {'>': '', '=': '', '<': ''}, '快充电量(%)': {'>': '', '=': '', '<': ''}, '行李厢容积(L)': {'>': '', '=': '', '<': ''}, '电池组质保年限': {'>': '', '=': '', '<': ''}, '高度(mm)': {'>': '', '=': '', '<': ''}, '实测续航里程(km)': {'>': '', '=': '', '<': ''}, '油箱容积(L)': {'>': '', '=': '', '<': ''}, '最大功率(kW)': {'>': '', '=': '', '<': ''}, '前电动机最大扭矩(N·m)': {'>': '', '=': '', '<': ''}, '系统综合功率(kW)': {'>': '', '=': '', '<': ''}, '气缸数(个)': {'>': '', '=': '', '<': ''}, '轴距(mm)': {'>': '', '=': '', '<': ''}, '后电动机最大功率(kW)': {'>': '', '=': '', '<': ''}, '充电桩价格': {'>': '', '=': '', '<': ''}, '后轮胎规格': {'>': '', '=': '', '<': ''}, '行程(mm)': {'>': '', '=': '', '<': ''}, '最大载重质量(kg)': {'>': '', '=': '', '<': ''}, '电池组质保公里': {'>': '', '=': '', '<': ''}, '中控台彩色大屏尺寸': {'>': '', '=': '', '<': ''}, '宽度(mm)': {'>': '', '=': '', '<': ''}, '挡位个数': {'>': '', '=': '', '<': ''}, '最大马力(Ps)': {'>': '', '=': '', '<': ''}, '电动机总功率(kW)': {'>': '', '=': '', '<': ''}, '整车质保年限': {'>': '', '=': '', '<': ''}, '最大扭矩转速(rpm)': {'>': '', '=': '', '<': ''}, '前轮胎规格': {'>': '', '=': '', '<': ''}, '排量(L)': {'>': '', '=': '', '<': ''}, '座位数(个)': {'>': '', '=': '', '<': ''}, '车门数(个)': {'>': '', '=': '', '<': ''}, '整车质保公里': {'>': '', '=': '', '<': ''}, '货箱尺寸(mm)': {'>': '', '=': '', '<': ''}, '官方0-100km/h加速(s)': {'>': '', '=': '', '<': ''}, '最小离地间隙(mm)': {'>': '', '=': '', '<': ''}, '工信部续航里程(km)': {'>': '', '=': '', '<': ''}, '后轮距(mm)': {'>': '', '=': '', '<': ''}, '电池容量(kWh)': {'>': '', '=': '', '<': ''}, '系统综合扭矩(N·m)': {'>': '', '=': '', '<': ''}, '排量(mL)': {'>': '', '=': '', '<': ''}, '压缩比': {'>': '', '=': '', '<': ''}, '实测离地间隙(mm)': {'>': '', '=': '', '<': ''}, '实测油耗(L/100km)': {'>': '', '=': '', '<': ''}, '整备质量(kg)': {'>': '', '=': '', '<': ''}, '缸径(mm)': {'>': '', '=': '', '<': ''}, '第三排座椅': {'>': '', '=': '', '<': ''}}, 'set_dict': {}, 'set_mode': 'or', 'rank': {'completed_len': 0, 'len': 146, 'completed_per': 0}, 'is_dict': {'电机布局': set(), '后悬架类型': set(), '前桥限滑差速器/差速锁': set(), '电池类型': set(), '资讯关键词': set(), '座椅材质': set(), '前制动器类型': set(), '指定拆词': set(), '口碑参数': set(), '进气形式': set(), '前悬架类型和后悬架类型': set(), '后排座椅放倒方式': set(), '车身参数': set(), '后排车门开启方式': set(), '外观描述': set(), '油耗描述': set(), '询价用词': set(), '变速箱类型': set(), '变速箱和简称': set(), '环保标准': set(), '供油方式': set(), '多天窗': set(), '配气机构': set(), '前悬架类型': set(), '动力描述': set(), '前桥限滑差速器/差速锁和后桥限滑差速器/差速锁': set(), '前制动器类型和后制动器类型': set(), '国别': set(), '近光灯': set(), '助力类型': set(), '缸盖材料和缸体材料': set(), '侧滑门': set(), '热门': set(), '可加热/制冷杯架': set(), 'CD/DVD': set(), '级别': set(), '动作指令': set(), '后制动器类型': set(), '可变悬架': set(), '发动机特有技术': set(), '城市': set(), '排量描述': set(), '能源类型': set(), '变速箱': set(), '保养项目': set(), '厂商': set(), '扬声器品牌': set(), '配置描述': set(), '颜色': set(), '远光灯': set(), '价格描述': set(), '问公里': set(), '缸盖材料': set(), '备胎规格': set(), '品牌': set(), '中央差速器结构': set(), '论坛用词': set(), '发动机': set(), '近光灯和远光灯': set(), '问价格': set(), '发动机型号': set(), '生产厂商': set(), '外接音源接口': set(), '简称': set(), '驱动电机数': set(), '版型': set(), '保养次数': set(), '用途选车': set(), '四驱形式': set(), '问时间': set(), '缸体材料': set(), '加速度描述': set(), '结构': set(), '驻车制动类型': set(), '车体结构': set(), '车窗一键升降': set(), '车身配置': set(), '后桥限滑差速器/差速锁': set(), '方向盘调节': set(), '省': set(), '颜色类型': set(), '驱动方式': set()}, 'not_dict': {'电机布局': set(), '后悬架类型': set(), '前桥限滑差速器/差速锁': set(), '电池类型': set(), '资讯关键词': set(), '座椅材质': set(), '前制动器类型': set(), '指定拆词': set(), '口碑参数': set(), '进气形式': set(), '前悬架类型和后悬架类型': set(), '后排座椅放倒方式': set(), '车身参数': set(), '后排车门开启方式': set(), '外观描述': set(), '油耗描述': set(), '询价用词': set(), '变速箱类型': set(), '变速箱和简称': set(), '环保标准': set(), '供油方式': set(), '多天窗': set(), '配气机构': set(), '前悬架类型': set(), '动力描述': set(), '前桥限滑差速器/差速锁和后桥限滑差速器/差速锁': set(), '前制动器类型和后制动器类型': set(), '国别': set(), '近光灯': set(), '助力类型': set(), '缸盖材料和缸体材料': set(), '侧滑门': set(), '热门': set(), '可加热/制冷杯架': set(), 'CD/DVD': set(), '级别': set(), '动作指令': set(), '后制动器类型': set(), '可变悬架': set(), '发动机特有技术': set(), '城市': set(), '排量描述': set(), '能源类型': set(), '变速箱': set(), '保养项目': set(), '厂商': set(), '扬声器品牌': set(), '配置描述': set(), '颜色': set(), '远光灯': set(), '价格描述': set(), '问公里': set(), '缸盖材料': set(), '备胎规格': set(), '品牌': set(), '中央差速器结构': set(), '论坛用词': set(), '发动机': set(), '近光灯和远光灯': set(), '问价格': set(), '发动机型号': set(), '生产厂商': set(), '外接音源接口': set(), '简称': set(), '驱动电机数': set(), '版型': set(), '保养次数': set(), '用途选车': set(), '四驱形式': set(), '问时间': set(), '缸体材料': set(), '加速度描述': set(), '结构': set(), '驻车制动类型': set(), '车体结构': set(), '车窗一键升降': set(), '车身配置': set(), '后桥限滑差速器/差速锁': set(), '方向盘调节': set(), '省': set(), '颜色类型': set(), '驱动方式': set()}}}, 'rank': {'completed_len': 0, 'len': 1, 'completed_per': 0}, 'chain_name': '条件选车', 'is_dict': {}, 'not_dict': {}}}}}
db1 = redis.Redis(host='127.0.0.1', password="", port=6379, db=0)
warehouse = eval(db1.get("warehouse"))
# a_fun = "def funs(sentence,the_str):\n   if('a' in 'a'):\n      return True\n   else:      return False"
# c = eval(a_fun)
# print(c)
map_prefix2function = {"have":{"fun":"'[$arg0]' in '[$arg1]'","param":["[$split]_","[$origin_sentence]"]},"nothaveE":{"fun":"'[$arg0]' not in [$arg1]","param":["[$split]_","[$orca_entity_names]"]},"nothave":{"fun":"'[$arg0]' not in '[$arg1]'","param":["[$split]_","[$origin_sentence]"]}}
#########todo make shape of chain dict##########

########todo make precondition#############
#########todo make chains#######################

###########todo make index ###################

#######todo def make_warehouse():###############
# the_warehouse = copy.deepcopy(warehouse)
#for i in warehouse["选车"]["chains"]["chain1"]:
#    if

def make_term(name,value,logic=1):
    return {"name":name,"value":value,"logic":logic}

def execute_condition(judgement,origin_sentence,orca_entity):
    judgement_condition = judgement.split("_")

    if judgement_condition[0] in map_prefix2function:
        the_judgement = map_prefix2function[judgement_condition[0]]
        _fun = copy.deepcopy(the_judgement["fun"])

        for index in range(len(the_judgement["param"])):
            the_term = "$$$$$$"
            if '[$split]' in the_judgement["param"][index]:
                tmp_term = judgement.split(the_judgement["param"][index].replace('[$split]',""))
                if len(tmp_term)==2:
                    the_term=tmp_term[1]
            elif '[$origin_sentence]' in the_judgement["param"][index]:
                the_term = origin_sentence

            elif '[$orca_entity_names]' in the_judgement["param"][index]:
                tmp_l = []
                for enti in orca_entity:
                    tmp_l.append(enti["name"])
                the_term = tmp_l

            elif the_judgement["param"][index]!="":
                the_term = the_judgement["param"][index]

            if the_term!="$$$$$$":
                _fun = _fun.replace("[$arg"+str(index)+"]",str(the_term))
        return eval(_fun)
    else:
        return False

# def get_qulifier(a):
#     return a

def do_statistics(slot_part):
    if len(slot_part["set_dict"])!=0:    ####判断有没有set_dict嵌套，递归增加
        for set_dicts in slot_part["set_dict"]:
            do_statistics(slot_part["set_dict"][set_dicts])

    for judges in slot_part["self_judgement"]:  #####把judge全部判断好
        if slot_part["self_judgement"][judges]:
            slot_part["rank"]["completed_len"]+=1

    if "set_mode" in slot_part:      ####把judge判断好之后的rank重新计算
        if slot_part["set_mode"]=="or" and slot_part["rank"]["completed_len"]>=1:
            slot_part["rank"]["completed_per"] = 1
        else:
            slot_part["rank"]["completed_per"] = int(float(slot_part["rank"]["completed_len"])/float(slot_part["rank"]["len"]))

    if len(slot_part["set_dict"])!=0:    ####判断有没有set_dict嵌套，递归增加
        for set_dicts in slot_part["set_dict"]:
            if slot_part["set_dict"][set_dicts]["rank"]["completed_per"]==1:
                slot_part["rank"]["completed_len"]+=1




def fill_local_dict(name,value,logic,slot_dict):#############对is_not_range填槽
    print("name:::",name)
    pattern = re.compile("__\d+")
    name_for_list = re.sub(pattern, "", name)
    if name in slot_dict["index"]["str_index"]:   ##该name存在于str_index的index中，表示是str形式的值
        paths = slot_dict["index"]["str_index"][name] ##获取一个路径集合
        for path in paths:  ##填充每个路径
            length_of_path = len(path)
            if length_of_path>0:
                get_value = 'slot_dict["chains"]["'+path[0]+'"]'
                flag = 1  ##==1
                while flag<length_of_path:
                    get_value+='[path['+str(flag)+']]'
                    flag+=1
                tmp_slot = eval(get_value)
                if int(logic):
                    flag_TF = (tmp_slot["is_dict"][name]=="")
                    tmp_slot["is_dict"][name]=value
                    if flag_TF:
                        if name not in tmp_slot["not_dict"]:
                            tmp_slot["rank"]["completed_len"] += 1
                        if name in tmp_slot["not_dict"] and tmp_slot["not_dict"][name]=="":
                            tmp_slot["rank"]["completed_len"] += 1
                        if name in tmp_slot["not_dict"] and tmp_slot["not_dict"][name]==value:
                            tmp_slot["not_dict"][name] = ""
                else:
                    flag_TF = (tmp_slot["not_dict"][name]=="")
                    tmp_slot["not_dict"][name]=value
                    if flag_TF:
                        if name in tmp_slot["is_dict"] and tmp_slot["is_dict"][name]=="":
                            tmp_slot["rank"]["completed_len"] += 1
                        if name in tmp_slot["is_dict"] and tmp_slot["is_dict"][name]==value:
                            tmp_slot["is_dict"][name] = ""

    elif name_for_list in slot_dict["index"]["list_index"]:
        paths = slot_dict["index"]["list_index"][name]
        for path in paths:  ##填充每个路径
            length_of_path = len(path)
            if length_of_path>0:
                get_value = 'slot_dict["chains"]["'+path[0]+'"]'
                flag = 1  ##==1
                while flag<length_of_path:
                    get_value+='[path['+str(flag)+']]'
                    flag+=1
                tmp_slot = eval(get_value) ##获取暂时性的目标slot的上一层

                if name in tmp_slot["is_dict"] and len(tmp_slot["is_dict"][name]) == 0:
                    if name not in tmp_slot["not_dict"]:
                        tmp_slot["rank"]["completed_len"] += 1
                    elif name in tmp_slot["not_dict"] and len(tmp_slot["not_dict"][name]) == 0:
                        tmp_slot["rank"]["completed_len"] += 1

                if int(logic):
                    tmp_slot["is_dict"][name].add(value)
                    if value in tmp_slot["not_dict"][name]:  ######如果在逆反的集合中，才remove
                        tmp_slot["not_dict"][name].remove(value)
                else:
                    tmp_slot["not_dict"][name].add(value)
                    if value in tmp_slot["is_dict"][name]:  ######如果在逆反的集合中，才remove
                        tmp_slot["is_dict"][name].remove(value)

    elif name in slot_dict["index"]["range_index"]:
        paths = slot_dict["index"]["range_index"][name]
        for path in paths:  ##填充每个路径
            length_of_path = len(path)
            if length_of_path>0:
                print(path,paths)
                get_value = 'slot_dict["chains"]["'+path[0]+'"]'
                flag = 1  ##==1
                while flag<length_of_path:
                    get_value+='[path['+str(flag)+']]'
                    flag+=1
                tmp_slot = eval(get_value) ##获取暂时性的目标slot的上一层

                is_blank = True
                for the_value in tmp_slot["range_dict"][name].values():
                    if the_value!="":
                        is_blank=False
                        break
                if is_blank:
                    tmp_slot["rank"]["completed_len"]+=1
                if int(logic): ###其实range的全是正逻辑
                    if "<" in value:
                        tmp_slot["range_dict"][name]["<"] = value
                        tmp_slot["range_dict"][name]["="] = ""
                        if tmp_slot["range_dict"][name][">"]!="" and float(value[1:])<=float(tmp_slot["range_dict"][name][">"][1:]):
                            tmp_slot["range_dict"][name][">"] = ""

                    elif ">" in value:
                        tmp_slot["range_dict"][name][">"] = value
                        tmp_slot["range_dict"][name]["="] = ""
                        if tmp_slot["range_dict"][name]["<"]!="" and float(value[1:])>=float(tmp_slot["range_dict"][name]["<"][1:]):
                            tmp_slot["range_dict"][name]["<"] = ""
                    else:
                        tmp_slot["range_dict"][name]["="] = value
                        tmp_slot["range_dict"][name]["<"] = ""
                        tmp_slot["range_dict"][name][">"] = ""


def fill_boolean_dict(chain,origin_sentence,slot_dict,orca_entity):       ######对自判断填槽
    if chain in slot_dict["index"]["boolean_index"]:
        paths = slot_dict["index"]["boolean_index"][chain]
        for path in paths:
            length_of_path = len(path)
            if length_of_path>0:
                get_value = 'slot_dict["chains"]["'+chain+'"]'
                #print(get_value)
                flag = 0  ##==1
                while flag<length_of_path-1:
                    get_value+='[path['+str(flag)+']]'
                    flag+=1
                get_value+='["self_judgement"]'
                tmp_slot = eval(get_value)

                for judgement in tmp_slot:
                    tmp_slot[judgement] = execute_condition(judgement,origin_sentence,orca_entity)



def fill_slot(intent,orca_result,origin_sentence):
    slot_dict = copy.deepcopy(warehouse[intent])
###########对precondition和self_judgement填槽########################
    for chain in slot_dict["precondition"]:
        if len(slot_dict["precondition"][chain])==0:
            slot_dict["precondition"][chain] = True
            ##############boolean逐个填槽####################
            fill_boolean_dict(chain,origin_sentence,slot_dict,orca_result)
            ##############boolean逐个填槽####################
        else:
            for index in range(len(slot_dict["precondition"][chain])-1,-1,-1):
                if execute_condition(slot_dict["precondition"][chain][index],origin_sentence):
                    slot_dict["precondition"][chain].pop(index)
            if len(slot_dict["precondition"][chain]) == 0:
                slot_dict["precondition"][chain] = True
                ##############boolean逐个填槽####################
                fill_boolean_dict(chain,origin_sentence,slot_dict,orca_result)
                ##############boolean逐个填槽####################
            else:
                slot_dict["precondition"][chain] = False
###########对precondition和self_judgement填槽########################

    #orca_result = get_qulifier(orca_result) ####解析出修饰词，返回的是term类型 [{"name":"","value":"","logic":"1"}]
    ##############is_not_range逐个填槽####################
    for entity in orca_result:
        entity_name = entity["name"]
        entity_value = entity["value"]
        entity_logic = entity["logic"]
        fill_local_dict(entity_name,entity_value,entity_logic,slot_dict)
    #################is_not_range逐个填槽####################

###################################################至此填槽完毕##########################################################

####################作统计，即从叶子节点对rank作运算##################
    for chains in slot_dict["chains"]:
        do_statistics(slot_dict["chains"][chains])
        slot_dict["chains"][chains]["rank"]["completed_per"] =(float(slot_dict["chains"][chains]["rank"]["completed_len"])/float(slot_dict["chains"][chains]["rank"]["len"]))
####################作统计，即从叶子节点对rank作运算##################
    return slot_dict

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
    return terms,target_chain


def testttttttt(file_name):
    aaa = open("errorss","a",encoding="utf8")
    import time
    from get_qualifier import get_qualifier
    hahahahaha = open(file_name,"r",encoding="utf8")
    for gkjdfhjk in hahahahaha:
        gkjdfhjk = gkjdfhjk.strip().split("\t")
        test_sents = gkjdfhjk[0]

        #orca_results = [{"name":"车系","value":"宝马5系","logic":"1"},{"name":"配置参数","value":"全景天窗","logic":"1"},{"name":"价格","value":"<300000","logic":"1"},{"name":"国别","value":"日本","logic":"0"},{"name":"动力","value":"<50","logic":"1"},{"name":"国别_1","value":"德国","logic":"1"}]
        #test_sents = "我要一个油耗低的50万-100万,80万左右,30万以内，最多20万,轴距5m以内排量2.0t以内第三排座位,这个车好不好的啊"
        # test_sents = "给我来一个30万以内的SUV，不要日本车"
        # test_sents = "给我推荐一个宝马5系的车"
        # test_sents = "宝马5系带不带全景天窗"
        # test_sents = "思域第1次保养都更换哪些东西都需要保养什么东西"
        # test_sents = "50万的车和100万的车哪个好"
        #test_sents = "宝马5系一年花费多少？"

        orca_results,orca_intent = get_qualifier(test_sents)
        orca_intent = gkjdfhjk[1]
        # print("原句:::{}".format(test_sents))
        # print("orca_意图:{}++++++++++++++++解析后的实体:{}".format(orca_intent,orca_results))
        # aa = time.time()
        if orca_intent not in warehouse:
            aaa.write("意图错误:::"+test_sents+"\n")
            continue
        slot_result = fill_slot(intent=orca_intent,orca_result=orca_results,origin_sentence=test_sents)
        # print("解析理解所用时间:::",time.time()-aa)
        # db1 = redis.Redis(host='127.0.0.1', password="123456", port=6379, db=1)
        # db1.set(str(user_id),slot_result)
        terms,target_chain_ = parse_slot(slot_result)
        # print(slot_result)
        print("目标链的内容:::",slot_result["chains"][target_chain_])
        print("目标链的排名:::",slot_result["chains"][target_chain_]["rank"])
        print("产生的terms:::",terms)
        print("目标子意图:::",slot_result["chains"][target_chain_]["chain_name"])

        if slot_result["chains"][target_chain_]["chain_name"]!=gkjdfhjk[2]:

            aaa.write(test_sents+"\t"+"实际结果::"+slot_result["chains"][target_chain_]["chain_name"]+"\t"+"预期结果:::"+gkjdfhjk[2]+"\t"+"被选链条:::{}".format(target_chain_)+"\n")
            print(test_sents)

        # print("目标子意图:::",slot_result["chains"]["chain5"])

        # print("chain2:::",slot_result["chains"]["chain2"]["rank"])
        #print("获取的查询term:::",terms)
        #print(slot_result["chains"]["chain1"])
            # for entity in orca_result:
        # for intent in warehouse:
        #
        #     print(intent)
            # warehouse[intent]["index"] = intent_index
        ###########todo make index ###################

        message_id = 0
        #print(warehouse)

        #print(slot_dict["chains"]["chain1"])
    aaa.close()

def test_sts(sts):
    from get_qualifier import get_qualifier
    import time


    #orca_results = [{"name":"车系","value":"宝马5系","logic":"1"},{"name":"配置参数","value":"全景天窗","logic":"1"},{"name":"价格","value":"<300000","logic":"1"},{"name":"国别","value":"日本","logic":"0"},{"name":"动力","value":"<50","logic":"1"},{"name":"国别_1","value":"德国","logic":"1"}]
    #test_sents = "我要一个油耗低的50万-100万,80万左右,30万以内，最多20万,轴距5m以内排量2.0t以内第三排座位,这个车好不好的啊"
    # test_sents = "给我来一个30万以内的SUV，不要日本车"
    # test_sents = "给我推荐一个宝马5系的车"
    # test_sents = "宝马5系带不带全景天窗"
    # test_sents = "思域第1次保养都更换哪些东西都需要保养什么东西"
    # test_sents = "50万的车和100万的车哪个好"
    #test_sents = "宝马5系一年花费多少？"

    orca_results,orca_intent = get_qualifier(sts)
    orca_intent = orca_intent
    print("原句:::{}".format(sts))
    print("orca_意图:{}++++++++++++++++解析后的实体:{}".format(orca_intent,orca_results))
    aa = time.time()

    slot_result = fill_slot(intent=orca_intent,orca_result=orca_results,origin_sentence=sts)
    print("解析理解所用时间:::",time.time()-aa)
    # db1 = redis.Redis(host='127.0.0.1', password="123456", port=6379, db=1)
    # db1.set(str(user_id),slot_result)
    terms,target_chain_ = parse_slot(slot_result)
    # print(slot_result)
    print("目标链的内容:::",slot_result["chains"][target_chain_])
    print("目标链的排名:::",slot_result["chains"][target_chain_]["rank"])
    print("产生的terms:::",terms)
    print("目标子意图:::",slot_result["chains"][target_chain_]["chain_name"])

    # print("目标子意图:::",slot_result["chains"]["chain5"])

    # print("chain2:::",slot_result["chains"]["chain2"]["rank"])
    #print("获取的查询term:::",terms)
    #print(slot_result["chains"]["chain1"])
        # for entity in orca_result:
    # for intent in warehouse:
    #
    #     print(intent)
        # warehouse[intent]["index"] = intent_index
    ###########todo make index ###################

if __name__=="__main__":
    # testttttttt("nums")
    # test_sts("宝马5系多少公里换压箱油？")
    testttttttt("nums")