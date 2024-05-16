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

# params = {
#     'legend.fontsize': 15,
#     # 'figure.figsize': (15, 5),
#     'axes.labelsize': 20,
#     'axes.titlesize': 20,
#     # 'font.family': "Times New Roman",
#     'xtick.labelsize': 15,
#     'ytick.labelsize': 15,
#          }

matplotlib.rcParams.update({"font.size": 15})
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
from itertools import cycle
lines = ["-","--",":","-."]
linecycler = cycle(lines)


# # pylab.rcParams.update(params)
# plt.rcParams['text.usetex'] = True

"""
plot evaluation box plot for TCP technique(s)
"""

def collect_data(tcps, filters, data_type="mean"):
    """
    each data point is a seed, each project has 10 seeds
    thus, each data point is the average across all builds per stage, then across all stages of that seed
    """
    df = []
    for tcp in tcps:
        df.append(analysis_utils.agg_tcp_wise_data(tcp=tcp, filters=filters, data_type=data_type))
    df = pd.concat(df, axis=0)
    return df


def sort_tcp_by_mean(df, metric, ascending):
    means = df.groupby("tcp").mean().reset_index().sort_values(by=metric, ascending=ascending)
    return means["tcp"].values.tolist()


def add_axis_line(ax0, vertical=True):
    if vertical:
        ax0.xaxis.grid(True, linestyle="-", which="major", color="lightgrey",
                        # alpha=0.5
                        )
    else:
        ax0.yaxis.grid(True, linestyle="-", which="major", color="lightgrey",
                       # alpha=0.5
                       )
    ax0.set_axisbelow(True)


def vertical_box_plots(tcps, tcp_group_name):
    fig_dir = f"figures/{tcp_group_name}"
    os.makedirs(fig_dir, exist_ok=True)
    df = collect_data(tcps)
    for metric in eval_const.METRIC_NAMES:
        metric_df = df[["tcp", metric]]
        # sort the tcps from worse to best, by increasing mean
        tcps = sort_tcp_by_mean(metric_df, metric, ascending=True)
        print(metric, "Worst to Best TCPs: ", ", ".join(tcps))
        
        fig, ax0 = plt.subplots(figsize=(8, 3.5))
        meanprops = {"markerfacecolor":'white', 'marker':'o', 'markeredgecolor': 'blue'}
        x = [metric_df[metric_df["tcp"] == tcp][metric].dropna().values.tolist() for tcp in tcps]
        ax0.boxplot(x, widths=0.7, showmeans=True, patch_artist=True, 
                    boxprops = dict(facecolor="lightgrey"),
                    whis=1.5, sym="+", vert=False,
                    meanprops=meanprops, medianprops=dict(color="red"))
        # pretty formatting
        ax0.set_yticklabels([marco.MARCOS[t] for t in tcps])
        ax0.set_xlabel(metric)
        add_axis_line(ax0, vertical=True)
        add_axis_line(ax0, vertical=False)
        ax0.set_xlim(left=0, right=1)
        plt.tight_layout()
        fig.savefig(f"{fig_dir}/{metric}.jpg", bbox_inches="tight")
        # fig.savefig(f"{fig_dir}/{metric}.pdf", bbox_inches="tight")
        plt.close(fig)


