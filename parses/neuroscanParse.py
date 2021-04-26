import socket
import numpy as np
import socket
import pickle
import time
from datetime import datetime
from threading import Timer
from threading import Thread
import threading
from scipy.io import savemat
from flask_socketio import SocketIO, emit
from myresponse import success,fail
import scipy.io as scio

# 线程通信
global fos_flag
fos_flag = 0

# 兼容了两台不同的neuroscan
# 可以发送消息给计算机视觉模块
class TCPParser(Thread):
    def __init__(self, name="neuroscan", host="127.0.0.1", port=4000, save_data=False, save_len=9000000):  # 可以通过初始化来传递参数
        super(TCPParser, self).__init__()
        self.tcp_status = False    # Tcp是否连接
        self.data_status = False   # Neuroscan是否有数据传输
        self.buffer_ing = False    # 是否创建了buffer
        self.name = name
        self.host = host
        self.port = port
        self.save_data = save_data
        # 初始化发送数据包，CTRL 3 5表示请求获取Header，CTRL 3 3表示请求获取数据
        pack = [[67], [84], [82], [76], [0], [3], [0], [5], [0], [0], [0], [0]]
        self.packet = np.array(pack).astype(np.uint8)
        self.soc = socket.socket()
        self.basic_info_len = 0
        self.resolution = 0
        self.data_channels = 0
        self.event_channels = 0
        self.channels = 0
        self.basic_samples = 0   # 单条数据采样点数量
        self.basic_srate = 0
        self.data_len = 0
        self.event_msg = []
        self.half_save = save_len
        self.save_path = 'E:\\xsw_space\\data\\'
        self.save_filename = 'neuroscan_data'
        self.global_buffer = np.zeros((self.half_save * 2, 64)).astype(np.float32)   # 只存储64通道数据
        self.global_events = np.zeros((self.half_save * 2)).astype(np.float32)
        self.event_chan = 41   # 事件通道
        self.save_fos = 1   # 文件保存的命名
        self.end = 0
        self.channel_names = ['FP1', 'FPZ', 'FP2', 'AF3', 'AF4', 'F7', 'F5', 'F3', 'F1', 'FZ', 'F2', 'F4', 'F6', 'F8',
                              'FT7', 'FC5', 'FC3', 'FC1', 'FCZ', 'FC2', 'FC4', 'FC6', 'FT8', 'T7', 'C5', 'C3', 'C1',
                              'CZ', 'C2', 'C4', 'C6', 'T8', 'M1', 'TP7', 'CP5', 'CP3', 'CP1', 'CPZ', 'CP2', 'CP4', 'CP6',
                              'TP8', 'M2', 'P7', 'P5', 'P3', 'P1', 'PZ', 'P2', 'P4', 'P6', 'P8', 'PO7', 'PO5', 'PO3',
                              'POZ', 'PO4', 'PO6', 'PO8', 'CB1', 'O1', 'OZ', 'O2', 'CB2']
        self.connect_server()  # 创建TCP连接
        self.tcp_client = None
        self.tcp_end = 0
        self.concurrent = True  # 避免tcp_end还没到最后，但是end已经回到了零点
        self.reset_end = 190000  # RSVP范式重置游标
        self.session_end = 160000  # RSVP范式中每个session对应的时间戳
        self.rest_time = False   # RSVP中间的休息时间

    def set_save_params(self, path='./data', filename='neuroscan_data'):
        self.save_path = path
        self.save_filename = filename

    def set_save_len(self, len):
        self.half_save = len  # 重新设定buffer长度并初始化
        self.global_buffer = np.zeros((self.half_save * 2, 68)).astype(np.float32)
        self.global_events = np.zeros((self.half_save * 2, 1)).astype(np.float32)
        self.end = 0
        self.save_fos = 1

    def get_channels_name(self):
        return self.channel_names

    def parse_header(self, msg):
        if len(msg) != 12:
            print("Data头部解析有误，请检查连接是否断开！")
            return None
        header_id = msg[0:4]  # id: CTRL/FILE/DATA
        header_code = np.array(msg[4:6])
        header_code.dtype = '>i2'  # code: 1(General),2(Server),3(Client)
        header_req = np.array(msg[6:8])
        header_req.dtype = '>i2'  #
        header_size = np.array((msg[8:12]))
        header_size.dtype = '>i4'  # bodySize: self.data_len
        return header_id, header_code, header_req, header_size

    def parse_basic_info(self, msg):
        basic_size = np.array(msg[0:4])
        basic_size.dtype = '<i4'
        if basic_size != self.basic_info_len:
            print("basicInfo长度不匹配，basicInfo解析失败")
            return
        self.data_channels = np.array(msg[4:8])
        self.data_channels.dtype = '<i4'
        self.event_channels = np.array(msg[8:12])
        self.event_channels.dtype = '<i4'
        self.basic_samples = np.array(msg[12:16])
        self.basic_samples.dtype = '<i4'
        self.basic_srate = np.array(msg[16:20])
        self.basic_srate.dtype = '<i4'
        basic_bytes = np.array(msg[20:24])
        basic_bytes.dtype = '<i4'
        self.resolution = np.array(msg[24:28])
        self.resolution.dtype = np.float32
        self.channels = self.data_channels + self.event_channels
        self.data_len = int(self.channels * self.basic_samples * basic_bytes)
        print(f"待接收数据信息：脑电信号通道数为{self.data_channels}，事件信号通道数为{self.event_channels}，"
              f"采样点数量为{self.basic_samples}，采样率为{self.basic_srate}，单个样本字节数为{basic_bytes}")

    def reinit(self):   # debug
        self.tcp_status = False
        self.data_status = False
        self.buffer_ing = False
        self.end = 0
        self.save_fos = 1
        self.soc = socket.socket()
        self.connect_server()
        self.parse_data()

    def close(self):
        self.tcp_status = False
        self.data_status = False
        time.sleep(0.1)
        self.soc.close()
        print("TCP 连接已断开！")

    def connect_server(self):
        print(f"准备开启{self.name}")
        self.soc.connect((self.host, self.port))
        print(f"{self.host}:{self.port} 连接成功")
        self.packet[7,] = 5
        self.soc.sendto(self.packet, (self.host, self.port))
        recv_data = self.soc.recv(40000)
        neuro_id, code, req, self.basic_info_len = self.parse_header(recv_data)
        if neuro_id == b'DATA' and code == 1 and req == 3:
            print(f"basicInfo接收成功，长度为{self.basic_info_len}")
        else:
            print("未正确接收到basicInfo信息！")
        # 请求获取数据，修改request_code
        self.packet[7, ] = 3
        self.soc.sendto(self.packet, (self.host, self.port))
        recv_data = self.soc.recv(self.basic_info_len)
        self.parse_basic_info(recv_data)
        self.tcp_status = True

    def create_batch(self,chnames):
        pass

    # def startTcp(self):
    #     if self.tcp_status is False:
    #         print("TCP 尚未建立连接，Buffer建立失败！")
    #         return False
    #     if self.data_status is False:
    #         print("Neuroscan 尚未开始采集数据，请点击Neuroscan数据采集按钮，并重新构建Buffer！")
    #         return False
    #     print(f"开始创建Buffer ...")
    #     self.buffer_ing = True

    def parse_data(self):
        iter_num = 1
        debug_num = 1
        global fos_flag
        if self.tcp_status is False:
            print("TCP 尚未建立连接，Buffer建立失败！")
            return
        recv_data = self.soc.recv(40000)   # 如果还没打开数据采集按钮，这在这里阻塞，采集后唤醒
        neuro_id, code, req, _ = self.parse_header(recv_data)
        if neuro_id == b'CTRL' and code == 2 and req == 1:
            print("Neuroscan 服务器已经开始传输数据，等待实验开始 ...")
            self.data_status = True
        else:
            print("数据传输控制代码错误，重启下试试...")
        # recv_data = self.soc.recv(40000)  # 需要接收两次，第二次就不解析了
        next_data_len = self.data_len   # 下一次需要获取的数据段的长度
        while self.buffer_ing is False:  # 阻塞
            if debug_num % 2 == 1: recv_len = 12
            # else: recv_len = self.data_len  # 固定的40ms的数据，69*40
            else: recv_len = next_data_len  # 固定的40ms的数据，69*40
            recv_data = self.soc.recv(recv_len)
            if debug_num % 2 == 1:  # 解析头部
                neuro_id, code, req, header_length = self.parse_header(recv_data)
                # print(f"输出当前的头信息：{neuro_id}, {code}, {req}, {header_length}")
                if neuro_id == b"DATA" and code == 2 and req == 2: pass
                elif neuro_id == b"CTRL" and code == 2 and req == 2:
                    print("Neuroscan 服务端已关闭了数据接收，进程关闭。")
                    return
                elif neuro_id == b"CTRL" and code == 2 and req == 1:
                    debug_num -= 1  # 继续接收头部，说明下一条不是数据
                else:
                    print(f"阻塞时头部解析失败！{neuro_id}, {code}, {req}")
                    return
            else:
                # 数据段判断是否取完
                bytes_len = len(recv_data)
                if bytes_len == next_data_len:
                    next_data_len = self.data_len
                else:
                    next_data_len -= bytes_len
                    debug_num -= 1
            debug_num += 1
            if debug_num == 11:
                self.buffer_ing = True
                break

        if debug_num % 2 == 0:   # 额外处理头部，从第一个非0的数据部开始处理，再之前会出现前半部分为0的情况
            next_data_len = self.data_len
            # 避免一次性没取完，进行兼容
            while next_data_len > 0:
                iter_num = 3
                recv_data = self.soc.recv(next_data_len)
                if next_data_len == self.data_len:   # 多次获取数据段的第一次
                    recv_extra_data = recv_data
                else:
                    recv_extra_data += recv_data
                next_data_len -= len(recv_data)
            neuro_data = np.array([recv_extra_data[i:i + 4] for i in range(0, self.data_len, 4)])
            neuro_data.dtype = '<i4'
            neuro_data = neuro_data.reshape((self.basic_samples, self.channels))
            events = neuro_data[:, self.event_chan]
            neuro_data = np.delete(neuro_data, self.event_chan, axis=1)
            print("提前的数据部维度：", neuro_data.shape)
            target_mat = neuro_data * self.resolution
            self.global_buffer[self.end: self.end + self.basic_samples, :] = target_mat[:, :64]
            self.global_events[self.end: self.end + self.basic_samples] = events
            self.end += self.basic_samples

        print("开始存储数据，当前时间点：", time.time())
        while self.data_status:
            if iter_num % 2 == 1: recv_len = 12
            else: recv_len = self.data_len  # 固定的40ms的数据，69*40
            if iter_num % 2 == 1:   # 解析头部
                recv_data = self.soc.recv(recv_len)
                neuro_id, code, req, header_length = self.parse_header(recv_data)
                # print(f"Acquire Neuroscan 32-bit Raw Data, length = {header_length}")
                if neuro_id == b"DATA" and code == 2 and req == 2: pass
                elif neuro_id == b"CTRL" and code == 2 and req == 2:
                    print("Neuroscan 服务端已关闭了数据接收，进程关闭。")
                    break
                else:
                    print(f"数据头部接收错误！接收数据长度为{len(recv_data)}，接收数据为\n{recv_data}")
                    break
            else:  # 解析数据部
                # print("收到数据~")
                while recv_len > 0:
                    recv_data = self.soc.recv(recv_len)
                    if recv_len == self.data_len:
                        recv_real_data = recv_data
                    else:
                        recv_real_data += recv_data
                    recv_len -= len(recv_data)
                neuro_data = np.array([recv_real_data[i:i + 4] for i in range(0, self.data_len, 4)])
                neuro_data.dtype = '<i4'
                neuro_data = neuro_data.reshape((self.basic_samples, self.channels))
                # print(self.name, "数据部维度：", neuro_data.shape, "，当前长度：", self.end)
                # 提取事件，删除对应列
                # data是把4个int8合并成一个int32，而event只取第一个int8作为事件标记
                # 在这里取的是int32，需要验证前24位是否全为0，全为0则正确
                events = neuro_data[:, self.event_chan]    # (40, 1)
                neuro_data = np.delete(neuro_data, self.event_chan, axis=1)
                target_mat = neuro_data * self.resolution
                # 数据buffer
                self.global_buffer[self.end: self.end + self.basic_samples, :] = target_mat[:, :64]
                # 事件buffer
                self.global_events[self.end: self.end + self.basic_samples] = events
                self.end += self.basic_samples
                # 通过均值来判断同步的延迟
                # mean_t = np.mean(target_mat[:, 39])
                # if mean_t < 0: print("normal")
                # else: print("test")
                if self.end >= self.reset_end:   # RSVP范式，一个session结束后重置游标，新数据覆盖前一段即可
                    self.end = 0
                    self.rest_time = False
                if self.rest_time is False and self.end >= self.session_end:
                    self.rest_time = True
                    fos_flag = 1
                # 循环队列优化数组申请过大问题
                if self.end == self.half_save * 2:  # 循环队列到达末尾
                    self.end = 0
                    self.concurrent = False
                if self.save_data and (self.end == self.half_save or self.end == 0):  # 保存前半段
                    sa = threading.Thread(target=self.save_mat, args=())
                    sa.start()
            iter_num += 1

    def get_batch(self, start_fos, maxlength):
        if start_fos <= -1:
            start_fos = self.end - maxlength
        rend = min(self.end, start_fos + maxlength)
        eeg_data = self.global_buffer[start_fos:rend, :]
        print(eeg_data.shape)
        return eeg_data.T, int(rend)

    def get_buffer_fos(self):
        return self.end

    # 由于使用了循环队列实现Buffer，因此无法在过程中主动保存，只能选择是否保存全部信号
    # 保存的信号按照编号保存到本地文件中
    def save_mat(self):
        print(f"开始保存第{self.save_fos}段数据至mat格式文件中...")
        if self.end == self.half_save:
            savemat(self.save_path + self.filename + '_'+str(self.save_fos)+'.mat',
                    {'dat': self.global_buffer[: self.half_save], 'event': self.global_events[: self.half_save]})
        else:
            savemat(self.save_path + self.filename + '_' + str(self.save_fos) + '.mat',
                    {'dat': self.global_buffer[self.half_save:], 'event': self.global_events[self.half_save:]})
        print(f"第{self.save_fos}段数据保存完成！")
        self.save_fos += 1

    def run(self):
        self.parse_data()

    def message_queue(self):
        self.tcp_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_client.connect(('10.1.25.56', 9000))
        self.tcp_end = 0
        while True:
            if self.tcp_end + 1000 > self.end and self.concurrent:
                time.sleep(0.5)
            else:
                send_data = self.global_buffer[self.tcp_end: self.tcp_end + 1000, :]
                self.tcp_client.send(pickle.dumps(send_data))
                self.tcp_end += 1000
                if self.tcp_end == self.half_save * 2:
                    self.tcp_end = 0
                if not self.concurrent:
                    self.concurrent = True
                print("当前游标：", self.end)
        tcp_client.close()


