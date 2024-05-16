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

import marco
import analysis_utils

matplotlib.rcParams.update({"font.size": 15})
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
from itertools import cycle
lines = ["-","--",":","-."]
linecycler = cycle(lines)



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


if __name__ == "__main__":
    multi_vertical_box_plots(marco.FILTER_COMBOS[0])
    pass