#!/bin/bash

# working directory
working_directory=$(pwd)

# create/override logfile_restart.log that log the latest restart
echo "This logfile documents only the latest restart event from $(date '+%m-%d-%Y %H:%M:%S'):" > logfile_restart.log 2>&1
echo >> logfile_restart.log 2>&1

# terminate running instances of IAV-Distortion
$working_directory/quit.sh >> logfile_restart.log 2>&1

# restart systems bluetooth interface
sudo systemctl restart bluetooth


port_process=$(sudo netstat -tulnp | grep :5000)
echo "Process on port 5000: $port_process" >> logfile_restart.log 2>&1


count=0
max_count=30
while lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; do
    if [ $count -ge $max_count ]; then
        echo "Error: Could not free port 5000 after $max_count attempts" >> logfile_restart.log 2>&1
        exit 1
    fi
    # Get the PID of the process
    PID=$(sudo lsof -t -i:5000)
    kill -9 $PID
    count=$((count+1))
    echo "Waiting for port 5000 to become free... (Try: $count)" >> logfile_restart.log 2>&1
    sleep 1
done

sleep 5

# start IAV-Distortion using the run_IAV-Distortion.sh
echo "Restarting IAV-Distortion..." >> logfile_restart.log 2>&1
$working_directory/run_IAV-Distortion.sh > /dev/null 2>&1