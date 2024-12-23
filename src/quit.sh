#!/bin/bash

#working directory
working_directory=$(pwd)

# get list of PIDs for main.py
pids=$(pgrep -f "main.py")

# kill each
echo "Terminating running instances of IAV Distortion"
for pid in $pids
do
  if [[ ! -z $pid ]]
  then
    echo "Terminating process $pid"
    kill -TERM $pid
  fi
done
echo "All processes terminated"

sleep 5