# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 10:43:41 2020

@author: zhkgo
"""
import socket
import matplotlib.pyplot as plt
import threading
import numpy as np
import time

class TCPParser:  # The script contains one main class which handles Streamer data packet parsing.

    def __init__(self, host, port, name):
        self.host = host
        self.port = port
        self.data_log = b''
        self.name = name
        self.done = False
        # print(testnum)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.end=0
    def reinit(self):
        self.done = False
        # self.data_log = b''
        # print(testnum)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.crate_batch(self.ch_names,self.sampleRate)
    def close(self):
        self.done=True
        #先停200ms确保当前正在接受的数据解析完毕
        time.sleep(0.2)
        self.sock.close()
    def saveData(self):
        ctime=time.strftime("%Y%m%d%H%M%S",time.localtime())
        savepathlog="data/log"+ctime+".npy"
        savepathvalue="data/value"+ctime+".npy"
        np.save(savepathlog,self.data_log)
        np.save(savepathvalue,self.signals[:self.end])
        
    def create_batch(self, ch_names, sampleRate=1000):
        self.ch_names = ch_names
        self.sampleRate = sampleRate
        self.signals = np.zeros((len(ch_names), 3600000))
        self.buffer = b''
    #获取指定位置的数据 如果传入-1 或者过大的时间值，则返回最新的，
    #若存在滤波器，会在数据返回之前进行滤波
    #windows为长度 startpos为起点
    def get_batch(self,startPos:int,maxlength=200):
        if startPos<=-1 :
            startPos=self.end-maxlength
        rend=min(self.end,startPos+maxlength)
        arr=self.signals[:,startPos:rend]
        return arr,rend
    
    def bufferToSignal(self, size):
        batchbuffer = []
        tot = size * len(self.ch_names)
        for i in range(tot):
            batchbuffer.append(self.buffer[4 * i:4 * i + 4])
        batchbuffer = np.array(batchbuffer).reshape(len(self.ch_names), size)
        batchbuffer.dtype = np.float32
        # 存在可以优化的空间 通过预分配大容量signals 已优化
        # self.signals = np.hstack([self.signals, batchbuffer])
        self.signals[:,self.end:self.end+size]=batchbuffer
        self.end=self.end+size                
        # 更新buffer
        # print("-----Signals已更新-------END:",self.end)
        self.buffer = self.buffer[ 4* tot:]

        return 8 * tot
    def getCur(self,windows):
        myend=self.end
        return self.signals[:,myend-windows:myend]
    def parse_data(self):
        while not self.done:
            data = self.sock.recv(921600)
            self.data_log += data
            self.buffer += data
            # 4表示四个字节 一个单精度
            # 0.02表示拿到0.02秒的数据就更新signals
            # print("=======================receive Data===================")
            if len(self.buffer) > 4 * len(self.ch_names) * self.sampleRate * 0.02:
                # with open("getdata.txt","w") as f:
                #     f.write("here")
                # print("=======================parse Data===================")
                points = len(self.buffer) // (4 * len(self.ch_names))
                self.bufferToSignal(points)
                # time.sleep(5)
    def example_plot(self):

        data_thread = threading.Thread(target=self.parse_data)
        data_thread.start()

        refresh_rate = 0.03
        runtime = 0


        while True:  # runtime < duration/refresh_rate:
            self.signal_log = self.signals[:, self.end-500:self.end]
            # self.time_log = self.time_log[:,-1000:]
            plt.clf()
            try:
                plt.plot(self.signal_log[1])
            except:
                pass
            plt.xlabel('Timestamp')
            plt.ylabel('Peak-to-Peak uV')
            plt.title('Streamer TCP/IP EEG Sensor Data Output')
            plt.pause(refresh_rate)
            runtime += 1
        plt.show()

        self.done = True
        data_thread.join()
#tcp = TCPParser('localhost', 8712)
#tcp.crate_batch(['Fz' for i in range(32)])
#tcp.parse_data()