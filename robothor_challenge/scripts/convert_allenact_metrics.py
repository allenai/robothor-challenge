from robothor_challenge.challenge import ALLOWED_ACTIONS
import argparse
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
    parser = argparse.ArgumentParser(description="Convert JSON metrics file from allenact test to submission file for RoboThor ObjectNav challenge.")

    parser.add_argument(
        "--input", "-i",
        help="Filepath for test metrics from allenact.",
        required=True)
    parser.add_argument(
        "--output", "-o",
        help="Output challenge metrics to this file.",
        required=True)
    parser.add_argument(
        "--test", "-t",
        help="Converting test set metrics.",
        action="store_true")

    args = parser.parse_args()

    with open(args.input, "r") as read_file:
        allenact_metrics = json.load(read_file)

    challenge_metrics = {"episodes" : {}}
    episode_results = []

    for episode in allenact_metrics[0]["tasks"]:
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
                action_success = args.test or episode["success"]
            else:
                prev_traj = episode_metrics["trajectory"][i]
                next_traj = episode_metrics["trajectory"][i+1]
                action_success = prev_traj != next_traj
            episode_metrics["actions_taken"][i]["success"] = action_success

        if not args.test:
            episode_metrics["success"] = episode["success"]
            episode_results.append({
                "shortest_path" : episode["task_info"]["path_to_target"],
                "path" : episode_metrics["trajectory"],
                "success" : episode_metrics["success"]
            })

        challenge_metrics["episodes"][episode["task_info"]["id"]] = episode_metrics

    num_episodes = len(challenge_metrics["episodes"])

    if not args.test:
        challenge_metrics["success"] = sum([e["success"] for e in challenge_metrics["episodes"].values()]) / num_episodes
        challenge_metrics["spl"] = ai2thor.util.metrics.compute_spl(episode_results)

    challenge_metrics["ep_len"] = sum([len(e["trajectory"]) for e in challenge_metrics["episodes"].values()]) / num_episodes

    with open(args.output, "w") as output:
        json.dump(challenge_metrics, output)


if __name__ == "__main__":
    main()
