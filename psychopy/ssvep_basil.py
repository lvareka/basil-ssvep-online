from psychopy import visual, core, logging  # import some libraries from PsychoPy
import random
from datetime import datetime

# LAB STREAMING LAYER
from pylsl import StreamInfo, StreamOutlet

from psychopy import event
    
# ----------------------
# constants
# size of the window
WINWIDTH = 1920
WINHEIGHT = 1200
REFRESH_RATE = 60


def get_keypress():
    keys = event.getKeys()
    if keys:
        return keys[0]
    else:
        return None
        

def shutdown(win):
    win.close()
    core.quit()


# end of configuration
# ----------------------


# ----------------------------------------------------------------------------------
# main window settings
main_win = visual.Window(size=(WINWIDTH, WINHEIGHT), units='height', fullscr = True, gammaErrorPolicy='warn')
main_win.color = 'white' 
rectangle = visual.Rect(win=main_win, units="pix", width=400, height=400, fillColor=[1, -1, -1])


# Set up LabStreamingLayer stream.
info = StreamInfo(name='psychopy_stimuli', type='Markers', channel_count=1, channel_format='string', source_id='psychopy_stimuli_001')
outlet = StreamOutlet(info) # Broadcast the stream.

imageStim1 = visual.ImageStim(main_win, size=(400, 400), pos=(650, 350), units='pix', image='figures/lamp.png')
imageStim2 = visual.ImageStim(main_win, size=(400, 400), pos=(-650, 350),units='pix', image='figures/radio.png')
imageStim3 = visual.ImageStim(main_win, size=(400, 400), pos=(0, -350),units='pix', image='figures/phone.png')

#grating.color = 'black'

for i in range(1, 7):
  
    # start
    outlet.push_sample(['S  1'])
    for frameN in range(20 * REFRESH_RATE): # 20 seconds
        key_press = get_keypress()
        if key_press == 'q':
            shutdown(main_win)
        if frameN % 5 < 3: # 12 Hz
            #rectangle.draw() 
            imageStim1.draw()
        if frameN % 4 <= 1: # 15 Hz
            imageStim2.draw()
        if frameN % 3 == 0: # 20 Hz
            imageStim3.draw()
       # else:
       #     emptyStim.draw()
        main_win.flip()          # wait for the screen refresh  
    

    # stop
    outlet.push_sample(['S  2'])
    for frameN in range(10 * REFRESH_RATE): # 10 seconds
        main_win.flip()          # wait for the screen refresh  
    
main_win.close()