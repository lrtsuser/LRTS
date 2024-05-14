import sys
import os
import pandas as pd
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import eval_const
import eval_metric

FIGDIR = "figures"
os.makedirs(FIGDIR, exist_ok=True)


def add_axis_line(ax0):
    ax0.yaxis.grid(True, linestyle="-", which="major", color="lightgrey",
               alpha=0.5)
    ax0.set_axisbelow(True)


def draw_boxplot(metric, tcp):
    """
    draw box plot per project
    each data point is a build result average across seed
    """
    print("drawing", metric, tcp)

    # get data points
    data = []
    means = []
    for project in const.PROJECTS:
        df = pd.read_csv(os.path.join(eval_const.evaloutcomedir, project, "evaluation.csv"))
        df = df[df["tcp"] == tcp][["pr_build", metric]]
        df = df.groupby("pr_build").mean().reset_index()
        data.append(df[metric].values.tolist())
        means.append(df[metric].mean())
    
    # draw plot
    ticks = [x for x in range(0, len(const.PROJECTS), 1)] # 0, 2, 4, ...
    positions = [x for x in ticks]

    fig, axes = plt.subplots(figsize=(13, 3))
    add_axis_line(axes)
    axes.boxplot(x=data,
        # patch_artist=True,
        positions=positions,
        widths=0.3,
        # showcaps=False,
        # sym="",
        # whiskerprops=dict(color=box_color),
        # boxprops=dict(facecolor=box_color, edgecolor=box_color),
        # medianprops=dict(linewidth=1.5, color='white'),
        # zorder=1,
        )
    axes.plot(positions, means,
        linestyle="", marker="o", label="Mean"
        # markersize=7
        )
    plt.xticks(ticks, [const.PROJECT_PRETTY[p] for p in const.PROJECTS])
    plt.legend(loc="lower left")
    plt.title(f"Metric: {metric}, TCP: {tcp}")
    
    plt.tight_layout()
    fig.savefig(f"{FIGDIR}/{metric}_{tcp}.jpg", bbox_inches="tight")
    

def compute_cdf(x):
    x = np.sort(x)
    y = np.arange(len(x)) / float(len(x))
    return x, y


def draw_cdf(metric, tcp):
    nrows, ncols = 2, 5
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(13, 5))
    fig.suptitle(f"CDF on {tcp}")
    fig.supxlabel(metric)
    fig.supylabel("%Builds")

    for index, project in enumerate(const.PROJECTS):
        df = pd.read_csv(os.path.join(eval_const.evaloutcomedir, project, "evaluation.csv"))
        df = df[df["tcp"] == tcp][["pr_build", metric]]
        df = df.groupby("pr_build").mean().reset_index()

        row_index = index // ncols
        col_index = index % ncols
        add_axis_line(axes[row_index, col_index])
        x, y = compute_cdf(df[metric].values)
        axes[row_index, col_index].plot(x, y)
        axes[row_index, col_index].set_title(project)
    
    plt.tight_layout()
    fig.savefig(f"{FIGDIR}/cdf_{metric}_{tcp}.jpg", bbox_inches="tight")

if __name__ == "__main__":
    for tcp in eval_const.EVAL_TCPS:
        draw_boxplot(metric=eval_metric.APFDc_one_to_one.__name__, tcp=tcp)
    pass