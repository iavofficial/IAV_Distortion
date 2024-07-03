#!/bin/bash

working_directory=$(pwd)
echo "Working directory: $working_directory"

# move pipfile to current working directory
echo "Getting Pipfile from root directory..."
mv ../Pipfile .

# remove old pipenv
echo "Removing old pipenv if existing..."
pipenv --rm
if [ -f "Pipfile.lock" ]; then
    rm Pipfile.lock
fi

# restet VIRTUAL_ENV to cleat the path for pipenv environment
export VIRTUAL_ENV=""

# install pipenv
echo "Installing pipenv..."
pipenv install --skip-lock

# get jquery dependencies
ui_resources_directory="UserInterface/static/external_resources"

# list of required resources:
jquery_version="3.7.1"
jquery_url="https://code.jquery.com/jquery-$jquery_version.min.js"
jquery_directory=$ui_resources_directory

socketio_version="4.7.5"
socketio_url="https://cdnjs.cloudflare.com/ajax/libs/socket.io/$socketio_version/socket.io.js"
socketio_directory="$ui_resources_directory/socketio/$socketio_version"

# remove old files if exist
if [ -d "$ui_resources_directory" ]; then
    echo "Removing old external recources..."
    rm -rf $ui_resources_directory
fi

# recreate directories
echo "Creating directories for external resources..."
if [ ! -d "$jquery_directory" ]; then
    mkdir -p $jquery_directory
fi
if [ ! -d "$socketio_directory" ]; then
    mkdir -p $socketio_directory
fi

# download resources - resources must be added here!
echo "Downloading external resources..."
if [ $(command -v wget) ]; then
    wget -P "$jquery_directory" "$jquery_url"
    wget -P "$socketio_directory" "$socketio_url"
elif [ $(command -v curl) ]; then
    cd "$working_directory/$jquery_directory" && { curl -O "$jquery_url" ; cd -; }
    cd "$working_directory/$socketio_directory" && { curl -O "$socketio_url" ; cd -; }
else
    echo -e "\033[0;31mError: wget or curl requiered! \033[0m"
    read
fi