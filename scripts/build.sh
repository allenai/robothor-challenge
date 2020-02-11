#!/bin/bash

if [ -e /proc/driver/nvidia/version ]; then
    NVIDIA_VERSION=`cat /proc/driver/nvidia/version` docker build -t robothor-challenge:latest .
else
    echo "Error: Nvidia driver not found at /proc/driver/nvidia/version; Please ensure you have an Nvidia GPU device and appropriate drivers are installed."
    exit 1;
fi;


