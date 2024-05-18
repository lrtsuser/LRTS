import pandas as pd
import os
import sys
from datetime import datetime
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

os.makedirs("dataset_viz", exist_ok=True)

def tab_dataset_summary():
    df = pd.read_csv(const.DATASET_FILE)
    stats = pd.DataFrame(columns=[
        "Project",
        "Oldest build date",
        "Latest build date",
        "Period (days)",
        "#CI builds", 
        "#TSR",
        "Avg #TC in All TSRs",
        "Avg TSR duration (hours) in All TSRs",
        "#Failed TSR",
        "Avg #TC in Failed TSRs",
        "Avg #Failed TC in Failed TSRs",
        "Avg TSR duration (hours) in Failed TSRs",
    ])

    print("average tsr duration (hours)", df["test_suite_duration_s"].mean() / (60*60))
    print("number of builds", len(df[["project", "pr_name", "build_id"]].drop_duplicates()))

    for idx, project in enumerate(const.PROJECTS):
        tmp = df[(df["project"] == project)]
        stats.loc[idx, "Project"] = const.PROJECT_PRETTY[project]

        max_date = datetime.fromtimestamp(tmp["build_timestamp"].max())
        min_date = datetime.fromtimestamp(tmp["build_timestamp"].min())
        stats.loc[idx, "Period (days)"] = (max_date - min_date).days
        stats.loc[idx, "Oldest build date"] = tmp["build_date"].min()
        stats.loc[idx, "Latest build date"] = tmp["build_date"].max()

        stats.loc[idx, "#CI builds"] = len(tmp[["project", "pr_name", "build_id"]].drop_duplicates())
        stats.loc[idx, "#TSR"] = len(tmp)
        stats.loc[idx, "Avg #TC in All TSRs"] = int((tmp["num_pass_class"] + tmp["num_fail_class"]).mean())
        stats.loc[idx, "Avg TSR duration (hours) in All TSRs"] = round(tmp["test_suite_duration_s"].mean() / (60*60), 3)

        failed = tmp[tmp["num_fail_class"] > 0]
        stats.loc[idx, "#Failed TSR"] = len(failed)
        stats.loc[idx, "Avg #TC in Failed TSRs"] = int((failed["num_pass_class"] + failed["num_fail_class"]).mean())
        stats.loc[idx, "Avg #Failed TC in Failed TSRs"] = int(failed["num_fail_class"].mean())
        stats.loc[idx, "Avg TSR duration (hours) in Failed TSRs"] = round(failed["test_suite_duration_s"].mean() / (60*60), 3)

    fname = "dataset_viz/dataset_summary.csv"
    print(f"output to  {fname}")
    stats.to_csv(fname, index=False)


def plot_ci_history_process_per_build(df):
    """take average across stage"""
    ret = df.copy()
    ret["num_test_class"] = ret["num_pass_class"] + ret["num_fail_class"]
    ret["test_suite_duration_s"] = ret["test_suite_duration_s"] / (60 * 60) 
    ret = ret[["project", "pr_name", "build_id", "build_date", "test_suite_duration_s", "num_test_class"]]
    ret = ret.groupby(["project", "pr_name", "build_id", "build_date"]).mean().reset_index()
    ret = ret.sort_values(by=["build_date"], ascending=True)
    return ret


def compute_cdf(x):
    x = np.sort(x)
    y = 100 * np.arange(len(x)) / float(len(x))
    return x, y


def plot_ci_distribution():
    """for each project, plot the change of test suite duration and size cdf"""
    fig, main_ax = plt.subplots(nrows=2, ncols=5, figsize=(27, 6))    

    duration_color = "black"
    size_color = "grey"

    dataset = pd.read_csv(const.DATASET_FILE)
    for i, project in enumerate(const.PROJECTS):
        ax = main_ax[i // 5, i % 5]
        df = plot_ci_history_process_per_build(dataset[(dataset["project"] == project)])
        y, x = compute_cdf(df["test_suite_duration_s"].values)
        ax.plot(x, y, color=duration_color, linewidth=4)
        ax.tick_params(axis='y', labelcolor=duration_color)

        ax2 = ax.twinx()  # instantiate a second axes that shares the same x-axis
        y, x = compute_cdf(df["num_test_class"].values)
        ax2.plot(x, y, color=size_color, linestyle="--", linewidth=4)
        ax2.tick_params(axis='y', labelcolor=size_color)
        for tick in ax.get_yticklabels():
            tick.set_fontweight('bold')
        for tick in ax2.get_yticklabels():
            tick.set_fontweight('bold')

        ax.set_title(const.PROJECT_PRETTY[project], fontsize=22)

    plt.tight_layout()
    fig.supxlabel("% CI builds", fontsize=22, y=-0.05)

    # left label
    ax = fig.add_subplot(1, 1, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    [ax.spines[side].set_visible(False) for side in ('left', 'top', 'right', 'bottom')]
    ax.patch.set_visible(False)
    ax.set_ylabel('TSR duration (hours)', labelpad=30, fontsize=22, color=duration_color, fontweight='bold')
    # right label
    fig.supylabel("TSR size (#Test classes)", color=size_color, fontsize=22, x=1, weight='bold')
    fig.savefig(f"dataset_viz/ci_dist.jpg", bbox_inches="tight")
    fig.savefig(f"dataset_viz/ci_dist.pdf", bbox_inches="tight")
    plt.close(fig)

    pass


if __name__ == "__main__":
    tab_dataset_summary()
    plot_ci_distribution()
    pass