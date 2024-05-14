import pandas as pd
import os
import sys
import json
import multiprocessing as mp

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import eval_const

"""per build, go historically from earlest to latest, get the test-file cocurrence matrix
whenever a test failed or its result transitioned
"""

def max_test_file_failure_hist(test, occurance, changeset, history):
    """
    for a test in build_N, for each file f_i in the change set,
    obtain the total (t, f_i) freq from build 1 to N-1, 
    then find the max freq across files
    return 0 if test has not failed before
    """
    # occurance records the total (t, f_i) freq from build 1 to N-1
    # only look at file in change set
    if test in occurance:
        max_tf_fail_freq = max([v for k, v in occurance[test].items() if k in changeset] + [0])
        failure_count = history[test]["failure_count"]
        max_tf_fail_freq_rel = max_tf_fail_freq / failure_count
        return max_tf_fail_freq, max_tf_fail_freq_rel
    return 0, 0


def max_test_file_transition_hist(test, occurance, changeset, history):
    if test in occurance:
        max_tf_trans_freq = max([v for k, v in occurance[test].items() if k in changeset] + [0])
        transition_count = history[test]["transition_count"]
        max_tf_trans_freq_rel = max_tf_trans_freq / transition_count
        return max_tf_trans_freq, max_tf_trans_freq_rel
    return 0, 0


def update_failure_occ(test, outcome, occurance, changeset):
    """add test if test has not failed before, incre fail count per file for this test"""
    # only do failed test
    if outcome == eval_const.FAIL:
        for file in changeset:
            if test not in occurance:
                occurance[test] = {}
            if file not in occurance[test]:
                occurance[test][file] = 0
            occurance[test][file] += 1
    return occurance


def update_transition_occ(test, outcome, occurance, changeset, history):
    # only do test with transitioned outcome
    if outcome != history[test]["last_outcome"]:
        for file in changeset:
            if test not in occurance:
                occurance[test] = {}
            if file not in occurance[test]:
                occurance[test][file] = 0
            occurance[test][file] += 1
    return occurance


def update_history(test, outcome, history):
    if outcome != history[test]["last_outcome"]:
        history[test]["transition_count"] += 1
    if outcome == eval_const.FAIL:
        history[test]["failure_count"] += 1
    history[test]["last_outcome"] = outcome
    return history


def build_test_file_hist_occurance_matrix(project):
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

        # load changset info
        with open(os.path.join(eval_const.changeinfodir, f"{project}.json"), "r") as f:
            change_info = json.load(f)

        # {test: {f1: freq1, f2: freq2,}}
        failure_occ = {}
        transition_occ = {}

        # for each test, store its last outcome, total number of transition and failure so far
        history = {}
        for index, (pr_name, build_id) in enumerate(stage_df):
            print("walking", project, stage, index, pr_name, build_id)
            # read test result csv
            build = pd.read_csv(os.path.join(
                eval_const.trdir, project,
                f"{pr_name}_build{build_id}", "stage_" + stage, eval_const.TEST_CLASS_CSV))
            changeset = set(change_info[f"{pr_name}_build{build_id}"]["changed_files"])
            
            features = []
            # get feature for each test in this build
            for row_idx, row in build.iterrows():
                test = row["testclass"]
                duration = row["duration"]
                outcome = row["outcome"]

                if test not in history:
                    history[test] = {
                        "last_outcome": 0,
                        "transition_count": 0,
                        "failure_count": 0,
                    }

                # get the feature from prior history
                max_tf_fail_freq, max_tf_fail_freq_rel = max_test_file_failure_hist(
                    test=test, occurance=failure_occ, changeset=changeset, history=history)
                max_tf_trans_freq, max_tf_trans_freq_rel = max_test_file_transition_hist(
                    test=test, occurance=transition_occ, changeset=changeset, history=history)

                # update occurance matrices
                failure_occ = update_failure_occ(test, outcome, failure_occ, changeset)
                transition_occ = update_transition_occ(test, outcome, transition_occ, changeset, history)
                
                # failure_count = history[test]["failure_count"]
                # transition_count = history[test]["transition_count"]
                # update history
                history = update_history(test, outcome, history)

                features.append([test, max_tf_fail_freq, max_tf_fail_freq_rel, 
                        max_tf_trans_freq, max_tf_trans_freq_rel,
                        #    failure_count, transition_count
                        ])

            # save the per build feature data
            features = pd.DataFrame(features, columns=[
                "testclass",
                "max_test_file_failure_frequency",
                "max_test_file_failure_frequency_relative",
                "max_test_file_transition_frequency",
                "max_test_file_transition_frequency_relative",
                # "failure_count", "transition_count",
            ])

            build_dir = os.path.join(eval_const.feadir, project, f"{pr_name}_build{build_id}", "stage_" + stage)
            os.makedirs(build_dir, exist_ok=True)
            features.to_csv(os.path.join(build_dir, eval_const.TF_HIST_FILE), index=False)


if __name__ == "__main__":
    for project in const.PROJECTS:
        build_test_file_hist_occurance_matrix(project)
    pass

