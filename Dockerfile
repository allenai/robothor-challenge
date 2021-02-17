FROM ai2thor-docker:latest

COPY requirements.txt /app/
COPY robothor_challenge/scripts/download_thor_buid.py /app/

RUN pip3 install -r requirements.txt && python3 /app/download_thor_buid.py

WORKDIR /app/robothor-challenge
