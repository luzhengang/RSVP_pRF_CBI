# -*- coding: utf-8 -*-
#
# rsvp_sweep.py
#
# Run RSVP (Rapid Serial Visual Presentation) sweep task for pRF modeling
# 1. Load experiment parameters from rsvp_params.txt
# 2. Enter subject info; Initialize data file
# 3. Check for Data & Stimuli folders
# 4. Automatically configure remaining parameters
# 5. Load all images; Create stimuli
# 6. Set position and speed for left-to-right, right-to-left, top-to-bottom, and bottom-to-top
# 7. Generate set of images to be presented
# 8. Define sweep function
# 9. Set up Eyetracker
# 10. Target presentation & peripheral calibration
# 11. Instructions
# 12. Run sweeps
#
# Created: 2/21/20
# Updated: 7/26/21
# Jeff Kravitz
# Curtis Lab
# New York University
# modified by zhengang lu 11/2023
# 1. The masks have a length of the image size so don't cut the image into half
#   e.g.,bore_mask_TL = visual.Rect(win=win, fillColor = color, lineColor = color, size = image_h * 1)
# 2. gui.dlg changed to screen=1 so the sub info shown on the secondary screen
# 3. add fps as a parameter
# 4. time stamped every event
# 5. add while t < trial_time, wait to deal with dropping frame
# 6. turn waitBlanking = False in visual_win. won't wait for next frame if frame dropped
# 7. save empirical timing data
# 8. add experiment starting time and each bar/set duration as input
# 9. Note that in testing mode, will take extra time to run RunTimeInfo
# >------------------------------------------------------------<


# 0. Load modules
from __future__ import division, print_function
from psychopy import logging, core, visual, gui, event
from psychopy.core import StaticPeriod, CountdownTimer
from psychopy.iohub import launchHubServer
from psychopy.info import RunTimeInfo
from datetime import datetime
from inspect import getsourcefile
from os.path import abspath
import pylink
import os.path
import platform
import glob
import numpy as np
import math
import random
import os
import psy_utility as psyut
import time

# 1. Load experiment parameters from rsvp_params.txt
params = psyut.get_params(params_filename = 'rsvp_params.txt')

# Process list params
params['screen_res'] = [int(i) for i in params['screen_res']]
params['stim_bounds'] = [int(j) for j in params['stim_bounds']]
if params['constrained_set'] == ['']: params['constrained_set'] = []
else: params['constrained_set'] = [int(k) for k in params['constrained_set']]
params['background_color'] = [int(l) for l in params['background_color']]
params['text_color'] = [int(m) for m in params['text_color']]
params['fix_color'] = [int(n) for n in params['fix_color']]

# Pull some vars from the dict now so we won't have to do spend time doing that during sweep
color = params['background_color']
text_color = params['text_color'] 
fix_color = params['fix_color']
pulse_cue = params['pulse_cue']
tr = params['tr']
n_trials = params['n_trials']
n_bars = params['n_bars']
targ_cooldown = params['targ_cooldown']
testing = params['testing']
response_period = params['response_period']
show_feedback = params['show_feedback']
feedback_frames = params['feedback_frames']
save_log = params['save_log']
stair_lower = params['stair_lower']
stair_upper = params['stair_upper']
targ_rate = params['targ_rate']
response_key = params['response_key']
bore_mask = params['bore_mask']

fps = 60                                        # Frame rate of display computer. Should be set to 60
# Check that specified parameters make sense
if params['response_period'] > params['targ_cooldown']:
    raise Exception('Error: response_period must not be greater than targ_cooldown. Please check rsvp_params.txt and try again.')


# 2. Enter session info; Initialize data file
subinfo = gui.Dlg(title='RSVP Sweep', screen=1)
subinfo.addText('Session Info')
subinfo.addField('Subject Initials')
subinfo.addField('Run Number')
subinfo.addField('Stimuli Duration', choices=[150,166,183,200,216,233,250,266,283,300,316,333,350,366,383,400,416,433,450,466,483,500,516,533,550,566,583,600])
subinfo.addField('Eyetracker', False)
subinfo.addField('MRI', False)
subinfo.addField('Fullscreen', False)
subinfo.addField('Use Second Monitor', False)
sub_data = subinfo.show()
if subinfo.OK:
    print('\n\n')
    print('>-----------Start-Run-----------< \n')
    print('Subject:          ' + sub_data[0].upper())
    print('Run:              ' + sub_data[1])
    print('Stim Duration:    ' + str(sub_data[2]) + ' ms')
    print('Target Cooldown:  ' + str(math.trunc(params['targ_cooldown'] * 1000)) + ' ms')
    print('Response Period:  ' + str(math.trunc(params['response_period'] * 1000)) + ' ms')
    print('Eyetracking:      ' + str(sub_data[3]))
    print('MRI:              ' + str(sub_data[4]))
    print('\n')
