#!/bin/bash

# get workind directory
working_directory=$(pwd)

# terminate running instances of IAV-Distortion
$working_directory/src/quit.sh

# pull the latest version of the installed branch
git pull

# make all utility scripts executable
find "$working_directory" -type f -iname "*.sh" -exec chmod +x {} \;

# get dependencies
$working_directory/src/get_dependencies.sh

# Wait for user input before closing
echo "Update finished..."
sleep 10