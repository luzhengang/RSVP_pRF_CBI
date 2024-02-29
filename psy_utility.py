# -*- coding: utf-8 -*-
#
# psy_utility.py
#
# A Series of supporting functions for smooth psychopy experiments
# 1. Load experiment parameters from exp_params.txt
# 2. Enter session info
# 3. Check for Data folders; Initialize data file
# 4. Setup eyetracker configuration info to pass into the main experiment script
#
# Created: 12/13/21
# Updated: 12/15/21
# Jeff Kravitz
# Curtis Lab
# New York University
# >------------------------------------------------------------<


# 0. Load modules
from psychopy import gui
from datetime import datetime
from os.path import abspath
from inspect import getsourcefile
import os.path
import platform


# 1. Load experiment parameters from exp_params.txt
# This function will load in variables from a params file as long as it follows the specified format
def error_message():
    print('\n\nError: Please check params file. Ensure that it follows the format used in psy_utility.py. The format is as follows: \n')
    print('Each param will use 3 lines. 1. variable_name, description, and variable_format, 2. value, and 3. filler space')
    print('First line begins with variable_name = description... Format: string, int, float, or list')
    print('The spaces are important. There must be a space after the hash, and a space before the equals sign, and a space after the capitalized format, as in Format: ')
    print('Second line is the value for the variable')
    print('Third line is a filler marker, e.g. ---------#')
    print('Repeat for each param \n')
    print('Example:')
    print('# disp_units = Units used to display stimuli. Options: pix; deg not yet supported. Format: string')
    print('pix')
    print('---------# \n\n')
          
def get_params(params_filename):
    params = {}
    try:
        params_txt = open(params_filename)
        params_list = params_txt.readlines()
        i = 1
        for line in params_list:
            this_line = line[0:-1]
            if i % 3 == 1:
                if this_line[0:2] != '# ':
                    print('\nError: Issue with: ' + str(this_line) + '\n')
                    raise Exception()
                var_name = this_line.split(sep = ' =')[0][2:]
                var_format = this_line.split(sep = 'Format: ')[-1]
            if i % 3 == 2:
                if var_format == 'string':
                    params[var_name] = str(this_line)
                elif var_format == 'int':
                    params[var_name] = int(this_line)
                elif var_format == 'float':
                    params[var_name] = float(this_line)
                elif var_format == 'bool':
                    params[var_name] = str(this_line) == 'True'
                elif var_format == 'list':
                    params[var_name] = list(this_line.split(sep = ','))
            i += 1
        params_txt.close()
    except:
        error_message()
    return params


# 2. Enter session info
# This function will run a psychopy GUI to collect standard experiment information
# To add a field to the GUI, pass a dict to the new_fields argument
#  - To add a set of options, pass: {'field_name': [1,2,3]}  or  ['list', 'of', 'your', 'options']
#  - To add a yes/no option, pass: {'field_name': False}  or  {'field_name': True}
#  - To add a blank field for text or number entry, pass: {'field_name': None}
#  - You can add as many fields as you want, just add each one to the dict passed to new_fields
#  - To run the standard GUI with no new fields, simply leave new_fields argument blank.
def run_gui(exp_name = 'PsychoPy Skeleton', new_fields = {}):
    subinfo = gui.Dlg(title = exp_name)
    subinfo.addText('Session Info')
    subinfo.addField('Subject Initials')
    subinfo.addField('Run Number')
    subinfo.addField('Eyetracker', False)
    subinfo.addField('MRI', False)
    subinfo.addField('Fullscreen', False)
    subinfo.addField('Use Second Monitor', False)
    if new_fields:
        key_list = []
        keys = list(new_fields.keys())
        for key in keys:
            if type(new_fields[key]) is list:
                subinfo.addField(key, choices = new_fields[key])
            elif new_fields[key] == None:
                subinfo.addField(key)
            else:
                subinfo.addField(key, new_fields[key])
            key_list.append(key)
    sub_data = subinfo.show()
    if subinfo.OK:
        print('\n\n')
        print('>-----------Start-Run-----------< \n')
        print('Subject:          ' + sub_data[0].upper())
        print('Run:              ' + sub_data[1])
        print('Eyetracking:      ' + str(sub_data[2]))
        print('MRI:              ' + str(sub_data[3]))
        if new_fields:
            i = 4
            for key in keys:
                print((key + ':').ljust(18) + str(sub_data[i]))
                i += 1
        print('\n')
    else:
        raise Exception('Error: User cancelled')
    run_info = {}
    run_info['sub_name'] = sub_data[0].upper()
    run_info['run_number'] = sub_data[1]
    run_info['eye_tracking'] = sub_data[2]
    run_info['scanning'] = sub_data[3]
    run_info['fullscreen'] = sub_data[4]
    if sub_data[5]:
        run_info['which_screen'] = 1
    else:
        run_info['which_screen'] = 0
    if new_fields:
        j = 6
        for key in keys:
            run_info[key] = sub_data[i]
            j += 1
            
    return run_info


