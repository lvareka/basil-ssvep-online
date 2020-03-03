import threading
from pylsl import StreamInlet, resolve_stream
import time
from PyQt5 import QtCore
import threading
import numpy as np


# Collects start / stop LSL markers
# and executes processing with existing data
# on demand.
# On-line BASIL SSVEP BCI
# Lukas Vareka, 2020
class CollectLslMarkersBlinks(threading.Thread):
    running = True
    marker_list = []
    lsl_eeg_collector = None

    # connects to data source and processor
    def __init__(self, lsl_eeg, eeg_processor):
        super(CollectLslMarkersBlinks, self).__init__()
        self.lsl_eeg_collector = lsl_eeg
        self.eeg_processor = eeg_processor

    # Execution of the entire on-line workflow
    def run(self):
        markers = resolve_stream('name', 'psychopy_stimuli')
        inlet = StreamInlet(markers[0])
        startt = 0
        self.lsl_eeg_collector.recording = True
        last_marker = None

        while self.running:
            # get a new sample (you can also omit the timestamp part if you're not
            # interested in it)
            print('Waiting for marker..')
            marker, timestamp = inlet.pull_sample()
            print(marker)

            eeg_data = self.lsl_eeg_collector.eeg_data
            s_rate = self.lsl_eeg_collector.s_rate

            if not eeg_data:
                continue

            if last_marker:
                eeg_data = np.transpose(eeg_data)
                self.eeg_processor.process(eeg_data, s_rate, last_marker)
                self.lsl_eeg_collector.clear_eeg_data()
            last_marker = marker

            # Terminate the whole workflow
    def terminate(self):
        self.running = False

