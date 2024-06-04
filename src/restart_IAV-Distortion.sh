#!/bin/bash

# working directory
working_directory=$(pwd)

# terminate running instances of IAV-Distortion
$working_directory/quit.sh

# start IAV-Distortion using the run_IAV-Distortion.sh
echo "Restarting IAV-Distortion..."
$working_directory/run_IAV-Distortion.sh