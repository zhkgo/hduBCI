# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 15:40:45 2020

@author: zhkgo
"""

import threading
from flask import Flask,request
from flask import render_template
import json
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
    app.run(port=10086) 

