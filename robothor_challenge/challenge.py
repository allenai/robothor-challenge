from typing import Dict, Any
import os
import sys
import glob
import json
import yaml
import time
import gzip
import random
import logging

import multiprocessing as mp
import queue
import threading
import ai2thor.controller
import ai2thor.util.metrics

from robothor_challenge.startx import startx


logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
ch.flush = sys.stdout.flush
ch.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

ALLOWED_ACTIONS =  ["MoveAhead", "RotateRight", "RotateLeft", "LookUp", "LookDown", "Stop"]


def get_object_by_type(event_objects, object_type):
    for obj in event_objects:
        if obj['objectId'].split("|")[0] == object_type:
            return obj
    return None


class RobothorChallenge:

    def __init__(self, agent_class, agent_kwargs, cfg_file, render_depth=False):
        self.agent_class = agent_class
        self.agent_kwargs = agent_kwargs

        self.config = self.load_config(cfg_file, render_depth)

        self.setup_env()
        self.controller_kwargs = {
            "commit_id": self.config["thor_build_id"],
            "width": self.config["width"],
            "height": self.config["height"],
            **self.config["initialize"]
        }

        self.current_scene = None
        self.reachable_positions_per_scene = {}

    def load_config(self, cfg_file, render_depth):
        logger.info("Loading configuration from: %s" % cfg_file)
        with open(cfg_file, "r") as f:
            config = yaml.safe_load(f.read())
        if render_depth:
            config["initialize"]["renderDepthImage"] = True
        return config

    def setup_env(self):
        if "DISPLAY" not in os.environ:
            xthread = threading.Thread(target=startx)
            xthread.daemon = True
            xthread.start()
            import time
            # XXX change this to use xdpyinfo
            time.sleep(4)

    def load_split(self, dataset_dir, split):
        split_paths = os.path.join(dataset_dir, split, "episodes", "*.json.gz")
        split_paths = sorted(glob.glob(split_paths))

        episode_list = []
        dataset = {}

        for split_path in split_paths:
            logger.info("Loading: {path}".format(path=split_path))

            with gzip.GzipFile(split_path, "r") as f:
                episodes = json.loads(f.read().decode("utf-8"))

                # Build a dictionary of the dataset indexed by scene, object_type
                curr_scene = None
                curr_object = None
                points = []
                scene_points = {}
                for data_point in episodes:
                    if curr_object != data_point["object_type"]:
                        scene_points[curr_object] = points
                        curr_object = data_point["object_type"]
                        points = []
                    if curr_scene != data_point["scene"]:
                        dataset[curr_scene] = scene_points
                        curr_scene = data_point["scene"]
                        scene_points = {}

                    points.append(data_point)

                episode_list += episodes

        return episode_list, dataset

    def inference_worker(
        self,
        worker_ind: int,
        in_queue: mp.Queue,
        out_queue: mp.Queue,
        agent_class: Any,
        agent_kwargs: Dict[str, Any],
        controller_kwargs: Dict[str, Any],
        max_steps: int,
        test: bool
    ):
        agent = agent_class(**agent_kwargs)
        controller = ai2thor.controller.Controller(**controller_kwargs)

        while True:
            try:
                e = in_queue.get(timeout=1)
            except queue.Empty:
                break

            logger.info("Task Start id:{id} scene:{scene} target_object:{object_type} initial_position:{initial_position} rotation:{initial_orientation}".format(**e))
            controller.initialization_parameters["robothorChallengeEpisodeId"] = e["id"]
            print(e["scene"])
            controller.reset(e["scene"])
            teleport_action = {
                "action": "TeleportFull",
                **e["initial_position"],
                "rotation": {"x": 0, "y": e["initial_orientation"], "z": 0},
                "horizon": e["initial_horizon"],
                "standing": True
            }
            controller.step(action=teleport_action)

            total_steps = 0
            agent.reset()

            episode_metrics = {
                "trajectory" : [{
                    **e["initial_position"],
                    "rotation" : float(e["initial_orientation"]),
                    "horizon" : e["initial_horizon"]
                }],
                "actions_taken" : []
            }

            stopped = False
            while total_steps < max_steps and stopped is False:
                total_steps += 1
                event = controller.last_event
                event.metadata.clear()

                action = agent.act({
                    "object_goal" : e["object_type"],
                    "depth" : event.depth_frame,
                    "rgb" : event.frame
                })

                if action not in ALLOWED_ACTIONS:
                    raise ValueError("Invalid action: {action}".format(action=action))

                logger.info("Agent action: {action}".format(action=action))
                event = controller.step(action=action)
                episode_metrics["trajectory"].append({
                    **event.metadata["agent"]["position"],
                    "rotation": event.metadata["agent"]["rotation"]["y"],
                    "horizon": event.metadata["agent"]["cameraHorizon"]
                })
                episode_metrics["actions_taken"].append({
                    "action": action,
                    "success": event.metadata["lastActionSuccess"]
                })
                stopped = action == "Stop"

            if not test:
                target_obj = get_object_by_type(event.metadata["objects"], e["object_type"])
                assert target_obj is not None
                target_visible = target_obj["visible"]
                episode_metrics["success"] = stopped and target_visible

            if not test:
                episode_result = {
                    "path": episode_metrics["trajectory"],
                    "shortest_path": e["shortest_path"],
                    "success": episode_metrics["success"]
                }
            else:
                episode_result = None

            out_queue.put((e["id"], episode_metrics, episode_result))

        controller.stop()
        print(f"Worker {worker_ind} Finished.")

    def inference(self, episodes, nprocesses=1, test=False):
        send_queue = mp.Queue()
        receive_queue = mp.Queue()

        expected_count = len(episodes)
        for e in episodes:
            send_queue.put(e)

        processes = []
        for worker_ind in range(nprocesses):
            p = mp.Process(
                target=self.inference_worker,
                kwargs=dict(
                    worker_ind=worker_ind,
                    in_queue=send_queue,
                    out_queue=receive_queue,
                    agent_class=self.agent_class,
                    agent_kwargs=self.agent_kwargs,
                    controller_kwargs=self.controller_kwargs,
                    max_steps=self.config["max_steps"],
                    test=test
                ),
            )
            p.start()
            processes.append(p)
            time.sleep(0.2)

        metrics = {"episodes" : {}}
        episode_results = []

        while len(metrics["episodes"]) < expected_count:
            try:
                ep_id, episode_metrics, episode_result = receive_queue.get(timeout=10)
                metrics["episodes"][ep_id] = episode_metrics
                if not test:
                    episode_results.append(episode_result)
            except TimeoutError:
                print("Went 10 seconds without a new episode result.")
                if all(not p.is_alive() for p in processes):
                    try:
                        ep_id, episode_metrics, episode_result = receive_queue.get(timeout=1)
                        metrics["episodes"][ep_id] = episode_metrics
                        if not test:
                            episode_results.append(episode_result)
                    except TimeoutError:
                        raise RuntimeError("All processes dead but nothing in queue!")

        for p in processes:
            p.join(timeout=2)

        metrics["ep_len"] = sum([len(em["trajectory"]) for em in metrics["episodes"].values()]) / len(metrics["episodes"])

        if not test:
            metrics["success"] = sum([r["success"] for r in episode_results]) / len(episode_results)
            metrics["spl"] = ai2thor.util.metrics.compute_spl(episode_results)

        if not test:
            logger.info("Total Episodes: {episode_count} Success:{success} SPL:{spl} Episode Length:{ep_len}".format(episode_count=len(episodes), success=metrics["success"], spl=metrics["spl"], ep_len=metrics["ep_len"]))
        else:
            logger.info("Total Episodes: {episode_count} Episode Length:{ep_len}".format(episode_count=len(episodes), ep_len=metrics["ep_len"]))

        return metrics


    def _change_scene(self, scene):
        if self.current_scene != scene:
            self.current_scene = scene
            self.controller.reset(scene)
            logger.info("Changed to scene: '{scene}'".format(scene=scene))

    def move_to_point(self, datapoint):
        self._change_scene(datapoint["scene"])
        logger.info("Moving to position: {p}, y-rotation: {rot}, horizon: {hor}".format(
            p=datapoint["initial_position"],
            rot=datapoint["initial_orientation"],
            hor=datapoint["initial_horizon"]
        ))
        return self.controller.step(
            action="TeleportFull",
            x=datapoint["initial_position"]["x"],
            y=datapoint["initial_position"]["y"],
            z=datapoint["initial_position"]["z"],
            rotation={"x" : 0, "y" : datapoint["initial_orientation"], "z" : 0},
            horizon=datapoint["initial_horizon"],
            standing=True
        )

    def move_to_random_dataset_point(self, dataset, scene, object_type):
        if scene in dataset:
            if object_type in dataset[scene]:
                datapoint = random.choice(dataset[scene][object_type])
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
            logger.warning("No scene: '{scene}' in dataset".format(scene=scene))
            return None

    def move_to_random_point(self, scene, y_rotation=0, horizon=0):
        if "test" in scene:
            raise RuntimeError(
                "Moving to random points is not posible in test scenes"
            )
        reachable_positions = self._get_reachable_positions_in_scene(scene)
        p = random.choice(reachable_positions)
        return self.move_to_point({
            "initial_position": p,
            "initial_orientation": y_rotation,
            "initial_horizon": horizon,
            "scene" : scene
        })

    def _get_reachable_positions_in_scene(self, scene):
        self._change_scene(scene)
        if scene not in self.reachable_positions_per_scene:
            event_reachable = self.controller.step({
                "action" : "GetReachablePositions",
                "gridSize" : self.config["initialize"]["gridSize"]
            })
            self.reachable_positions_per_scene[scene] = event_reachable.metadata["actionReturn"]
        return self.reachable_positions_per_scene[scene]
