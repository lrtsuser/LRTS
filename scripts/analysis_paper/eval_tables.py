import pandas as pd
import os
import sys
import numpy as np
from scipy import stats
import scikit_posthocs as sp
import itertools


script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "analysis_paper")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import marco

METRIC = "APFDc_one_to_one"



def get_testing_split(project, tcp, df):
    test_set = pd.read_csv(f"../evaluation/ml_data/{project}/test_builds.csv")
    test_set = test_set[["pr_name", "build_id"]].values.tolist()
    test_set = [f"{pr_name}_build{build_id}" for pr_name, build_id in test_set]
    newdf = df[df["pr_build"].isin(test_set)]
    # print("processing", project, tcp, len(df), len(newdf))
    return newdf


def gather_data(tcps, groupbys, testing_split=False):
    # get data for all tcp techniques
    # project, tcp, pr_build, seed, apfdc 1-1
    df = []
    for tcp in tcps:
        for project in const.PROJECTS: 
            current = pd.read_csv(f"../evaluation/eval_outcome/{project}/{tcp}.csv")
            if testing_split:
                current = get_testing_split(project, tcp, current)
            df.append(current)
    df = pd.concat(df, axis=0, ignore_index=True).reset_index(drop=True)
    # print("before agg", len(df))
    # comment the agg columns
    df = df.groupby(groupbys).mean().reset_index()
    # print("after agg", len(df))
    # print(df.head())
    df = df.rename(columns={METRIC: "metric"})
    df = df[["tcp", "project", "metric"]]
    return df


def sort_tcp_by_mean_desc(df):
    means = df.groupby("tcp").mean().reset_index().sort_values(by="metric", ascending=False)
    return means["tcp"].values.tolist()


def get_mean(tcps, df):
    data = {}
    for tcp in tcps:
        data[tcp] = df[df["tcp"] == tcp]["metric"].mean()
    return data


def get_median(tcps, df):
    data = {}
    for tcp in tcps:
        data[tcp] = df[df["tcp"] == tcp]["metric"].median()
    return data


def get_num_best_projects(tcps, df):
    # per tcp, see how many projects have the best mean metric value across all tcps
    # TODO: we only have 10 projects, not very useful
    pass


def get_nemenyi_test_group(tcps, df):
    data = [(t, df[df["tcp"] == t]["metric"].values.tolist()) for t in tcps]

    # get fridman result
    print(stats.friedmanchisquare(*[x[1] for x in data]))

    # conduct the Nemenyi post-hoc test
    nemenyi = sp.posthoc_nemenyi_friedman(np.array([x[1] for x in data]).T)
    new_names = {i: tcps[i] for i in range(len(tcps))}
    nemenyi = nemenyi.rename(columns=new_names, index=new_names)

    # get groups
    groups = []
    for i, tcp1 in enumerate(tcps):
        for j, tcp2 in enumerate(tcps):
            # go diagonal, no repeation
            if j > i:
                pvalue = nemenyi.loc[tcp1, tcp2]
                # null hypthesis is true, these two tcps are in the same group
                if pvalue > 0.05:
                    print(i, j, tcp1, tcp2, pvalue)
                    add_to_group = False
                    for k, group in enumerate(groups):
                        if tcp1 in group or tcp2 in group:
                            groups[k] = list(set(group + [tcp1, tcp2]))
                            add_to_group = True
                            break
                    if not add_to_group:
                        groups.append([tcp1, tcp2])
    
    # add isolate tcps to group
    added_tcps = set(list((itertools.chain.from_iterable(groups))))
    for tcp in set(tcps) - added_tcps:
        groups.append([tcp])

    # print("number of groups", len(groups))
    # print(groups)

    return groups


def assign_group_letters(tcps, groups):
    # assume tcps has been sorted left to right from highest to lowest metric value

    # for each group, get the best value
    for i, group in enumerate(groups):
        values = [tcps.index(t) for t in group]
        groups[i] = (min(values), group)
    
    # sort by values, best group first
    groups.sort(key=lambda x: x[0], reverse=False)
    # print("sorted", groups)

    # assign group letter
    letters = {}
    for i, group in enumerate(groups):
        for tcp in group[1]:
            letters[tcp] = chr(ord('A') + i)
    return letters


