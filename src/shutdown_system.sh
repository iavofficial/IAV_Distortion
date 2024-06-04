#!/bin/bash

# working directory
working_directory=$(pwd)

# terminate running instances of IAV-Distortion
$working_directory/quit.sh

# shutdown system
sudo shutdown now