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
for test t in Build suite_N, extract its data from previous build suite_1 to suite_N-1

from https://dl.acm.org/doi/10.1145/3460319.3464834, get
- F1.1 failure count, total number of times t failed
- F1.2 last failure, amount of CI runs since last failure
- F1.4 last transition, amount of CI runs since last transition
- F1.5 average test execution time across previous builds

- F2.1 Maximum (test, file)-failure frequency, Given a test t in Suite_N, 
    for each file in the combined changeset, 
    we first obtain the total (t, file)-failure frequency from {suite_1 ... suite_N-1}. 
    Then, we determine the maximum across all files, 
    as the combined changeset is as risky for t as its riskiest file.
"""


def update_history(d, new_average_duration, duration, outcome):
    if outcome == eval_const.FAIL:
        d["failure_count"] += 1
    
    if outcome == eval_const.FAIL:
        d["last_failure"] = 1
    else:
        d["last_failure"] += 1
    
    if outcome == d["last_outcome"]:
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


def build_historical_data(project):
    """
    walk the historical test runs from oldest to newest
    build the historical features per-build per-test in bottom-up way
    """
    os.makedirs(os.path.join(eval_const.feadir, project), exist_ok=True)

    df = pd.read_csv(const.OMIN_FILE)
    df = df[df["project"] == project]
    stages = list(set(df["stage_id"].values.tolist()))

    for stage in stages:
        # select builds with this stage/job
        stage_df = df[df["stage_id"] == stage]
        # sort the build from oldest to latest
        stage_df = stage_df.sort_values("build_timestamp", ascending=True)
        stage_df = stage_df[["pr_name", "build_id"]].values.tolist()

        history = {}
        for index, (pr_name, build_id) in enumerate(stage_df):
            print("walking", project, stage, index, pr_name, build_id)
            # read test result csv
            build = pd.read_csv(os.path.join(
                eval_const.trdir, project, 
                f"{pr_name}_build{build_id}", "stage_" + stage, eval_const.TEST_CLASS_CSV))
            
            # update the historical data per test
            # get the features for tests in this build
            features = []
            for row_idx, row in build.iterrows():
                test = row["testclass"]
                duration = row["duration"]
                outcome = row["outcome"]
                
                if test not in history:
                    history[test] = {
                        "failure_count": 0,
                        "last_failure": 0,
                        "transition_count": 0,
                        "last_transition": 0,
                        "average_duration": 0,
                        "last_duration": 0,
                        "run_count": 0,
                        "last_outcome": 0,
                    }

                # for the current build N, get features from 1 to N-1
                # average duration
                prev_average = history[test]["average_duration"]
                run_count = history[test]["run_count"]
                new_average = (prev_average * run_count + duration) / (run_count + 1)

                # other features
                features.append([
                    test,
                    history[test]["failure_count"],
                    history[test]["last_failure"],
                    history[test]["transition_count"],
                    history[test]["last_transition"],
                    round(new_average, 3),
                    history[test]["last_duration"],
                    # history[test]["last_outcome"],
                ])

                # update history of this test with current result to be used for next build
                history[test] = update_history(history[test], new_average, duration, outcome)

            # save the per build feature data
            features = pd.DataFrame(features, columns=[
                "testclass",
                "failure_count", "last_failure",
                "transition_count", "last_transition",
                "average_duration", "last_duration",
                # "last_outcome",
            ])

            build_dir = os.path.join(eval_const.feadir, project, f"{pr_name}_build{build_id}", "stage_" + stage)
            os.makedirs(build_dir, exist_ok=True)
            features.to_csv(os.path.join(build_dir, eval_const.HIST_FILE), index=False)


if __name__ == "__main__":
    for project in const.PROJECTS:
        build_historical_data(project)
    pass