def multi_vertical_box_plots(filters):
    plotting_tcps = [
        (marco.TRAD_TCPS, "Traditional"),
        (marco.IR_TCPS, "IR"),
        (marco.ML_TCPS, "ML"),
        (marco.RL_TCPS, "RL"),
    ]

    fig_dir = "figures"
    os.makedirs(fig_dir, exist_ok=True)

    nrows = len(plotting_tcps)
    ncols = len(marco.METRIC_NAMES)
    sorting_metric = marco.METRIC_NAMES[0]
    fig, ax = plt.subplots(nrows=nrows, ncols=ncols, figsize=(ncols*5, nrows*2.5), 
                           gridspec_kw={'width_ratios': [1,1,1,1], 'height_ratios': [1,6/9,5/9,6/9]})
    for row_idx, (tcps, tcp_group_name) in enumerate(plotting_tcps):
        df = collect_data(tcps, filters)
        # sort tcp by one metric
        tcps = sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=True)
        print(sorting_metric, "Worst to Best TCPs: ", ", ".join(tcps))
        for col_idx, metric in enumerate(marco.METRIC_NAMES):
            metric_df = df[["tcp", metric]]
            # sort the tcps from worse to best, by increasing mean
            meanprops = {"markerfacecolor":'white', 'marker':'o', 'markeredgecolor': 'blue'} 
            x = [metric_df[metric_df["tcp"] == tcp][metric].dropna().values.tolist() for tcp in tcps]
            bp = ax[row_idx, col_idx].boxplot(x, widths=0.3, showmeans=True, patch_artist=True, 
                        boxprops = dict(facecolor="lightgrey"),
                        whis=1.5, sym="+", vert=False,
                        meanprops=meanprops, medianprops=dict(color="red", linewidth=4))
            if row_idx == 0 and col_idx == 0:
                ax[row_idx, col_idx].legend([bp['means'][0], bp['medians'][0]], ['Mean', 'Median'])
            # pretty formatting
            if col_idx == 0:
                ax[row_idx, col_idx].set_yticklabels([marco.MARCOS[t] for t in tcps])
                # ax[row_idx, col_idx].set_ylabel(tcp_group_name, fontsize=22)
                # ax[row_idx, col_idx].yaxis.set_label_coords(-1, len(plotting_tcps - row_idx)*2)
            else:
                ax[row_idx, col_idx].tick_params(labelleft=False)
            if row_idx == len(plotting_tcps) - 1:
                ax[row_idx, col_idx].set_xlabel(marco.MARCOS[metric], fontsize=22)
            add_axis_line(ax[row_idx, col_idx], vertical=True)
            add_axis_line(ax[row_idx, col_idx], vertical=False)
            ax[row_idx, col_idx].set_xlim(left=0, right=1)
    # fig.suptitle(analysis_utils.get_title(filters), fontsize=30)
    # fig.supxlabel(f"Evaluation of TCP groups (sorted in descending {marco.MARCOS[sorting_metric]} from top to bottom)", fontsize=30)
    plt.tight_layout()
    fig.savefig(f"{fig_dir}/{analysis_utils.get_title(filters)}.jpg", bbox_inches="tight")
    fig.savefig(f"{fig_dir}/{analysis_utils.get_title(filters)}.pdf", bbox_inches="tight")
    # fig.savefig(f"{fig_dir}/{metric}.pdf", bbox_inches="tight")
    plt.close(fig)



def plot_trad_ml_for_generalizability(filters):
    plotting_tcps = [
        (marco.TRAD_TCPS, "Traditional", 0, 0, 1),
        (marco.IR_TCPS, "IR", 0, 1, 6/9),
        (marco.ML_TCPS, "ML", 1, 0, 5/9),
        (marco.RL_TCPS, "RL", 1, 1, 6/9),
    ]

    fig_dir = "figures"
    os.makedirs(fig_dir, exist_ok=True)

    nrows = 4
    ncols = 1
    sorting_metric = marco.METRIC_NAMES[0]
    fig, ax = plt.subplots(nrows=nrows, ncols=ncols, figsize=(ncols*7, nrows*2.5), gridspec_kw={'height_ratios': [1,6/9, 5/9, 6/9]})
    for idx, (tcps, tcp_group_name, row_idx, col_idx, ratio) in enumerate(plotting_tcps):
        df = collect_data(tcps, filters)
        # sort tcp by one metric
        tcps = sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=True)
        print(sorting_metric, "Worst to Best TCPs: ", ", ".join(tcps))
        metric_df = df[["tcp", sorting_metric]]
        # sort the tcps from worse to best, by increasing mean
        meanprops = {"markerfacecolor":'white', 'marker':'o', 'markeredgecolor': 'blue'} 
        x = [metric_df[metric_df["tcp"] == tcp][sorting_metric].dropna().values.tolist() for tcp in tcps]
        bp = ax[idx].boxplot(x, widths=0.3, showmeans=True, patch_artist=True, 
                    boxprops = dict(facecolor="lightgrey"),
                    whis=1.5, sym="+", vert=False,
                    meanprops=meanprops, medianprops=dict(color="red", linewidth=4))
        if idx == 0:
            ax[idx].legend([bp['means'][0], bp['medians'][0]], ['Mean', 'Median'])
        # pretty formatting
        ax[idx].set_yticklabels([marco.MARCOS[t] for t in tcps])
        add_axis_line(ax[idx], vertical=True)
        add_axis_line(ax[idx], vertical=False)
        ax[idx].set_xlim(left=0, right=1)
        # ax[row_idx, col_idx].set_ylim(top=10 * ratio, bottom=0)
    # fig.suptitle(analysis_utils.get_title(filters), fontsize=30)
    # fig.supxlabel(f"Evaluation of TCP groups (sorted in descending {marco.MARCOS[sorting_metric]} from top to bottom)", fontsize=30)
    plt.tight_layout()
    fig.savefig(f"{fig_dir}/small_{analysis_utils.get_title(filters)}.jpg", bbox_inches="tight")
    fig.savefig(f"{fig_dir}/small_{analysis_utils.get_title(filters)}.pdf", bbox_inches="tight")
    # fig.savefig(f"{fig_dir}/{metric}.pdf", bbox_inches="tight")
    plt.close(fig)


