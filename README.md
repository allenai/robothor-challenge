<p align="center">
  <img width = "50%" src='/images/robothor_challenge_logo.svg' />
  </p>

--------------------------------------------------------------------------------

# RoboTHOR-Challenge

Welcome to the RoboTHOR Challenge. The task for the RoboTHOR Challenge is to build a model/agent that can navigate towards a particular object in a room using the [RoboTHOR](https://ai2thor.allenai.org) embodied agent environment. Please follow the instructions below to get started.

## Installation

To begin working on your own model you must have Docker installed on your host and a Nvidia GPU (required for 3D rendering).


Clone or fork this repository
```bash
git clone https://github.com/allenai/robothor-challenge
```

Build the Docker container
```
cd robothor-challenge
./scripts/build.sh
```

Run evaluation on random agent
```
./scripts/evaluate_train.sh
```

At this point you should see log messages that resemble the following:
```
2020-02-11 05:08:00,545 [INFO] robothor_challenge - Task Start id:59 scene:FloorPlan_Train1_1 target_object:BaseballBat|+04.00|+00.04|-04.77 initial_position:{'x': 7.25, 'y': 0.910344243, 'z': -4.708334} rotation:180
2020-02-11 05:08:00,895 [INFO] robothor_challenge - Agent action: MoveAhead
2020-02-11 05:08:00,928 [INFO] robothor_challenge - Agent action: RotateLeft
2020-02-11 05:08:00,961 [INFO] robothor_challenge - Agent action: MoveBack
2020-02-11 05:08:00,989 [INFO] robothor_challenge - Agent action: Stop
```

## Model

Your model must subclass ```robothor_challenge.agent.Agent``` and implement the method ```act```. For an episode to be successful, the agent must be within 1 meter of the target object and the object must also be visible to the agent.  To declare success, respond with the ```Stop``` action.  If ```Stop``` is not sent within the maxmimum number of steps (100 max), the episode will be considered failed and the next episode will be initialized.  The following agent (found in example_agent.py) takes a random action on each event:

```python
from robothor_challenge.agent import Agent
from robothor_challenge import RobothorChallenge
import random
import logging
logging.getLogger().setLevel(logging.INFO)


class SimpleRandomAgent(Agent):

    def reset(self):
        pass

    def act(self, observations):
        # observations contains the following keys: rgb(numpy RGB frame), depth (None by default), object_goal(category of target object)
        action = random.choice(['MoveAhead', 'MoveBack', 'RotateRight', 'RotateLeft', 'LookUp', 'LookDown', 'Stop'])
        return action

if __name__ == '__main__':
    agent = SimpleRandomAgent()
    r = RobothorChallenge(agent=agent)
    r.inference()
```

Each episode has the following structure:
```javascript
 {
        "difficulty": "easy", // Task difficulty
        "id": 0,
        "initial_orientation": 180, // Initial orientation of the agent
        "initial_position": { // Initial position of the agent
            "x": 3.0,
            "y": 0.910344243,
            "z": -1.75
        },
        "object_id": "Apple|+01.98|+00.77|-01.75", // Id of the target object
        "object_type": "Apple", // Target object category
        "scene": "FloorPlan_Train1_1", // Name of the scene
        "shortest_path": [ // Coordinates of the points along the shortest path
            {
                "x": 3.0,
                "y": 0.0103442669,
                "z": -1.75
            },
            {
                "x": 2.75,
                "y": 0.0103442669,
                "z": -1.75
            }
        ],
        "shortest_path_length": 0.25, // Length of the shortest path
        "target_position": { // Position of the target
            "x": 1.979,
            "y": 0.7714,
            "z": -1.753
        }
}

```

When you have a model to evaluate, modify the Dockerfile to copy any files and update the requirements.txt as needed. Once you have built the image, you can run the evaluation script to calculate the SPL value.

## Dataset

The dataset consists of 27595 training episodes and 6116 val episodes where each episode consists of an agent starting position/rotation and target object.  

The following target object types exist in the dataset:
* Alarm Clock
* Apple
* Baseball Bat
* Basketball
* Bowl
* Garbage Can
* House Plant
* Laptop
* Mug
* Spray Bottle
* Television
* Vase

| Split | Difficulty | Total |
| ----- |:----------:|:-----:|
|Train|easy| 8939 | 
|Train|medium| 8939 | 
|Train|hard| 9717| 
|Val|easy| 1974 | 
|Val|medium| 1974 | 
|Val|hard| 2168 | 



All the episodes for each split (train/val) can be found within the dataset/{train/val}.json files.  Configuration parameters for the environment can be found within dataset/challenge_config.yaml.  These are the same values that will be used for generating the leaderboard.  You are free to train your model with whatever parameters you choose, but these params will be reset to the original values for leaderboard evaluation.

## Dataset Utility Functions

Once you've created your agent class:

```python
agent = SimpleRandomAgent()
r = RobothorChallenge(agent=agent)
```

You can move to points in the dataset by calling the following functions in the `RobothorChallenge` class:


To move to a random point in the dataset for a particular `scene` and `object_type`:

```python
event = r.move_to_random_dataset_point("FloorPlan_Train2_1", "Apple")
```

Useful if you load the dataset yourself, to move to a specific dataset point:

```python
event = r.move_to_point(datasetpoint)
```
Where `datapoint` is an entry in the json dataset.

To move to a random point in the scene, given by the [`GetReachablePositions`](https://ai2thor.allenai.org/robothor/documentation/#get-reachable-positions) unity function:

```python
event = r.move_to_random_point("FloorPlan_Train1_1", y_rotation=180)
```

All of these return an `Event Object` with the frame and metadata (see: [documentation](https://ai2thor.allenai.org/robothor/documentation/#metadata)). This is the data you will likely use for training.

To test the `RobothorChallenge` class make sure you set the environment variables `CHALLENGE_SPLIT` with `train` or `val`, and `CHALLENGE_CONFIG` to point to a challenge config yaml file. e.g. from the repo's root `./dataset/challenge_config.yaml`. This is set by the [evaluate_train](./scripts/evaluate_train.sh) script to run with docker.

## Challenge Submissions

We will be using [EvalAI](https://evalai.cloudcv.org) to host the challenge. You will be submitting your docker image for evaluation using the [EvalAI CLI](https://evalai-cli.cloudcv.org/).  During leaderboard evaluation, separate scenes/points will be used to determine your score.

To submit your models, please follow the [challenge submission link](https://evalai.cloudcv.org/web/challenges/challenge-page/558/overview).


## Acknowledgments

We would like to thank [Rishabh Jain](https://rishabhjain.xyz/) for the help for setting up the EvalAI leaderboard.

