#!/bin/bash
nvidia_version=`cat /proc/driver/nvidia/version |grep 'NVRM version:'| grep -oE "Kernel Module\s+[0-9.]+"| awk {'print $3'}`
nvidia_major_version=`echo $nvidia_version |sed "s/\..*//"`
driver_filename="NVIDIA-Linux-x86_64-$nvidia_version.run"
driver_url="http://us.download.nvidia.com/XFree86/Linux-x86_64/$nvidia_version/$driver_filename"
wget $driver_url -P /root/
if [ $?  -eq 0 ]; then
    sh /root/$driver_filename -s --no-kernel-module
else
    apt-get update
    apt-get install -y nvidia-driver-$nvidia_major_version=$nvidia_version-0ubuntu1\
        nvidia-utils-$nvidia_major_version=$nvidia_version-0ubuntu1\
        libnvidia-gl-$nvidia_major_version=$nvidia_version-0ubuntu1\
        nvidia-dkms-$nvidia_major_version=$nvidia_version-0ubuntu1\
        nvidia-kernel-source-$nvidia_major_version=$nvidia_version-0ubuntu1 \
        libnvidia-ifr1-$nvidia_major_version=$nvidia_version-0ubuntu1 \
        libnvidia-cfg1-$nvidia_major_version=$nvidia_version-0ubuntu1 \
        libnvidia-decode-$nvidia_major_version=$nvidia_version-0ubuntu1 \
        libnvidia-encode-$nvidia_major_version=$nvidia_version-0ubuntu1 \
        nvidia-compute-utils-$nvidia_major_version=$nvidia_version-0ubuntu1 \
        libnvidia-compute-$nvidia_major_version=$nvidia_version-0ubuntu1 \
        libnvidia-fbc1-$nvidia_major_version=$nvidia_version-0ubuntu1 \
        xserver-xorg-video-nvidia-$nvidia_major_version=$nvidia_version-0ubuntu1
fi;
