<p align="center"><img width = "50%" src='./images/robothor_challenge_logo.svg' /></p><hr>

# 2021 RoboTHOR Object Navigation Challenge

Welcome to the [2021 RoboTHOR Object Navigation (ObjectNav) Challenge](https://ai2thor.allenai.org/robothor/cvpr-2021-challenge/) hosted at the
[CVPR'21 Embodied-AI Workshop](https://embodied-ai.org/).
The goal of this challenge is to build a model/agent that can navigate towards a given object in
a room using the [RoboTHOR](https://ai2thor.allenai.org/robothor/) embodied-AI environment. Please follow the instructions below
to get started.

### Contents

- [Installation](#installation)
- [Submitting to the Leaderboard](#submitting-to-the-leaderboard)
- [Agent](#agent)
- [Dataset](#dataset)
- [Using AllenAct Baselines](#using-allenact-baselines)

## Installation

If you are planning to evaluate an agent trained in AllenAct, you may simply `pip install ai2thor==2.7.2`, skip the following instructions, and follow [our example for evaluating AllenAct baselines](#using-allenact-baselines) below instead.

Otherwise, to begin working on your own model you must have an GPU (required for 3D rendering).

<details>
<summary><b>Local Installation</b></summary>
<p>

Clone or fork this repository
```bash
git clone https://github.com/allenai/robothor-challenge
cd robothor-challenge
```

Install `ai2thor` (we assume you are using Python version 3.6 or later):
```bash
pip3 install -r requirements.txt
python3 robothor_challenge/scripts/download_thor_build.py
```

Run evaluation on random agent
```bash
python3 runner.py -a agents.random_agent -c ./challenge_config.yaml -d ./dataset -o ./random_metrics.json.gz --debug --nprocesses 1
```

This command runs inference with the random agent over the debug split. You can pass the args (`--train`, `--val`, and/or `--test`) or `--submission` instead to run this agent on other splits.

</p>
</details>

<details>
<summary><b>Docker Installation</b></summary>
<p>

If you prefer to use docker, you may follow these instructions instead:

Build the `ai2thor-docker` image
```bash
git clone https://github.com/allenai/ai2thor-docker
cd ai2thor-docker && ./scripts/build.sh && cd ..
```

Then, build the `robothor-challenge` image
```bash
git clone https://github.com/allenai/robothor-challenge
cd robothor-challenge && docker build -t robothor-challenge .
```

Run evaluation with random agent
```bash
EVAL_CMD="python3 runner.py -a agents.random_agent -c ./challenge_config.yaml -d ./dataset -o ./random_metrics.json.gz --debug --nprocesses 1"

docker run --privileged --env="DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix:rw -v $(pwd):/app/robothor-challenge -it robothor-challenge:latest bash -c $EVAL_CMD
```

This command runs inference with the random agent over the debug split. You can pass the args (`--train`, `--val`, and/or `--test`) or `--submission` instead to run this agent on other splits.

You can update the Dockerfile and example script as needed to setup your agent.

</p>
</details>


After installing and running the demo, you should see log messages that resemble the following:
```
2020-02-11 05:08:00,545 [INFO] robothor_challenge - Task Start id:59 scene:FloorPlan_Train1_1 target_object:BaseballBat|+04.00|+00.04|-04.77 initial_position:{'x': 7.25, 'y': 0.910344243, 'z': -4.708334} rotation:180
2020-02-11 05:08:00,895 [INFO] robothor_challenge - Agent action: MoveAhead
2020-02-11 05:08:00,928 [INFO] robothor_challenge - Agent action: RotateLeft
2020-02-11 05:08:00,989 [INFO] robothor_challenge - Agent action: Stop
```

## Submitting to the Leaderboard

We will be using an [AI2 Leaderboard](https://leaderboard.allenai.org/) to host the challenge. The team with the best submission made by May 31st (midnight, [anywhere on earth](https://time.is/Anywhere_on_Earth)) will be announced at the [CVPR'21 Embodied-AI Workshop](https://embodied-ai.org/) and invited to produce a video describing their approach. You will be submitting your metrics file (e.g. `submission_metrics.json.gz` as below) for evaluation. During leaderboard evaluation, we will validate your results and compute several metrics (success rate, SPL, proximity-only success rate, proximity-only SPL, and episode length). Submissions will be ranked on the leaderboard by SPL on the test set.

To generate a submission, use the following evaluation command:
```bash
python3 runner.py -a agents.your_agent_module -c ./challenge_config.yaml -d ./dataset -o ./submission_metrics.json.gz --submission --nprocesses 8
```

We have provided an [example submission file](https://prior-leaderboards-public.s3-us-west-2.amazonaws.com/robothor-objectnav/demo-trajectories-2021/example_submission.json.gz) for you to view. The episodes in this example has been evaluated using our baselines (50% by a random agent and 50% by our baseline AllenAct agent).

If you are evaluating an agent trained in AllenAct, please follow our example in [Using AllenAct Baselines](#using-allenact-baselines) instead.

You can make your submission at the following URL: https://leaderboard.allenai.org/robothor_objectnav/submissions/public

## Agent

In order to generate the `metrics.json.gz` file for your agent, your agent must subclass 
`robothor_challenge.agent.Agent` and implement the `act` method.
Please place this agent in the `agents/` directory. For an episode to be successful,
the agent must be within 1 meter of the target object and the object must also be visible to the agent. 
To declare success, respond with the `Stop` action. If `Stop` is not sent within the maxmimum number of steps
(500 max), the episode will be considered failed and the next episode will be initialized. The agent in
`agents/random_agent.py` takes a random action at each step. You must also implement a `build()` function to specify how
the agent class should be initialized. Be sure any dependencies required by your agent are included in `$PYTHONPATH`.

<details>
<summary><b>agents/random_agent.py</b></summary>
<p>

```python
from robothor_challenge.agent import Agent
import random

ALLOWED_ACTIONS = ["MoveAhead", "RotateRight", "RotateLeft", "LookUp", "LookDown", "Stop"]

class SimpleRandomAgent(Agent):
    def reset(self):
        pass

    def act(self, observations):
        rgb = observations["rgb"]           # np.uint8 : 480 x 640 x 3
        depth = observations["depth"]       # np.float32 : 480 x 640 (default: None)
        goal = observations["object_goal"]  # str : e.g. "AlarmClock"

        action = random.choice(ALLOWED_ACTIONS)

        return action

def build():
    agent_class = SimpleRandomAgent
    agent_kwargs = {}
    # resembles SimpleRandomAgent(**{})
    render_depth = False
    return agent_class, agent_kwargs, render_depth
```

</p>
</details>

## Dataset

The dataset is divided into the following splits:

| Split | # Episodes | Files |
| ----- |:-----:|-----|
| Debug | 4 | `dataset/debug/episodes/FloorPlan_Train1_1.json.gz` |
| Train | 108000 | `dataset/train/episodes/FloorPlan_Train*.json.gz`|
| Val   | 1800 | `dataset/val/episodes/FloorPlan_Val*.json.gz` | 
| Test  | 2040 | `dataset/test/episodes/FloorPlan_test-challenge*.json.gz` |

where each file is a compressed json file corresponding to a list of
dictionaries. Each element of the list corresponds to a single episode of object navigation.

<details>
<summary><b>Episode Structure</b></summary>
<p>
Here is an example of the structure of a single episode in our training set.

```javascript
{
    "id": "FloorPlan_Train1_1_AlarmClock_0",
    "scene": "FloorPlan_Train1_1",
    "object_type": "AlarmClock",
    "initial_position": {
        "x": 3.75,
        "y": 0.9009997248649597,
        "z": -2.25
    },
    "initial_orientation": 150,
    "initial_horizon": 30,
    "shortest_path": [
        { "x": 3.75, "y": 0.0045, "z": -2.25 },
        ... ,
        { "x": 9.25, "y": 0.0045, "z": -2.75 }
    ],
    "shortest_path_length": 5.57
}
```

The keys `"shortest_path"` and `"shortest_path_length"` are hidden from episodes in the `test` split.

</p>
</details>

<details>
<summary><b>Target Objects</b></summary>
<p>

The following (12) target object types exist in the dataset:
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

</p>
</details>

All the episodes for each split (train/val/test) can be found within `dataset/`. There is also a "debug" split available. Configuration parameters for the environment can be found within `dataset/challenge_config.yaml`. These are the same values that will be used for generating the leaderboard. You are free to train your model with whatever parameters you choose, but these params will be reset to the original values for leaderboard evaluation.

### Utility Functions

Once you've created your agent class and loaded your dataset:

```python
cfg = 'challenge_config.yaml'
agent_class, agent_kwargs, render_depth = agent_module.build()
r = RobothorChallenge(cfg, agent_class, agent_kwargs, render_depth=render_depth)
train_episodes, train_dataset = r.load_split('dataset', 'train')
```

You can move to points in the dataset by calling the following functions in the `RobothorChallenge` class:


To move to a random point in the dataset for a particular `scene` and `object_type`:

```python
event = r.move_to_random_dataset_point(train_dataset, "FloorPlan_Train2_1", "Apple")
```

Useful if you load the dataset yourself, to move to a specific dataset point:

```python
datapoint = random.choice(train_dataset["FloorPlan_Train2_1"]["Apple"])
event = r.move_to_point(datasetpoint)
```

To move to a random point in the scene, given by the [`GetReachablePositions`](https://ai2thor.allenai.org/robothor/documentation/#get-reachable-positions) unity function:

```python
event = r.move_to_random_point("FloorPlan_Train1_1", y_rotation=180)
```

All of these return an `Event Object` with the frame and metadata (see: [documentation](https://ai2thor.allenai.org/robothor/documentation/#metadata)). This is the data you will likely use for training.

## Using AllenAct Baselines

We have built support for this challenge into the [AllenAct framework](https://allenact.org/), this support includes
1. Several CNN->RNN model baseline model architectures along with our best pretrained model checkpoint
   (trained for 300M steps) obtaining a test-set succcess rate of ~26%.
1. Reinforcement/imitation learning pipelines for training with
   [Distributed Decentralized Proximal Policy Optimization (DD-PPO)](https://arxiv.org/abs/1911.00357)
   and DAgger.
1. Utility functions for visualization and caching (to improve training speed). 

For more information, or to see how to evaluate a trained AllenAct model, see [here](https://github.com/allenai/allenact/tree/master/projects/objectnav_baselines#robothor-objectnav-2021-challenge).

### Converting AllenAct metrics to evaluation trajectories

When using AllenAct, it is generally more convenient to run evaluation within AllenAct rather than using the evaluation
script we provide in this repository. When doing this evaluation, the metrics returned by AllenAct are in a somewhat
different format than expected when submitting to our leaderboard. Because of this we provide the
`robothor_challenge/scripts/convert_allenact_metrics.py` script to convert metrics produced by AllenAct to those expected by our leaderboard
submission format.

```bash
export ALLENACT_VAL_METRICS = /path/to/metrics__val_*.json
export ALLENACT_TEST_METRICS = /path/to/metrics__test_*.json

python3 -m robothor_challenge.scripts.convert_allenact_metrics -v $ALLENACT_VAL_METRICS -t $ALLENACT_TEST_METRICS -o submission_metrics.json.gz
```
