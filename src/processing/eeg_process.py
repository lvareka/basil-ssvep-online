import numpy as np
from sklearn.cross_decomposition import CCA
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
import src.data.config as config


# Performs on-line classification
# On-line BASIL SSVEP BCI
# Inspired by: https://github.com/aaravindravi/PythonBox_OpenViBE_SSVEP_CCA
# Lukas Vareka, 2020
class EEGProcessor(QtCore.QObject):
    set_results_signal = pyqtSignal(object, object, object, object)
    add_status_signal  = pyqtSignal(str)
    channel_id = 0

    def __init__(self):
        super(EEGProcessor, self).__init__()
        self.s_rate = 0

    def get_reference_signals(self, length, target_freq):
        # generate sinusoidal reference templates for CCA for the first and second harmonics
        reference_signals = []
        t = np.arange(0, (length / (self.s_rate)), step=1.0 / (self.s_rate))
        # First harmonics/Fundamental freqeuncy
        reference_signals.append(np.sin(np.pi * 2 * target_freq * t))
        reference_signals.append(np.cos(np.pi * 2 * target_freq * t))
        # Second harmonics
        reference_signals.append(np.sin(np.pi * 4 * target_freq * t))
        reference_signals.append(np.cos(np.pi * 4 * target_freq * t))
        reference_signals = np.array(reference_signals)
        return reference_signals

    def find_corr(self, n_components, eeg_data, freq):
        # Perform Canonical correlation analysis (CCA)
        # eeg_data - consists of the EEG
        # freq - set of sinusoidal reference templates corresponding to the flicker frequency
        cca = CCA(n_components)
        corr = np.zeros(n_components)
        result = np.zeros((freq.shape)[0])
        for freqIdx in range(0, (freq.shape)[0]):
            print(np.shape(eeg_data))
            cca.fit(eeg_data.T, np.squeeze(freq[freqIdx, :, :]).T)
            O1_a, O1_b = cca.transform(eeg_data.T, np.squeeze(freq[freqIdx, :, :]).T)
            indVal = 0
            for indVal in range(0, n_components):
                corr[indVal] = np.corrcoef(O1_a[:, indVal], O1_b[:, indVal])[0, 1]
            result[freqIdx] = np.max(corr)
        result = result / max(result)
        return result

    # Compute spectral energies
    # in the neighborhood of target frequencies
    def evaluate_spectral(self, freqs, ps):
        delta = 0.3
        energy = [0, 0, 0]
        for i in range(0, len(freqs)):
            for j in range(0, len(config.frequencies)):
                if  abs(config.frequencies[j] - freqs[i]) < delta:
                    energy[j] = energy[j] + ps[i] * ps[i]
        if max(energy) != 0:
            energy = energy / max(energy)
        self.add_status_signal.emit('Spectral energy: ' + str(energy))
        return energy

    # Compute spectral differences
    # between close and more distant neighborhood
    # of target frequencies
    def evaluate_spectral_diffs(self, freqs, ps):
        delta1 = 0.3
        delta2 = 1
        energy = [0, 0, 0]
        baseline = [0, 0, 0]
        for i in range(0, len(freqs)):
            for j in range(0, len(config.frequencies)):
                if abs(config.frequencies[j] - freqs[i]) < delta1:
                    energy[j] = energy[j] + ps[i] * ps[i]
                if abs(config.frequencies[j] - freqs[i]) < delta2 and abs(config.frequencies[j] - freqs[i]) > delta1:
                    baseline[j] = baseline[j] + ps[i] * ps[i]
        for i in range(0, len(energy)):
            energy[i] = energy[i] / baseline[i]
        if max(energy) != 0:
            energy = energy / max(energy)
        self.add_status_signal.emit('Spectral energy diff: ' + str(energy))
        return energy

    # Compute CCA-related metrics
    # as shown in:
    # https://github.com/aaravindravi/PythonBox_OpenViBE_SSVEP_CCA
    def evaluate_corr(self, eeg_data):
        eeg_shape = np.shape(eeg_data)
        # Generate a vector of sinusoidal reference templates for all SSVEP flicker frequencies
        freq1 = self.get_reference_signals(eeg_shape[1], config.frequencies[0])
        freq2 = self.get_reference_signals(eeg_shape[1], config.frequencies[1])
        freq3 = self.get_reference_signals(eeg_shape[1], config.frequencies[2])
        # Application of the CCA python function for each of the frequencies
        n_components = 1
        # Concatenate all templates into one matrix
        freq = np.array([freq1, freq2, freq3])
        # Compute CCA
        cca_result = self.find_corr(n_components, eeg_data, freq)
        self.add_status_signal.emit('CCA results: ' + str(cca_result))
        return cca_result

    # Process the data package,
    # calculate various metrics useful for
    # on-line classification,
    # computed weighted mean of these metrics
    # and pass the results to the GUI
    def process(self, eeg_data, s_rate):
        self.s_rate = s_rate
        # print('EEG data: ', eeg_data)
        eeg_shape = np.shape(eeg_data)
        self.add_status_signal.emit('Received new EEG data package: ')
        self.add_status_signal.emit('Size: ' + str(eeg_shape))
        self.add_status_signal.emit('Sampling rate: ' + str(s_rate))

        if s_rate == 0:
            return

        # frequency spectrum
        dt = 1 / s_rate
        ps = np.abs(np.fft.fft(eeg_data[self.channel_id])) ** 2
        freqs = np.fft.fftfreq(eeg_data[self.channel_id].size, dt)
        idx = np.argsort(freqs)

        # simply average spectral energies
        spectral_result = self.evaluate_spectral(freqs[idx], ps[idx])

        # simply average spectral difference in energies
        spectral_diff_result = self.evaluate_spectral_diffs(freqs[idx], ps[idx])

        # use CCA to estimate correlations
        cca_result = self.evaluate_corr(eeg_data)

        # give one overall result (weighting various results)
        result = spectral_result * 0.1 + spectral_diff_result * 0.6 + cca_result * 0.3

        # Find the maximum canonical correlation coefficient and corresponding class for the given SSVEP/EEG data
        predicted_class = np.argmax(result) + 1

        self.set_results_signal.emit(predicted_class, result, freqs[idx], ps[idx])
