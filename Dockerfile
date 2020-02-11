FROM nvidia/cuda:10.2-devel-ubuntu18.04

RUN apt-get update && apt-get -y install python3-pip libxrender1 libsm6 xserver-xorg-core xorg python3-venv vim pciutils wget git
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY requirements.txt scripts/install_nvidia.sh /app/
RUN pip3 install -r requirements.txt && python3 -c "import ai2thor.controller; ai2thor.controller.Controller(download_only=True)"
RUN NVIDIA_VERSION=$NVIDIA_VERSION /app/install_nvidia.sh

COPY robothor_challenge /app/robothor_challenge
COPY example_agent.py ./

CMD /bin/bash
