from robothor_challenge.startx import startx
import ai2thor.controller
import ai2thor.util.metrics
import json
import threading
import yaml
import os
import sys
import logging

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
ch.flush = sys.stdout.flush
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

class RobothorChallenge:

    def __init__(self, agent_cls):
        self.setup_env()
        self.agent_cls = agent_cls
        self.load_config()
        self.controller = ai2thor.controller.Controller(width=self.config['width'], height=self.config['height'], **self.config['initialize'])

    def load_config(self):
        if 'CHALLENGE_CONFIG' not in os.environ:
            raise ValueError("CHALLENGE_CONFIG not in environment")

        if 'CHALLENGE_SPLIT' not in os.environ:
            raise ValueError("CHALLENGE_SPLIT not in environment")

        logger.info("Loading configuration from: {CHALLENGE_CONFIG}".format(**os.environ))
        split_path = os.path.join(os.path.dirname(os.environ['CHALLENGE_CONFIG']), os.environ['CHALLENGE_SPLIT'] + ".json")
        logger.info("Loading split: {path}".format(path=split_path))
        with open(os.environ['CHALLENGE_CONFIG']) as f:
            self.config = yaml.safe_load(f.read())

        with open(split_path) as f:
            self.episodes = json.loads(f.read())
        

    def inference(self):
        episode_results = []
        for e in self.episodes:
            episode_result = dict(shortest_path= e['shortest_path'], success=False, path=[])
            episode_results.append(episode_result)
            agent = self.agent_cls(e)
            logger.info("Task Start id:{id} scene:{scene} target_object:{object_id} initial_position:{initial_position} rotation:{initial_orientation}".format(**e))
            self.controller.reset(e['scene'])
            teleport_action = dict(action='TeleportFull')
            teleport_action.update(e['initial_position'])
            self.controller.step(action=teleport_action)
            self.controller.step(action=dict(action='Rotate', rotation=dict(y=e['initial_orientation'], horizon=0.0)))
            total_steps = 0
            episode_result['path'].append(self.controller.last_event.metadata['agent']['position'])

            stopped = False
            while total_steps < self.config['max_steps'] and not stopped:
                total_steps +=1 
                action = agent.on_event(self.controller.last_event)
                logger.info("Agent action: {action}".format(**action))
                event = self.controller.step(action)
                stopped = event.metadata['lastAction'] == 'Stop'
                episode_result['path'].append(self.controller.last_event.metadata['agent']['position'])

            if stopped:
                simobj = self.controller.last_event.get_object(e['object_id'])
                episode_result['success'] = simobj['visible']

        spl = ai2thor.util.metrics.compute_spl(episode_results)
        logger.info("Total Episodes: {episode_count} SPL:{spl}".format(episode_count=len(episode_results), spl=spl))

        return spl

    def setup_env(self):
        xthread = threading.Thread(target=startx)
        xthread.daemon = True
        xthread.start()
        import time
        # XXX change this to use xdpyinfo
        time.sleep(4)
