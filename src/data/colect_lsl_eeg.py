import threading
from pylsl import StreamInlet, resolve_stream
import src.data.config as config
from PyQt5.QtCore import QThread


# Collects EEG samples and sampling rate.
# On-line BASIL SSVEP BCI
# Lukas Vareka, 2020
class CollectLslEeg(QThread):
    recording = True
    running = False
    s_rate = 0
    eeg_data = []

    # reference towards a window
    def __init__(self):
        super(CollectLslEeg, self).__init__()

    def run(self):
        self.eeg_data = []
        streams = resolve_stream('name', config.eeg_stream_name)
        print('EEG streams', streams)
        inlet = StreamInlet(streams[0])
        self.s_rate = inlet.info().nominal_srate()

        while self.running:
            if self.recording:
                # get a new sample (you can also omit the timestamp part if you're not
                # interested in it)
                sample, timestamp = inlet.pull_sample(timeout=config.collector_timeout)
                if sample is None:
                    self.running = False
                else:
                    self.eeg_data.append(sample)

    def clear_eeg_data(self):
        self.eeg_data = []

