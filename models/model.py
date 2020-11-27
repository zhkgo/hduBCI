from sklearn import svm
import pickle
def getModel():
    model=None
    with open("data/model/svm.model","rb") as f:
        model=pickle.load(f)
    return model