#!/usr/bin/env python
# -*- coding:utf-8 -*-
import redis

r = redis.Redis(host='127.0.0.1',password="", port=6379,db=0)
#r.set('name', 'aaa')   #添加
print (r.get('warehouse'))   #获取