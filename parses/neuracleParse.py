# -*- coding: utf-8 -*-
"""
Created on Tue Nov 17 10:43:41 2020

@author: zhkgo
"""
import socket
import matplotlib.pyplot as plt
import threading
import numpy as np
class TCPParser:  # The script contains one main class which handles Streamer data packet parsing.

    def __init__(self, host, port):
        self.host = host
        self.port = port
        # self.data_log = b''
        self.done =False
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
        self.sock.close()
        
    def crate_batch(self, ch_names, sampleRate=1000):
        self.ch_names = ch_names
        self.sampleRate = sampleRate
        self.signals = np.zeros((len(ch_names), 3600000))
        self.buffer = b''
    def get_batch(self,times=2000):
        # with open("buffer.txt","w") as f:
        #     f.write(str(self.signals[:,-1000:]))
        # print("innerBatch",id(self.end))
        print("================= SELF-END:",self.end)
        print("----------------------")
        print(str(self.signals[:,self.end-times:self.end]))
        print("----------------------")
        return self.signals[:,self.end-times:self.end]
    def bufferToSignal(self, size):
        batchbuffer = []
        tot = size * len(self.ch_names)
        for i in range(tot):
            batchbuffer.append(self.buffer[4 * i:4 * i + 4])
        batchbuffer = np.array(batchbuffer).reshape(len(self.ch_names), size)
        batchbuffer.dtype = np.float32
        # 存在可以优化的空间 通过预分配大容量signals
        # self.signals = np.hstack([self.signals, batchbuffer])
        print(batchbuffer)
        self.signals[:,self.end:self.end+size]=batchbuffer
        self.end=self.end+size                
        # 更新buffer
        print(id(self.end))
        print("-----Signals已更新-------END:",self.end)
        print(str(self.signals[:,:self.end]))
        print("----------------------")
        self.buffer = self.buffer[4 * tot:]

        return 4 * tot

    def parse_data(self):
        while not self.done:
            data = self.sock.recv(921600)
            # self.data_log += data
            self.buffer += data
            # 4表示四个字节 一个单精度
            # 0.02表示拿到0.02秒的数据就更新signals
            print("=======================receive Data===================")
            if len(self.buffer) > 4 * len(self.ch_names) * self.sampleRate * 0.02:
                # with open("getdata.txt","w") as f:
                #     f.write("here")
                print("=======================parse Data===================")
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
