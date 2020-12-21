# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 10:23:11 2020

@author: zhkgo
"""
from scipy import signal
from scipy.signal import butter
from scipy.signal import resample
class BciFilter:
    def __init__(self,low=1,high=40,sampleRate=1000,sampleRateTo=1000,idxs=[]):
        self.low=low
        self.high=high
        self.sampleRate=sampleRate
        self.sampleRateTo=sampleRateTo
        self.idxs=idxs
        # 8表示8阶
        nyq=self.sampleRate/2
        low=self.low/nyq
        high=self.high/nyq
        self.b,self.a=butter(4,[low,high],'bandpass')
        
    def deal(self,data):
        #先滤波后降采样
        data=data[self.idxs]
        data=signal.filtfilt(self.b,self.a,data)
        secs=data.shape[1]/self.sampleRate
        samps=int(secs*self.sampleRateTo)
        if samps>0:
            data=resample(data,samps,axis=1)
        # self.ch_names
        return data