def plot_first_failure(filters):
    plotting_tcps = [
        (marco.TRAD_TCPS, "Traditional", 0, 0, 1),
        (marco.IR_TCPS, "IR", 1, 0, 6/9),
    ]

    fig_dir = "figures"
    os.makedirs(fig_dir, exist_ok=True)

    nrows = 2
    ncols = 1
    sorting_metric = marco.METRIC_NAMES[0]
    fig, ax = plt.subplots(nrows=nrows, ncols=ncols, figsize=(ncols*7, nrows*3), gridspec_kw={'height_ratios': [1,6/9]})
    for idx, (tcps, tcp_group_name, row_idx, col_idx, ratio) in enumerate(plotting_tcps):
        df = collect_data(tcps, filters)
        # sort tcp by one metric
        tcps = sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=True)
        print(sorting_metric, "Worst to Best TCPs: ", ", ".join(tcps))
        metric_df = df[["tcp", sorting_metric]]
        # sort the tcps from worse to best, by increasing mean
        meanprops = {"markerfacecolor":'white', 'marker':'o', 'markeredgecolor': 'blue'} 
        x = [metric_df[metric_df["tcp"] == tcp][sorting_metric].dropna().values.tolist() for tcp in tcps]
        bp = ax[row_idx].boxplot(x, widths=0.3, showmeans=True, patch_artist=True, 
                    boxprops = dict(facecolor="lightgrey"),
                    whis=1.5, sym="+", vert=False,
                    meanprops=meanprops, medianprops=dict(color="red", linewidth=4))
        if idx == 0:
            ax[row_idx].legend([bp['means'][0], bp['medians'][0]], ['Mean', 'Median'])
        # pretty formatting
        ax[row_idx].set_yticklabels([marco.MARCOS[t] for t in tcps])
        add_axis_line(ax[row_idx], vertical=True)
        add_axis_line(ax[row_idx], vertical=False)
        ax[row_idx].set_xlim(left=0, right=1)
        # ax[row_idx, col_idx].set_ylim(top=10 * ratio, bottom=0)
    # fig.suptitle(analysis_utils.get_title(filters), fontsize=30)
    # fig.supxlabel(f"Evaluation of TCP groups (sorted in descending {marco.MARCOS[sorting_metric]} from top to bottom)", fontsize=30)
    plt.tight_layout()
    fig.savefig(f"{fig_dir}/small_{analysis_utils.get_title(filters)}.jpg", bbox_inches="tight")
    fig.savefig(f"{fig_dir}/small_{analysis_utils.get_title(filters)}.pdf", bbox_inches="tight")
    # fig.savefig(f"{fig_dir}/{metric}.pdf", bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    multi_vertical_box_plots(marco.FILTER_COMBOS[0])
    pass