# if __name__ == '__main__':
#     thread_acquire = TCPParser("第一个Scan", host="10.1.25.96")  # 局域网10.1.25.42
#     thread_acquire.start()
#
#     # thread_acquire1 = TCPParser("第二个Scan", host="10.1.25.96")  # 10.1.25.42
#     # thread_acquire1.start()
#
#     while True:
#         line = input()
#         if line == "7":
#             break
#     thread_acquire.startTcp()
#     # thread_acquire1.startTcp()
#     # thread_acquire.message_queue()
#     print("数据开始传输")
#     start_t = time.time()
#     # time.sleep(3)
#     thread_acquire.get_batch(-1, 1000)
    # while True:
    #     time.sleep(0.5)
    #     if fos_flag == 1 and thread_acquire.get_buffer_fos() >= 160000 and thread_acquire1.get_buffer_fos() >= 160000:
    #         fos_flag = 0
    #         # 获取两个线程对应的数据并进行预测处理，同时把预测的结果发送给计算机视觉
    #         print("模拟数据通信，时差", time.time()-start_t)
    #         start_t = time.time()

    # eegs = thread_acquire.get_batch(38, 1000)
    # chans = thread_acquire.get_channels_name()
    # print(eegs.shape)
    # for i in range(10, 14):
    #     print(chans[i], " : ", eegs[i, 50:60])
    # time.sleep(8)
    # thread_acquire.close()