else:
    raise Exception('Error: User cancelled')
date = datetime.now().strftime('%m-%d-%Y_hr%H_min%M_sec%S')
sub_name = sub_data[0].upper()
run_number = sub_data[1]
stim_dur = sub_data[2]
eye_tracking = sub_data[3]
scanning = sub_data[4]
fullscreen = sub_data[5]
if sub_data[6]:
    which_screen = 1
else:
    which_screen = 0

# Configure system
run_info = {'fullscreen': fullscreen,
            'which_screen': which_screen,
            'sub_name': sub_name,
            'run_number': run_number}
filename, edf_filename, mac = psyut.config_sys(exp_name = 'RSVP pRF', run_info=run_info)


# 3. Check for Data/Stimuli folders; Initialize data file
path = abspath(getsourcefile(lambda:0))
if mac:
    sep_loc = path.rfind('/')
else:
    sep_loc = path.rfind('\\')
path = path[0:sep_loc + 1]
stim_path = path + 'Stimuli'
if not os.path.isdir(stim_path):
    raise Exception('Error: There is no stimuli folder in the current directory')
data_path = path + 'Data'
if not os.path.isdir(data_path):
    os.mkdir(data_path)
if mac:
    stim_path += '/*.jpg'
    filename = data_path + '/' + sub_name + '_run' + run_number + '_' + date + '_' + 'rsvp_sweep_' + 'summary'
else:
    stim_path += '\\*.jpg'
    filename = data_path + '\\' + sub_name + '_run' + run_number + '_' + date + '_' + 'rsvp_sweep_' + 'summary'
datafile = open(filename + '.csv', 'w')
datafile.write('Trial_Number,Sweep_Onset,Sweep_Duration,Sweep_Direction,Refresh_Rate,Stim_Duration,Accuracy,Correct,Total,Mean_RT,False_Positives\n')
if len(sub_name) < 4:
    edf_filename = sub_name + '_R' + str(run_number)
    long_edf_name = False
else:
    edf_filename = sub_name[0:3] + '_R' + str(run_number)
    long_edf_filename = sub_name + '_R' + str(run_number)
    long_edf_name = True
#edf_filename = sub_name + '_R' + str(run_number)
if params['save_log']:
    stim_log = open(filename + '_stimlog.csv', 'w')
    stim_log.write('trial,barOnset,imageOnset,direct,i1img,i1x,i1y,i2img,i2x,i2y,i3img,i3x,i3y,i4img,i4x,i4y,i5img,i5x,i5y,i6img,i6x,i6y,t,targ_here,targ_img,targ_slot,RT\n')

# 4. Automatically configure remaining parameters
if scanning:
    resp_key_text = params['response_key']            # Key used to respond to target stimuli
else:
    if mac: response_key = ' '
    else: response_key = 'space'
    resp_key_text = 'space'
    bore_mask = False
bar_dur = params['tr_per_bar'] * params['tr']   # Duration of each bar step, in seconds
sweep_rate = bar_dur * fps                      # Rate at which bar moves, in frames
frames_per_set = []
set_list = []
time_list = []
min_frames_per_set=int(150/(1000/fps))
max_frames_per_set=int(600/(1000/fps))
for i in list(range(min_frames_per_set,max_frames_per_set+1)):
    frames_per_set.append(i)
    set_list.append(math.trunc(sweep_rate / i))
    time_list.append(math.trunc(i*1000/fps))
