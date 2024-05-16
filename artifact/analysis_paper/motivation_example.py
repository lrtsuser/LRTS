import sys
import os
import pandas as pd
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import matplotlib.gridspec as gridspec
import matplotlib.pylab as pylab

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..", "")
local_dir = os.path.join(script_dir, "..", "analysis_paper")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import ana_paper_utility

params = {
    # 'legend.fontsize': 'x-large',
    # 'figure.figsize': (15, 5),
    'axes.labelsize': 20,
    'axes.titlesize': 20,
    # 'font.family': "Times New Roman",
    'xtick.labelsize': 15,
    'ytick.labelsize': 15,
         }
pylab.rcParams.update(params)


# show qtf is bad on earlist time 
"""
candidate:
kafka: 
- PR-10003, 3, 1 fail
- PR-12603, 4, 6 fail
- PR-13284, 4, 8 fail
- PR-13447, 3, 3 fail 
"""

def get_data(project, pr_name, build_id):
    outcomes = pd.read_csv(f"../evaluation/test_result/{project}/testclass/{pr_name}_build{build_id}.csv")
    features = pd.read_csv(f"../evaluation/tcp_features/{project}/{pr_name}_build{build_id}/historical.csv")
    duration = features[["testclass", "average_duration"]]
    return pd.merge(outcomes, duration, "inner", "testclass")



def get_precentage(data):
    total_time = data["duration"].sum()
    numtests = len(data.index)
    numfaults = len(data[data["outcome"] == 1].index)
    print(total_time, numtests, numfaults)
    
    num_fault_detected, prec_fault_detected = 0, []
    num_test_executed, prec_test_executed = 0, []
    test_cost_incurred, prec_test_cost_incurred = 0, []

    for index, row in data.iterrows():
        duration = row["duration"]
        outcome = row["outcome"]
        num_fault_detected += outcome
        prec_fault_detected.append(100 * num_fault_detected / numfaults)
        num_test_executed += 1
        prec_test_executed.append(100 * num_test_executed / numtests)
        test_cost_incurred += duration
        prec_test_cost_incurred.append(100 * test_cost_incurred / total_time)
    
    data["prec_fault_detected"] = prec_fault_detected
    data["prec_test_executed"] = prec_test_executed
    data["prec_test_cost_incurred"] = prec_test_cost_incurred
    return data


def myplot():
    data = get_data("kafka", "PR-13447", 3)
    # qtf
    data = data.sort_values("average_duration", ascending=True)
    data = get_precentage(data)
    
    # # p1: y % fault detected, x %test suite executed
    # # p2: y % fault detected, x %test suite cost incurred
    # # p3: y execution time, test class
    # nrows, ncols = 1, 1
    # fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(5, 2))
    # # fig.suptitle("CDF of Builds with Failed Tests by the #Tests Classes")
    # fig.supxlabel("%Test suite executed")
    # fig.supylabel("%Faults detected")
    
    # add_axis_line(axes)
    # axes.plot(data["testclass"], data["duration"])
    # # axes[row_index, col_index].hist(tmp["testclass_count"], bins=150, color="b")
    # # axes[row_index, col_index].set_title(project)

    gs = gridspec.GridSpec(2, 2, 
                           height_ratios=[1.25, 1]
                           )
    fig = plt.figure(figsize=(9, 6))
    ax1 = plt.subplot(gs[1, :])
    # ax1.margins(0.05)           # Default margin is 0.05, value 0 means fit
    ax1.plot(data["testclass"], data["duration"] / 60)
    ax1.tick_params(labelbottom=False, bottom=False)
    ax1.set_xlabel("Test classes prioritized by QTF")
    ax1.set_ylabel("Cost (minutes)")

    ax2 = plt.subplot(gs[0, 0])
    # ax2.margins(2, 2)           # Values >0.0 zoom out
    ax2.plot(data["prec_test_executed"], data["prec_fault_detected"], color="pink")
    ax2.fill_between(data["prec_test_executed"], data["prec_fault_detected"], color="pink", alpha=.5)
    ax2.set_title("APFD")
    ax2.set_xlabel("% Test suite executed")
    ax2.set_ylabel("% Faults detected")

    ax3 = plt.subplot(gs[0, 1])
    # ax3.margins(x=0, y=-0.25)   # Values in (-0.5, 0.0) zooms in to center
    ax3.plot(data["prec_test_cost_incurred"], data["prec_fault_detected"], color="royalblue")
    ax3.fill_between(data["prec_test_cost_incurred"], data["prec_fault_detected"], color="royalblue", alpha=.5)
    ax3.set_title("APFDc")
    ax3.set_xlabel("% Test suite cost incurred")

    plt.tight_layout()
    fig.savefig(f"figures/example.jpg", bbox_inches="tight")
    fig.savefig(f"figures/example.pdf", bbox_inches="tight")
    pass


if __name__ == "__main__":
    myplot()
    pass