from robothor_challenge.agent import Agent
from robothor_challenge import RobothorChallenge
import random
import logging
logging.getLogger().setLevel(logging.INFO)


class SimpleRandomAgent(Agent):

    def reset(self):
        pass

    def act(self, event, target_object_type):
        action = random.choice(['MoveAhead', 'MoveBack', 'RotateRight', 'RotateLeft', 'LookUp', 'LookDown', 'Stop'])
        return action


if __name__ == '__main__':
    agent = SimpleRandomAgent()
    r = RobothorChallenge(agent=agent)
    r.inference()
