import numpy as np
from sklearn.cross_decomposition import CCA
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from sklearn.preprocessing import normalize
from statistics import mean
from operator import truediv
import re

# Performs on-line classification
# On-line BASIL SSVEP BCI
# Inspired by: https://github.com/aaravindravi/PythonBox_OpenViBE_SSVEP_CCA
# Lukas Vareka, 2020
class EEGProcessorBlinks(QtCore.QObject):
    set_results_signal = pyqtSignal(object, object, object, object)
    add_status_signal  = pyqtSignal(str)
    channel_id = 0

    def __init__(self):
        super(EEGProcessorBlinks, self).__init__()
        self.s_rate = 0
        self.results = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.counter = [0, 0, 0, 0, 0, 0, 0, 0, 0]

    def find_grads(self, eeg_data, eeg_shape):

        diffs = []
        # for each channel
        for i in range(0, eeg_shape[0]):
            channel_data = eeg_data[i][:]
            diff = abs(max(channel_data) - min(channel_data))
            diffs.append(diff)
        return mean(diffs)


    def process(self, eeg_data, s_rate, marker):
        self.s_rate = s_rate
        # print('EEG data: ', eeg_data)

        self.add_status_signal.emit('Received new EEG data package: ')
        self.add_status_signal.emit('Sampling rate: ' + str(s_rate))
        eeg_shape = np.shape(eeg_data)

        if s_rate == 0:
            return

        diff = self.find_grads(eeg_data, eeg_shape)
        numbers = re.findall('\d+', marker[0])
        marker_id = int(numbers[0]) - 1

        self.results[marker_id] = self.results[marker_id] + diff
        self.counter[marker_id] = self.counter[marker_id] + 1

        results = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        for i in range(0, len(self.results)):
            if self.counter[i] > 0:
                results[i] = self.results[i] / self.counter[i]


        # Find the maximum canonical correlation coefficient and corresponding class for the given SSVEP/EEG data
        max_result = max(results, key=float)
        predicted_class = np.argmax(results) + 1
        print(predicted_class)
        print(str(results))
        print(range(0, eeg_shape[1]))
        print(str(eeg_data[self.channel_id][:]))

      #  self.set_results_signal.emit(predicted_class, results, range(1, eeg_shape[1]), eeg_data[self.channel_id][:])
