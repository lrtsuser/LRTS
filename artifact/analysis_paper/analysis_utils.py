import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
from scipy.stats.mstats import gmean
import matplotlib.gridspec as gridspec
import matplotlib.pylab as pylab


script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "analysis_paper")
eval_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)
sys.path.append(eval_dir)

import const
import evaluation.eval_const as eval_const
import evaluation.eval_utils as eval_utils
import marco

IR_CTRL_DURATION = "Duration"
IR_CTRL_NFAIL = "#Failures"
IR_CTRL_FAILRATIO = "Fail Ratio"
IR_CTRL_CHGSIZE = "Change Size"
IR_CTRLS = [IR_CTRL_DURATION, IR_CTRL_NFAIL, IR_CTRL_FAILRATIO, IR_CTRL_CHGSIZE]
IR_CTRL_QUANTILES = [[0, 0.25], [0.26, 0.5], [0.51, 0.74], [0.75, 1]]

def get_dataset(filters):
    if len(filters) == 0:
        return "d_nofilter"
    else:
        return "d_" + "_".join(filters)
        

def get_title(filters):
    return "eval-" + marco.DATASET_MARCO["_".join(filters)]
    # if len(filters) == 0:
    #     return "eval-no_filter"
    # else:
    #     return f"eval-{'_'.join(filters)}" 

# load stage information
def load_stages_with_50builds():
    ret = {}
    df = pd.read_csv(const.DATASET_FILE)
    project_stages = df[["project", "stage_id"]].drop_duplicates().values.tolist()
    for project, stage in project_stages:
        num_builds = len(df[(df["project"] == project) & (df["stage_id"] == stage)])
        if num_builds > 50:
            if project not in ret:
                ret[project] = []
            ret[project].append(stage)
    return ret            
STAGES = load_stages_with_50builds()


def filter_stages(project, df):
    # remove evaluation outcomes from stages with <50 builds in a project
    return df[df["stage_id"].isin(STAGES[project])]


def read_eval_df(project, tcp, filters):
    return pd.read_csv(os.path.join(
        eval_const.evaloutcomedir, get_dataset(filters), 
        f"{project}/{tcp}.csv.zip"))


def read_eval_df_rebuttal(project, tcp, filters):
    return pd.read_csv(os.path.join(
        eval_const.evaloutcomedir, "rebuttal_d_jira_stageunique_freqfail", 
        f"{project}/{tcp}.csv.zip"))


def get_testing_split(project, df):
    testing_builds = pd.read_csv(os.path.join(
        eval_const.mldir, project, eval_const.ML_TESTING_SET))
    testing_builds = testing_builds[["project", "pr_name", "build_id", "stage_id"]]
    testing_df = pd.merge(testing_builds, df, "left", on=["project", "pr_name", "build_id", "stage_id"])
    # print(project, "FULL DATASET SIZE", len(df), "TESTING SPLIT", len(testing_df))
    return testing_df


def agg_project_wise_data(project, tcp, filters, data_type="mean"):
    """
    input: a csv from eval_outcome for a (project, tcp) tuple
    1. get means across builds per stage
    2. get mean across stages from step 1. (we dont want one project with many stages to dominate)
    return a df of [seed, metric1, metric2, ...]
    """
    agg_level1 = ["seed"]

    df = read_eval_df(project, tcp, filters)
    df = filter_stages(project, df)

    if tcp.startswith("RL"):
        # ML is already testing set
        df = get_testing_split(project, df)
    if data_type == "mean":
        agg = df[agg_level1 + eval_const.METRIC_NAMES].groupby(
            agg_level1).mean().reset_index()
    elif data_type == "median":
        agg = df[agg_level1 + eval_const.METRIC_NAMES].groupby(
            agg_level1).median().reset_index()
    elif data_type == None:
        agg = df[eval_const.METRIC_NAMES]
    agg["tcp"] = tcp
    agg["project"] = project
    return agg


def agg_tcp_wise_data(tcp, filters, data_type="mean"):
    """get seed-wise data points from all projects for a group of tcps"""
    df = []
    for project in const.PROJECTS:
        df.append(agg_project_wise_data(project, tcp, filters, data_type))
    df = pd.concat(df, axis=0)
    return df


def control_df(df, col, quantiles):
    df = df[(df[col] >= df[col].quantile(quantiles[0])) 
        & (df[col] <= df[col].quantile(quantiles[1]))]
    return df

def agg_project_wise_data_controlled(
        project, tcp, filters, data_type="mean", controlled_var=None, quantiles=[]):
    agg_level1 = ["seed"]

    df = read_eval_df(project, tcp, filters)
    df = filter_stages(project, df)

    # FILTERING BASED ON NUMBER OF FAILURES OF A BUILD
    if controlled_var == IR_CTRL_NFAIL:
        control = pd.read_csv(const.DATASET_FILTER_FILE)
        control = control[["project", "pr_name", "build_id", "stage_id", "num_fail_class"]]
        df = pd.merge(df, control, how="inner", on=["project", "pr_name", "build_id", "stage_id"])
        df = control_df(df, "num_fail_class", quantiles)
        
    # FILTERING BASED ON CHANGE SIZE
    if controlled_var == IR_CTRL_CHGSIZE:
        control = pd.read_csv(os.path.join(eval_const.changeinfodir, "change_stats.csv"))
        control = control[["project", "pr_name", "build_id", "num_changed_line"]]
        df = pd.merge(df, control, how="inner", on=["project", "pr_name", "build_id"])
        df = control_df(df, "num_changed_line", quantiles)

    # FILTERING BASED ON RATIO OF FAILURES OF A BUILD
    if controlled_var == IR_CTRL_FAILRATIO:
        control = pd.read_csv(const.DATASET_FILTER_FILE)
        control['fail_ratio'] = control["num_fail_class"] / (control["num_fail_class"] + control["num_pass_class"])
        df = pd.merge(df, control, how="inner", on=["project", "pr_name", "build_id", "stage_id"])
        df = control_df(df, "fail_ratio", quantiles)

    # FILTERING BASED ON TEST SUITE DURATION OF A BUILD
    if controlled_var == IR_CTRL_DURATION:
        control = pd.read_csv(const.DATASET_FILTER_FILE)
        control = control[["project", "pr_name", "build_id", "stage_id", "test_suite_duration_s"]]
        df = pd.merge(df, control, how="inner", on=["project", "pr_name", "build_id", "stage_id"])
        df = control_df(df, "test_suite_duration_s", quantiles)

    if tcp.startswith("RL"):
        df = get_testing_split(project, df)
    if data_type == "mean":
        agg = df[agg_level1 + eval_const.METRIC_NAMES].groupby(
            agg_level1).mean().reset_index()
    elif data_type == "median":
        agg = df[agg_level1 + eval_const.METRIC_NAMES].groupby(
            agg_level1).median().reset_index()
    elif data_type == None:
        agg = df[eval_const.METRIC_NAMES]
    agg["tcp"] = tcp
    agg["project"] = project
    return agg



def agg_tcp_wise_data_controlled(
        tcp, filters, data_type="mean", controlled_var=None, quantiles=[]):
    """get seed-wise data points from all projects for a group of tcps"""
    df = []
    for project in const.PROJECTS:
        df.append(agg_project_wise_data_controlled(
            project, tcp, filters, data_type, controlled_var, quantiles))
    df = pd.concat(df, axis=0)
    return df

if __name__ == "__main__":
    pass