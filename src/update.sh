#!/bin/bash

# create/oferride logfile for latest update attempt
logfile_path="logfiles/"
logfile_name="logfile_update.log"
logfile=$logfile_path$logfile_name
mkdir -p $logfile_path
exec > $logfile 2>&1
echo "This logfile documents only the latest update event from $(date '+%m-%d-%Y %H:%M:%S'):"
echo

# get workind directory
working_directory=$(pwd)

# terminate running instances of IAV Distortion
$working_directory/quit.sh

# reset the working directory to the latest commit from the repository (additional files like .env or logfiles will not be affected)
git reset --hard
# fetch up to date version from the repository
git fetch origin
# pull the latest version from the repository in the lokal working directory
git pull

# make all utility scripts executable
find "$working_directory" -type f -iname "*.sh" -exec chmod +x {} \;

# get dependencies
$working_directory/get_dependencies.sh

# Wait for user input before closing
echo "Update finished..."
sleep 10
$working_directory/restart_system.sh