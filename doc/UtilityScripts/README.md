# Utility Scripts
The subsequent section describes the utility scripts and their respective functionalities.
The term "utility scripts" refers to (primarily) bash scripts which facilitate functions that have been separated from the main program (such as the installation of the program). 

## Unix environment
The subsequent utility scripts are intended for Unix environments and have been tested on Raspberry PI OS.

### installer.sh
[!IMPORTANT]
This script requires an active internet connection.


### install.sh
[!IMPORTANT]
This script requires an active internet connection.

This script undergoes the process to establishing all necessary preconditions and requirements to properly run IAV-Distortion.
The script accomplishes the following tasks:
1. Configures the password for the StaffUI.
2. Installs the virtual pipenv environment.
3. Downloads further required external resources (such as JavaScript libraries).
4. Creates a Desktop Item, from which IAV-Distortion can be initiated.
5. Makes the remaining utility scripts executable.
6. Optionally configures the program's auto-start feature (using a cron job).

### update.sh
[!IMPORTANT]
This script requires an active internet connection.

tbd.

### run_IAV-Distortion.sh
This script will run IAV-Distortion in it's virtual pipenv environment.

### quit.sh
This script will identify running processes of main.py and terminate them.

[!WARNING]
This can interfere with other processes running other main.py scripts and terminate them.

### restart_system.sh
tbd.

### restart_program.sh
tbd.