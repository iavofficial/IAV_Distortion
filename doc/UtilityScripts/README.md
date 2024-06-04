# Utility Scripts
The subsequent section describes the utility scripts and their respective functionalities.
The term "utility scripts" refers to (primarily) bash scripts which facilitate functions that have been separated from the main program (such as the installation of the program). 

## Unix environment
The subsequent utility scripts are intended for Unix environments and have been tested on Raspberry PI OS.

### installer.sh
[!IMPORTANT]
This script requires an active internet connection and *git* installed on the system.

This script serves as a sort of installer.
It can be downloaded and run on the target system to obtain IAV-Distortion from GitHub and install it subsequently.
The script performs the following tasks:
1. Checks if a folder named "IAV-Distortion" already exists and asks if it should be used for installation. (**WARNING:** All data within this folder will be overwritten!)
If no such folder exists or if the existing one should not be used for installation, it asks for the desired installation path.
If multiple such folders exist, an additional warning is issued.
2. Queries which branch from the IAV-Distortion repository should be used.
3. Clones the desired branch from the repository.
4. Makes the installation script executable.
5. Optionally: Executes the installation script (refer to install.sh).

### install.sh
[!IMPORTANT]
This script requires an active internet connection and *wget* or *curl* installed on the system

This script undergoes the process to establishing all necessary preconditions and requirements to properly run IAV-Distortion.
The script accomplishes the following tasks:
1. Configures the password for the StaffUI.
2. Installs the virtual pipenv environment.
3. Downloads further required external resources (such as JavaScript libraries).
4. Creates a Desktop Item, from which IAV-Distortion can be initiated.
5. Makes the remaining utility scripts executable.
6. Checks for configured autostarts of other installations of IAV-Distortion and gives a warning if some were found.
7. Optionally configures the program's auto-start feature (using a cron job).

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
This script will immediately restart the host system.

### restart_IAV-Distortion.sh
Restart IAV-Distortion by first terminating the running instances using *quit.sh* afterwards restart IAV-Distortion using *run_IAV-Distrotion.sh*.

### shutdown_system.sh
Terminate all running instances of IAV-Distortion and shutdown the host system.