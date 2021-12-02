import pickle
import threading

import numpy as np
import socket
import time


class DSIDevice:
    EEG_buffer = []
    EEG_data = []
    counter = 0
    batch_size = 50
    channels = []
    # socket_ = object
    frequency = {}
    d = 0
    done = False

    def __init__(self, host, port,name):
        self.host = host
        self.data_log = b''
        self.port = port
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.end = 0


    # 刷新
    def reinit(self):
        self.done = False
        # self.data_log = b''
        # print(testnum)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self.crate_batch(self.ch_names, self.sampleRate)

    def saveData(self,name,startpos):
        ctime = time.strftime("%Y%m%d%H%M%S", time.localtime())
        savepathvalue = "data/" + name +ctime+ ".npy"
        np.save(savepathvalue, self.signals[:,startpos:self.end])

    def create_batch(self,_=1,__=1):
        self.signals = np.zeros((24, 3600000))

    def ascall_index(self, chr_):
        return int(chr_)

    def count_sum(self, data):
        sum_ = 0
        for i in data:
            sum_ += int(i)
        return sum_

    def decode_header(self, header):
        packet_start = header[:5]
        packet_type = int(header[5])
        packet_length = int(header[6]) + int(self.ascall_index(header[7]))
        # print(ascall_index(header[7]))
        packet_number = self.count_sum(header[8:12])
        # print('packet_start:',packet_start,'packet_type:',packet_type,'packet_length:',packet_length,'packet_number:',packet_number)
        return packet_type, packet_length

    def decode_event_pack(self, data):
        event_code = self.count_sum(data[:4])
        sending_note = self.count_sum(data[4:8])
        msg_length = self.count_sum(data[8:12])
        if event_code == 9:
            msg = {"channels": str(data[12:12 + msg_length])[2:-1].replace(" ", "").split(',')}
            if self.counter == 0:
                self.channels = msg
        elif event_code == 10:
            msg = {
                "mains frequency,sampling frequency": str(data[12:12 + msg_length])[2:-1].replace(" ", "").split(',')}
            self.frequency = msg
        else:
            msg = {'other': str(data[12:12 + msg_length])[2:-1]}
        # print('event_code:',event_code,'sending_note:',sending_note,'msg_length:',msg_length,'msg:')
        return msg_length, msg

    def remove_head_mistake(self, data):
        length_ = 0
        for i in data:
            if chr(i) != '@':
                length_ += 1
                continue
            else:
                break
        return length_

    def decode_EEG_sensor(self, data):
        ch_data = data[11:]
        eeg_data = []
        for i in range(0, len(ch_data), 4):
            # print(ch_data[i:i+4])
            a = ch_data[i:i + 4]
            eeg_data.append(a)
        eeg_data = np.array(eeg_data)
        eeg_data.dtype = np.float32
        # print('timestamp:',timestamp,'data_counter:',data_counter,'ADC_status:',ADC_status,'ch_data:',ch_data)
        return len(data), eeg_data

    def parse_data(self):
        # print("start recv")
        #startT=time.time()
        while not self.done:
        # for i in range(20):
            data = self.sock.recv(2048000)
            self.data_log += data
            # print(data)
            index = 0
            len_ = len(data)
            while 1:
                try:
                    length_ = self.remove_head_mistake(data[index:])
                    index += length_
                    packet_header = data[index:12 + index]
                    index += 12
                    packet_type, packet_length = self.decode_header(packet_header)
                    packet_data = data[index:index + packet_length]
                    if packet_type == 5:
                        msg_length, msg = self.decode_event_pack(packet_data)
                    elif packet_type == 1:
                        msg_length, msg = self.decode_EEG_sensor(packet_data)
                        self.signals[:,self.end:self.end+1] = np.array(msg[:24]).reshape(24,1)
                        self.end+=1
                        # print(self.end)
                    index += msg_length

                    # print(self.end,index)
                    # print(msg_length, msg, '\n ******************************')
                    if index>=len_:
                        break
                except Exception as e:
                    print(e)
                    break
            #print("当前经过时间%s"%(time.time()-startT))
            #print("TCP时间%s"%self.end)
            #print("采样率：",self.end//(time.time()-startT))



    def get_device_info(self):
        return self.channels,self.frequency

    def get_batch(self, startPos: int, maxlength=200):
        if startPos <= -1:
            startPos = self.end - maxlength
        rend = min(self.end, startPos + maxlength)
        arr = self.signals[:, startPos:rend]
        return arr, rend

    # def get_batch_data(self):
    #     if len(self.EEG_data)>self.counter+self.batch_size:
    #         EEG_batch_data = self.EEG_data[self.counter:self.counter+self.batch_size]
    #         self.counter+=self.batch_size
    #     else:
    #         EEG_batch_data = self.EEG_data[self.counter:]
    #         self.counter = self.EEG_data.shape[0]

        # return EEG_batch_data

    def close(self,savefile=True):
        self.done = True
        time.sleep(0.2)
        self.socket_.close()


# data = read_data('dsi.pkl')
#import time

#if __name__ == "__main__":
    # s = connect_socket("localhost", 8844)
    #dsi = DSIDevice("localhost", 8844, "dsi")
    #dsi.create_batch()
    #thread=threading.Thread(target=dsi.recv_data)
    #thread.start()
    #
    # time.sleep(5)
    # DSI_INFO = dsi.get_device_info()
    # print(DSI_INFO)
    # while 1:
    #     try:
    #         EEG_batch = dsi.get_batch(-1)
    #         print(len(EEG_batch),EEG_batch[0].shape)
    #         # print(EEG_batch)
    #     except Exception:
    #         print("结束！")
    #         break
    # dsi.close_device()
    #