dur_idx = time_list.index(stim_dur)
image_h = params['stim_bounds'][1] / 6                                                                      # Size of each image
params['screen_width'] = params['screen_height'] * params['screen_res'][0] / params['screen_res'][1]        # Screen width in cm
params['screen_h_deg'] = 180 / math.pi * np.arctan(params['screen_height'] / (2 * params['view_dist']))     # Screen height in degrees
params['screen_w_deg'] = 180 / math.pi * np.arctan(params['screen_width'] / (2 * params['view_dist']))      # Screen height in degrees
params['ppd'] = params['screen_res'][1] / params['screen_h_deg']                                            # Pixels per degree
params['fix_size']  /= 100

# 5. Load all images; Create stimuli; Test parameters
win = visual.Window(params['screen_res'],
                    fullscr = fullscreen,
                    monitor="testMonitor",
                    screen = which_screen,
                    waitBlanking=False,
                    allowGUI = True,
                    units = 'pix',
                    colorSpace = 'rgb',
                    color = color)
image_fns = glob.glob(stim_path)
a1 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create image 1
a2 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create image 2
a3 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create image 3
a4 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create image 4
a5 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create image 5
a6 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create image 6
b1 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create buffer image 1
b2 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create buffer image 2
b3 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create buffer image 3
b4 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create buffer image 4
b5 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create buffer image 5
b6 = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                                   # Create buffer image 6
targ_image = visual.ImageStim(win=win, size = (image_h, image_h), units = 'pix')                                           # Create target image
fix_cross = visual.ShapeStim(win=win, vertices = 'cross', fillColor = color, lineColor = color, size = (image_h * params['fix_size']))    # Create fixation cross
fix_circle = visual.Circle(win=win, fillColor = fix_color, lineColor = color, size = (image_h * params['fix_size']))                      # Create fixation circle
fix_dot = visual.Circle(win=win, fillColor = fix_color, lineColor = fix_color, size = (image_h * params['fix_size'] / 4))                 # Create fixation dot
bore_mask_L = visual.Rect(win=win, fillColor = color, lineColor = color, size = image_h * 1)                                    # Create left bore mask
bore_mask_R = visual.Rect(win=win, fillColor = color, lineColor = color, size = image_h * 1)                                    # Create right bore mask


# Test parameters
if testing:
    logging.console.setLevel(logging.WARNING)
    runtime_info = RunTimeInfo(win=win, refreshTest = True)
    desired_msPerFrame = 1000 / fps
    actual_msPerFrame = runtime_info['windowRefreshTimeAvg_ms']
    actual_fps = 1000 / actual_msPerFrame
    print(actual_fps)
    if abs(desired_msPerFrame - actual_msPerFrame) > 1:
        win.close()
        core.quit()
        frame_error_msg = 'Error: The frame rate of the display computer does not match the desired frame rate.\n\n\
                        Desired frames per second: {:d} \n\
                        Actual frames per second:  {:.2f} \n'.format(fps, actual_fps)
        raise Exception(frame_error_msg)


# 6. Set position and speed for left-to-right, right-to-left, top-to-bottom, and bottom-to-top
l_marg = -1 * params['stim_bounds'][0] / 2 + image_h / 2       # Define left margin
r_marg = params['stim_bounds'][0] / 2 - image_h / 2            # Define right margin
t_marg = params['stim_bounds'][1] / 2 - image_h / 2            # Define top margin
b_marg = -1 * params['stim_bounds'][1] / 2 + image_h / 2       # Define bottom margin
L2R_pos = []
R2L_pos = []
T2B_pos = []
B2T_pos = []
spacing = [image_h * 2.5, image_h * 1.5, image_h * 0.5, image_h * -0.5, image_h * -1.5, image_h * -2.5]
types = ['L2R', 'T2B', 'R2L', 'B2T']
n_stim_set = len(image_fns)
trial = 1
real_resp_time = params['response_period'] - params['response_delay']
# Set initial position for each image
for j in list(range(0,6)):
    L2R_pos.append((l_marg, spacing[j]))
    R2L_pos.append((r_marg, spacing[j]))
    T2B_pos.append((spacing[j], t_marg))
    B2T_pos.append((spacing[j], b_marg))
