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

os.makedirs("tables", exist_ok=True)

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

    fname = "tables/dataset_summary.csv"
    print(f"output to  {fname}")
    stats.to_csv(fname, index=False)

if __name__ == "__main__":
    tab_dataset_summary()
    pass