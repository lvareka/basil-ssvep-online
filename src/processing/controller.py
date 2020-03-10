from PyQt5 import QtCore
import src.processing.eeg_process
from src.data import colect_lsl_eeg, collect_lsl_markers
from pylsl import resolve_streams
import src.data.config as config


# Ensures collecting both EEG and marker data
# using a separate threads
# Lukas Vareka, 2020
class Controller(QtCore.QThread):

    # reference towards a window
    def __init__(self):
        super(Controller, self).__init__()

        # Connects marker collector with EEG data source and processor
        self.eeg_collector = colect_lsl_eeg.CollectLslEeg()
        self.eeg_processor = src.processing.eeg_process.EEGProcessor()
        self.marker_collector = collect_lsl_markers.CollectLslMarkers(self, self.eeg_collector, self.eeg_processor)
        self.running = False
        self.terminated = False

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