lr_dist = r_marg - l_marg
lr_dist = lr_dist / (params['n_bars'] - 1)
tb_dist = t_marg - b_marg
tb_dist = tb_dist / (params['n_bars'] - 1)
bore_mask_L.pos = (l_marg, t_marg)
bore_mask_R.pos = (r_marg, t_marg)
# Set jump distance for each sweep direction
L2R_speed = (lr_dist, 0)
R2L_speed = (-1 * lr_dist, 0)
T2B_speed = (0, -1 * tb_dist)
B2T_speed = (0, tb_dist)
# Set fixed target
image_set = list(range(0,n_stim_set))
if bool(params['constrained_set']):
    targ = random.choice(params['constrained_set'])
else:
    targ = random.choice(image_set)


# 7. Generate set of images to be presented
# Same distractor items cannot be presented in the same set
def gen_set(targ, last_set):
    image_set = list(range(0,n_stim_set))
    if len(last_set) > 0:
        for l in last_set:
            image_set.remove(l)
    current_set = []
    if targ in image_set: image_set.remove(targ)
    #for k in list(range(0,6)):
    #    current_set.append(random.choice(image_set))
    #    image_set.remove(current_set[k])
    current_set = random.sample(image_set, k = 6)
    return current_set


# 8. Define sweep function ====================================================================================================================<
def sweep(tStartExp, bar_dur, direct, refresh_rate, trial, targ=targ, targ_rate=targ_rate, sweep_rate=sweep_rate,
          a1=a1, a2=a2, a3=a3, a4=a4, a5=a5, a6=a6, b1=b1, b2=b2, b3=b3, b4=b4, b5=b5, b6=b6):
    # Initialize target cooldown timer; Start static period to load sweep
    if eye_tracking:
        et.sendMessage('xDAT 1')
    static = StaticPeriod(screenHz = fps)
    static.start(tr)

    # Initialize variables
    a_targ_here = False
    b_targ_here = False
    targ_here = False
    show_buffer = False
    break_out = False
    loop_count = 1
    next_frame_ref = 1
    next_set_idx = 1
    feedback_frames_rem = 0
    last_targ_idx = 0
    ref_counter = 0
    bar_counter = 1
    false_pos = 0
    correct = 0
    total = 0
    rt = []
    start_rt = None

    # Set sweep timing
    refresh_rate = frames_per_set[dur_idx]
    sets_per_bar = set_list[dur_idx]
    stim_dur = time_list[dur_idx]
    stim_dur = stim_dur / 1000
    total_sets = sets_per_bar * n_bars
    gap = bar_dur - (stim_dur * sets_per_bar)
    set_timings = [0, stim_dur]
    set_bar_num = [1, 1]
    y = 1
    for i in list(range(2, total_sets + 2)):
        x = set_timings[i - 1] + stim_dur
        if i % sets_per_bar == 0:
            x += gap
            y += 1
        set_timings.append(x)
        set_bar_num.append(y)
    sweep_dur = set_timings[-2]

    # Select target image; Initialize image sets
    a_images = [a1, a2, a3, a4, a5, a6]
    b_images = [b1, b2, b3, b4, b5, b6]
    a_set = gen_set(targ=targ, last_set=[])
    b_set = gen_set(targ=targ, last_set=a_set)

    # Set position and speed for left-to-right or top-to-bottom
    if direct == 'L2R':
        position = L2R_pos              # Set starting image positions
        speed = L2R_speed               # Set distance to add for each new bar location
        max_slot = 5                    # Set slots in which target can be displayed when bar is masked
        mask_bar = [1, n_bars]          # Set which bars should be masked
    elif direct == 'T2B':
        position = T2B_pos
        speed = T2B_speed
        max_slot = 4
        mask_bar = [1, n_bars + 1]
    elif direct == 'R2L':
        position = R2L_pos
        speed = R2L_speed
        max_slot = 5
        mask_bar = [1, n_bars]
    elif direct == 'B2T':
        position = B2T_pos
        speed = B2T_speed
        max_slot = 4
        mask_bar = [n_bars, n_bars]
    for z, each in enumerate(a_images, start = 0):
        each.pos = position[z]                              # Set starting position for each image in set A
    for z, each in enumerate(b_images, start = 0):
        each.pos = position[z]                              # Set starting position for each image in set B

    # Generate and load initial image sets
    a_show_targ = random.randint(1, targ_rate)              # Randomize if target is presented
    if stim_dur > targ_cooldown or not a_show_targ == 1:    # Prevent set B from showing target if target cooldown has not reset after showing target in set A
        b_show_targ = random.randint(1, targ_rate)
    else:
        b_show_targ = 0
    if bore_mask and (direct == 'L2R' or direct ==  'T2B' or direct == 'R2L'):                                  # Prevent first target from being displayed in masked slot
        a_targ_slot = random.randint(1, max_slot)                                                               # Randomize position if target is presented
    else:
        a_targ_slot = random.randint(0, 5)
    if bore_mask and (set_bar_num[next_set_idx] == mask_bar[0] or set_bar_num[next_set_idx] >= mask_bar[1]):    # Prevent second target from being displayed in masked slot
        b_targ_slot = random.randint(1, 4)                                                                      # Randomize position if target is presented
    else:
        b_targ_slot = random.randint(0, 5)
    if a_show_targ == 1:
        a_set[a_targ_slot] = targ
        a_targ_here = True
        targ_here = True
        total += 1
        last_targ_idx = 0
    if b_show_targ == 1:
        b_set[b_targ_slot] = targ
        b_targ_here = True
        total += 1
        last_targ_idx = 1
    for x, each in enumerate(a_images, start = 0):
        each.image = image_fns[a_set[x]]                # Load each image in set A
    for x, each in enumerate(b_images, start = 0):
        each.image = image_fns[b_set[x]]                # Load each image in set B

    # End static period to load stimuli
    static.complete()
    if mac: keypress = iokeyboard.getPresses(keys = [response_key])
    else: keypress = event.getKeys(keyList = [response_key])
    start_rt = core.MonotonicClock()
    if eye_tracking:
        et.sendMessage('xDAT 2')
    if testing:
        test = [0,0]
        win.recordFrameIntervals = True
    this_rt = []
    if targ_here:
        response_timer = CountdownTimer(response_period)
    else:
        response_timer = CountdownTimer(0)

    tStartSweep=time.time()-tStartExp
    print('%ss sweep starts'%tStartSweep)
    tStartImage=tStartSweep
    sweeptimer = CountdownTimer(sweep_dur)
    # Start sweep (24TRs)
    while sweeptimer.getTime()>0:
        # e.g., for every 157 frames in 2TRs 2.6s
        # can change to use bartimer to control bar presentation time
        # but may add extra time acculumated through the whole run
        # in addition, at high speed will notice the gap between bars unsmooth sweep
        # bartimer = CountdownTimer(bar_dur)
        for frame in range(1, int(sweep_rate) + 1):
            # Check response time period
            if feedback_frames_rem == 0:
                fix_circle.fillColor = fix_color
                feedback_frames_rem -= 1
            elif feedback_frames_rem > 0:
                feedback_frames_rem -= 1

            # Check key resonses for accuracy; Give feedback
            if response_timer.getTime() <= 0: targ_here = False
            if response_key in keypress:
                if mac: keypress = iokeyboard.getPresses(keys = [response_key])
                else: keypress = event.getKeys(keyList = [response_key])
                if targ_here == True and response_timer.getTime() < real_resp_time and response_timer.getTime() > 0:               # Check for hits
                    this_rt.append(start_rt.getTime())
                    rt.append(this_rt[-1])
                    if show_feedback: fix_circle.fillColor = 'green'
                    feedback_frames_rem = feedback_frames
                    correct += 1
                    targ_here = False
                else: 
                    false_pos += 1

            # Refresh images on proper frame
            if frame % refresh_rate == 0:
                if testing:
                    print('Dropping frames?')
                next_set_idx += 1
                loop_count += 1
                if mac: keypress = iokeyboard.getPresses(keys = [response_key])
                else: keypress = event.getKeys(keyList = [response_key])
                if show_buffer:
                    a_set = gen_set(targ=targ, last_set=b_set)                                                                      # Randomly generate new set of distractor images
                    if set_timings[next_set_idx] - set_timings[last_targ_idx] > targ_cooldown:                                      # Prevent next set from showing target if target cooldown has not reset after showing target in previous sets
                        a_show_targ = random.randint(1, targ_rate)                                                                  # Randomize if target is presented
                        if bore_mask and (set_bar_num[next_set_idx] == mask_bar[0] or set_bar_num[next_set_idx] >= mask_bar[1]):    # Prevent next target from being displayed in masked slot
                            a_targ_slot = random.randint(1, max_slot)                                                               # Randomize position if target is presented
                        else:
                            a_targ_slot = random.randint(0, 5)
                        a_targ_here = False
                        if a_show_targ == 1:
                            a_set[a_targ_slot] = targ
                            a_targ_here = True
                            total += 1
                            last_targ_idx = next_set_idx
                        else:
                            a_targ_here = False
                    else:
                        a_targ_here = False
                else:
                    b_set = gen_set(targ=targ, last_set=a_set)                                                                      # Randomly generate new set of distractor images
                    if set_timings[next_set_idx] - set_timings[last_targ_idx] > targ_cooldown:                                      # Prevent next set from showing target if target cooldown has not reset after showing target in previous sets
                        b_show_targ = random.randint(1, targ_rate)                                                                  # Randomize if target is presented
                        if bore_mask and (set_bar_num[next_set_idx] == mask_bar[0] or set_bar_num[next_set_idx] >= mask_bar[1]):    # Prevent next target from being displayed in masked slot
                            b_targ_slot = random.randint(1, 4)                                                                      # Randomize position if target is presented
                        else:
                            b_targ_slot = random.randint(0, 5)
                        b_targ_here = False
                        if b_show_targ == 1:
                            b_set[b_targ_slot] = targ
                            b_targ_here = True
                            total += 1
                            last_targ_idx = next_set_idx
                        else:
                            b_targ_here = False
                    else:
                        b_targ_here = False
                if frame == sweep_rate:
                    next_frame_ref = 1
                else:
                    next_frame_ref = frame + 1

            # Update image set a or b depending on which is not displayed
            if frame % next_frame_ref == 0 and ref_counter < 6:
                if show_buffer:
                    a_images[ref_counter].image = image_fns[a_set[ref_counter]]
                else:
                    b_images[ref_counter].image = image_fns[b_set[ref_counter]]
                ref_counter += 1
                next_frame_ref += 1
                if frame == sweep_rate:
                    next_frame_ref = 1
            elif ref_counter >= 6:
                ref_counter = 0
                next_frame_ref = math.pi

            # Check key response
            if mac: keypress = iokeyboard.getPresses(keys = [response_key])
            else: keypress = event.getKeys(keyList = [response_key])

            # Check key response for escape to quit experiment
            if mac: quit_key = iokeyboard.getPresses(keys = ['escape'])
            else: quit_key = event.getKeys(keyList = ['escape'])
            if 'escape' in quit_key:
                win.close()
                core.quit()
                raise Exception('User quit experiment with escape key')

            # Update bar location on proper frame
            if frame % sweep_rate == 0:
                bar_counter += 1
                for each in a_images:
                    each.pos += speed
                for each in b_images:
                    each.pos += speed

            # Stop bar at edge of screen
            if (a1.pos[0] > r_marg or     # Right edge
                a1.pos[0] < l_marg or     # Left edge
                a1.pos[1] < b_marg or     # Bottom edge
                a1.pos[1] > t_marg):      # Top edge
                # Remove last target addition if not displayed
                if a_targ_here and show_buffer:
                    total -= 1
                elif b_targ_here and not show_buffer:
                    total -= 1
                break_out = True
                break

            # Show each updated image
            if loop_count <= set_list[dur_idx]:
                if not show_buffer:
                    for each in a_images:
                        each.draw()
                elif show_buffer:
                    for each in b_images:
                        each.draw()
            elif frame % sweep_rate == 0:
                loop_count = 1
            if bore_mask:
                if bar_counter == 1 or bar_counter == n_bars:
                    bore_mask_L.draw()
                    bore_mask_R.draw()
            fix_circle.draw()
            fix_cross.draw()
            fix_dot.draw()
            win.flip()
            # record bar starts time
            if frame ==1:
                tStartBar=time.time()-tStartExp
            if (frame-1) % refresh_rate == 0:
                tStartImage = time.time()-tStartExp
                            
            # Alternate between sets a and b; Save stimuli info to log
            if (frame + 1) % refresh_rate == 0:
                string_rt = str(this_rt)[1:-2]
                if show_buffer:
                    if save_log:
                        stim_log.write('%i,%f,%f,%s,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%f,%s,%i,%i,%s\n'
                                       %(trial,tStartBar,tStartImage,direct,b_set[0],b1.pos[0],b1.pos[1],b_set[1],b2.pos[0],b2.pos[1],b_set[2],b3.pos[0],b3.pos[1],b_set[3],b4.pos[0],b4.pos[1],b_set[4],b5.pos[0],b5.pos[1],b_set[5],
                                         b6.pos[0],b6.pos[1],(set_timings[next_set_idx - 1] + ((sweep_dur + tr) * (trial - 1))),b_targ_here,targ,b_targ_slot,string_rt))
                    show_buffer = False
                    if a_targ_here:
                        targ_here = True
                        response_timer.reset(response_period)
                        start_rt = core.MonotonicClock()
                    elif response_timer.getTime() <= 0: targ_here = False
                else:
                    if save_log:
                        stim_log.write('%i,%f,%f,%s,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%i,%f,%s,%i,%i,%s\n'
                                       %(trial,tStartBar,tStartImage,direct,a_set[0],a1.pos[0],a1.pos[1],a_set[1],a2.pos[0],a2.pos[1],a_set[2],a3.pos[0],a3.pos[1],a_set[3],a4.pos[0],a4.pos[1],a_set[4],a5.pos[0],a5.pos[1],a_set[5],
                                         a6.pos[0],a6.pos[1],(set_timings[next_set_idx - 1] + ((sweep_dur + tr) * (trial - 1))),a_targ_here,targ,a_targ_slot,string_rt))
                    show_buffer = True
                    if b_targ_here:
                        targ_here = True
                        response_timer.reset(response_period)
                        start_rt = core.MonotonicClock()
                    elif response_timer.getTime() <= 0: targ_here = False
                this_rt = []

            if testing:
                test.append(win.nDroppedFrames)
                if test[-1] > test[-2]:
                    print('Overall, %i frames were dropped.' % win.nDroppedFrames)
                    print('Frame: %i' % frame)
        # while bartimer.getTime()>0:
        #     win.flip()
        if break_out:
            # wait to meet the sweep duration
            fix_circle.fillColor = fix_color
            fix_circle.draw()
            fix_cross.draw()
            fix_dot.draw()
            while sweeptimer.getTime() > 0:
                win.flip()
            break
    tSweepEnd = time.time()-tStartExp
    win.flip()
    accuracy = 100 * correct / total
    print('Direction: %s'%direct)
    print('Accuracy: %d%%' % accuracy)
    mean_rt = np.average(rt)
    datafile.write('%i,%f,%f,%s,%i,%f,%f,%i,%i,%f,%i\n' %(trial, tStartSweep, tSweepEnd-tStartSweep, direct, refresh_rate, stim_dur, accuracy, correct, total, mean_rt, false_pos))

    return accuracy
