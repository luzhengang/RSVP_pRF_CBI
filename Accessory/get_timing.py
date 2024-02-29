# -*- coding: utf-8 -*-
#
# rsvp_timing.py
#
# Generate a CSV file that details the timing of the rsvp_sweep.py file for MRI expriments
# 1. Load experiment parameters from rsvp_params.txt
# 2. Configure remaining parameters
# 3. Write experiment sequence to csv
# 
#
# Created: 11/9/21
# Updated: 11/9/21
# Jeff Kravitz
# Curtis Lab
# New York University
# >------------------------------------------------------------<


# 0. Import modules
import math
import platform 
import sys
sys.path.append("..")

import psy_utility as psyut


# 1. Load experiment parameters from rsvp_params.txt
if platform.system() == 'Darwin' or platform.system() == 'Linux':
    mac = True
elif platform.system() == 'Windows':
    mac = False
else:
    print('Error: OS not recognized')
if mac:
    params_filename = '../rsvp_params.txt'
else:
    params_filename = '..\rsvp_params.txt'


try:
    params = psyut.get_params(params_filename = params_filename)
except:
    print('\n\nError: Please check params file')
    
'''
try:
    params = open(params_filename)
    params_list = params.readlines()
    n_trials = int(params_list[7][0:-1])
    n_bars = int(params_list[10][0:-1])
    tr = float(params_list[13][0:-1])
    tr_per_bar = int(params_list[16][0:-1])
    extended_start = params_list[67][0:-1] == 'True'
    params.close()
except: 
    print('\n\nError: Please check params file') 
'''

# 2. Configure remaining parameters

trs_per_sweep = 1 + params['tr_per_bar'] * params['n_bars']
total_trs = 1 + trs_per_sweep * params['n_trials']
types = ['Left to Right', 'Top to Bottom', 'Right to Left', 'Bottom to Top']
filename = 'RSVP_pRF_MRI_timing'
datafile = open(filename + '.csv', 'w')
datafile.write('Time,TR,Program Stage,Sweep Number,Sweep Direction\n')


# 3. Write experiment sequence to csv
# - extended_start parameter causes the rsvp_sweep.py program to use an alternative startup sequence, which must be accounted for. All other structure is the same 
if params['extended_start']:
    tr_wait = math.ceil(9.5 / params['tr'])
    datafile.write('-,-,Load program,-,-\n')
    datafile.write('0,0,Get Ready! and wait for spacebar and MRI signal,-,-\n')
    time = params['tr']
    this_tr = 1
    for i in list(range(1,tr_wait+1)):
        if i == tr_wait:
            datafile.write('%f,%i,Wait for MRI signal,-,-\n' %(time,this_tr))
        else:
            datafile.write('%f,%i,Fixate and Wait,-,-\n' %(time,this_tr))
        time += params['tr']
        this_tr += 1
    for sweep in list(range(0,params['n_trials'])):
        direc = types[sweep % 4]
        datafile.write('%f,%i,Load stimuli,%i,%s\n' %(time,this_tr,sweep+1,direc))
        time += params['tr']
        this_tr += 1
        step = 1   
        for j in list(range(1,params['n_bars']+1)):
            for k in list(range(0,params['tr_per_bar'])):
                datafile.write('%f,%i,Step %i,%i,%s\n' %(time,this_tr,step,sweep+1,direc))
                time += params['tr']
                this_tr += 1
            step += 1
else:
    datafile.write('-,-,Load and wait for MRI signal,-,-\n')
    datafile.write('0,0,-,-,-\n')
    datafile.write('%f,1,Get ready message,-,-\n' %params['tr'])
    time = params['tr'] * 2
    this_tr = 2
    for sweep in list(range(0,params['n_trials'])):
        direc = types[sweep % 4]
        datafile.write('%f,%i,Load stimuli,%i,%s\n' %(time,this_tr,sweep+1,direc))
        time += params['tr']
        this_tr += 1
        step = 1   
        for j in list(range(1,params['n_bars']+1)):
            for k in list(range(0,params['tr_per_bar'])):
                datafile.write('%f,%i,Step %i,%i,%s\n' %(time,this_tr,step,sweep+1,direc))
                time += params['tr']
                this_tr += 1
            step += 1
            
        
# Clean up
datafile.close()