def evaluation_table(tcps):
    # tcp, mean, median, group, #best.project
    # each data point is the average across builds in a project in a seed
    df = gather_data(tcps, groupbys=["project", "tcp", "pr_build"])

    # sort tcp by overall mean
    tcps = sort_tcp_by_mean_desc(gather_data(tcps, groupbys=["project", "tcp", "pr_build"]))

    means = get_mean(tcps, df)
    medians = get_median(tcps, df)
    groups = get_nemenyi_test_group(tcps, df)
    letters = assign_group_letters(tcps, groups)

    for tcp in tcps:
        row = [marco.MARCOS[tcp], round(means[tcp], 3), round(medians[tcp], 3), letters[tcp]]
        convert_row_to_latex_format(row)
    pass


def get_row_values_for_hybrid_evaluation_tables(tcp, model, data):
    ret = [
        data[model]["means"][model+tcp] if model+tcp in data[model]["means"] else "-",
        # data[model]["medians"][model+tcp] if model+tcp in data[model]["medians"] else "-",
        data[model]["letters"][model+tcp] if model+tcp in data[model]["letters"] else "-",
    ]
    ret = [round(x, 3) if isinstance(x, float) else x for x in ret]

    if model is not "":
        if ret[0] is not "-":
            basic = data[""]["means"][tcp]
            new = ret[0]
            improvement = 100 * (new - basic) / basic
            improvement = f"{int(improvement)}\%"
            return [ret[0], improvement, ret[1]]
        else:
            return [ret[0], "-", ret[1]]
    return ret


def convert_row_to_latex_format(row):
    center, right, left = "c", "r", "l"
    template = "\\multicolumn{{1}}{{{align}|}}{{{value}}}"
    formatted_rows = []
    for i, x in enumerate(row):
        # right for digit, otherwise center
        if i not in [0, len(row) - 1]:
            # align = right if isinstance(x, float) else center
            x = "{:.3f}".format(x) if isinstance(x, float) else x
            align = center if not x.endswith("%") else right
            x = template.format(align=align, value=x)
        formatted_rows.append(x)
    line = " & ".join(formatted_rows)
    line += "\\\\ \\hline"
    print(line)

   

def hybrid_evaluation_tables(basic_tcps):
    # on testing data
    # tcp, [basic mean, median, group], [hybrid1 mean, median, group] ...

    data = {}
    models = ["", marco.COST_PREFIX, marco.HIST_PREFIX, marco.HISTCOST_PREFIX]
    for model in models:

        if model == "":
            tcps = marco.BASIC_TCPS
        elif model == marco.COST_PREFIX:
            tcps = [model + x for x in basic_tcps if x not in [marco.RANDOM_TCP, marco.QTF_TCP]]
        elif model == marco.HIST_PREFIX:
            tcps = [model + x for x in basic_tcps if x not in [marco.RANDOM_TCP, marco.FC_TCP]]
        elif model == marco.HISTCOST_PREFIX:
            tcps = [model + x for x in basic_tcps if x not in [marco.RANDOM_TCP, marco.FC_TCP, marco.QTF_TCP]]
        
        df = gather_data(tcps, groupbys=["project", "tcp", "pr_build"], testing_split=True)
        tcps = sort_tcp_by_mean_desc(df)

        means = get_mean(tcps, df)
        medians = get_median(tcps, df)
        groups = get_nemenyi_test_group(tcps, df)
        letters = assign_group_letters(tcps, groups)

        data[model] = {
            "means": means,
            "medians": medians,
            "letters": letters,
            }
        
    tcps_order_by_basic = sort_tcp_by_mean_desc(gather_data(basic_tcps, groupbys=["project", "tcp", "pr_build"], testing_split=True))

    rows = []
    for tcp in tcps_order_by_basic:
        basic = get_row_values_for_hybrid_evaluation_tables(tcp, "", data)
        cost = get_row_values_for_hybrid_evaluation_tables(tcp, marco.COST_PREFIX, data)
        hist = get_row_values_for_hybrid_evaluation_tables(tcp, marco.HIST_PREFIX, data)
        histcost = get_row_values_for_hybrid_evaluation_tables(tcp, marco.HISTCOST_PREFIX, data)
        row = [marco.MARCOS[tcp]] + basic + cost + hist + histcost
        rows.append(row)
        convert_row_to_latex_format(row)
    # get column wise mean
    for row in rows:
        print(",".join([str(x) for x in row]))
    pass


if __name__ == "__main__":
    evaluation_table(marco.TRAD_TCPS)
    evaluation_table(marco.IR_TCPS)
    evaluation_table(marco.ML_TCPS)
    # hybrid_evaluation_tables(marco.BASIC_TCPS)
    pass