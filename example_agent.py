from robothor_challenge.agent import Agent
from robothor_challenge import RobothorChallenge
import random
import logging
logging.getLogger().setLevel(logging.INFO)


class SimpleRandomAgent(Agent):

    def on_event(self, event):
        action = dict(action=random.choice(['MoveAhead', 'MoveBack', 'RotateRight', 'RotateLeft', 'Stop']))
        return action


if __name__ == '__main__':
    r = RobothorChallenge(agent_cls=SimpleRandomAgent)
    r.inference()
