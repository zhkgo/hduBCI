# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 15:40:45 2020
@author: zhkgo

尚未开发完成
wait for finish
"""

from werkzeug.utils import secure_filename
from flask import request, Flask,render_template
from bcifilter import BciFilter
from experiment import Experiment
from parses.neuracleParse import TCPParser
from myresponse import success,fail
import importlib
import os
app = Flask(__name__)
@app.route('/datashow')
def dataShow():
    return  render_template("dataShow.html")

@app.route('/')
def index():
    return render_template("index.html")



#创建实验
@app.route("/api/createExperiment")
def createExperiment():
    global experiment
    if experiment!=None:
        return fail("实验已存在，无需创建，或者请先删除")
    try:    
        experiment=Experiment()
        sessions=int(request.args.get('sessions'))
        trials=int(request.args.get('trials'))
        duration=int(request.args.get('duration'))
        interval=int(request.args.get('interval'))
        tmin=int(request.args.get('tmin'))
        tmax=int(request.args.get('tmax'))
        device=int(request.args.get('device'))
        experiment.setParameters(sessions,trials,duration,interval,tmin,tmax,device)
    except Exception as e:
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
        return fail(str(e))

    return success()

#创建TCP连接
@app.route("/api/createTcp")
def createTcp():
    global experiment
    if experiment==None:
        return fail("请先创建实验")
    try:
        tcp=TCPParser('localhost', 8712)
        ch_nums=experiment.device_channels
        tcp.crate_batch(ch_nums)
        experiment.set_dataIn(tcp)
    except Exception as e:
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
    res=experiment.predictOnce()
    return success(res)

@app.route("/api/saveData")
def savedata():
    global experiment
    experiment.tcp.saveData()
    return success()

@app.route('/api/getdata')
def getdata():
    global experiment
    print("TCP END WHEN GET DATA",experiment.tcp.end)
    try:
        timeend=int(request.args.get('timeend'))
        arr,timeend=experiment.getData(timeend)
        # print(arr)
    except Exception as e:
        return fail(str(e))
    # ['Fz','Cz','Pz','P3','P4','P7','P8','Oz','O1','O2','T7','T8']
    return success({"data":arr.tolist(),'ch_names':experiment.tcp.ch_names,'timeend':timeend})
    
if __name__ == '__main__':
    app.debug = False # 设置调试模式，生产模式的时候要关掉debug
    experiment = None
    app.config['JSON_AS_ASCII'] = False
    app.run(port=10086) 

