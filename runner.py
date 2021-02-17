from robothor_challenge.challenge import RobothorChallenge
import os
import argparse
import importlib
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
        "--output-dir", "-o",
        default="results",
        help="Directory to output results to.",
    )
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

    if os.path.exists(args.output_dir) is False:
        os.makedirs(args.output_dir, exist_ok=True)

    if args.debug:
        debug_episodes, debug_dataset = r.load_split("debug")
        r.inference(
            debug_episodes,
            nprocesses=args.nprocesses,
            metrics_file=os.path.join(args.output_dir, "debug_metrics.json"),
            test=False
        )

    if args.train:
        train_episodes, train_dataset = r.load_split("train")
        r.inference(
            train_episodes,
            nprocesses=args.nprocesses,
            metrics_file=os.path.join(args.output_dir, "train_metrics.json"),
            test=False
        )

    if args.val:
        val_episodes, val_dataset = r.load_split("val")
        r.inference(
            val_episodes,
            nprocesses=args.nprocesses,
            metrics_file=os.path.join(args.output_dir, "val_metrics.json"),
            test=False
        )

    if args.test:
        test_episodes, test_dataset = r.load_split("test")
        r.inference(
            test_episodes,
            nprocesses=args.nprocesses,
            metrics_file=os.path.join(args.output_dir, "test_metrics.json"),
            test=True
        )


if __name__ == "__main__":
    main()
