# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 13:43:13 2020

@author: zhkgo
"""
from io import BytesIO
from copy import deepcopy
import numpy as np
from mne.io import read_raw
import matplotlib.pyplot as plt 
import time
datasets = []
# need_channels=['FZ','FC1','FC2','C3','CZ','C4','CP1','CP2','P7','P3','PZ','P4','P8','O1','OZ','O2']
need_channels=['Fz' for i in range(33)]
# data = read_raw("data/lgw.cnt", preload=True)
# datasets.insert(0, data)
# datasets.insert(1, deepcopy(data))
# data = datasets[1]
# data.pick_channels(need_channels,ordered=True)
# data.filter(1.0, 40.0)
# data.pick_channels(['O1','O2'],ordered=True)
# data,_= data[:,:]
# data=data.astype(np.float32).T
# data=np.ascontiguousarray(data)
# mbytes=BytesIO()
# mbytes.write(data)
# printMem(a)
data=np.load("data/log20201117172718.npy").tolist()
import socket
import os
#声明类型，生成socket链接对象
server = socket.socket()
#监听接收端口元组(本地，端口)，绑定要监听的端口
server.bind(('localhost',8712))
#最大监听数，允许多少人在排队

server.listen(5)
channels=len(need_channels)
# endlen=len(mbytes.getvalue())
endlen=len(data)
# data=data.astype('bytes')
try:
    while True:
        print("等待客户端连接指令")
        conn,addr = server.accept() #返回链接的标记位conn，与连接的地址
        print("客户端%s已连接"%(conn))
        t=0
        while True:
            # conn.sendall(mbytes.getvalue()[t*channels*4:t*channels*4+channels*4*20])
            conn.sendall(data[t*channels*4:t*channels*4+channels*4*20])
            time.sleep(0.02)
            t+=20
            if t>=endlen:
                t=0
        # server.close()
except Exception as e:
    print("----------------")
    print(e)
    server.close()