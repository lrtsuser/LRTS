import pandas as pd
import os
import sys
from scipy import stats
import scikit_posthocs as sp
import numpy as np
from statsmodels.stats.multicomp import pairwise_tukeyhsd

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import eval_const
import eval_metric

def get_testing_split(project, tcp, df):
    test_set = pd.read_csv(os.path.join(eval_const.mldir, project, "test_builds.csv"))
    test_set = test_set[["pr_name", "build_id"]].values.tolist()
    test_set = [f"{pr_name}_build{build_id}" for pr_name, build_id in test_set]
    newdf = df[df["pr_build"].isin(test_set)]
    # print(project, tcp, len(df), len(newdf))
    return newdf


def eval_summary(use_testing_set=False):
    """
    for each project, compute the geometric average metric value across builds and seeds
    use_testing_set: compute eval outcome for a specific set of builds, i.e., testing split for ML approach
    """
    summary = []
    # metric, project, tcp1, tcp2
    for metric in eval_metric.METRICS_NAME:
        for project in const.PROJECTS:
            row = [metric, const.PROJECT_PRETTY[project]]
            for tcp in eval_const.EVAL_TCPS:
                df = pd.read_csv(os.path.join(eval_const.evaloutcomedir, project, f"{tcp}.csv"))
                if use_testing_set:
                    df = get_testing_split(project, tcp, df)
                metric_values = df[df["tcp"] == tcp][metric]
                row.append(round(metric_values.mean(), 3))
            summary.append(row)
    summary = pd.DataFrame(summary, columns=["metric", "project"] + eval_const.EVAL_TCPS)
    file_name = "evaluation_alldata.csv" if not use_testing_set else "evaluation_testingdata.csv"
    summary.to_csv(os.path.join(eval_const.evaloutcomedir, file_name), index=False)
    pass

def add_to_group(groups, tcp1, tcp2):
    # groups is a adj list
    added = False
    current = groups.copy()
    for index, group in enumerate(current):
        if tcp1 in group or tcp2 in group:
            group += [tcp1, tcp2]
            groups[index] = list(set(group))
            added = True
            break
    if not added:
        groups.append([tcp1, tcp2])
    return groups


def add_rest_to_group(groups, tcps):
    added = set()
    for g in groups:
        added = added.union(set(g))
    for tcp in set(tcps) - added:
        groups.append([tcp])
    return groups


def get_nemenyi_groups(df):
    groups = []
    cols = df.columns.values
    for index, (tcp1, row_values) in enumerate(df.iterrows()):
        for tcp2 in cols[index+1:]:
            # null hypo is true, two tcp are the same
            if row_values[tcp2] > 0.05:
                print(tcp1, tcp2, row_values[tcp2])
                # put them into the same group
                groups = add_to_group(groups, tcp1, tcp2)
    # all other un-grouped techniques forms ind group
    groups = add_rest_to_group(groups, cols)
    return groups


def nemenyi_test(use_testing_set=False):
    """perform nemenyi test on the evaluation results from RTPs"""
    for metric in eval_metric.METRICS_NAME:
        print("checking", metric)
        outcomes = {}
        # for each tcp, get the eval outcome from csv
        for project in const.PROJECTS:
            for tcp in eval_const.EVAL_TCPS:
                if tcp not in outcomes:
                    outcomes[tcp] = []
                df = pd.read_csv(os.path.join(eval_const.evaloutcomedir, project, f"{tcp}.csv"))
                if use_testing_set:
                    df = get_testing_split(project, tcp, df)
                values = df[df["tcp"] == tcp].groupby("pr_build").mean().reset_index()
                outcomes[tcp] += values[metric].values.tolist()
        
        outcomes = [(k, v) for k, v in outcomes.items()]
        # get fridman result
        print(stats.friedmanchisquare(*[x[1] for x in outcomes]))
        # get nemenyi
        data = np.array([x[1] for x in outcomes])
        # Conduct the Nemenyi post-hoc test
        nemenyi = sp.posthoc_nemenyi_friedman(data.T)
        new_names = {i: outcomes[i][0] for i in range(len(outcomes))}
        nemenyi = nemenyi.rename(columns=new_names, index=new_names)
        nemenyi.to_csv(os.path.join(eval_const.evaloutcomedir, f"nemenyi_{metric}.csv"))
        groups = get_nemenyi_groups(nemenyi)
        print("number of groups", len(groups))
        print(groups)
    pass


def get_limited_hist_results():
    """
    metric, project, tcp_w1, tcp_w2, ...
    QTF(AVG), FC, LT, LF
    """
    os.makedirs(os.path.join(eval_const.evaloutcomedir, "limited_history"), exist_ok=True)

    for tcp in [eval_const.QTF_AVG_TCP, eval_const.FC_TCP, eval_const.LF_TCP, eval_const.LT_TCP]:
        summary = []
        for metric in eval_metric.METRICS_NAME:
            for project in const.PROJECTS:
                row = [metric, const.PROJECT_PRETTY[project]]
                # all variants with limited hist, and the original
                tcp_windows = [f"limhist{window}_{tcp}" for window in eval_const.WINDOW_SIZES] + [tcp]
                for tcp_window in tcp_windows:
                    df = pd.read_csv(os.path.join(eval_const.evaloutcomedir, project, f"{tcp_window}.csv"))
                    metric_values = df[df["tcp"] == tcp_window][metric]
                    row.append(round(metric_values.mean(), 3))
                summary.append(row)

        columns = ["metric", "project"] + [f"limhist{window}_{tcp}" for window in eval_const.WINDOW_SIZES] + [tcp]
            
        summary = pd.DataFrame(summary, columns=columns)
        summary.to_csv(os.path.join(eval_const.evaloutcomedir, "limited_history", f"{tcp}.csv"), index=False)
    pass

if __name__ == "__main__":
    # eval_summary(use_testing_set=True)
    # nemenyi_test(use_testing_set=True)
    get_limited_hist_results()
    pass