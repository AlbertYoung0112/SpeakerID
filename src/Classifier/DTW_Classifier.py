import sys
import os
lib_path = os.path.abspath(os.path.join(sys.path[0], '..'))
sys.path.append(lib_path)
from src.PreProcessing import *
from src.VoiceDataSetBuilder import *
from src.FileLoader import *
import matplotlib.pyplot as plt
from sklearn.externals import joblib
from sklearn.model_selection import train_test_split
from numpy import *

class DTW_Classifier:
    '''
    This is the DTW_Classifier of different voice information.
    We try to utilized multiple methods to actualize the classification task
    and this is one of them.
    '''

    def __init__(self, DataListName, ModelListName = '../DataSet/ModelList_all.txt'):
        '''
        The type of classifier should be choosed.
        '''
        self.DataListName = DataListName
        self.ModelListName = ModelListName

    def read_data(self, DataListName):
        '''
        Load original data
        You can choose different output shape.
        :DataListName: The log.txt path
        '''
        eff_label_list = []
        eff_mfcc = []
        processer = PreProcessing(512, 128)
        wav_list, frame_list, mfcc_list, energy_list, zcr_list, endpoint_list, label_list = processer.process(DataListName)
        for i in range(len(mfcc_list)):
            temp = processer.effective_feature(mfcc_list[i], endpoint_list[i])
            if endpoint_list[i][1]-endpoint_list[i][0] != 0:
                eff_label_list.append(label_list[i])
                eff_mfcc.append(mfcc_list[i])
            else:
                continue
        return eff_mfcc, eff_label_list
    
    def load_target(self, ModelListName):
        '''
        Load model data
        this is the model data for classification
        :ModelListName: The Model_log.txt path
        '''
        eff_label_list = []
        eff_mfcc = []
        processer = PreProcessing(512, 128)
        wav_list, frame_list, mfcc_list, energy_list, zcr_list, endpoint_list, label_list = processer.process(ModelListName)
        for i in range(len(mfcc_list)):
            temp = processer.effective_feature(mfcc_list[i], endpoint_list[i])
            if endpoint_list[i][1]-endpoint_list[i][0] != 0:
                eff_label_list.append(label_list[i])
                eff_mfcc.append(mfcc_list[i])
            else:
                continue
        return eff_mfcc, eff_label_list
    
    def dtw(self, x, y):
        """
        Computes Dynamic Time Warping (DTW) of two sequences.
        :param array x: N1*M array
        :param array y: N2*M array
        :param func dist: distance used as cost measure
        Returns the minimum distance, the cost matrix, the accumulated cost matrix, and the wrap path.
        """
        assert len(x)
        assert len(y)
        r, c = len(x), len(y)
        D0 = zeros((r + 1, c + 1))
        D0[0, 1:] = inf
        D0[1:, 0] = inf
        D1 = D0[1:, 1:] # view
        for i in range(r):
            for j in range(c):
                D1[i, j] = linalg.norm(x[i] - y[j])
        C = D1.copy()
        for i in range(r):
            for j in range(c):
                D1[i, j] += min(D0[i, j], D0[i, j+1], D0[i+1, j])
        '''
        if len(x)==1:
            path = zeros(len(y)), range(len(y))
        elif len(y) == 1:
            path = range(len(x)), zeros(len(x))
        else:
            path = self._traceback(D0)
        '''
        return D1[-1, -1] / sum(D1.shape)
        #return D1[-1, -1] / sum(D1.shape), C, D1, path

    def _traceback(self, D):
        i, j = array(D.shape) - 2
        p, q = [i], [j]
        while ((i > 0) or (j > 0)):
            tb = argmin((D[i, j], D[i, j+1], D[i+1, j]))
            if (tb == 0):
                i -= 1
                j -= 1
            elif (tb == 1):
                i -= 1
            else: # (tb == 2):
                j -= 1
            p.insert(0, i)
            q.insert(0, j)
        return array(p), array(q)
        
    def classify(self, Data, target_list, target_label_list):
        '''
        Classify the voice data using DTW
        '''
        label = zeros(len(Data))
        for i in range(len(Data)):
            temp = self.dtw(Data[i],target_list[0])
            for j in range(len(target_list)):
                if temp > self.dtw(Data[i],target_list[j]):
                    temp = self.dtw(Data[i],target_list[j])
                    label[i] = target_label_list[j]
        return label
    
    def train(self, Data, Label):
        #TODO How to train a dtw classifier is unknown till now. We could come up with a idea
        #about how to select better models to optimize the performance of classifier.
        target_list, target_label_list = self.load_target(self.ModelListName)
        target_list = array(target_list)
        target_label_list = array(target_label_list)
        np.save("target_list.npy",target_list)
        np.save("target_label_list.npy", target_label_list)
    
    def apply(self, Data):
        '''
        Apply the classifier with given data.
        :Data: original data
        Returns the predicted labels of original data.
        '''
        target_list = np.load("target_list.npy")
        target_label_list = np.load("target_label_list.npy")
        label = self.classify(Data, target_list, target_label_list)
        return label

    def show_accuracy(self, y_pre, y_true):
        acc = 0
        for i in range(len(y_pre)):
            if y_pre[i] == int(y_true[i]):
                acc += 1
        acc = acc / len(y_pre)
        print("acc:", round(acc, 2))
