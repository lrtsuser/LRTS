import pandas as pd
import os
import sys
import json
import multiprocessing as mp
import matplotlib.pyplot as plt
import itertools
import numpy as np

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import eval_const
import eval_tcp
import eval_utils
import eval_metric

NSEEDS = 10


def construct_testrun_objects(project, pr_name, build_id, stage_id):
    # load original test run from build
    df = pd.read_csv(os.path.join(
        eval_const.trdir, project, f"{pr_name}_build{build_id}", "stage_" + stage_id, eval_const.TEST_CLASS_CSV))
    tests = []
    for index, row in df.iterrows():
        tests.append(eval_utils.Test(
            name=row["testclass"],
            duration=row["duration"] + 0.001,
            outcome=row["outcome"],
            last_outcome=row["last_outcome"]))
    return tests


def eval_tcp_on_build(project, tcp, pr_name, build_id, stage_id, index, filters):
    """load prioritized tests, return relative positions of failed tests"""
    filtered_fails, filtered_trans = eval_utils.load_filter_tests(
        project, pr_name, build_id, stage_id, filters)
    # print(project, pr_name, build_id, stage_id, filtered_fails, filtered_trans)
    seed = 0
    ordered_tests = eval_utils.load_ordered_tests(
        project, pr_name, build_id, stage_id, tcp, seed)
    num_tests = len(ordered_tests)
    failed_test_poses = [i + 1 for i in range(len(ordered_tests)) if ordered_tests[i].outcome == eval_const.FAIL]
    failed_test_rel_poses = [i / num_tests for i in failed_test_poses]
    # logging
    if index % 1000 == 0:
        print("evaluating", project, tcp, pr_name, build_id, stage_id, index,
            "#failed tests", len([1 for t in ordered_tests if t.outcome == eval_const.FAIL]))
        sys.stdout.flush()
    return failed_test_rel_poses



def filter_builds(df, filters):
    fail_filter_ret = df["num_fail_class"] > 0
    for f in filters:
        ff_col = "num_fail_class+" + (f + "_for_fail" if f != eval_const.FILTER_FIRST else "first_failure")
        fail_filter_ret = fail_filter_ret & (df[ff_col] > 0)
    trans_filter_ret = df["num_trans_class"] > 0
    for f in filters:
        tf_col = "num_trans_class+" + (f + "_for_trans" if f != eval_const.FILTER_FIRST else "first_trans")
        trans_filter_ret = trans_filter_ret & (df[tf_col] > 0)
    return df[fail_filter_ret | trans_filter_ret]


def parse_eval_result_to_df(project, data):
    df = []
    for tcp in data:
        for pr_build_stage in data[tcp]:
            for seed in data[tcp][pr_build_stage]:
                pr_name, build_id, stage_id = pr_build_stage.split(",, ")
                row = [project, tcp, pr_name, build_id, stage_id, seed]
                # append metric results
                for metric in eval_const.METRIC_NAMES:
                    value = data[tcp][pr_build_stage][seed][metric]
                    row.append(round(value, 3))
                df.append(row)
    identifiers = ["project", "tcp", "pr_name", "build_id", "stage_id", "seed"]
    df = pd.DataFrame(df, columns=identifiers + eval_const.METRIC_NAMES)
    return df



def get_testing_split(project, df):
    """only eval on a subset of builds, i.e., testing split for ML approach"""
    testing_builds = pd.read_csv(os.path.join(
        eval_const.mldir, project, eval_const.ML_TESTING_SET))
    testing_builds = testing_builds[["pr_name", "build_id", "stage_id"]].values.tolist()

    testing_df = []
    for index, (pr_name, build_id, stage_id) in enumerate(testing_builds):
        current = df[(df["pr_name"] == pr_name) & (df["build_id"] == build_id) & (df["stage_id"] == stage_id)]
        testing_df.append(current)
    testing_df = pd.concat(testing_df, axis=0)
    print(project, "FULL DATASET SIZE", len(df), "TESTING SPLIT", len(testing_df))
    
    return testing_df



def eval_tcp_on_project(project, tcp, filters):
    """
    parallel on builds
    """

    # load to be evaluated builds
    df = pd.read_csv(const.OMIN_FILTER_FILE)
    df = df[df["project"] == project]
    df = filter_builds(df, filters)
    
    # evaluating ML RTP only on the testing dataset
    if "ML_" in tcp:
        print("USING TESTING SET FOR", tcp)
        df = get_testing_split(project, df)
    
    builds = df[["pr_name", "build_id", "stage_id"]].values.tolist()
    print("EVALUATING", project, tcp, len(builds), "FILTER", filters)

    args = [(project, tcp, pr_name, build_id, stage_id, index, filters) 
            for index, (pr_name, build_id, stage_id) in enumerate(builds)]
    pool = mp.Pool(mp.cpu_count())
    result = pool.starmap(eval_tcp_on_build, args)
    return result



def eval():
    filters = eval_const.FILTER_COMBOS[0]
    result = {}
    for i, project in enumerate(const.PROJECTS):
        # evaluate tcp
        for j, tcp in enumerate(eval_const.EVAL_TCPS):
            ret = eval_tcp_on_project(project, tcp, filters)
            print("builds", len(ret))
            result[f"{project},{tcp}"] = ret
    with open("failed_test_rel_pos_figs/pos.json", "w") as f:
        json.dump(result, f)    
            
def draw():
    data = json.load(open("failed_test_rel_pos_figs/pos.json", "r"))
    for j, tcp in enumerate(eval_const.EVAL_TCPS):
        result = []
        for key in data.keys():
            if key.endswith(tcp):
                result += data[key]
        result = list(itertools.chain(*result))
        result = np.array(result)
        # Create a histogram plot
        plt.clf()
        plt.hist(result)
        plt.xlabel('Failed Test Position After Prioritization / Test Suite Run Size')
        plt.ylabel('Frequency')
        plt.title(f'{tcp}, mean: {result.mean()}')
        plt.tight_layout()
        # Save the plot as a PNG file
        plt.savefig(f'failed_test_rel_pos_figs/{tcp}.png')



if __name__ == "__main__":
    # eval()
    draw()
    pass