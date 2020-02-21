#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/../

export ROBOTHOR_BASE_DIR=`pwd`

# Inference on train split
X11_PARAMS=""
if [ -e /tmp/.X11-unix ]; then
  echo "Using local X11 server"
  X11_PARAMS="-e DISPLAY=$DISPLAY  -v /tmp/.X11-unix:/tmp/.X11-unix:rw"
  xhost +local:root
fi;

docker run  -v $ROBOTHOR_BASE_DIR/dataset:/opt/robothor-challenge/dataset -e "CHALLENGE_SPLIT=train" -e "CHALLENGE_CONFIG=/opt/robothor-challenge/dataset/challenge_config.yaml" --privileged $X11_PARAMS -it robothor-challenge:latest python3 example_agent.py

if [ -e /tmp/.X11-unix ]; then
    xhost -local:root
fi;

