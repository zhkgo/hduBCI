from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
import numpy as np
import pickle
from sklearn import svm
from sklearn.pipeline import Pipeline

'''
demo 文件。
关键点两个函数，
1.getClassName 应当返回所有自定义类的类名，如果存在报错说不认识这个类的时候可以加入
2.getModel 返回模型对象，可以在里面加载模型参数等等，模型对象需要有predict函数，输入原始数据(batch,C,T)，输出(batch,1)
3.模型可以自己进行封装，比如把原来不是predict的封装成带predict函数的类，加入预处理等等。
'''
def getClassName():
    return ['FlatFeature','BrainClass']
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
class BrainClass:
    def __init__(self):
        self.model=None
        self.scaler=getScaler()
        with open("models/svm.model","rb") as f:
            self.model=pickle.load(f)
        self.pipe=Pipeline(steps=[('scaler', self.scaler), ('svm', self.model)])
    def aug_train(self,train_x,train_y):
        train_x=self.scaler.fit_transform(train_x,train_y)
        self.model.fit(train_x,train_y)
        self.pipe=Pipeline(steps=[('scaler', self.scaler), ('svm', self.model)])
    def predict(self,test_x):
        return self.pipe.predict(test_x)

def getModel():
    return BrainClass()
