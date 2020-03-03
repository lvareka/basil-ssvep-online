from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QStatusBar
import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import src.data.collect_lsl_all as collect_lsl_all
import src.data.config as config


# Main GUI for BASIL SSVEP
# Lukas Vareka, 2020
class PlotWindow(QtWidgets.QMainWindow):
    stopping = False

    def __init__(self):
        super(PlotWindow, self).__init__()
        uic.loadUi('gui/window.ui', self)
        self.show()
        self.setFixedSize(self.size())
        self.predicted_class = None
        self.result = None
        self.freqs = None
        self.amplitudes = None
        self.pbStart.pressed.connect(self.run)
        self.pbStop.pressed.connect(self.stop)
        self.collect_worker = collect_lsl_all.AllDataCollector()
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        self.collect_worker.eeg_processor.set_results_signal.connect(self.set_results)
        self.collect_worker.eeg_processor.add_status_signal.connect(self.teStatus.append)

        self.collect_worker.marker_collector.add_status_signal.connect(self.statusBar.showMessage)
        self.collect_worker.marker_collector.send_timeout_signal.connect(self.set_timeout_value)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)
        self.time_out = 0

        self.lblImage.setPixmap(QtGui.QPixmap('../figures/unknown.jpg'))
        self.lblImage.show()

    # Received results from signal processor -> update the state
    def set_results(self, predicted_class, result, freqs, amplitudes):
        self.predicted_class = predicted_class
        self.result = result
        self.freqs = freqs
        self.amplitudes = amplitudes
        self.status_output()
        self.display_fig()

    def set_timeout_value(self, timeout):
        self.time_out = timeout

    # Print status (typically classification results)
    def status_output(self):
        # Print the predicted class label
        self.teStatus.append('Predicted class: ' + str(self.predicted_class))
        self.teStatus.append('Predicted class name: ' + str(config.names[self.predicted_class - 1]))
        self.teStatus.append('Result: ' + str(self.result))

        self.result.sort()
        confidence = 100 * (self.result[2] - self.result[1])
        self.pbConfidence.setValue(confidence)

    # Display figure (corresponding to the action taken)
    # and spectral plot
    def display_fig(self):
        # Display image
        img_name = '../figures/' + config.names[self.predicted_class - 1] + '.jpg'

        self.lblImage.setPixmap(QtGui.QPixmap(img_name))
        self.lblImage.show()

        # Display plot
        scene = QtWidgets.QGraphicsScene()
        figure = Figure()
        axes = figure.gca()
        axes.set_title("SSVEP channel spectra")
        axes.set_xlabel('Frequencies [Hz]')
        axes.set_ylabel('Amplitudes')
        subset_fq = (self.freqs > 2) & (self.freqs <= 25)
        axes.autoscale(True)
        axes.plot(self.freqs[subset_fq], self.amplitudes[subset_fq])

        # Show vertical lines corresponding to frequencies
        for i in range(0, len(config.frequencies)):
            axes.axvline(x=config.frequencies[i], color='r', alpha=0.5)
            axes.text(config.frequencies[i], max(self.amplitudes[subset_fq]) * 0.75, config.names[i], rotation=90,
                      color='r', verticalalignment='bottom')

        canvas = FigureCanvas(figure)
        scene.addWidget(canvas)
        self.gvPlots.setScene(scene)

    # Check LSL EEG and marker state
    # and update the GUI accordingly
    def update_status(self):
        eeg_status, marker_status = collect_lsl_all.AllDataCollector.check_lsl()
        self.switch_lsl_status(self.lblMarkerStatus, marker_status)
        self.switch_lsl_status(self.lblEEGStatus, eeg_status)

        self.pbStart.setEnabled(marker_status & eeg_status)
        self.pbStop.setEnabled(marker_status & eeg_status)

        if not (marker_status & eeg_status) and not self.stopping and self.collect_worker.running:
            self.stop()

        self.pbStart.setEnabled((not self.collect_worker.running) & marker_status & eeg_status
                                & (not self.collect_worker.terminated))
        self.sbChannelID.setEnabled((not self.collect_worker.running) & (not self.collect_worker.terminated) & (not self.cbAllChannels.isChecked()))
        self.cbAllChannels.setEnabled((not self.collect_worker.running) & (not self.collect_worker.terminated))
        self.pbStop.setEnabled(self.collect_worker.running)

        if self.time_out > 0:
            self.time_out = self.time_out - 1
            self.statusBar.showMessage('Waiting for a marker (time_out = ' + str(self.time_out) + ') ..')

        if self.collect_worker.terminated:
            self.statusBar.showMessage('Stopped. To run again, please restart the application.')

    # Switches the button between the ON/OFF states
    def switch_lsl_status(self, lbl_status, is_on):
        if is_on:
            lbl_status.setText('ON')
            lbl_status.setStyleSheet('color: green')
        else:
            lbl_status.setText('OFF')
            lbl_status.setStyleSheet('color: red')

    # Start collecting and evaluating data
    def run(self):
        self.collect_worker.eeg_processor.channel_id = self.sbChannelID.value()
        self.collect_worker.eeg_processor.all_channels = self.cbAllChannels.isChecked()
        self.collect_worker.start()
        self.teStatus.append('Running..')

    # Stop collecting and evaluating data
    # -> requests collecting threads to finish but
    # needs to wait for the time_out
    def stop(self):
        self.stopping = True
        self.collect_worker.stop()
        self.teStatus.append('Stopping, please wait..')

    # Close the window and entire application
    def close(self):
        print('Closing the application..')
        self.stop()
        sys.exit(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    dw = PlotWindow()
    app.aboutToQuit.connect(dw.close)
    exit_code = app.exec_()
    sys.exit(exit_code)




