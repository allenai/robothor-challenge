#!/bin/bash
if [ ! -e /proc/driver/nvidia/version ]; then
    echo "Error: Nvidia driver not found at /proc/driver/nvidia/version; Please ensure you have an Nvidia GPU device and appropriate drivers are installed."
    exit 1;
fi;

NVIDIA_VERSION=`cat /proc/driver/nvidia/version | grep 'NVRM version:'| grep -oE "Kernel Module\s+[0-9.]+"| awk {'print $3'}` 
NVIDIA_MAJOR=`echo $NVIDIA_VERSION | tr "." "\n" | head -1  | tr -d "\n"`
NVIDIA_MINOR=`echo $NVIDIA_VERSION | tr "." "\n" | head -2  | tail -1| tr -d "\n"`
NVIDIA_MM="$NVIDIA_MAJOR.$NVIDIA_MINOR"

# https://docs.nvidia.com/deploy/cuda-compatibility/index.html#binary-compatibility__table-toolkit-driver
if (( $(echo "$NVIDIA_MM >= 440.33" | bc -l) )); then
    CUDA_VERSION=10.2
elif (( $(echo "$NVIDIA_MM >= 418.39" | bc -l) )); then
    CUDA_VERSION=10.1
elif (( $(echo "$NVIDIA_MM >= 410.48" | bc -l) )); then
    CUDA_VERSION=10.0
elif (( $(echo "$NVIDIA_MM >= 396.26" | bc -l) )); then
    CUDA_VERSION=9.2
elif (( $(echo "$NVIDIA_MM >= 390.46" | bc -l) )); then
    CUDA_VERSION=9.1
elif (( $(echo "$NVIDIA_MM >= 384.81" | bc -l) )); then
    CUDA_VERSION=9.0
else
    echo "No valid CUDA version found for nvidia driver $NVIDIA_VERSION"
    exit 1
fi

echo "Building Docker container with CUDA Version: $CUDA_VERSION, NVIDIA Driver: $NVIDIA_VERSION"
NVIDIA_VERSION=$NVIDIA_VERSION docker build --build-arg CUDA_VERSION=$CUDA_VERSION -t robothor-challenge:latest .


