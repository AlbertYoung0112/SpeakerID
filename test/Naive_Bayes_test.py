import sys
import os
lib_path = os.path.abspath(os.path.join(sys.path[0], '..'))
sys.path.append(lib_path)
from src.Classifier.Naive_Bayes_Classifier import *

'''
Prerequisite: Database should be built before running demo.
The training data cannot have multiple labels.
Please speak loudly in a quiet place when you build the database.
'''

foldername = '../DataSet/DataList_all.txt'

'''
This is the demo of naive bayes classifier which seems to be a little 
complex and you can choose three different Naive Bayes Classifier by changing 
the parameter 'Type'.
The statistic parameter of NB clf can be adjusted in the 'Naive_Bayes_Classifier'.
'''

Classifier = Naive_Bayes_Classifier(foldername)
Data, Label = Classifier.read_data(foldername, 'e', 25)
Classifier.train(Data, Label)
