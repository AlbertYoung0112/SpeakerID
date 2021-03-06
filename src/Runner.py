import os
import sys
lib_path = os.path.abspath(os.path.join(sys.path[0], '..'))
sys.path.append(lib_path)
from src.Classifier import Classifier
from src.PreProcessing import PreProcessing
import numpy as np
import matplotlib.pyplot as plt
import time
from multiprocessing import Queue

classifier_classes = Classifier.classifier_dict()
abspath = os.path.abspath(sys.path[0])
CONFIG = {
    'frame size': 512,
    'overlap': 128,
    'sample rate': 44100,
    'is training': True,
    'is streaming': True,
    'continuous stream': False,
    'data list': '../DataSet/DataList_all.txt',
    'classifier': ['SVM', 'KNN'],
    'argumentation': True,
    'debug tool': False,
    'error stat': False
}

frame_count = np.zeros((101,))
print(frame_count.shape, frame_count)


def main():
    preprocessor = PreProcessing(frame_size=CONFIG['frame size'],
                                 overlap=CONFIG['overlap'])
    if CONFIG['debug tool']:
        plt.figure(1)
        plt.figure(2)
        plt.ion()
        plt.show()
    if CONFIG['is streaming']:
        try:
            if not CONFIG['continuous stream']:
                preprocessor_proc, queue_dict = preprocessor.process_stream()
                preprocessor_proc.start()
                preprocessor.recorder.start_streaming()
                result_stat = {}
                while True:
                    ep = queue_dict['endpoint'].get(True)
                    effective_mfcc = queue_dict['mfcc'].get(True)
                    if CONFIG['debug tool']:
                        wav = queue_dict['wave'].get(True)
                        plt.clf()
                        plt.subplot(221)
                        plt.plot(wav)
                        plt.title('Input Wave')
                        plt.axvline(ep[0] * (CONFIG['frame size'] - CONFIG['overlap']), color='r')
                        plt.axvline(ep[1] * (CONFIG['frame size'] - CONFIG['overlap']), color='r')
                        plt.subplot(222)
                        plt.title("MFCC")
                        plt.imshow(effective_mfcc)
                        plt.subplot(223)
                        plt.title('ZCR')
                        zcr = queue_dict['zcr'].get(True)
                        plt.plot(zcr)
                        plt.axvline(ep[0], color='r')
                        plt.axvline(ep[1], color='r')
                        plt.subplot(224)
                        plt.title('Energy')
                        energy = queue_dict['energy'].get(True)
                        plt.plot(energy)
                        plt.axvline(ep[0], color='r')
                        plt.axvline(ep[1], color='r')
                        plt.draw()
                        plt.pause(0.001)
                    #effective_feature = preprocessor.effective_feature(zcr, ep)
                    #effective_mfcc = preprocessor.effective_feature(mfcc, ep)
                    print("LENGTH:",
                          round(effective_mfcc.shape[0] *
                          (CONFIG['frame size'] - CONFIG['overlap']) / CONFIG['sample rate'] * 1000, 1),
                          'ms')
                    if len(effective_mfcc) == 0:
                        continue
                    effective_mfcc = effective_mfcc.reshape((1, -1))
                    if(effective_mfcc.shape[1] >= 1092):
                        effective_mfcc = effective_mfcc[:, :1092]
                    else:
                        effective_mfcc = np.concatenate((effective_mfcc, np.zeros((1, 1092 - effective_mfcc.shape[1]))), axis=1)
                    result = {}
                    for classifier_name, classifier_class in classifier_classes.items():
                        if 'all' in CONFIG['classifier'] or classifier_name in CONFIG['classifier']:
                            classifier = classifier_class(None)
                            dataIn = np.concatenate((effective_mfcc,
                                                     np.concatenate((effective_mfcc[:, :741], np.zeros((effective_mfcc.shape[0], 351))), axis=1),
                                                     np.concatenate((np.zeros((effective_mfcc.shape[0], 351)), effective_mfcc[:, 351:]), axis=1),
                                                     ), axis=0)
                            raw_res = classifier.apply(dataIn)
                            res = list(map(int, raw_res))
                            res = np.argmax(np.bincount(res))
                            if res == 4:
                                print(raw_res)
                            result[classifier_name] = res
                            print(classifier_name, res)
                    if CONFIG['error stat']:
                        actual_label = 'a'
                        while not actual_label.isdigit():
                            actual_label = input('What does the fox say?')
                            if actual_label == '-':
                                actual_label = '10'
                        actual_label = int(actual_label)
                        for classifier_name, res in result.items():
                            if 'all' in CONFIG['classifier'] or classifier_name in CONFIG['classifier']:
                                if classifier_name not in result_stat.keys():
                                    result_stat[classifier_name] = np.zeros((10, 11))
                                result_stat[classifier_name][res, actual_label] += 1
                        while not queue_dict['endpoint'].empty():
                            queue_dict['endpoint'].get(False)
                            queue_dict['mfcc'].get(False)
            else:
                preprocessor_proc, queue_dict = preprocessor.process_continuous_stream()
                preprocessor_proc.start()
                preprocessor.recorder.start_streaming()
                result_stat = {}
                mfcc_buffer = np.zeros((1, 1092))
                frame_cnt = 0
                res_list = {"KNN": [], "SVM": [], "naive_bayes": [], "random_forest": [], "Decision_Tree": []}
                res_filt = {"KNN": [], "SVM": [], "naive_bayes": [], "random_forest": [], "Decision_Tree": []}
                res_percent = {"KNN": [], "SVM": [], "naive_bayes": [], "random_forest": [], "Decision_Tree": []}
                while True:
                    mfcc = queue_dict['mfcc'].get(True)
                    print("Raw mfcc shape =", mfcc.shape)
                    mfcc = mfcc.reshape((1, -1))
                    mfcc_buffer = np.concatenate((mfcc_buffer[:, mfcc.shape[1]: ], mfcc), axis=1)
                    print("mfcc buffer shape =", mfcc_buffer.shape)
                    for classifier_name, classifier_class in classifier_classes.items():
                        if 'all' in CONFIG['classifier'] or classifier_name in CONFIG['classifier']:
                            classifier = classifier_class(None)
                            res = classifier.apply(mfcc_buffer)
                            res = int(res[0])
                            print(classifier_name, res)
                            res_list[classifier_name].append(res)
                            res_filt[classifier_name].append(np.argmax(np.bincount(res_list[classifier_name][-20:])))
                            res_percent[classifier_name].append(
                                np.count_nonzero(
                                    np.array(res_list[classifier_name][-20:]) == res_filt[classifier_name][-1]
                                ) * 5
                            )
                    frame_cnt += 1
                    if frame_cnt % 20 == 0:
                        plt.figure(1)
                        if res_percent['KNN'][-1] > 70 and res_percent['SVM'][-1] > 70:
                            plt.clf()
                            plt.subplot(121)
                            plt.plot(res_filt['KNN'], 'r')
                            plt.plot(res_filt['SVM'], 'b')
                        plt.subplot(122)
                        plt.plot(res_list['KNN'], 'r')
                        plt.plot(res_list['SVM'], 'b')
                        plt.figure(2)
                        plt.clf()
                        plt.plot(res_percent['KNN'], 'r')
                        plt.plot(res_percent['SVM'], 'b')
                        plt.pause(0.001)

        except KeyboardInterrupt:
            print('Exit')
        except Exception as e:
            print("Fucking", e)
            print("Emmmmm")
        finally:
            if CONFIG['error stat']:
                i = 1
                n = len(result_stat)
                print(1)
                plt.figure(1)
                for classifier_name, graph in result_stat.items():
                    if 'all' in CONFIG['classifier'] or classifier_name in CONFIG['classifier']:
                        print(classifier_name)
                        plt.subplot(2, n/2 + 1, i)
                        plt.imshow(graph)
                        plt.colorbar()
                        plt.title(classifier_name)
                        plt.xlabel("Expected")
                        plt.ylabel("Actual")
                        i += 1
                plt.waitforbuttonpress()
            preprocessor_proc.terminate()
            del preprocessor
            exit()
    else:
        wav_list, frame_list, mfcc_list, energy_list, \
        zcr_list, endpoint_list, label_list = preprocessor.process(CONFIG['data list'], CONFIG['argumentation'])
        print('Data set Size:', len(wav_list))
        eff_zcr_list = np.zeros((1, 500))
        eff_mfcc_list = np.zeros((1, 1092))
        eff_label_list = []

        for i in range(len(energy_list)):
            if mfcc_list[i].shape[0] > 100:
                frame_count[100] += 1
            else:
                frame_count[mfcc_list[i].shape[0]] += 1
            if mfcc_list[i].shape[0] < 20:
                continue

            temp = mfcc_list[i].reshape((1, -1))
            if(temp.shape[1] >= 1092):
                temp = temp[:, :1092]
            else:
                temp = np.concatenate((temp, np.zeros((1, 1092 - temp.shape[1]))), axis=1)
            if len(temp) != 0:
                eff_label_list.append(label_list[i])
            else:
                continue
            eff_mfcc_list = np.concatenate((eff_mfcc_list, temp), axis=0)
        x = np.linspace(1, 102 * 13, 101)
        plt.plot(x, frame_count)
        plt.show()
        eff_mfcc_list = eff_mfcc_list[1:]
        print(eff_mfcc_list.shape)

        for classifier_name, classifier_class in classifier_classes.items():
            if CONFIG['is training']:
                if 'all' in CONFIG['classifier'] or classifier_name in CONFIG['classifier']:
                    # Todo: Print training result and validation result
                    # Todo: Save the model to a dir.
                    print(classifier_name)
                    classifier = classifier_class(None)
                    classifier.train(eff_mfcc_list, eff_label_list)


if __name__ == '__main__':
    main()
