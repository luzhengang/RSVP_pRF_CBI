#!/usr/bin/env python3

# rsvp_stim_prep.py
# /share/home/jeff/docs/imagery_docs/experiments/rsvp/
# 
# Prepare stimuli for rsvp_sweep experiment
# 1. Make stimuli directory if it doesn't exist
# 2. Check for unprocessed stimuli directory
# 3. Generate new_image template images for resizing
# 4. Load all unprocessed images; Resize/reshape all images

# Created: 3/2/20
# Updated: 3/2/20
# Jeff Kravitz
# >------------------------------------------------------------<


# Notes:
# - This script is designed for processing:
#       - stimuli appearing on a white or grey background
#       - stimuli that is no larger than 800x800 pix, and no smaller than 100x100 pix
#       - stimuli that are pngs
# - All images are reshaped into square .jpg files


# 0. Load modules
from inspect import getsourcefile
from os.path import abspath
from PIL import Image
import os.path
import glob


# 0. Set parameters
background_color = 'grey'   # Options: grey, white, black

# 1. Make stimuli directory if it doesn't exist
path = abspath(getsourcefile(lambda:0))
sep_loc = path.rfind('/')
path = path[0:sep_loc + 1]
stimuli_path = path + 'Stimuli'
if not os.path.isdir(stimuli_path):
    os.mkdir(stimuli_path)


# 2. Check for unprocessed stimuli directory
#unproc_stimuli_path = path + 'Unprocessed_Stimuli'
unproc_stimuli_path = path + 'Unproc_Stimuli_pngs'
if not os.path.isdir(unproc_stimuli_path):
    raise Exception('There is no folder containing stimuli to process... \
                    please copy your stimuli folder to {}'.format(path))


# 3. Generate blank new_image template images for resizing/reshaping
if background_color == 'grey':
    color = (127,127,127)
elif background_color == 'white':
    color = (255,255,255)
elif background_color == 'black':
    color = (0,0,0)
blank_200 = Image.new('RGBA', (200, 200), color)
blank_300 = Image.new('RGBA', (300, 300), color)
blank_400 = Image.new('RGBA', (400, 400), color)
blank_500 = Image.new('RGBA', (500, 500), color)
blank_600 = Image.new('RGBA', (600, 600), color)
blank_700 = Image.new('RGBA', (700, 700), color)
blank_800 = Image.new('RGBA', (800, 800), color)


# 4. Load all unprocessed images; Resize/reshape all images
all_images = glob.glob(unproc_stimuli_path + '/*')
for image in all_images:
    sep_loc = image.rfind('/')
    image_filename = image[sep_loc + 1:-4]
    old_image = Image.open(image)
    if old_image.size[0] > 700 or old_image.size[1] > 700:
        new_image = blank_800.copy()
    elif old_image.size[0] > 600 or old_image.size[1] > 600:
        new_image = blank_700.copy() 
    elif old_image.size[0] > 500 or old_image.size[1] > 500:
        new_image = blank_600.copy()
    elif old_image.size[0] > 400 or old_image.size[1] > 400:
        new_image = blank_500.copy()
    elif old_image.size[0] > 300 or old_image.size[1] > 300:
        new_image = blank_400.copy()
    elif old_image.size[0] > 200 or old_image.size[1] > 200:
        new_image = blank_300.copy()
    else:
        new_image = blank_200.copy()
    pos = []
    pos.append(round((new_image.size[0] - old_image.size[0]) / 2))
    pos.append(round((new_image.size[1] - old_image.size[1]) / 2))
    #new_image.paste(old_image, (pos[0], pos[1]))
    new_image.paste(old_image, (pos[0], pos[1]), old_image)
    new_image.load()
    final_image = Image.new("RGB", new_image.size, (127,127,127))
    final_image.paste(new_image, mask = new_image.split()[3])
    new_image = final_image.copy()
    new_image = new_image.resize((200,200), Image.ANTIALIAS)
    if os.stat(image).st_size > 65000:
        quality = 85
    elif os.stat(image).st_size > 35000:
        quality = 85
    else: quality = 85
    
    new_image.save(stimuli_path + '/' + image_filename + '.jpg', optimize = True, quality = quality)
    del new_image, old_image
    

all_images = glob.glob(stimuli_path + '/*')
for image in all_images:
    sep_loc = image.rfind('/')
    image_filename = image[sep_loc + 1:-4]
    new_image = Image.open(image)
    if os.stat(image).st_size > 8000:
        quality = 50
        new_image.save(stimuli_path + '/' + image_filename + '.jpg', optimize = True, quality = quality)
    
    