# =============================================================================================================================================<


# 9. Set up Eyetracker
if eye_tracking:
    # Configure eyetracker
    tracker_config = psyut.config_et(params, edf_filename, mac)
    if mac: io = launchHubServer(window=win, **tracker_config)
    else: io = launchHubServer(**tracker_config)
    et = io.devices.tracker
    setup = et.runSetupProcedure()
    # Begin recording
    io.clearEvents()
    et.sendMessage('xDAT 101')
    et.setRecordingState(True)
else:
    io = launchHubServer()
# Setup ioHub keyboard method
if mac: iokeyboard = io.devices.keyboard


inst_text = visual.TextStim(win = win, color = text_color, height = image_h / 4, wrapWidth = params['stim_bounds'][0])
# 10. Target presentation & peripheral calibration
if params['calibrate_targ']:
    calib_x = [l_marg, 0, r_marg, 0]
    calib_y = [0, t_marg, 0, b_marg]
    calib_text = 'You will now be presented with the target so that you will have an idea of what the image looks like in your peripheral vision. Please press %s to indicate that you have seen the target in each location. Press %s to begin.' % (resp_key_text, resp_key_text)
    inst_text.text = calib_text
    inst_text.draw()
    targ_image.image = image_fns[targ]
    win.flip()
    if mac: iokeyboard.waitForPresses(keys = [response_key])
    else: event.waitKeys(keyList = [response_key])
    targ_image.draw()
    win.flip()
    if mac: iokeyboard.waitForPresses(keys = [response_key])
    else: event.waitKeys(keyList = [response_key])
    for c in list(range(0, 4)):
        targ_image.pos = (calib_x[c], calib_y[c])
        targ_image.draw()
        fix_circle.draw()
        fix_cross.draw()
        fix_dot.draw()
        win.flip()
        if mac: iokeyboard.waitForPresses(keys = [response_key])
        else: event.waitKeys(keyList = [response_key])
    win.flip()


