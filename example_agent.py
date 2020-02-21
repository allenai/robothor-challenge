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
