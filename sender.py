# -*- coding: utf-8 -*-
"""
Created on Thu Nov 12 13:43:13 2020

@author: zhkgo
"""
from io import BytesIO
from copy import deepcopy
import numpy as np
# from mne.io import read_raw
import matplotlib.pyplot as plt 
import time
import mne
datasets = []
# need_channels=['FZ','FC1','FC2','C3','CZ','C4','CP1','CP2','P7','P3','PZ','P4','P8','O1','OZ','O2']
# need_channels=['Fz' for i in range(33)]
need_channels=['FP1','FPZ','FP2','AF3','AF4','F7','F5','F3','F1','FZ','F2','F4','F6','F8','FT7','FC5','FC3','FC1','FCZ','FC2','FC4','FC6','FT8','T7','C5','C3','C1','CZ','C2','C4','C6','T8','M1','TP7','CP5','CP3','CP1','CPZ','CP2','CP4','CP6','TP8','M2','P7','P5','P3','P1','PZ','P2','P4','P6','P8','PO7','PO5','PO3','POZ','PO4','PO6','PO8','CB1','O1','OZ','O2','CB2']
data = mne.io.read_raw_cnt("data/lgw.cnt", preload=True)
datasets.insert(0, data)
datasets.insert(1, deepcopy(data))
data = datasets[1]
data.pick_channels(need_channels,ordered=True)
# data.filter(1.0, 40.0)
data,_= data[:,:]
print(data.shape)
data=data.astype(np.float32).T
data=np.ascontiguousarray(data)
mbytes=BytesIO()
mbytes.write(data)
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
            time.sleep(0.5)
            t+=20
            if t>=endlen:
                t=0
        # server.close()
except Exception as e:
    print("----------------")
    print(e)
    server.close()