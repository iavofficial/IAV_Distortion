#!/bin/bash

working_directory=$(pwd)

# install pipenv
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
    rm -rf $ui_resources_directory
fi

# recreate directories
if [ ! -d "$jquery_directory" ]; then
    mkdir -p $jquery_directory
fi
if [ ! -d "$socketio_directory" ]; then
    mkdir -p $socketio_directory
fi

# download resources - resources must be added here!
if [ $(command -v wget) ]; then
    wget -P "$jquery_directory" "$jquery_url"
    wget -P "$socketio_directory" "$socketio_url"
elif [ $(command -v curl) ]; then
    cd "$working_directory/$jquery_directory" && { curl -O "$jquery_url" ; cd -; }
    cd "$working_directory/$socketio_directory" && { curl -O "$socketio_url" ; cd -; }
else
    echo "Error: wget or curl requiered!"
    read
fi

# create desktop item
current_user=$(whoami)
desktop_item="/home/$current_user/Desktop/iav_distortion.desktop"

if [ -f "$desktop_item" ]; then
    rm -rf $desktop_item
fi

echo "[Desktop Entry]" > "$desktop_item"
echo "Name=IAV Distortion" >> "$desktop_item"
echo "Comment=Run IAV Distortion" >> "$desktop_item"
echo "Exec=$working_directory/run.sh" >> "$desktop_item"
echo "Terminal=true" >> "$desktop_item"
echo "Type=Application" >> "$desktop_item"
echo "Name[de_DE]=IAV Distortion" >> "$desktop_item"
echo "Path=$working_directory" >> "$desktop_item"

# make run.sh and desctop item executable
chmod +x run.sh
chmod +x $desktop_item

# add add run.sh to autostart
(crontab -l 2>/dev/null; echo "@reboot cd $working_directory && bash run.sh && cd") | crontab -

# finish message
echo "Finished. Please check for errors!"
read