# 3. Check for Data folders; Initialize data file
# This function will configure the program to the OS, check for a data folder and make one if it doesn't exist,
# and create unique filenames based on runtime info and date/time in order to minimze chances of overwrite.
# csv files are safe from overwrite with this system, but edf files are still vulnerable due to filename length limit.
def config_sys(exp_name, run_info):
    date = datetime.now().strftime('%m-%d-%Y_hr%H_min%M_sec%S')
    if platform.system() == 'Darwin' or platform.system() == 'Linux':
        mac = True
    elif platform.system() == 'Windows':
        mac = False
    else:
        raise Exception('Error: Cannot detect OS')
    # Fullscreen Mac warning
    if run_info['fullscreen'] and mac and run_info['which_screen'] == 1:
        mac_notice = gui.Dlg(title='Warning')
        mac_notice.addText('WARNING: Since Mavericks or newer, Mac OSx does not allow fullscreen projection ')
        mac_notice.addText('to a second monitor. The experiment should still run, but if you experience issues, ')
        mac_notice.addText('set the second monitor as the primary monitor. To do this, open System Preferences -> ')
        mac_notice.addText('Displays -> Arrangements, and then drag the white bar from one monitor to the other.')
        mac_notice.addText(' ')
        mac_notice.show()
        if not mac_notice.OK:
            raise Exception('Error: User cancelled')
            
    path = abspath(getsourcefile(lambda:0))
    if mac:
        sep_loc = path.rfind('/')
    else:
        sep_loc = path.rfind('\\')
    path = path[0:sep_loc + 1]
    data_path = path + 'Data'
    if not os.path.isdir(data_path):
        os.mkdir(data_path)
    if mac:
        filename = data_path + '/' + run_info['sub_name'] + '_run' + run_info['run_number'] + '_' + date + '_' + exp_name + '_summary'
    else:
        filename = data_path + '\\' + run_info['sub_name'] + '_run' + run_info['run_number'] + '_' + date + '_' + exp_name + '_summary'
    # Code to (attempt to)  allow edfs to be named with 8+ chars - not functional yet
    #if len(run_info['sub_name']) < 4:
    #    edf_filename = run_info['sub_name'] + '_R' + str(run_info['run_number'])
    #    long_edf_name = False
    #else:
    #    edf_filename = run_info['sub_name'][0:3] + '_R' + str(run_info['run_number'])
    #    long_edf_filename = run_info['sub_name'] + '_R' + str(run_info['run_number'])
    #    long_edf_name = True
    edf_filename = run_info['sub_name'] + '_R' + str(run_info['run_number'])
    
    return filename, edf_filename, mac
    

# 4. Setup eyetracker configuration info to pass into the main experiment script
def config_et(params, edf_filename, mac):
    eyetracker_config = {'name': 'tracker'}
    eyetracker_config['model_name'] = 'EYELINK 1000 DESKTOP'
    eyetracker_config['runtime_settings'] = {'sampling_rate': 500, 'track_eyes': 'RIGHT'}
    eyetracker_config['default_native_data_file_name'] = edf_filename
    eyetracker_config['network_settings'] = params['eyetracker_ip']
    if mac:
        eyetracker_config['calibration'] = {'auto_pace': True,
                                            'target_duration': 1.5,
                                            'target_delay': 1.0,
                                            'screen_background_color': (0, 0, 0),
                                            'type': params['calib_type'],
                                            'unit_type': None, # None == use same units as psychopy win
                                            'color_type': None, # None == use same color space as psychopy win
                                            'target_attributes': {'outer_diameter': 33,
                                                                  'inner_diameter': 6,
                                                                  'outer_fill_color': [-0.5, -0.5, -0.5],
                                                                  'inner_fill_color': [-1, 1, -1],
                                                                  'outer_line_color': [1, 1, 1],
                                                                  'inner_line_color': [-1, -1, -1]}}
    tracker_config = {'eyetracker.hw.sr_research.eyelink.EyeTracker': eyetracker_config}
    
    return tracker_config

