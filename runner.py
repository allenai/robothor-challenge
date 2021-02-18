from robothor_challenge.challenge import RobothorChallenge
import os
import argparse
import importlib
import json
import logging
logging.getLogger().setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="Inference script for RoboThor ObjectNav challenge.")

    parser.add_argument(
        "--agent", "-a",
        default="agents.random_agent",
        help="Relative module for agent definition.",
    )
    parser.add_argument(
        "--dataset-dir", "-d",
        default="dataset",
        help="Filepath to challenge dataset.",
    )
    parser.add_argument(
        "--output", "-o",
        default="metrics.json",
        help="Filepath to output results to.",
    )

    parser.add_argument(
        "--submission",
        action="store_true")

    parser.add_argument(
        "--debug",
        action="store_true")
    parser.add_argument(
        "--train",
        action="store_true")
    parser.add_argument(
        "--val",
        action="store_true")
    parser.add_argument(
        "--test",
        action="store_true")

    parser.add_argument(
        "--nprocesses", "-n",
        default=1,
        type=int,
        help="Number of parallel processes used to compute inference.",
    )

    args = parser.parse_args()

    agent = importlib.import_module(args.agent)
    agent_class, agent_kwargs, render_depth = agent.build()

    r = RobothorChallenge(agent_class, agent_kwargs, args.dataset_dir, render_depth=render_depth)

    challenge_metrics = {}

    if args.submission:
        args.debug = False
        args.train = False
        args.val = True
        args.test = True

    if args.debug:
        debug_episodes, debug_dataset = r.load_split("debug")
        challenge_metrics["debug"] = r.inference(
            debug_episodes,
            nprocesses=args.nprocesses,
            test=False
        )

    if args.train:
        train_episodes, train_dataset = r.load_split("train")
        challenge_metrics["train"] = r.inference(
            train_episodes,
            nprocesses=args.nprocesses,
            test=False
        )

    if args.val:
        val_episodes, val_dataset = r.load_split("val")
        challenge_metrics["val"] = r.inference(
            val_episodes,
            nprocesses=args.nprocesses,
            test=False
        )

    if args.test:
        test_episodes, test_dataset = r.load_split("test")
        challenge_metrics["test"] = r.inference(
            test_episodes,
            nprocesses=args.nprocesses,
            test=True
        )

    with open(args.output, 'w') as write_file:
        json.dump(challenge_metrics, write_file)


if __name__ == "__main__":
    main()
