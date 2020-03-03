from pylsl import StreamInlet, resolve_stream
import time
import threading
import numpy as np
import src.data.config as config
from PyQt5.QtCore import pyqtSignal, QThread


# Collects start / stop LSL markers
# and executes processing with existing data
# on demand.
# On-line BASIL SSVEP BCI
# Lukas Vareka, 2020
class CollectLslMarkers(QThread):
    running = True
    marker_list = []
    lsl_eeg_collector = None
    add_status_signal = pyqtSignal(str)
    send_timeout_signal = pyqtSignal(int)

    # connects to data source and processor
    def __init__(self, lsl_eeg, eeg_processor):
        super(CollectLslMarkers, self).__init__()
        self.lsl_eeg_collector = lsl_eeg
        self.eeg_processor = eeg_processor

    # Execution of the entire on-line workflow
    def run(self):
        markers = resolve_stream('name', config.marker_stream_name)
        inlet = StreamInlet(markers[0])

        while self.running:
            # get a new sample (you can also omit the timestamp part if you're not
            # interested in it)
            self.send_timeout_signal.emit(int(config.collector_timeout))
            marker, timestamp = inlet.pull_sample(timeout=config.collector_timeout)
            self.send_timeout_signal.emit(0)

            if marker is None:
                self.running = False
                self.add_status_signal.emit('Timeout passed with no marker received. Stopping the execution.')

            if marker == ['S  1']:  # start -> collect EEG samples
                self.lsl_eeg_collector.recording = True

                # self.lslEEG.terminate()
            if marker == ['S  2']:  # stop -> obtain EEG samples, stop collecting,
                                    # evaluate EEG frequencies
                self.lsl_eeg_collector.recording = False

                eeg_data = self.lsl_eeg_collector.eeg_data
                s_rate = self.lsl_eeg_collector.s_rate

                if not eeg_data:
                    continue

                eeg_data = np.transpose(eeg_data)
                self.add_status_signal.emit('Processing received data package..')
                self.eeg_processor.process(eeg_data, s_rate)
                self.lsl_eeg_collector.clear_eeg_data()

    # Terminate the whole workflow
    def terminate(self):
        self.running = False

