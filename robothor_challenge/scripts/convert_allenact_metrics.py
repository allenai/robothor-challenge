from robothor_challenge.challenge import ALLOWED_ACTIONS
import argparse
import gzip
import json
import ai2thor.util.metrics


allenact_to_ai2thor_actions = {
    "MoveAhead" : "MoveAhead",
    "RotateRight" : "RotateRight",
    "RotateLeft" : "RotateLeft",
    "LookUp" : "LookUp",
    "LookDown" : "LookDown",
    "End" : "Stop"
}
assert set(allenact_to_ai2thor_actions.values()) == set(ALLOWED_ACTIONS)


def main():
    parser = argparse.ArgumentParser(description="Convert JSON metrics files from allenact val and test splits to submission file for RoboThor ObjectNav challenge.")

    parser.add_argument(
        "--val-metrics", "-v",
        help="Filepath for val metrics from allenact.",
        required=True)
    parser.add_argument(
        "--test-metrics", "-t",
        help="Filepath for test metrics from allenact.",
        required=True)
    parser.add_argument(
        "--output", "-o",
        help="Output challenge metrics to this file.",
        default="submission_metrics.json.gz")

    args = parser.parse_args()

    with open(args.val_metrics, "r") as read_file:
        allenact_val_metrics = json.load(read_file)
    with open(args.test_metrics, "r") as read_file:
        allenact_test_metrics = json.load(read_file)

    challenge_metrics = {}

    for split in ["val", "test"]:
        if split == "val":
            tasks = allenact_val_metrics[0]["tasks"]
        else:
            tasks = allenact_test_metrics[0]["tasks"]

        challenge_metrics[split] = {"episodes" : {}}
        episode_results = []

        for episode in tasks:
            episode_metrics = {}

            episode_metrics["trajectory"] = [{
                "x" : p["x"],
                "y" : p["y"],
                "z" : p["z"],
                "rotation" : p["rotation"]["y"],
                "horizon" : p["horizon"]
            } for p in episode["task_info"]["followed_path"]]

            episode_metrics["actions_taken"] = [{
                "action": allenact_to_ai2thor_actions[a]
            } for a in episode["task_info"]["taken_actions"]]

            if episode_metrics["actions_taken"][-1] == {"action" : "Stop"}:
                episode_metrics["trajectory"].append(
                    episode_metrics["trajectory"][-1]
                )

            for i in range(len(episode_metrics["actions_taken"])):
                if episode_metrics["actions_taken"][i]["action"] == "Stop":
                    action_success = split == "test" or episode["success"]
                else:
                    prev_traj = episode_metrics["trajectory"][i]
                    next_traj = episode_metrics["trajectory"][i+1]
                    action_success = prev_traj != next_traj
                episode_metrics["actions_taken"][i]["success"] = action_success

            if split != "test":
                episode_metrics["success"] = episode["success"]
                episode_results.append({
                    "shortest_path" : episode["task_info"]["path_to_target"],
                    "path" : episode_metrics["trajectory"],
                    "success" : episode_metrics["success"]
                })

            challenge_metrics[split]["episodes"][episode["task_info"]["id"]] = episode_metrics

        num_episodes = len(challenge_metrics[split]["episodes"])

        if split != "test":
            challenge_metrics[split]["success"] = sum([e["success"] for e in challenge_metrics[split]["episodes"].values()]) / num_episodes
            challenge_metrics[split]["spl"] = ai2thor.util.metrics.compute_spl(episode_results)

        challenge_metrics[split]["ep_len"] = sum([len(e["trajectory"]) for e in challenge_metrics[split]["episodes"].values()]) / num_episodes

    with gzip.open(args.output, "wt", encoding="utf-8") as zipfile:
        json.dump(challenge_metrics, zipfile)


if __name__ == "__main__":
    main()
