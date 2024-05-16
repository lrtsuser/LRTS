import pandas as pd
import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
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
import marco
import analysis_utils
import evaluation.eval_const as eval_const
import evaluation.eval_utils as eval_utils


fig_dir = "figures/rl"
os.makedirs(fig_dir, exist_ok=True)


def load_rl_eval_data(project, tcp, filters):
    df = analysis_utils.read_eval_df(project, tcp, filters)
    df = analysis_utils.filter_stages(project, df)
    return df
    

# def plot_CI_hist_learning_trend(metric, filters):
#     print(filters)
#     omni = pd.read_csv(const.DATASET_FILE)
#     for project in const.PROJECTS:
#         ntcps = len(eval_const.RL_TCPS)
#         fig, ax = plt.subplots(nrows=ntcps, ncols=1, figsize=(15, 2*ntcps))
#         for idx, tcp in enumerate(eval_const.RL_TCPS):
#             df = load_rl_eval_data(project, tcp, filters)
#             df = df[["pr_name", "build_id", "stage_id", metric]]
#             sorted_df = pd.merge(df, omni[omni["project"] == project][["pr_name", "build_id", "stage_id", "build_timestamp"]], 
#                                  "left", on=["pr_name", "build_id", "stage_id"])
#             sorted_df = sorted_df.dropna().sort_values(by=["build_timestamp"], ascending=True)
#             # stages = sorted_df["stage_id"].drop_duplicates().values.tolist()
#             sorted_df = sorted_df.groupby(["pr_name", "build_id", "stage_id"]).mean().reset_index()
#             # for stage in stages:
#             values = sorted_df[metric].rolling(30).mean().values.tolist()
#             ax[idx].plot(values, alpha=0.5)
#             ax[idx].set_title(tcp)
#         plt.tight_layout()
#         fig.savefig(f"{fig_dir}/{project}_{metric}.jpg", bbox_inches="tight")
#         # fig.savefig(f"{fig_dir}/{metric}.pdf", bbox_inches="tight")
#         plt.close(fig)

def plot_CI_hist_learning_trend(metric, filters):
    """each project is a line, each line is averaged across techniques"""
    print("filters", filters)
    fig, ax = plt.subplots(figsize=(15, 3))
    omni = pd.read_csv(const.DATASET_FILE)
    min_length = 1000000
    for project in const.PROJECTS:
        df = []
        for idx, tcp in enumerate([eval_const.RL_NN_TC_TCP]):
            tcp_df = load_rl_eval_data(project, tcp, filters)
            tcp_df = tcp_df[["tcp", "pr_name", "build_id", "stage_id", metric]].dropna()
            df.append(tcp_df)
        df = pd.concat(df, axis=0)
        # take average across techniques and stages
        df = df.groupby(["pr_name", "build_id"]).mean().reset_index()
        # sort results from oldest to latest builds
        build_ts_df = omni[omni["project"] == project][["pr_name", "build_id", "build_timestamp"]].drop_duplicates()
        df = pd.merge(df, build_ts_df, "left", on=["pr_name", "build_id"])
        df = df.sort_values(["build_timestamp"], ascending=True)
        values = df[metric].rolling(50).mean().dropna().values.tolist()
        # values = df[metric].values.tolist()
        print(project, len(values))
        if len(values) > 100:
            ax.plot(values, label=project)
    plt.title(f"{marco.MARCOS[metric]} moving average of the best RL TCP - RL (NN, TCFail)")
    plt.xlabel("CI builds (from oldest to latest)")
    plt.xlim(left=0, right=1000)
    plt.legend()
    plt.tight_layout()
    fig.savefig(f"{fig_dir}/allproject_{metric}.jpg", bbox_inches="tight")
    # fig.savefig(f"{fig_dir}/{metric}.pdf", bbox_inches="tight")
    plt.close(fig)

if __name__ == "__main__":
    plot_CI_hist_learning_trend("APFD_sameBug", marco.FILTER_COMBOS[-1])
    plot_CI_hist_learning_trend("APFDc_sameBug", marco.FILTER_COMBOS[-1])
    plot_CI_hist_learning_trend("NRPA", marco.FILTER_COMBOS[-1])