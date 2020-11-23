# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 15:40:45 2020
@author: zhkgo

尚未开发完成
wait for finish
"""

from flask import Flask,request
from flask import render_template
import json
from bcifilter import BciFilter
from experiment import Experiment
from parses.neuracleParse import TCPParser
app = Flask(__name__)

@app.route('/datashow')
def dataShow():
    return  render_template("dataShow.html")

@app.route('/')
def index():
    return render_template("index.html")

# @app.route('/api/stop')
# def stop():
#     global tcp,data_thread
#     tcp.done = True
#     tcp.close()
#     tcp=None
#     data_thread.join()
#     return  "ok"

# @app.route('/api/start')
# def start():
#     global data_thread,experiment
#     tcp = TCPParser('localhost', 8712)
#     tcp.crate_batch(['Fz' for i in range(32)])
#     data_thread = threading.Thread(target=tcp.parse_data)
#     data_thread.start()
#     return  "ok"

#创建实验
@app.route("/api/createExperiment")
def createExperiment():
    global experiment
    if experiment!=None:
        return "实验已存在，无需创建，或者请先删除"
    experiment=Experiment()
    return "ok"
#设置预处理器
@app.route("/api/createFilter")
def createFilter():
    global experiment
    if experiment==None:
        return "请先创建实验"
    low=1
    high=40
    sampleRateFrom=1000
    sampleRateTo=1000
    try:
        low=float(request.args.get('low'))
        high=float(request.args.get('high'))
        sampleRateTo=int(request.args.get('sampleRate'))
    except:
        return "error In get Parameters"
    mfilter=BciFilter(low,high,sampleRateFrom,sampleRateTo)
    experiment.set_filter(mfilter)
    return "ok"
#创建TCP连接
@app.route("/api/createTcp")
def createTcp():
    global experiment
    if experiment==None:
        return "请先创建实验"
    try:
        tcp=TCPParser('localhost', 8712)
        tcp.crate_batch(['Fz' for i in range(32)])
        # experiment.filter.sampleRate=experiment.tcp.sampleRate
        experiment.set_dataIn(tcp)
    except Exception as e:
        return str(e)
    return "ok"

#开始接收解析数据
@app.route("/api/startTcp")
def startTcp():
    global experiment
    if experiment==None:
        return "请先创建实验"
    try:
        experiment.start_tcp()
    except Exception as e:
        return str(e)
    return "ok"


#停止TCP连接
@app.route("/api/stopTcp")
def stopTcp():
    global experiment
    if experiment==None:
        return "请先创建实验"
    try:
        experiment.stop_tcp()
    except Exception as e:
        return str(e)
    return "ok"

#创建特征提取器
@app.route("/api/createScaler")
def createScaler():
    global experiment
    if experiment==None:
        return "请先创建实验"
    code_scaler=request.args.get("code")
    scope={}
    exec(code_scaler,scope)
    scaler=scope['scaler']
    experiment.set_scaler(scaler)
    return "ok"
#创建分类器
@app.route("/api/createClassfier")
def createClassfier():
    global experiment
    if experiment==None:
        return "请先创建实验"
    code_clf=request.args.get("code")
    scope={}
    exec(code_clf,scope)
    clf=scope['clf']
    experiment.set_classfier(clf)
    return "ok"

@app.route("/api/getResult")
def getResult():
    global experiment
    return experiment.predictOnce()

@app.route("/api/saveData")
def savedata():
    global experiment
    experiment.tcp.saveData()
    return "ok"

@app.route('/api/getdata')
def getdata():
    global experiment
    print("TCP END WHEN GET DATA",experiment.tcp.end)
    arr,timeend=experiment.tcp.get_batch(request.args.get('timeend'))
    # ['Fz','Cz','Pz','P3','P4','P7','P8','Oz','O1','O2','T7','T8']
    jsonarr=json.dumps({"data":arr.tolist(),'ch_names':experiment.tcp.ch_names,'timeend':timeend})
    return jsonarr
    
if __name__ == '__main__':
    app.debug = True # 设置调试模式，生产模式的时候要关掉debug
    experiment = None
    app.run(port=10086) 

