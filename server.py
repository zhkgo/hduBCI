# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 15:40:45 2020

@author: zhkgo
"""

import threading
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

@app.route('/api/stop')
def stop():
    global tcp,data_thread
    tcp.close()
    tcp=None
    data_thread.join()
    return  "ok"

@app.route('/api/start')
def start():
    global tcp,data_thread
    tcp = TCPParser('localhost', 8712)
    tcp.crate_batch(['Fz' for i in range(32)])
    data_thread = threading.Thread(target=tcp.parse_data)
    data_thread.start()
    # tcp.reinit()
    return  "ok"
@app.route("/api/createExperiment")
def createExperiment():
    global experiment
    if experiment!=None:
        return "实验已存在，无需创建，或者请先删除"
    experiment=Experiment()
@app.route("/api/createFilter")
def createFilter():
    if experiment==None:
        return "请先创建实验"
    low=1
    high=40
    sampleRateTo=1000
    try:
        low=float(request.args.get('low'))
        high=float(request.args.get('high'))
        sampleRateTo=int(request.args.get('sampleRate'))
    except:
        return "error In get Parameters"
    mfilter=BciFilter(low,high,tcp.sampleRate,sampleRateTo)
    experiment.set_filter(mfilter)
    return "ok"
@app.route("api/createScaler")
def createScaler():
    if experiment==None:
        return "请先创建实验"
    code_scaler=request.args.get("code")
    scope={}
    exec(code_scaler,scope)
    scaler=scope['scaler']
    experiment.set_scaler(scaler)
    return "ok"

@app.route("api/createClassfier")
def createClassfier():
    if experiment==None:
        return "请先创建实验"
    code_clf=request.args.get("code")
    scope={}
    exec(code_clf,scope)
    clf=scope['clf']
    experiment.set_classfier(clf)
    return "ok"

@app.route("/api/saveData")
def savedata():
    global tcp
    tcp.saveData()
    return "ok"

@app.route('/api/getdata')
def getdata():
    global tcp
    print("TCP END WHEN GET DATA",tcp.end)
    arr,timeend=tcp.get_batch(request.args.get('timeend'))
    # ['Fz','Cz','Pz','P3','P4','P7','P8','Oz','O1','O2','T7','T8']
    jsonarr=json.dumps({"data":arr.tolist(),'ch_names':tcp.ch_names,'timeend':timeend})
    return jsonarr
    
if __name__ == '__main__':
    app.debug = True # 设置调试模式，生产模式的时候要关掉debug
    tcp = None
    experiment = None
    app.run(port=10086) 

