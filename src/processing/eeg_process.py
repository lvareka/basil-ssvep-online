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
    set_results_signal = pyqtSignal(object, object, object, object, object)
    add_status_signal  = pyqtSignal(str)
    channel_id = 0
    all_channels = True
    all_spectral_result = []
    all_spectral_diff_result = []
    predicted_classes = []
    predicted_classes_weights = []


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

        energy = [0, 0, 0]
        for i in range(0, len(freqs)):
            for j in range(0, len(config.frequencies)):
                if  abs(config.frequencies[j] - freqs[i]) < config.fq_interval:
                    energy[j] = energy[j] + ps[i] * ps[i]
        if max(energy) != 0:
            energy = energy / max(energy)

        self.predicted_classes.append(np.argmax(energy) + 1)
        self.predicted_classes_weights.append(config.weights_classifier['spectral'])
        return energy

    # Compute spectral differences
    # between close and more distant neighborhood
    # of target frequencies
    def evaluate_spectral_diffs(self, freqs, ps):

        energy = [0, 0, 0]
        baseline = [0, 0, 0]
        for i in range(0, len(freqs)):
            for j in range(0, len(config.frequencies)):
                if abs(config.frequencies[j] - freqs[i]) < config.fq_interval:
                    energy[j] = energy[j] + ps[i] * ps[i]
                if abs(config.frequencies[j] - freqs[i]) < config.fq_baseline and abs(config.frequencies[j] - freqs[i]) > config.fq_interval:
                    baseline[j] = baseline[j] + ps[i] * ps[i]
        for i in range(0, len(energy)):
            energy[i] = energy[i] / baseline[i]
        if max(energy) != 0:
            energy = energy / max(energy)
        self.add_status_signal.emit('Spectral energy diff: ' + str(energy))

        self.predicted_classes.append(np.argmax(energy) + 1)
        self.predicted_classes_weights.append(config.weights_classifier['spectral_diff'])
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

        self.predicted_classes.append(np.argmax(cca_result) + 1)
        self.predicted_classes_weights.append(config.weights_classifier['cca'])
        return cca_result

    def calc_psd (self, eeg_signal):
        dt = 1 / self.s_rate
        ps = np.abs(np.fft.fft(eeg_signal)) ** 2
        freq_s = np.fft.fftfreq(eeg_signal.size, dt)
        idx = np.argsort(freq_s)
        return freq_s[idx], ps[idx]

    def evaluate_all_spectral(self, freq_s, ps):
        spectral_result = self.evaluate_spectral(freq_s, ps)

        # simply average spectral difference in energies
        spectral_diff_result = self.evaluate_spectral_diffs(freq_s, ps)

        self.all_spectral_result.append(spectral_result)
        self.all_spectral_diff_result.append(spectral_diff_result)
        return spectral_result, spectral_diff_result

    # Process the data package,
    # calculate various metrics useful for
    # on-line classification,
    # computed weighted mean of these metrics
    # and pass the results to the GUI
    def process(self, eeg_data, s_rate):
        self.predicted_classes = []
        self.predicted_classes_weights = []
        self.s_rate = s_rate
        # print('EEG data: ', eeg_data)
        eeg_shape = np.shape(eeg_data)
        self.add_status_signal.emit('Received new EEG data package: size: ' + str(eeg_shape))
        self.add_status_signal.emit('Sampling rate: ' + str(s_rate))

        if s_rate == 0:
            return

        # all individual EEG channel results to average later
        self.all_spectral_result = []
        self.all_spectral_diff_result = []

        # frequency spectrum
        if self.all_channels:

            for i in range(0, eeg_shape[0]):
                freq_s, ps = self.calc_psd(eeg_data[i])
                # simply average spectral energies
                self.evaluate_all_spectral(freq_s, ps)

            # for plotting, calculate mean spectrum
            mean_eeg = np.mean(eeg_data, axis=0)
            freq_s, ps = self.calc_psd(mean_eeg)

            # include ps of the mean signal, too
            self.evaluate_all_spectral(freq_s, ps)

            # average all individual (and mean) channel results to get
            # overall metrics
            spectral_result = np.mean(self.all_spectral_result, axis=0)
            spectral_diff_result = np.mean(self.all_spectral_diff_result, axis=0)

        else:
            freq_s, ps = self.calc_psd(eeg_data[self.channel_id])
            spectral_result, spectral_diff_result = self.evaluate_all_spectral(freq_s, ps)

        self.add_status_signal.emit('Spectral energy: ' + str(spectral_result))
        self.add_status_signal.emit('Spectral energy diff: ' + str(spectral_diff_result))

        # use CCA to estimate correlations
        cca_result = self.evaluate_corr(eeg_data)

        # give one overall result (weighting various results)
        result = spectral_result * config.weights_classifier['spectral'] + spectral_diff_result * \
                 config.weights_classifier['spectral_diff'] + cca_result * config.weights_classifier['cca']

        # Find the maximum canonical correlation coefficient and corresponding class for the given SSVEP/EEG data
        predicted_class = np.argmax(result) + 1

        # Percentage of same voting of various methods
        confidence = 0

        for i in range(0, len(self.predicted_classes)):
            if predicted_class == self.predicted_classes[i]:
                confidence = confidence + self.predicted_classes_weights[i]
        confidence = confidence / np.sum(self.predicted_classes_weights)

        self.set_results_signal.emit(predicted_class, result, freq_s, ps, confidence)
