# et_display.sh
# Change the screen that eyelink will use to calibrate the eyetracker
#
# Jeff Kravitz
# New York University

# Check active conda envionments
active_env=$CONDA_DEFAULT_ENV
if [ -z $active_env ]
then
  printf "\nError: There is no active environment. Please activate your psychopy env and try again.\n\n" && exit 0
fi
# conda activate clayspace_psychopy_env
env_dir=`which python`
env_dir=${env_dir/bin*/}
env_dir="${env_dir}lib/python3.6/site-packages/psychopy/iohub/devices/display/default_display.yaml"
# conda deactivate
filename=$env_dir
line=$(grep -n "device_number:" $filename)
linenum=${line:0:2}
echo ' '
echo 'This command changes the monitor to which the eyetracker will display. 0 refers to the first monitor. 1 refers to the second monitor, etc.'
echo 'The eyetracker is currently set to display to:'
old=`cat $filename | head -n $linenum | tail -n 1`
echo $old
echo 'Which monitor would you like to use to display the eyetracker?'
read new
sed -i '' "s/$old/    device_number: $new/" $filename
