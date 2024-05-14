import pandas as pd
import json
import zipfile
import os
import sys
import multiprocessing as mp
import glob

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import eval_const

"""
for test t in Build suite_N, extract its data from previous build suite_1 to suite_N-1 WITHIN A WINDOW SIZE

from https://dl.acm.org/doi/10.1145/3460319.3464834, get
- F1.1 failure count, total number of times t failed
- F1.2 last failure, amount of CI runs since last failure
- F1.4 last transition, amount of CI runs since last transition
- F1.5 average test execution time across previous builds
"""

def update_history(d, new_average_duration, duration, outcome):
    if outcome == eval_const.FAIL:
        d["failure_count"] += 1
    
    if outcome == eval_const.FAIL:
        d["last_failure"] = 1
    else:
        d["last_failure"] += 1
    
    if outcome != d["last_outcome"]:
        d["last_transition"] += 1
    else:
        d["last_transition"] = 1

    if outcome != d["last_outcome"]:
        d["transition_count"] += 1
    
    d["run_count"] += 1
    d["last_outcome"] = outcome
    d["last_duration"] = duration

    d["average_duration"] = new_average_duration
    
    return d


def find_last_failure(outcomes):
    for index in list(reversed(range(len(outcomes)))):
        if outcomes[index] == eval_const.FAIL:
            return len(outcomes) - (index + 1)
    return len(outcomes)


def find_last_transition(outcomes):
    for index in list(reversed(range(len(outcomes) - 1))):
        if outcomes[index] != outcomes[index + 1]:
            return len(outcomes) - (index + 2)
        return len(outcomes)


def build_historical_data(project, window_size):
    """
    walk the historical test runs from oldest to newest
    build the historical features per-build per-test in bottom-up way
    ONLY KEEP THE LASTEST window_size amount of runs of a test
    """
    os.makedirs(os.path.join(eval_const.feadir, project), exist_ok=True)

    df = pd.read_csv(const.OMIN_FILE)
    df = df[df["project"] == project]
    df = df[df["has_trunk_head_diff_data"] == True]
    df = df[df["build_timestamp"].notnull()]

    # sort the build from oldest to latest
    df = df.sort_values("build_timestamp", ascending=True)
    df = df[["pr_name", "build_id"]].values.tolist()

    history = {}
    for index, (pr_name, build_id) in enumerate(df):
        print("walking", project, window_size, index, pr_name, build_id)
        # read test result csv
        build = pd.read_csv(os.path.join(
            eval_const.trdir, 
            project, 
            eval_const.testclassdir, 
            f"{pr_name}_build{build_id}.csv"))
        
        # update the historical data per test
        # get the features for tests in this build
        features = []
        for row_idx, row in build.iterrows():
            test = row["testclass"]
            duration = row["duration"]
            outcome = row["outcome"]
            
            if test not in history:
                history[test] = {
                    "durations": [0],
                    "outcomes": [0],
                }

            outcomes = history[test]["outcomes"]
            failure_count = sum(outcomes)
            last_failure = find_last_failure(outcomes)
            transition_count = sum([1 for i in range(len(outcomes) - 1) if outcomes[i] != outcomes[i + 1]])
            last_transition = find_last_transition(outcomes)
            last_duration = history[test]["durations"][-1]
            average_duration = sum(history[test]["durations"]) / len(history[test]["durations"])

            features.append([
                test, failure_count, last_failure, 
                transition_count, last_transition,
                average_duration, last_duration,
            ])

            # update history of this test with current result to be used for next build
            history[test]["durations"] = history[test]["durations"][-(window_size-1):] + [duration]
            history[test]["outcomes"] = history[test]["outcomes"][-(window_size-1):] + [outcome]

        # save the per build feature data
        features = pd.DataFrame(features, columns=[
            "testclass",
            "failure_count", "last_failure",
            "transition_count", "last_transition",
            "average_duration", "last_duration",
        ])

        build_dir = os.path.join(eval_const.feadir, project, f"{pr_name}_build{build_id}", "window_history")
        os.makedirs(build_dir, exist_ok=True)
        features.to_csv(os.path.join(build_dir, eval_const.TEMPHIST_FILE.format(window_size=window_size)), index=False)


if __name__ == "__main__":
    for project in const.PROJECTS:
        for window_size in eval_const.WINDOW_SIZES:
            build_historical_data(project, window_size)
    pass

