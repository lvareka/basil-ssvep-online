from PyQt5 import QtWidgets, uic, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QStatusBar
import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import src.processing.controller as controller
import src.data.config as config
from functools import partial
import src.data.netio_control as netio_control

# Main GUI for BASIL SSVEP
# Lukas Vareka, 2020
class PlotWindow(QtWidgets.QMainWindow):
    stopping = False

    def __init__(self):
        super(PlotWindow, self).__init__()
        uic.loadUi('gui/window.ui', self)
        self.show()
        self.setFixedSize(self.size())
        self.netio = netio_control.Netio()
        self.predicted_class = None
        self.result = None
        self.freqs = None
        self.amplitudes = None
        self.confidence = 0
        self.pbStart.pressed.connect(self.run)
        self.pbStop.pressed.connect(self.stop)
        self.pbTrue.pressed.connect(partial(self.teStatus.append,  'Correctly detected'))
        self.pbFalse.pressed.connect(partial(self.teStatus.append, 'Incorrectly detected'))
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.controller = None

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)
        self.time_out = 0

        self.lblImage.setPixmap(QtGui.QPixmap('../figures/unknown.jpg'))
        self.lblImage.show()

    def setup(self):
        self.controller = controller.Controller()

        self.controller.eeg_processor.set_results_signal.connect(self.set_results)
        self.controller.eeg_processor.add_status_signal.connect(self.teStatus.append)

        self.controller.marker_collector.add_status_signal.connect(self.statusBar.showMessage)
        self.controller.marker_collector.send_timeout_signal.connect(self.set_timeout_value)
        self.controller.marker_collector.set_feedback_status.connect(self.pbTrue.setEnabled)
        self.controller.marker_collector.set_feedback_status.connect(self.pbFalse.setEnabled)

    # Received results from signal processor -> update the state
    def set_results(self, predicted_class, result, freqs, amplitudes, confidence):
        self.predicted_class = predicted_class
        self.result = result
        self.freqs = freqs
        self.amplitudes = amplitudes
        self.confidence = confidence

        # smart toggle
        self.netio.execute(predicted_class)
        self.status_output()
        self.display_fig()

    def set_timeout_value(self, timeout):
        self.time_out = timeout

    # Print status (typically classification results)
    def status_output(self):
        # Print the predicted class label
        self.teStatus.append('Classification result: ' + str(self.result))
        self.teStatus.append('Predicted class name: ' + str(config.names[self.predicted_class - 1]))

        # Clearly different values in results array?
        self.result.sort()
        confidence2 = 100 * (self.result[2] - self.result[1])

        # Average different confidence values
        self.pbConfidence.setValue((confidence2 + self.confidence * 100) / 2.0)

    # Display figure (corresponding to the action taken)
    # and spectral plot
    def display_fig(self):
        # Display image
        img_name = '../figures/' + config.names[self.predicted_class - 1] + '.png'

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
        eeg_status, marker_status = controller.Controller.check_lsl()

        self.switch_lsl_status(self.lblMarkerStatus, marker_status)
        self.switch_lsl_status(self.lblEEGStatus, eeg_status)

        self.pbStart.setEnabled(marker_status & eeg_status)
        self.pbStop.setEnabled(marker_status & eeg_status)
        if self.time_out > 0:
            self.time_out = self.time_out - 1
            self.statusBar.showMessage('Waiting for a marker (time_out = ' + str(self.time_out) + ') ..')

        if self.controller is not None:
            if not (marker_status & eeg_status) and not self.stopping and self.controller.running:
                self.stop()

            self.pbStart.setEnabled((not self.controller.running) & marker_status & eeg_status)
                                    # & (not self.controller.terminated))
            self.sbChannelID.setEnabled((not self.controller.running) & (not self.cbAllChannels.isChecked()))
            self.cbAllChannels.setEnabled((not self.controller.running))
            self.pbStop.setEnabled(self.controller.running)

            if self.controller.terminated:
                self.statusBar.showMessage('Stopped. To run again, please click on the start button.')

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
        self.setup()
        self.controller.eeg_processor.channel_id = self.sbChannelID.value()
        self.controller.eeg_processor.all_channels = self.cbAllChannels.isChecked()
        self.controller.start()
        self.teStatus.append('Running..')

    # Stop collecting and evaluating data
    # -> requests collecting threads to finish but
    # needs to wait for the time_out
    def stop(self):
        self.stopping = True

        if self.controller is not None:
            self.controller.stop()
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