# 11. Instructions
if not scanning:
    inst_text.text = 'For each trial, you will be presented with a target. You should maintain fixation on the cross in the center of the screen. If you see the target image, press the spacebar. Press the spacebar to begin.'
    inst_text.draw()
    win.flip()
    if mac: iokeyboard.waitForPresses(keys=[' '])
    else: event.waitKeys(keyList = ['space'])
    tStartExp = time.time()
    win.flip()

# 12. Run sweeps
if scanning:
    inst_text.text = 'Get ready!'
    inst_text.draw()
    if params['extended_start']:
        win.flip()
        if mac: iokeyboard.waitForPresses(keys = [' '])
        else: event.waitKeys(keyList = ['space'])
        fix_circle.draw()
        fix_cross.draw()
        fix_dot.draw()
        win.flip()
        tStartExp = time.time()
        if mac: iokeyboard.waitForPresses(keys = [pulse_cue])
        else: event.waitKeys(keyList = [pulse_cue])
        static = StaticPeriod(screenHz = fps)
        static.start(9.5)
        static.complete()
        if mac: iokeyboard.waitForPresses(keys = [pulse_cue])
        else: event.waitKeys(keyList = [pulse_cue])
    else:
        print('Subject is ready.')
        if mac: iokeyboard.waitForPresses(keys = [pulse_cue])
        else: event.waitKeys(keyList = [pulse_cue])
        win.flip() # see 'Get Ready' experiment starts!
        # et.sendMessage('xDAT 100')
        tStartExp = time.time()
        static = StaticPeriod(screenHz = fps)
        static.start(tr)
        static.complete()
