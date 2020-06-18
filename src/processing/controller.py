from PyQt5 import QtCore
import src.processing.eeg_process
from src.data import colect_lsl_eeg, collect_lsl_markers
from pylsl import resolve_streams
import src.data.config as config
import csv
import src.data.netio_control as netio_control
from datetime import datetime


# Ensures collecting both EEG and marker data
# using a separate threads
# Lukas Vareka, 2020
class Controller(QtCore.QThread):

    # reference towards a window
    def __init__(self, main_window):
        super(Controller, self).__init__()

        self.main_window = main_window

        # Connects marker collector with EEG data source and processor
        self.eeg_collector = colect_lsl_eeg.CollectLslEeg()
        self.eeg_processor = src.processing.eeg_process.EEGProcessor()
        self.marker_collector = collect_lsl_markers.CollectLslMarkers(self, self.eeg_collector, self.eeg_processor)
        self.running = False
        self.terminated = False

        self.predicted_class = None
        self.correct_class = None
        self.result = None
        self.freqs = None
        self.amplitudes = None
        self.confidence = 0

        self.netio = netio_control.Netio()

        self.eeg_processor.set_results_signal.connect(self.set_results)
        self.eeg_processor.set_partial_results.connect(self.set_partial_results)
        self.marker_collector.add_status_signal.connect(main_window.teStatus.append)
        self.marker_collector.send_timeout_signal.connect(main_window.set_timeout_value)
        self.marker_collector.set_feedback_status.connect(self.set_feedback_status)

        self.row = list()
        # self.row.append(datetime.now().strftime("%d/%m"))
        self.f = open('results.csv', 'a', newline='')
        self.writer = csv.writer(self.f)

    def run(self):
        # Starts collecting EEG and markers via LSL
        # = (from BASIL BCI and Psychopy)

        # Start everything
        self.running = True
        self.eeg_collector.running = True
        self.marker_collector.start()
        self.eeg_collector.start()

        # Wait for jobs done
        self.eeg_collector.wait()
        self.marker_collector.wait()
        self.running = False
        self.terminated = True

    # Force stop
    def stop(self):
        self.eeg_collector.running = False
        self.marker_collector.running = False

    # Received results from signal processor -> update the state
    def set_results(self, predicted_class, result, freqs, amplitudes, confidence):
        self.predicted_class = predicted_class
        self.result = result
        self.freqs = freqs
        self.amplitudes = amplitudes
        self.confidence = confidence

        if self.row:
            self.row.append(str(self.result[0]))
            self.row.append(str(self.result[1]))
            self.row.append(str(self.result[2]))

            self.row.append(str(self.predicted_class))

        # smart toggle
        # self.netio.execute(predicted_class)
        self.main_window.status_output(result, predicted_class, confidence)
        self.main_window.display_fig(predicted_class, freqs, amplitudes)

    # Records results from specific detection methods
    def set_partial_results(self, rtype, result):
        self.main_window.statusBar.showMessage(rtype + ': ' + str(result))
        self.main_window.teStatus.append(rtype + ': ' + str(result))
        self.row.append(str(result[0]))
        self.row.append(str(result[1]))
        self.row.append(str(result[2]))

    # Set feedback buttons depending
    # on current state of processing
    def set_feedback_status(self, status):
        self.main_window.pbFeedback1.setEnabled(status)
        self.main_window.pbFeedback2.setEnabled(status)
        self.main_window.pbFeedback3.setEnabled(status)

        # if finished with processing, finalize the CSV row
        if not status:
            if self.correct_class:
                self.row.append(str(self.correct_class))
                self.correct_class = None
            if self.row:
                self.writer.writerow(self.row)
                self.row.clear()

    # Based on the user feedback, set the class of object
    # that the user focused on
    def set_correct_class(self, correct_class):
        self.correct_class = correct_class
        self.main_window.teStatus.append('Correct class name: ' + self.correct_class)
        self.main_window.pbFeedback1.setEnabled(False)
        self.main_window.pbFeedback2.setEnabled(False)
        self.main_window.pbFeedback3.setEnabled(False)

    # Verifies if requested
    # LSL streams are available
    @staticmethod
    def check_lsl():
        streams = resolve_streams(wait_time=0.5)
        marker_status = False
        eeg_status = False

        for i in range(0, len(streams)):
            stream_name = streams[i].name()

            if stream_name == config.marker_stream_name:
                marker_status = True
            if stream_name == config.eeg_stream_name:
                eeg_status = True

        return eeg_status, marker_status
