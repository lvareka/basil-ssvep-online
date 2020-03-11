# basil-ssvep-online
The BASIL BCI project: SSVEP on-line classification

# Structure
* figures - containes stimuli pictures that are displayed in the desktop application
* src - Python source codes of the main project
* psychopy - contains Psychopy scripts for stimulation (needs to run simultaneously with the classifier)
* requirements.txt - define Python dependencies of the project

# Running the classifier
Requires Python 3.7.

To execute:
1. Directly run *run_basil_app.bat* to install all dependencies and run the main application.
2. If all dependencies including this project are installed, go to *./src* and execute *python main.py*.

# Quick start
* Once you run the application, notice two conditions that have to be met before classification can start. Both EEG data and marker-related LSL streams must be visible (i.e. they must turn from OFF to ON in the GUI). To satisfy these conditions:

1) Run Psychopy stimulation (Run *./psychopy/ssvep_basil.py*).
2) Ensure active EEG LSL stream (such as BASIL stream) is on, and its name corresponds to *eeg_stream_name* variable in: *src/data/config.py*

* Now the *Start* button should be enabled and clicked on. The participant gets ready for stimulation (in each run, he/she selects one picture to focus on). 

* After the stimulation, both a winning picture, classification confidence and a spectral plot are shown. As an optional feedback, the user can click on *True* or *False* buttons.

* When the marker stimulation is over or the user request stop using the *Stop* button, the application execution terminates after LSL timeout (to be set in *src/data/config.py* ).

* Then, it can be started again once both streams are available.
