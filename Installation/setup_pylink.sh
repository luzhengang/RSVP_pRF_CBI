# setup_pylink.sh
# Add Pylink (EyeLink eyetraacker package for python) to conda environment (Mac only)
# Instructions:
# - Ensure that you have a recent version of EyeLink Dev Kit installed in /Applications
# - Ensure that your envionment has python3.6 installed
# - Activate the environment in which you want to install pylink
# - Navigate to the location of setup_pylink.sh (it will run from anywhere you place it)
# - In your bash terminal: sh setup_pylink.sh
#
# Jeff Kravitz
# 1/20/22
# Curtis Lab
# New York University


# Check active conda envionments
active_env=$CONDA_DEFAULT_ENV
if [ -z $active_env ]
then
  printf "\nError: There is no active environment. Please activate your env and try again.\n\n" && exit 0
fi

# Find env
env_dir=$CONDA_PREFIX
py_dir="${env_dir}/lib/python3.6/"
env_dir="${env_dir}/lib/python3.6/site-packages/"
new_env_dir="${env_dir}pylink/"

# Check for python3.6
[ ! -d $py_dir ] && printf "\nError: This script only works for environments in which python3.6 is installed.\n\n" &&  exit 0

# Find EyeLink
eyelink_dir="/Applications/EyeLink"
[ ! -d $eyelink_dir ] && printf "\nError: EyeLink could not be found. Please make sure EyeLink Dev Kit is installed in Applications.\n\n" && exit 0
[ -d $eyelink_dir ] && printf "\nEyeLink found."

# Find Pylink
pylink_dir="/Applications/EyeLink/SampleExperiments/Python/3.6/pylink"
[ ! -d $pylink_dir ] &&  printf "\nError: Pylink 3.6 could not be found. Please update your EyeLink Dev Kit version.\n\n" && exit 0
[ -d $pylink_dir ] &&  printf "\nPylink found."

# Copy Pylink to env
if [ -d $new_env_dir ]
then
  printf "\nThere is already a copy of Pylink installed in this environment."
  printf "\nWould you like to remove the old copy of Pylink and continue?  y/n\n"
  read continue
  if [ "$continue" = "y" ]
  then
    rm -rf $new_env_dir
  else
    printf "\nCanceled. No changes made.\n\n"
  fi
fi
[ ! -d $new_env_dir ] && cp -r $pylink_dir $env_dir && [ -d $new_env_dir ] && printf "\nSuccess!\n\n" && exit 0
