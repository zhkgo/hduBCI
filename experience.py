# -*- coding: utf-8 -*-
"""
Created on Sat Nov 21 20:41:30 2020

@author: zhkgo
"""
import numpy as np
class Experience:
    def __init__(self):
        self.tcp=None
        self.classfier=None
        self.scaler=None
        self.filter=None
        self.channels=None
        self.res=np.zeros((3600))
        # self.end=0
    def set_dataIn(self,tcp):
        self.tcp=tcp
    def set_filter(self,sfilter):
        self.filter=sfilter
    def set_channel(self,ch_names):
        self.channels=ch_names
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
        data=self.tcp.getCur()
        if self.filter:
            data=self.filter.deal(data)
        if self.scaler:
            data=self.scaler.transform(data)
        self.res[0]=self.classfier.predict(data)
        np.roll(self.res,1)
    