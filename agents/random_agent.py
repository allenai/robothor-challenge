from robothor_challenge.agent import Agent
from robothor_challenge.challenge import ALLOWED_ACTIONS
import random


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
