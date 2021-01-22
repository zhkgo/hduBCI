# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 15:40:45 2020
@author: zhkgo

尚未开发完成
wait for finish
"""
# from flask_socketio import SocketIO, emit

from werkzeug.utils import secure_filename
from flask import request, Flask,render_template
from threading import Lock
import threading
from bcifilter import BciFilter
from experiment import Experiment
from flask_socketio import SocketIO, emit
import numpy as np
from parses.neuroscanParse import TCPParser
from myresponse import success,fail
import importlib
#from  gevent.pywsgi import WSGIServer
# from  geventwebsocket.websocket import WebSocket,WebSocketError
#from  geventwebsocket.handler import WebSocketHandler
import os
import traceback
from flask_cors import CORS
# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None
thread_lock = Lock()
app = Flask(__name__,static_url_path="")
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = 'secret!'
CORS(app, supports_credentials=True)
app.debug = False # 设置调试模式，生产模式的时候要关掉debug
socketio = SocketIO(app, async_mode=async_mode)
_thread=None #实验进行时的通讯线程
experiment = None


def WithThread(obj):
    """这是一个开启线程的装饰器"""
    def Threads(*args):
        t = threading.Thread(target=obj, args=args)
        t.start()

    return Threads

@app.route('/datashow')
def dataShow():
    return  render_template("dataShow.html")

@app.route('/')
def index():
    return render_template("home.html")

@app.route("/opera")
def h2():
    return render_template("opera.html",async_mode=socketio.async_mode)

def background_task():
    global experiment
    while experiment.fitSessions>0:
        socketio.sleep(0.1)
        res=experiment.trainThreadStep1()
        if res=="wait":
            continue
        if type(res) is str:
            print(res)
            socketio.emit('my_response',success({"finish":1,"message":res}))
            break
        socketio.emit('my_response',success({"finish":0,"sessions":res[0],"trials":res[1]}))
    if experiment.fitSessions>0:
        res=experiment.trainThreadStep2()
        socketio.emit('my_response',success({"finish":1,"message":res}))
    while True:
        socketio.sleep(0.1)
        res=experiment.predictThread()
        if res=="wait":
            continue
        if type(res) is str:
            print(res)
            socketio.emit('my_response',success({"finish":1,"message":res}))
            break
        socketio.emit('my_response',success({"finish":0,"predict":res[0],"true":res[1]}))

@socketio.event
def connect():
    global experiment,_thread
    try:
        experiment.start()
        print("实验开始")
        with thread_lock:
            if _thread is None:
                _thread = socketio.start_background_task(target=background_task)
    except Exception as e:
        traceback.print_exc()
        emit('my_response',fail(str(e)))
    emit('my_response', success())

#创建实验
@app.route("/api/createExperiment")
def createExperiment():
    global experiment
    try:    
        experiment=Experiment()
        sessions=int(request.args.get('sessions'))
        fitSessions=int(request.args.get("fitsessions"))
        trials=int(request.args.get('trials'))
        duration=int(request.args.get('duration'))
        interval=int(request.args.get('interval'))
        tmin=int(request.args.get('tmin'))
        tmax=int(request.args.get('tmax'))
        device=int(request.args.get('device'))
        experiment.setParameters(sessions,fitSessions,trials,duration,interval,tmin,tmax,device)
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success()

#设置预处理器
@app.route("/api/createFilter")
def createFilter():
    global experiment
    if experiment==None:
        return fail("请先创建实验")
    low=1
    high=40
    sampleRateFrom=1000
    sampleRateTo=1000
    try:
        low=float(request.args.get('low'))
        high=float(request.args.get('high'))
        sampleRateTo=int(request.args.get('sampleRate'))
        channels=eval(request.args.get('channels'))
        idxs=experiment.set_channel(channels)
        mfilter=BciFilter(low,high,sampleRateFrom,sampleRateTo,idxs)
        experiment.set_filter(mfilter)
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))

    return success()

#创建TCP连接
@app.route("/api/createTcp")
def createTcp():
    global experiment
    if experiment==None:
        return fail("请先创建实验")
    try:
        tcp=TCPParser(host='localhost', port=4000)
        ch_nums=experiment.device_channels
        print("tcp ",tcp)
        tcp.create_batch(ch_nums)
        experiment.set_dataIn(tcp)
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success()

#开始接收解析数据
@app.route("/api/startTcp")
def startTcp():
    global experiment
    if experiment==None:
        return fail("请先创建实验")
    try:
        experiment.start_tcp()
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success()


#停止TCP连接
@app.route("/api/stopTcp")
def stopTcp():
    global experiment
    if experiment==None:
        return fail("请先创建实验")
    try:
        experiment.stop_tcp()
    except Exception as e:
        print(e.with_traceback())
        return fail(str(e))
    return success()


@app.route("/api/createClassfier")
def createClassfier():
    global experiment
    if experiment==None:
        return fail("请先创建实验")
    try:
        module=importlib.import_module("models.classfier")
        for name in module.getClassName():
            content="globals()['"+name+"']=module."+name
            exec(content)
        experiment.set_classfier(module.getModel())
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success()

@app.route('/api/upload', methods=['POST', 'GET'])
def upload():
    if request.method == 'POST':
        f = request.files['file']
        basepath = os.path.dirname(__file__)
        upload_path = os.path.join(basepath, 'models',secure_filename(f.filename))
        f.save(upload_path)
        # print(f.filename)
        return success({"filename":f.filename})
    return fail("必须使用post方法上传文件")

@app.route("/api/getResult")
def getResult():
    global experiment
    try:
        res=experiment.predictOnce()
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success({"result":int(res)})

@app.route("/api/saveData")
def savedata():
    global experiment
    experiment.tcp.saveData()
    return success()

@app.route('/api/getdata')
def getdata():
    global experiment
    # print("TCP END WHEN GET DATA",experiment.tcp.end)
    try:
        timeend=int(request.args.get('timeend'))
        arr,rend=experiment.getData(timeend)
        # print(arr.tolist())
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    # print("返回数据维度：", np.array(arr).shape)
    # print(np.array(arr).shape)
    # ['Fz','Cz','Pz','P3','P4','P7','P8','Oz','O1','O2','T7','T8']
    return success({"data":arr.tolist(),'ch_names':experiment.channels,'timeend':rend})
    
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0',port=10086)
    #http_serve=WSGIServer(("0.0.0.0",10086),app,handler_class=WebSocketHandler)
    #http_serve.serve_forever()
    
