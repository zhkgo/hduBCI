# -*- coding: utf-8 -*-
"""
Created on Sat Nov 21 20:41:30 2020

@author: zhkgo
"""
import threading
import numpy as np
import time
class Experiment:
    def __init__(self):
        self.CHANNELS=[
            ['Fp1','Fp2','F3','F4','F7','F8','FC1','FC2','FC5','FC6','Cz','C3','C4','T7','T8','CP1','CP2','CP5','CP6','Pz','P3','P4','P7','P8','POz','PO3','PO4','PO5','PO6','Oz','O1','O2','ref'],#ref 参考电极
            ['FP1','FPZ','FP2','AF3','AF4','F7','F5','F3','F1','FZ','F2','F4','F6','F8','FT7','FC5','FC3','FC1','FCZ','FC2','FC4','FC6','FT8','T7','C5','C3','C1','CZ','C2','C4','C6','T8','M1','TP7','CP5','CP3','CP1','CPZ','CP2','CP4','CP6','TP8','M2','P7','P5','P3','P1','PZ','P2','P4','P6','P8','PO7','PO5','PO3','POZ','PO4','PO6','PO8','CB1','O1','OZ','O2','CB2'],
            ]
        self.tcps=[]
        self.classfier=None
        self.scaler=None
        self.filter=None
        self.channels=None
        self.res=np.zeros((7200,1))
        self.done=False
        self.tcpThread = []
        self.windows=1000

        #均值标准差用于修正波形显示
        self.means=None
        self.sigmas=None

        self.fitSessions=0
        self.startTimes=[] #实验开始时间 对于不同TCP连接 开始的点可能不同 单位ms
        self.sessions=0 #session数量 
        self.trials=0  #每个session的trial数量
        self.duration=0 #一个trail持续时间 单位ms
        self.interval=0 #session之间的间隔
        self.tmin=0 #截取时间起点（相比于trail开始的时间点 单位ms）
        self.tmax=0 #截取时间终点（相比于trail开始的时间点 单位ms）
        self.device=0  #device= 0 博瑞康 device=1 neuroscan 
        self.device_channels=[]
        self.events=[]
        self.fitEvents=[]
        self.trainData=[]
        self.labels=[]
        # self.end=0
    def finish(self):
        self.done=True
        self.stop_tcp()
    def start_tcp(self):
        assert len(self.tcps)>0,"请先初始化设置"
        self.tcpThread=[]
        for tcp in self.tcps:
            thred=threading.Thread(target=tcp.parse_data)
            thred.start()
            self.tcpThread.append(thred)
    def saveData(self):
        for tcp,startTime in zip(self.tcps,self.startTimes):
            tcp.saveData(startTime)
            print(tcp.name,end=':')
            print("TCP线程数据已保存")
    def stop_tcp(self):
        for tcp,thred,startTime in zip(self.tcps,self.tcpThread,self.startTimes):
            tcp.close()
            tcp.saveData(startTime)
            thred.join()
            print(tcp.name,end=':')
            print("TCP线程已成功关闭")
    def setParameters(self,sessions:int,fitSessions:int,trials:int,duration:int,interval:int,tmin:int,tmax:int,device:int):
        self.sessions=sessions
        self.trials=trials
        self.duration=duration
        self.interval=interval
        self.tmin=tmin
        self.tmax=tmax
        self.fitSessions=fitSessions
        cur=0
        
        for i in range(self.fitSessions):
            for j in range(self.trials):
                self.fitEvents.append(cur)
                cur+=self.duration
            cur+=self.interval

        for i in range(self.fitSessions,self.sessions):
            for j in range(self.trials):
                self.events.append(cur)
                cur+=self.duration
            cur+=self.interval
        self.device=device
        assert device<2,"设备编号应当小于2"
        self.device_channels=self.CHANNELS[self.device]
    #暂未重写 先留着 还没啥用处
    def restart_tcp(self):
        self.stop_tcp()
        for tcp in self.tcps:
            tcp.reinit()
        self.start_tcp( )

    def set_dataIn(self,tcp):
        self.tcps.append(tcp)
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
    #windows为长度 startpos为相对起点
    # 返回滤波后数据和数据截止时间点
    #数据格式为 channels*times
    # 如果tcpid=-1 则返回全部按通道叠加后的数据，否则返回对应通道的数据
    def getData(self,startpos:int,windows=1000,tcpid=0,median=False,normalize=False):
        assert len(self.tcps)>0,"请先设置TCP"
        if tcpid!=-1:
            data,rend=self.tcps[tcpid].get_batch(self.startTimes[tcpid]+startpos if startpos> -1 else -1, maxlength=windows)
            if self.filter:
                data = self.filter.deal(data)
            rend-=self.startTimes[tcpid]
            return data,int(rend)
        totdata = []
        totrend = 100000000
        minl=100000
        for tcp,startTime in zip(self.tcps,self.startTimes):
            data,rend= tcp.get_batch(startTime+startpos if startpos> -1 else -1, maxlength=windows)
            if self.filter:
                data = self.filter.deal(data)
            totdata.append(data)
            print("Experimrnt get rend:", rend)
            rend-=startTime
            totrend=min(totrend,rend) #对齐
            minl=min(minl,data.shape[1])
        # print(minl)
        for i in range(len(totdata)):
            totdata[i]=totdata[i][:,:minl]
            # print("totdata:",end='')
            # print(totdata[i].shape)
            if median:
                totdata[i]=np.median(totdata[i],axis=0,keepdims=True)
        totdata = np.concatenate(totdata,axis=0)
        if normalize:
            if self.means is None:
                self.means=np.mean(totdata,axis=1,keepdims=True)
            if self.sigmas is None:
                self.sigmas=np.std(totdata,axis=1,keepdims=True)
            totdata=(totdata-self.means)/self.sigmas
        print("Experimrnt return rend:", totrend)
        return totdata,int(totrend)

    def set_scaler(self,scaler):
        # assert hasattr(scaler,"fit"),"特征提取器不存在fit函数"
        assert hasattr(scaler,"fit_transform"),"特征提取器不存在fit_transform函数"
        assert hasattr(scaler,"transform"),"特征提取器不存在fit函数"
        self.scaler=scaler

    def set_classfier(self,clf):
        # assert hasattr(clf,'fit'),"分类器不存在fit函数"
        assert hasattr(clf, 'predict'),"分类器不存在predict函数"
        if self.fitSessions>0:
            assert hasattr(clf, 'aug_train'),"预训练参数不为0时必须包含增强训练(aug_train)函数"    
        self.classfier = clf
        try:
            self.labels=np.load("models/labels.npy")
            print("标签长度为：",len(self.labels))
        except:
            assert False,"模型加载完毕，未检测到标签"
    def startRecord(self):
        assert len(self.tcps)>0 ,"接入数据不能为空"
        self.startTimes=[]
        for tcp in self.tcps:
            self.startTimes.append(tcp.end)
    def stopRecord(self):
        self.finish()
        return "实验结束"
    def getMinEnd(self):
        minv=100000000
        for tcp,startTime in zip(self.tcps,self.startTimes):
            minv=min(minv,tcp.end-startTime)
        return minv

    def trainThreadStep1(self):
        fitslen=len(self.fitEvents)
        while self.i<fitslen:
            if self.fitEvents[self.i]+self.tmax<self.getMinEnd():
                sample,_=self.getData(self.fitEvents[self.i]+self.tmin,self.tmax-self.tmin)
                self.trainData.append(sample)
                self.i+=1
                # print("当前采集了%s条数据"%(self.i))
                # print(sample.shape)
                # print("数据维度为%s"%(sample.shape))
                return int((self.i-1)//self.trials+1),int((self.i-1)%self.trials+1)
            else:
                return "wait"
        return "预训练参数采集完毕,正在增量训练中"

    def trainThreadStep2(self):
        self.trainLabel=self.labels[:len(self.fitEvents)]
        self.classfier.aug_train(np.array(self.trainData), self.trainLabel)
        self.i=0
        return "增量训练完毕,即将开始测试"

    def predictThread(self):
        eventslen=len(self.events)
        fitslen=len(self.fitEvents)
        lenlabels=len(self.labels)
        # eeendtime=time.time()
        # print("当前经过时间",eeendtime-self.startTTT)
        # print("数据段游标移动",self.tcp.end-self.startTime)
        while self.i<eventslen:
            if self.events[self.i]+self.tmax<self.getMinEnd():
                self.res[self.i]=self.predictOnce(self.events[self.i]+self.tmin,self.tmax-self.tmin)
                # np.roll(self.res,1,axis=0)
                self.i+=1
                return int(self.res[self.i-1]),int(self.labels[self.i-1+fitslen]) if lenlabels>self.i-1+fitslen else "未给出"
            else:
                return "wait"
        self.finish()#结束实验 保存数据
        return "实验结束"
    
    def start(self):
        assert len(self.tcps)>0 ,"接入数据不能为空"
        assert self.classfier !=None, "分类器不能为空"
        self.startTimes=[]
        for tcp in self.tcps:
            self.startTimes.append(tcp.end)
        self.startTTT=time.time()
        self.i=0
        
    def predictOnce(self,startpos=-1,windows=1000):
        assert len(self.tcps)>0,"接入数据不能为空"
        assert self.classfier !=None, "分类器不能为空"
        data,_=self.getData(startpos,windows=windows,tcpid=-1)
        data=np.expand_dims(data,axis=0)
        label=self.classfier.predict(data)[0]
        return label