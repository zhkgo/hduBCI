# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 15:54:33 2020

@author: zhkgo
"""
#code 0为正常 1为异常
import json

def response(code=0,data="success"):
    return json.dumps({"code":code,"data":data})
def success(data="success"):
    return response(code=0,data=data)
def fail(data="some error appears"):
    return response(code=1,data=data)

    