#!/bin/bash

# create/oferride logfile for latest update attempt
exec > logfile_update.log 2>&1
echo "This logfile documents only the latest update event from $(date '+%m-%d-%Y %H:%M:%S'):"
echo

# get workind directory
working_directory=$(pwd)

# terminate running instances of IAV-Distortion
$working_directory/quit.sh

# fetch up to date version from the repository
git fetch origin

# reset the working directory to the latest commit from the repository (additional files like .env or logfiles will not be affected)
git reset --hard

# make all utility scripts executable
find "$working_directory" -type f -iname "*.sh" -exec chmod +x {} \;

# get dependencies
$working_directory/get_dependencies.sh

# Wait for user input before closing
echo "Update finished..."
sleep 10
$working_directory/restart_system.sh