# Maintain fixation display across sweeps
fix_circle.autoDraw = True
fix_cross.autoDraw = True
fix_dot.autoDraw = True

# Run each sweep
trialOnset = []
trialDur = []
for x in list(range(0, n_trials)):
    if eye_tracking:
        eye_msg = 'trial ' + str(trial)
        et.sendMessage(eye_msg)
    print('Sweep #%i' %(x+1))
    print('Stimuli Duration: ' + str(time_list[dur_idx]) + ' ms')
    tStartTrial = time.time()
    accuracy = sweep(tStartExp=tStartExp, bar_dur=bar_dur, direct = types[x % 4], refresh_rate = set_list[dur_idx], trial=trial)
    print('%ss sweep stops\n'%(time.time()-tStartExp))
    trial += 1
    # Staircase image refresh rate by indexing list of appropriate refresh rates
    if dur_idx < len(set_list) - 1 and accuracy < stair_lower:
            dur_idx += 1
    elif dur_idx > 0 and accuracy >= stair_upper:
            dur_idx -= 1
    tTrialEnd = time.time()
    trialOnset.append(tStartTrial-tStartExp)
    trialDur.append(tTrialEnd-tStartTrial)
# add 12s blank screen in the end
endtimer = CountdownTimer(13)
# fix_circle.draw()
# fix_cross.draw()
# fix_dot.draw()
while endtimer.getTime() > 0:
    win.flip()
expt_dur = time.time()-tStartExp
# Save parameters, Close CSV file & Eyetracker
params['expt_dur']=expt_dur
params['trial_onset']=trialOnset
params['trial_dur']=trialDur
datafile.write('\n\n\n')
for key in params:
    datafile.write(key + ',' + str(params[key]) + '\n')
datafile.close()
if save_log:
    stim_log.close()
if eye_tracking:
    et.sendMessage('xDAT 111')
    et.setRecordingState(False)
    et.setConnectionState(False)
    io.quit()
    if long_edf_name:
        os.rename(edf_filename, long_edf_filename)


print('Run ' + str(run_number) + ' (' + str(expt_dur) + ' s)' + ' completed! \n')
# print(expt_end-expt_start) = 1.3
win.close()
core.quit()
