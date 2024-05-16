import glob
import os
import sys
import pandas as pd
import gzip
import json

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import eval_const


class Test:
    def __init__(self, name, duration, outcome, last_outcome=None):
        self.name = name
        self.duration = duration
        self.outcome = outcome
        self.last_outcome = last_outcome
        self.base_score = None
        self.hybrid_score = None
        self.prio_score = None
        self.tie_score = None

    def update_scores(self, base_score, hybrid_score, tie_score):
        self.base_score = base_score
        self.hybrid_score = hybrid_score
        self.tie_score = tie_score
        self.prio_score = self.base_score * self.hybrid_score


def gather_test_classes_from_all_suites(project, pr_name, build_id):
    files = glob.glob(
            os.path.join(eval_const.trdir, project, 
                         f"{pr_name}_build{build_id}", "stage_*", eval_const.TEST_CLASS_CSV))
    tests = set()
    for file in files:
        stage_tests = set(pd.read_csv(file)["testclass"].values.tolist())
        tests = tests.union(stage_tests)
    return list(tests)


def save_ordered_tests(ordered_tests, project, pr_name, build_id, stage_id, tcp, seed):
    output_dir = os.path.join(eval_const.orderedtestdir, project, 
                              f"{pr_name}_build{build_id}", f"stage_{stage_id}")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{tcp}_{seed}.json.gz")
    with gzip.open(output_path, "wt") as f:
        json.dump([vars(t) for t in ordered_tests], f)


def load_filter_tests(project, pr_name, build_id, stage_id, filters):
    input_dir = os.path.join(eval_const.trdir, project, 
                              f"{pr_name}_build{build_id}", f"stage_{stage_id}")
    # load to be filtered tests
    with gzip.open(os.path.join(input_dir, eval_const.FILTER_TESTS_FILE), "rt") as f:
        data = json.load(f)
        filtered_fails, filtered_trans = set(), set()
        for f in filters:
            filtered_fails = filtered_fails.union(set(data["for_fail"][f]))
            filtered_trans = filtered_trans.union(set(data["for_trans"][f]))
        return filtered_fails, filtered_trans


def load_ordered_tests(project, pr_name, build_id, stage_id, tcp, seed):
    input_dir = os.path.join(eval_const.orderedtestdir, project, 
                              f"{pr_name}_build{build_id}", f"stage_{stage_id}")
    input_path = os.path.join(input_dir, f"{tcp}_{seed}.json.gz")
    with gzip.open(input_path, "rt") as f:
        data = json.load(f)
        order_tests = []
        for d in data:
            t = Test(d["name"], d["duration"], d["outcome"], d["last_outcome"])
            t.update_scores(d["base_score"], d["hybrid_score"], d["tie_score"])
            order_tests.append(t)
        return order_tests
    

def get_dataset_name(filters):
    if len(filters) == 0:
        return "d_nofilter"
    else:
        return "d_" + "_".join(filters)
