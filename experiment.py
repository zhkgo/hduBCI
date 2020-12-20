# -*- coding: utf-8 -*-
"""
Created on Sat Nov 21 20:41:30 2020

@author: zhkgo
"""
import threading
import numpy as np
class Experiment:
    def __init__(self):
        self.CHANNELS=[
            ['Fp1','Fp2','F3','F4','F7','F8','FC1','FC2','FC5','FC6','Cz','C3','C4','T7','T8','CP1','CP2','CP5','CP6','Pz','P3','P4','P7','P8','POz','PO3','PO4','PO5','PO6','Oz','O1','O2','ref'],#ref 参考电极
            ['FP1','FPZ','FP2','AF3','AF4','F7','F5','F3','F1','FZ','F2','F4','F6','F8','FT7','FC5','FC3','FC1','FCZ','FC2','FC4','FC6','FT8','T7','C5','C3','C1','CZ','C2','C4','C6','T8','M1','TP7','CP5','CP3','CP1','CPZ','CP2','CP4','CP6','TP8','M2','P7','P5','P3','P1','PZ','P2','P4','P6','P8','PO7','PO5','PO3','POZ','PO4','PO6','PO8','CB1','O1','OZ','O2','CB2'],
            ]
        self.tcp=None
        self.classfier=None
        self.scaler=None
        self.filter=None
        self.channels=None
        self.res=np.zeros((3600,1))
        self.done=False
        self.tcpThread = None
        self.windows=1000
        
        self.startTime=0 #实验开始时间 单位ms
        self.sessions=0 #session数量 
        self.trials=0  #每个session的trial数量
        self.duration=0 #一个trail持续时间 单位ms
        self.interval=0 #session之间的间隔
        self.tmin=0 #截取时间起点（相比于trail开始的时间点 单位ms）
        self.tmax=0 #截取时间终点（相比于trail开始的时间点 单位ms）
        self.device=0  #device= 0 博瑞康 device=1 nueroscan 
        self.device_channels=[]
        
        # self.end=0
    def finish(self):
        self.done=True
        self.stop_tcp()
    def start_tcp(self):
        assert self.tcp !=None,"请先初始化设置" 
        self.tcpThread = threading.Thread(target=self.tcp.parse_data)
        self.tcpThread.start()
    def stop_tcp(self):
        self.tcp.close()
        self.tcp.saveData()
        self.tcpTread.join()
        print("TCP线程已成功关闭")
    def setParameters(self,sessions:int,trials:int,duration:int,interval:int,tmin:int,tmax:int,device:int):
        self.sessions=sessions
        self.trials=trials
        self.duration=duration
        self.interval=interval
        self.tmin=tmin
        self.tmax=tmax
        self.device=device
        assert device<2,"设备编号应当小于2"
        self.device_channels=self.CHANNELS[self.device]
    def restart_tcp(self):
        self.stop_tcp()
        self.tcp.reinit()
        self.start_tcp( )
    def set_dataIn(self,tcp):
        self.tcp=tcp
    def set_filter(self,sfilter):
        self.filter=sfilter
    def set_channel(self,ch_names):
        self.channels=ch_names
        idxs=[]
        for item in ch_names:
            idxs.append(self.device_channels.index(item))
        return idxs
    #获取指定位置的数据 如果传入-1 或者过大的时间值，则返回最新的，
    #若存在滤波器，会在数据返回之前进行滤波
    #windows为长度 startpos为起点
    def getData(self,startpos:int,windows=1000):
        data=self.tcp.get_batch(startpos,maxlength=windows)
        if self.filter:
            data=self.filter.deal(data)
        return data
    def set_scaler(self,scaler):
        # assert hasattr(scaler,"fit"),"特征提取器不存在fit函数"
        assert hasattr(scaler,"fit_transform"),"特征提取器不存在fit_transform函数"
        assert hasattr(scaler,"transform"),"特征提取器不存在fit函数"
        self.scaler=scaler
    def set_classfier(self,clf):
        # assert hasattr(clf,'fit'),"分类器不存在fit函数"
        assert hasattr(clf, 'predict'),"分类器不存在predict函数"
        self.classfier = clf
    def start(self):
        assert self.tcp !=None ,"接入数据不能为空"
        assert self.classfier !=None, "分类器不能为空"
        while not self.done:
            data=self.tcp.getCur()
            if self.filter:
                data=self.filter.deal(data)
            data=np.expand_dims(data,axis=0)
            # if self.scaler:
            #     data=self.scaler.transform(data)
            self.res[0]=self.classfier.predict(data)
            np.roll(self.res,1,axis=0)
    def predictOnce(self):
        assert self.tcp !=None ,"接入数据不能为空"
        assert self.classfier !=None, "分类器不能为空"
        data=self.tcp.getCur(self.windows)
        # print(data.shape)
        if self.filter:
            data=self.filter.deal(data)
        data=np.expand_dims(data,axis=0)
        # if self.scaler:
        #     data=self.scaler.transform(data)
        print(data.shape)
        label=self.classfier.predict(data)[0]
        return label