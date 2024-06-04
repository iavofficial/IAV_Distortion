#!/bin/bash

working_directory=$(pwd)

# set password, this has to be adapted in the future, so that the password won't be stored in clear text anywhere in the system
env_file="$working_directory/.env"

function configure_password() {
    while true; do
        while true; do
            read -s -p "Enter password for staffUI (at least 6 charakters): " password
            echo
            if [[ ${#password} -ge 6 ]]; then
                # accept input, since it has at least 6 charakters
                break
            else
                echo "Password must be at least 6 characters long. Please try again."
            fi
        done
            read -s -p "Confirm password: " password2
            echo
            if [ "$password" = "$password2" ]; then
                echo "Passwords match. Password safed!"
                if grep -q "ADMIN_PASSWORD=" "$env_file"; then
                    # If exists, use sed to replace its value
                    sed -i "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$password/" $env_file
                else
                    # If doesn't exist, append it to the env_file
                    echo "ADMIN_PASSWORD=$password" >> $env_file
                fi
                break
            else
                echo "Passwords do not match. Please try again."
            fi
    done
}

if [ -f "$env_file" ]; then
    echo "creating .env file"
    if grep -q "ADMIN_PASSWORD=" "$env_file"; then
        read -p "Password already set. Do you want to set a new one? (y/n) " -n 1 -r
        echo    # move to a new line
        if [[ $REPLY =~ ^[Yy]$ ]]
        then
            configure_password
        else
            echo "Using existing password."
        fi
    else
        echo "No password configured yet, please set one..."
        configure_password
    fi
else 
    echo "Die Datei $env_file existiert nicht. Sie wird erzeugt..."
    touch "$env_file"
    echo "Die Datei $env_file wurde erfolgreich erzeugt."
    configure_password
fi

# move pipfile to current working directory
mv ../Pipfile .

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
    echo -e "\033[0;31mError: wget or curl requiered! \033[0m"
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
echo "Exec=$working_directory/run_IAV-Distortion.sh" >> "$desktop_item"
echo "Terminal=true" >> "$desktop_item"
echo "Type=Application" >> "$desktop_item"
echo "Name[de_DE]=IAV Distortion" >> "$desktop_item"
echo "Path=$working_directory" >> "$desktop_item"

# make all utility scripts in current folder executable
find . -type f -iname "*.sh" -exec chmod +x {} \;

# add add run_IAV-Distortion.sh to autostart
check_cronjobs=$(crontab -l | grep "run_IAV-Distortion.sh")
cronjob="@reboot cd $working_directory && bash run_IAV-Distortion.sh && cd"
check_existence=$(crontab -l | grep -F "$cronjob")

if [ ! -z "$check_cronjobs" ]; then
    if [ "$check_cronjobs" != "$check_existence" ]; then
        echo -e "\033[0;33mCronjobs for IAV-Distortion found, that don't match this installation. Please check if these are from different instances of IAV-Distortion. Only one instance of IAV-Distortion should run.\033[0m"
        echo "$check_cronjobs"
    fi
fi


if [ -z "$check_existence" ]; then
    read -p "Do you want to add IAV-Distortion to the autostart? (y/n) " -n 1 -r
    echo    # move to a new line
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        (crontab -l 2>/dev/null; echo "$cronjob") | crontab -
        echo -e "\033[0;32mA cronjob has been created.\033[0m"
    else
        echo -e "\033[0;33mIAV-Distortion has not been added to the autostart.\033[0m"
    fi
else
    read -p "IAV-Distortion already in autostart. Do you want to keep it? (y/n) " -n 1 -r
    echo    # move to a new line    
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        echo -e "\033[0;32mCronjob kept. IAV-Distortion in autostart.\033[0m"
    else
        (crontab -l | grep -v -F "$cronjob") | crontab -
        echo -e "\033[0;33mIAV-Distortion removed from autostart.\033[0m"
    fi
fi

# finish message
echo "Finished. Please check for errors!"
read