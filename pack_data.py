# -*- coding: utf-8 -*-
#
# pack_data.py
# 
# Collect and package data after RSVP_pRF session
# 1. Check for operating system
# 2. Enter data packing options
# 3. Check to make sure requested data exists
# 4. Create directories & move files
#
# Created: 12/14/20
# Updated: 12/14/20
# Jeff Kravitz
# Curtis Lab
# New York University
# >------------------------------------------------------------<


# 0. Load modules
from psychopy import gui
from datetime import datetime
from inspect import getsourcefile
from os.path import abspath
import os.path
import platform
import shutil
import glob


# 1. Check for operating system
if platform.system() == 'Darwin' or platform.system() == 'Linux':
    mac = True
elif platform.system() == 'Windows':
    mac = False
else:
    other_os = gui.Dlg(title='Operating System')
    other_os.addText('What Operating System are you using? Select one.')
    other_os.addField('I am using Mac or Linux', False)
    other_os.addField('I am using Windows     ', False)
    other_os_info = other_os.show()
    if not other_os.OK:
        raise Exception('Error: User cancelled')
    mac  = other_os_info[0]
path = abspath(getsourcefile(lambda:0))
if mac:
    sep = '/'
else:
    sep = '\\'
sep_loc = path.rfind(sep)
path = path[0:sep_loc + 1]
data_path = path + 'Data'


# 2. Enter data packing options
runinfo = gui.Dlg(title='pack_data')
runinfo.addField('Subject Initials')
runinfo.addField('Zip packed data ', False)
runinfo.addText('Select the types of data to pack')
runinfo.addField('Summary files    ', False)
runinfo.addField('Log files        ', False)
runinfo.addField('EDF files        ', False)
run_data = runinfo.show()  
if not runinfo.OK:
    raise Exception('Error: User cancelled')
sub_name = run_data[0].upper()
zip_folder = run_data[1]
pack_behav = run_data[2]
pack_log = run_data[3]
pack_edfs = run_data[4]


# 3. Check to make sure requested data exists
if pack_behav and not os.path.isdir(data_path):
    raise Exception('Error: There is no behavioral csv data to pack')
elif not os.path.isdir(data_path):
    os.mkdir(data_path)
if pack_behav:
    behav_files = glob.glob(data_path + sep + sub_name + '*summary.csv')
    if len(behav_files) == 0:
        raise Exception('Error: There are no behavioral csv files to pack')
if pack_log:
    log_files = glob.glob(data_path + sep + sub_name + '*stimlog.csv')
    if len(log_files) == 0:
        raise Exception('Error: There are no stimuli log files to pack')
if pack_edfs:
    edf_files = glob.glob(path + sep + sub_name + '*.EDF')
    if len(edf_files) == 0:
        raise Exception('Error: There are no EDF files to pack')


# 4. Create directories & move files
date = datetime.now().strftime('%m-%d-%Y_hr%H_min%M_sec%S')
this_run = sub_name + '_' + str(date[0:10]) + '_RSVP_pRF'
pack_path = data_path + sep + this_run
if os.path.isdir(pack_path):
    pack_path += '_' + str(date[11:-1])
os.mkdir(pack_path)
if pack_behav:
    pack_sum_path = pack_path + sep + 'Summary'
    os.mkdir(pack_sum_path)
    for file in behav_files:
        shutil.move(file, pack_sum_path)
if pack_log:
    pack_log_path = pack_path + sep + 'Log'
    os.mkdir(pack_log_path)
    for file in log_files:
        shutil.move(file, pack_log_path)
if pack_edfs:
    pack_edf_path = pack_path + sep + 'EDF'
    os.mkdir(pack_edf_path)
    for file in edf_files:
        shutil.move(file, pack_edf_path)
if zip_folder:
    shutil.make_archive(pack_path, 'zip', pack_path)
message = gui.Dlg(title='status')
message.addText('Success!')
message.show()