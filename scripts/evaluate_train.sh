#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd $DIR/../

export ROBOTHOR_BASE_DIR=`pwd`

# Inference on train split
docker run  -v $ROBOTHOR_BASE_DIR/dataset:/opt/robothor-challenge/dataset -e "CHALLENGE_SPLIT=train" -e "CHALLENGE_CONFIG=/opt/robothor-challenge/dataset/challenge_config.yaml" --privileged  -it robothor-challenge:latest python3 example_agent.py
