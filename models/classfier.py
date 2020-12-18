from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
import numpy as np
import pickle
from sklearn import svm
from sklearn.pipeline import Pipeline

def getClassName():
    return ['FlatFeature']
class FlatFeature:
    def __init__(self,ch_nums=16,types="stand"):
        book={"minmax":MinMaxScaler,"stand":StandardScaler}
        self.ch_nums=ch_nums
        if types == None:
            self.scaler = None
        else:
            self.scaler=book[types]()
    def transform(self,data):
        res=np.array(data).reshape(data.shape[0],-1)
        if self.scaler == None:
            return res
        return self.scaler.transform(res)
    def fit_transform(self,data,label):
        res=np.array(data).reshape(data.shape[0],-1)
        if self.scaler is not None:
            return self.scaler.fit_transform(res)
        return res
def getScaler():
    scaler=None
    with open("models/ff.scaler","rb") as f:
        scaler=pickle.load(f)
    return scaler
def getModel():
    model=None
    with open("models/svm.model","rb") as f:
        model=pickle.load(f)
    pipe=Pipeline(steps=[('scaler', getScaler()), ('svm', model)])
    return pipe