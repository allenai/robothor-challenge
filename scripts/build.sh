#!/bin/bash

NVIDIA_VERSION=`cat /proc/driver/nvidia/version` docker build -t robothor-challenge:latest .
