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


def eval_tcp_on_build(project, tcp, pr_name, build_id, stage_id, index,
                      filters, save_ordered_tests=False, use_ordered_tests=False):
    """
    evaluate a tcp on a test run, return seed -> metric value 
    {
        seed1: {metric1:, metric2:, },
        seed2: {metric1:, metric2:, },
        ...
    }
    """
    results = {}
    if use_ordered_tests:
        filtered_fails, filtered_trans = eval_utils.load_filter_tests(
            project, pr_name, build_id, stage_id, filters)
        for seed in range(NSEEDS):
            ordered_tests = eval_utils.load_ordered_tests(
                project, pr_name, build_id, stage_id, tcp, seed)
            metric_values = eval_metric.compute_metrics(
                ordered_tests, filtered_fails, filtered_trans)
            results[f"seed_{seed}"] = metric_values
    else:
        tests = construct_testrun_objects(project, pr_name, build_id, stage_id)
        # setup tcp runner
        tcp_runner = eval_tcp.TestPrioritization(
            tests=tests,
            project=project,
            tcp=tcp,
            pr_name=pr_name,
            build_id=build_id,
            stage_id=stage_id,
        )
        # run tcp on this test run for a number of random seeds
        # record the evaluation outcome of each seed
        for seed in range(NSEEDS):
            ordered_tests = tcp_runner.run_tcp(seed)
            if save_ordered_tests:
                eval_utils.save_ordered_tests(
                    ordered_tests, project, pr_name, build_id, stage_id, tcp, seed)
            metric_values = eval_metric.compute_metrics(ordered_tests)
            results[f"seed_{seed}"] = metric_values
    # logging
    if index % 1000 == 0:
        print("evaluating", project, tcp, pr_name, build_id, stage_id, index,
            "#failed tests", len([1 for t in ordered_tests if t.outcome == eval_const.FAIL]),
            "#trans tests", len([1 for t in ordered_tests if t.outcome != t.last_outcome]))
        sys.stdout.flush()
    return results, pr_name, build_id, stage_id


# def filter_builds(df):
#     df = df[(df["num_fail_class"] > 0) | (df["num_trans_class"] > 0)]
#     return df


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
    df = pd.read_csv(const.DATASET_FILTER_FILE)
    df = df[df["project"] == project]
    df = filter_builds(df, filters)
    
    # evaluating ML RTP only on the testing dataset
    if "ML_" in tcp:
        print("USING TESTING SET FOR", tcp)
        df = get_testing_split(project, df)
    
    builds = df[["pr_name", "build_id", "stage_id"]].values.tolist()
    print("EVALUATING", project, tcp, len(builds), "FILTER", filters)

    eval_outcome = {}

    args = [(project, tcp, pr_name, build_id, stage_id, index, filters) 
            for index, (pr_name, build_id, stage_id) in enumerate(builds)]
    pool = mp.Pool(mp.cpu_count())
    result = pool.starmap(eval_tcp_on_build, args)
    for r in result:
        eval_outcome[f"{r[1]},, {r[2]},, {r[3]}"] = r[0]

    df = parse_eval_result_to_df(project, {tcp: eval_outcome})
    df.to_csv(os.path.join(eval_const.evaloutcomedir, eval_utils.get_dataset_name(filters), project, f"{tcp}.csv.zip"), index=False)
    return eval_outcome


def eval():
    for filters in eval_const.FILTER_COMBOS:
        for i, project in enumerate(const.PROJECTS):
            # create folder to store results
            project_outcome_dir = os.path.join(eval_const.evaloutcomedir, eval_utils.get_dataset_name(filters), project)
            os.makedirs(project_outcome_dir, exist_ok=True)

            # evaluate tcp
            for j, tcp in enumerate(eval_const.EVAL_TCPS):
                eval_tcp_on_project(project, tcp, filters)

if __name__ == "__main__":
    eval()
    pass