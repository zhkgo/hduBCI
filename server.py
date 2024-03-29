# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 15:40:45 2020
@author: zhkgo

尚未开发完成
wait for finish
"""
# from flask_socketio import SocketIO, emit

from werkzeug.utils import secure_filename
from flask import request, Flask, render_template
from threading import Lock
import threading
from bcifilter import BciFilter
from experiment import Experiment
from flask_socketio import SocketIO, emit
import numpy as np
from myresponse import success, fail
import importlib
import os
import traceback
from flask_cors import CORS

# Set this variable to "threading", "eventlet" or "gevent" to test the
# different async modes, or leave it set to None for the application to choose
# the best option based on installed packages.
async_mode = None
thread_lock = Lock()
app = Flask(__name__, static_url_path="")
app.config['JSON_AS_ASCII'] = False
app.config['SECRET_KEY'] = 'secret!'
CORS(app, supports_credentials=True)
app.debug = False  # 设置调试模式，生产模式的时候要关掉debug
socketio = SocketIO(app, async_mode=async_mode)
_thread = None  # 实验进行时的通讯线程
experiment = None


def WithThread(obj):
    """这是一个开启线程的装饰器"""

    def Threads(*args):
        t = threading.Thread(target=obj, args=args)
        t.start()

    return Threads


@app.route('/helloBrain')
def helloBrain():
    return render_template("helloBrain.html")


@app.route('/datashow')
def dataShow():
    return render_template("dataShow.html")


@app.route('/')
def index():
    return render_template("home.html")


@app.route("/opera")
def h2():
    return render_template("opera.html", async_mode=socketio.async_mode)


@app.route("/recoder")
def h3():
    return render_template("dataRecoder.html")


def background_task():
    global experiment
    while experiment.fitSessions > 0:
        socketio.sleep(0.1)
        res = experiment.trainThreadStep1()
        if res == "wait":
            continue
        if type(res) is str:
            print(res)
            socketio.emit('my_response', success({"finish": 1, "message": res}), namespace="/res")
            break
        socketio.emit('my_response', success({"finish": 0, "sessions": res[0], "trials": res[1]}), namespace="/res")
    if experiment.fitSessions > 0:
        res = experiment.trainThreadStep2()
        socketio.emit('my_response', success({"finish": 1, "message": res}), namespace="/res")
    while True:
        socketio.sleep(0.1)
        res = experiment.predictThread()
        if res == "wait":
            continue
        if type(res) is str:
            print(res)
            socketio.emit('my_response', success({"finish": 1, "message": res}), namespace="/res")
            break
        socketio.emit('my_response', success({"finish": 0, "predict": res[0], "true": res[1]}), namespace="/res")


@socketio.on('startexperiment', namespace='/res')
def connect():
    global experiment, _thread
    try:
        experiment.start()
        print("实验开始")
        # 此处可以添加socket端口，用于将结果发送到在其他终端的程序,建议设置全局变量，或者传输到background_task中
        with thread_lock:
            if _thread is None:
                _thread = socketio.start_background_task(target=background_task)
    except Exception as e:
        traceback.print_exc()
        emit('my_response', fail(str(e)), namespace="/res")
    emit('my_response', success(), namespace="/res")


# 创建实验
@app.route("/api/createExperiment")
def createExperiment():
    global experiment
    try:
        experiment = Experiment()
        sessions = int(request.args.get('sessions'))
        fitSessions = int(request.args.get("fitsessions"))
        trials = int(request.args.get('trials'))
        duration = int(request.args.get('duration'))
        interval = int(request.args.get('interval'))
        tmin = int(request.args.get('tmin'))
        tmax = int(request.args.get('tmax'))
        device = int(request.args.get('device'))
        experiment.setParameters(sessions, fitSessions, trials, duration, interval, tmin, tmax, device)
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success()


# 设置预处理器
@app.route("/api/createFilter")
def createFilter():
    global experiment
    if experiment is None:
        return fail("请先创建实验")
    low = 1
    high = 40
    sampleRateFrom = 300
    sampleRateTo = 1000
    try:
        low = float(request.args.get('low'))
        high = float(request.args.get('high'))
        sampleRateTo = int(request.args.get('sampleRate'))
        channels = eval(request.args.get('channels'))
        idxs = experiment.set_channel(channels)
        mfilter = BciFilter(low, high, sampleRateFrom, sampleRateTo, idxs)
        experiment.set_filter(mfilter)
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success()


# 创建TCP连接
@app.route("/api/createTcp")
def createTcp():
    global experiment
    if experiment is None:
        return fail("请先创建实验")
    try:
        host = request.args.get("host")
        port = request.args.get("port")
        tcpname = request.args.get("tcpname")
        if host is None:
            host = "127.0.0.1"  # 测试用 正常改成localhost
        if port is None:
            port = 8844
        if tcpname is None:
            tcpname = "dsi"
        else:
            port = int(port)
        TCPParser = experiment.getParse()
        tcp = TCPParser(host=host, port=port, name=tcpname)
        ch_nums = experiment.device_channels
        print("tcp ", tcp)
        tcp.create_batch(ch_nums)
        experiment.set_dataIn(tcp)
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success()


# 开始接收解析数据
@app.route("/api/startTcp")
def startTcp():
    global experiment
    if experiment is None:
        return fail("请先创建实验")
    try:
        experiment.start_tcp()
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success()


# 开始记录数据
@app.route("/api/startRecord")
def startRecord():
    global experiment
    if experiment is None:
        return fail("请先创建实验")
    try:
        experiment.startRecord()
    except Exception as e:
        print(e.with_traceback())
        return fail(str(e))
    return success()


# 停止记录数据
@app.route("/api/stopRecord")
def stopRecord():
    global experiment
    if experiment is None:
        return fail("请先创建实验")
    try:
        experiment.stopRecord()
    except Exception as e:
        print(e.with_traceback())
        return fail(str(e))
    return success()


# 停止TCP连接
@app.route("/api/stopTcp")
def stopTcp():
    global experiment
    if experiment is None:
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
    if experiment is None:
        return fail("请先创建实验")
    try:
        module = importlib.import_module("models.classfier")
        for name in module.getClassName():
            content = "globals()['" + name + "']=module." + name
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
        upload_path = os.path.join(basepath, 'models', secure_filename(f.filename))
        f.save(upload_path)
        # print(f.filename)
        return success({"filename": f.filename})
    return fail("必须使用post方法上传文件")


@app.route("/api/getResult")
def getResult():
    global experiment
    try:
        res = experiment.predictOnce()
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    return success({"result": int(res)})


@app.route("/api/saveData")
def savedata():
    global experiment
    experiment.saveData()
    return success()


# 返回每个人的平均脑电(仅支持双脑)
@app.route("/api/getdatamean")
def getDataMean():
    global experiment
    # print("TCP END WHEN GET DATA",experiment.tcp.end)
    try:
        timeend = int(request.args.get('timeend'))
        arr, rend = experiment.getData(timeend, windows=1000, tcpid=-1, median=True, normalize=True)
        # print(arr.tolist())
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    # TESTBEGIN
    # lchs=len(experiment.channels) #单机测试双脑 所以除以2 正常情况不除
    # TESTEND
    # arr1=arr[:lchs].mean(axis=0)
    # arr2=arr[lchs:].mean(axis=0)
    # ls=np.vstack([arr1, arr2]).tolist()
    # print(arr.shape)
    return success({"data": arr.tolist(), 'ch_names': ['S1', 'S2'], 'timeend': rend})


@app.route('/api/getdata')
def getdata():
    global experiment
    # print("TCP END WHEN GET DATA",experiment.tcp.end)
    try:
        timeend = int(request.args.get('timeend'))
        arr, rend = experiment.getData(timeend, show=True)
        # print(arr.tolist())
    except Exception as e:
        traceback.print_exc()
        return fail(str(e))
    # print("返回数据维度：", np.array(arr).shape)
    # print(np.array(arr).shape)
    # ['Fz','Cz','Pz','P3','P4','P7','P8','Oz','O1','O2','T7','T8']
    return success({"data": arr.tolist(), 'ch_names': experiment.channels, 'timeend': rend})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10086, debug=False)
    # http_serve=WSGIServer(("0.0.0.0",10086),app,handler_class=WebSocketHandler)
    # http_serve.serve_forever()
