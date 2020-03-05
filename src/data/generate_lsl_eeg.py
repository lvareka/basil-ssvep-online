import time
from random import random as rand
from pylsl import StreamInfo, StreamOutlet
import numpy as np
import src.data.config as config

# first create a new stream info (here we set the name to BioSemi,
# the content-type to EEG, 8 channels, 100 Hz, and float-valued data) The
# last value would be the serial number of the device or some other more or
# less locally unique identifier for the stream as far as available (you
# could also omit it but interrupted connections wouldn't auto-recover)
s_rate = 1000

info = StreamInfo(config.eeg_stream_name, 'EEG', 8, s_rate, 'float32', 'myuid34234')

# next make an outlet
outlet = StreamOutlet(info)

print("now sending data...")
length = 2794

target_freq = 14.9
t = np.arange(0, (length / s_rate), step=1.0 / s_rate)
# First harmonics/Fundamental freqeuncy
harmonic_signal = np.sin(np.pi * 2 * target_freq * t)

i = 0

while True:
    # make a new random 8-channel sample; this is converted into a
    # pylsl.vectorf (the data type that is expected by push_sample)
    i = i + 1
    if i >= np.shape(harmonic_signal)[0]:
        i = 0

    mysample = harmonic_signal[i] / 30.0 + [rand(), rand(), rand(), rand(), rand(), rand(), rand(), rand()]
    # now send it and wait for a bit
    outlet.push_sample(mysample)
    time.sleep(1.0 / s_rate )