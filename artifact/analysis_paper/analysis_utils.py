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

def get_dataset(filters):
    if len(filters) == 0:
        return "d_nofilter"
    else:
        return "d_" + "_".join(filters)
        

def get_title(filters):
    if len(filters) == 0:
        return "eval-no_filter"
    else:
        return f"eval-{'_'.join(filters)}" 

# load stage information
def load_stages_with_50builds():
    ret = {}
    df = pd.read_csv(const.OMIN_FILE)
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
    # agg_level1 = ["pr_name", "build_id"]
    agg_level1 = ["seed"]

    df = read_eval_df(project, tcp, filters)
    df = filter_stages(project, df)
    # FILTERING BASED ON NUMBER OF FAILURES OF A BUILD
    # tsr_multifail = pd.read_csv("/Users/samcheng/Desktop/bigRT/metadata/omin_filter.csv")
    # tsr_multifail = tsr_multifail[tsr_multifail["num_fail_class"] >= 11][["project", "pr_name", "build_id", "stage_id"]]
    # df = pd.merge(df, tsr_multifail, how="inner", on=["project", "pr_name", "build_id", "stage_id"])

    # # FILTERING BASED ON NUMBER OF FAILURES OF A BUILD
    # tsr_multifail = pd.read_csv("/Users/samcheng/Desktop/bigRT/metadata/omin_filter.csv")
    # tsr_multifail = tsr_multifail[["project", "pr_name", "build_id", "stage_id", "num_fail_class"]]
    # df = pd.merge(df, tsr_multifail, how="inner", on=["project", "pr_name", "build_id", "stage_id"])
    # df = df[(df["num_fail_class"] >= df['num_fail_class'].quantile(0.76)) 
    #     & (df["num_fail_class"] <= df['num_fail_class'].quantile(1))]
    
    # # FILTERING BASED ON CHANGE SIZE
    # change_stats = pd.read_csv("/Users/samcheng/Desktop/bigRT/evaluation/change_info/change_stats.csv")
    # change_stats = change_stats[["project", "pr_name", "build_id", "num_changed_line"]]
    # df = pd.merge(df, change_stats, how="inner", on=["project", "pr_name", "build_id"])
    # df = df[(df["num_changed_line"] >= df['num_changed_line'].quantile(0.76)) 
    #     & (df["num_changed_line"] <= df['num_changed_line'].quantile(1))]

    # FILTERING BASED ON RATIO OF FAILURES OF A BUILD
    # tsr_multifail = pd.read_csv("/Users/samcheng/Desktop/bigRT/metadata/omin_filter.csv")
    # tsr_multifail['fail_ratio'] = tsr_multifail["num_fail_class"] / (tsr_multifail["num_fail_class"] + tsr_multifail["num_pass_class"])
    # df = pd.merge(df, tsr_multifail, how="inner", on=["project", "pr_name", "build_id", "stage_id"])
    # df = df[(df["fail_ratio"] >= df['fail_ratio'].quantile(.76)) & (df["fail_ratio"] <= df['fail_ratio'].quantile(1))]

    # # FILTERING BASED ON TEST SUITE DURATION OF A BUILD
    # tsr_multifail = pd.read_csv("/Users/samcheng/Desktop/bigRT/metadata/omin_filter.csv")
    # tsr_multifail = tsr_multifail[["project", "pr_name", "build_id", "stage_id", "stage_duration_by_method_sum"]]
    # df = pd.merge(df, tsr_multifail, how="inner", on=["project", "pr_name", "build_id", "stage_id"])
    # df = df[(df["stage_duration_by_method_sum"] >= df['stage_duration_by_method_sum'].quantile(0.76)) 
    #     & (df["stage_duration_by_method_sum"] <= df['stage_duration_by_method_sum'].quantile(1))]

    # # FILTERING BASED ON TEST SUITE SIZE OF A BUILD
    # tsr_multifail = pd.read_csv("/Users/samcheng/Desktop/bigRT/metadata/omin_filter.csv")
    # tsr_multifail["num_exec_test"] = tsr_multifail["num_pass_class"] + tsr_multifail["num_fail_class"]
    # tsr_multifail = tsr_multifail[["project", "pr_name", "build_id", "stage_id", "num_exec_test"]]
    # df = pd.merge(df, tsr_multifail, how="inner", on=["project", "pr_name", "build_id", "stage_id"])
    # df = df[(df["num_exec_test"] >= df['num_exec_test'].quantile(0.75)) 
    #     & (df["num_exec_test"] <= df['num_exec_test'].quantile(1))]

    if tcp.startswith("RL"):
        # ML is already testing set
        df = get_testing_split(project, df)
    # df = get_testing_split(project, df)
    # print(project, tcp, "#failed builds", 
    #       len(df.dropna(subset=["APFD_sameBug"])[["pr_name", "build_id", "stage_id"]].drop_duplicates()))
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

if __name__ == "__main__":
    # print(STAGES)
    # agg_project_wise_means("kafka", "QTF")
    agg_tcp_wise_data("QTF")
    pass