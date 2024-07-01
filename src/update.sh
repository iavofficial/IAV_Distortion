#!/bin/bash

# get workind directory
working_directory=$(pwd)

# terminate running instances of IAV-Distortion
$working_directory/quit.sh

# discard all local changes, to prevent merge conflicts, won't delete added files (like .env)
git checkout .

# pull the latest version of the installed branch
git pull --strategy-option theirs

# make all utility scripts executable
find "$working_directory" -type f -iname "*.sh" -exec chmod +x {} \;

# get dependencies
$working_directory/get_dependencies.sh

# Wait for user input before closing
echo "Update finished..."
sleep 10
$working_directory/restart_system.sh