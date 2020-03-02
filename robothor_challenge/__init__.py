from robothor_challenge.startx import startx
import ai2thor.controller
import ai2thor.util.metrics
import json
import threading
import yaml
import os
import sys
import logging
import random

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
ch.flush = sys.stdout.flush
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

ALLOWED_ACTIONS =  ['MoveAhead', 'MoveBack', 'RotateRight', 'RotateLeft', 'LookUp', 'LookDown', 'Stop']

class RobothorChallenge:

    def __init__(self, agent):
        self.agent = agent
        self.dataset = {}
        self.load_config()
        self.current_scene = None
        self.reachable_positions_per_scene = {}
        if self.dataset_split == 'test':
            self.controller = ai2thor.controller.Controller(
                start_unity=False,
                port=8200,
                width=self.config['width'],
                height=self.config['height'],
                **self.config['initialize']
            )
        else:
            self.setup_env()
            self.controller = ai2thor.controller.Controller(
                width=self.config['width'],
                height=self.config['height'],
                **self.config['initialize']
            )

    @property
    def dataset_split(self):
        if 'CHALLENGE_SPLIT' not in os.environ:
            raise ValueError("CHALLENGE_SPLIT not in environment")
        return os.environ['CHALLENGE_SPLIT']

    def load_config(self):
        if 'CHALLENGE_CONFIG' not in os.environ:
            raise ValueError("CHALLENGE_CONFIG not in environment")


        logger.info("Loading configuration from: {CHALLENGE_CONFIG}".format(**os.environ))
        split_path = os.path.join(os.path.dirname(os.environ['CHALLENGE_CONFIG']),  self.dataset_split + ".json")
        logger.info("Loading split: {path}".format(path=split_path))
        with open(os.environ['CHALLENGE_CONFIG']) as f:
            self.config = yaml.safe_load(f.read())

        with open(split_path) as f:
            self.episodes = json.loads(f.read())

            # Build a dictionary of the dataset indexed by scene, object_type
            curr_scene = None
            curr_object = None
            points = []
            scene_points = {}
            for data_point in self.episodes:
                if curr_object != data_point['object_type']:
                    scene_points[curr_object] = points
                    curr_object = data_point['object_type']
                    points = []
                if curr_scene != data_point['scene']:
                    self.dataset[curr_scene] = scene_points
                    curr_scene = data_point['scene']
                    scene_points = {}

                points.append(data_point)


    def inference(self):
        episode_results = []
        for e in self.episodes:
            episode_result = dict(shortest_path= e['shortest_path'], success=False, path=[])
            episode_results.append(episode_result)
            logger.info("Task Start id:{id} scene:{scene} target_object:{object_id} initial_position:{initial_position} rotation:{initial_orientation}".format(**e))
            self.controller.initialization_parameters['robothorChallengeEpisodeId'] = e['id']
            self.controller.reset(e['scene'])
            teleport_action = dict(action='TeleportFull')
            teleport_action.update(e['initial_position'])
            self.controller.step(action=teleport_action)
            self.controller.step(action=dict(action='Rotate', rotation=dict(y=e['initial_orientation'], horizon=0.0)))
            total_steps = 0
            episode_result['path'].append(self.controller.last_event.metadata['agent']['position'])

            self.agent.reset()

            stopped = False
            while total_steps < self.config['max_steps'] and not stopped:
                total_steps +=1 
                event = self.controller.last_event
                # must clear out metadata during inference 
                event.metadata.clear()
                action = self.agent.act(dict(object_goal=e['object_type'], depth=None, rgb=event.frame))
                if action not in ALLOWED_ACTIONS:
                    raise ValueError("Invalid action: {action}".format(action=action))

                logger.info("Agent action: {action}".format(action=action))
                event = self.controller.step(action=action)
                stopped = action == 'Stop'
                episode_result['path'].append(self.controller.last_event.metadata['agent']['position'])

            if stopped:
                simobj = self.controller.last_event.get_object(e['object_id'])
                episode_result['success'] = simobj['visible']

        spl = ai2thor.util.metrics.compute_spl(episode_results)
        logger.info("Total Episodes: {episode_count} SPL:{spl}".format(episode_count=len(episode_results), spl=spl))

        return spl

    def setup_env(self):
        if 'DISPLAY' not in os.environ:
            xthread = threading.Thread(target=startx)
            xthread.daemon = True
            xthread.start()
            import time
            # XXX change this to use xdpyinfo
            time.sleep(4)

    def _change_scene(self, scene):
        if self.current_scene != scene:
            self.current_scene = scene
            self.controller.reset(scene)
            logger.info("Changed to scene: '{scene}'".format(scene=scene))

    def move_to_point(self, datapoint):
        self._change_scene(datapoint['scene'])
        p = datapoint['initial_position']
        logger.info("Moving to position: {p}, y-rotation: {rot}".format(p=p, rot=datapoint['initial_orientation']))
        return self.controller.step(
            action="TeleportFull",
            x=p['x'],
            y=p['y'],
            z=p['z'],
            rotation=dict(x=0, y=datapoint['initial_orientation'], z=0)
        )

    def move_to_random_dataset_point(self, scene, object_type):
        if scene in self.dataset:
            if object_type in self.dataset[scene]:
                datapoint = random.choice(self.dataset[scene][object_type])
                return self.move_to_point(datapoint)
            else:
                logger.warning(
                    "No object of type: '{object_type}' for scene: '{scene}', in dataset".format(
                        object_type=object_type,
                        scene=scene
                    )
                )
                return None
        else:
            logger.warning(
                "No scene: '{scene}' in dataset".format(
                    scene=scene
                )
            )
            return None

    def move_to_random_point(self, scene, y_rotation=0):
        reachable_positions = self._get_reachable_positions_in_scene(scene)
        p = random.choice(reachable_positions)
        return self.move_to_point(dict(
            initial_position=p,
            initial_orientation=y_rotation,
            scene=scene
        ))

    def _get_reachable_positions_in_scene(self, scene):
        self._change_scene(scene)
        if scene not in self.reachable_positions_per_scene:
            event_reachable = self.controller.step(
                dict(
                    action='GetReachablePositions',
                    gridSize=self.config['initialize']['gridSize']
                )
            )
            self.reachable_positions_per_scene[scene] = event_reachable.metadata['actionReturn']
        return self.reachable_positions_per_scene[scene]

