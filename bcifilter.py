# -*- coding: utf-8 -*-
"""
Created on Sun Nov 22 10:23:11 2021

@author: zhkgo
"""
from scipy import signal
from scipy.signal import butter
import numpy as np
from scipy.signal import resample


class BciFilter:
    def __init__(self, low=1, high=40, sampleRate=1000, sampleRateTo=1000, idxs=[]):
        self.low = low
        self.high = high
        self.sampleRate = sampleRate
        self.sampleRateTo = sampleRateTo
        self.idxs = idxs
        # 8表示8阶
        nyq = self.sampleRate / 2
        low = self.low / nyq
        high = self.high / nyq
        self.b, self.a = butter(4, [low, high], 'bandpass')
        self.buffer = np.random.rand(len(self.idxs), 2048)

    def deal(self, data):
        # 先滤波后降采样
        data = data[self.idxs]
        data = signal.filtfilt(self.b, self.a, data)
        secs = data.shape[1] / self.sampleRate
        samps = int(secs * self.sampleRateTo)
        if samps > 0:
            data = resample(data, samps, axis=1)
        # self.ch_names
        return data

    def norm(self, data):
        minnum = np.min(data, axis=1).reshape(-1, 1)
        maxnum = np.max(data, axis=1).reshape(-1, 1)
        data = (data - minnum) / (maxnum - minnum)
        data[np.isinf(data)] = 0
        return data

    def dealforshow(self, data):
        data = data[self.idxs]
        shape = data.shape[1]
        if data.shape[1] < self.buffer.shape[1]:
            np.roll(self.buffer, -shape, axis=1)
            self.buffer[:, -shape:] = data
            data = self.buffer
        data = signal.filtfilt(self.b, self.a, data)
        secs = data.shape[1] / self.sampleRate
        samps = int(secs * self.sampleRateTo)
        if samps > 0:
            data = resample(data, samps, axis=1)
        data = self.norm(data)
        return data[:, -shape:]

