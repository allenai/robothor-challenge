FROM ai2thor-docker:latest

COPY requirements.txt robothor_challenge/scripts/download_thor_build.py challenge_config.yaml /app/
RUN pip3 install requirements.txt && python3 download_thor_build.py
RUN rm /app/requirements.txt /app/install_nvidia.txt /app/example_agent.py /app/download_thor_build.py

# Add agent dependencies here

WORKDIR /app/robothor-challenge
