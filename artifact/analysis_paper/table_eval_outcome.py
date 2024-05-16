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
import plot_eval_outcome
import analysis_utils

PVALUE = 0.05


def collect_data_by_median(tcps, filters):
    """
    each data point is a seed, each project has 10 seeds
    thus, each data point is the average across all builds per stage, then across all stages of that seed
    """
    df = []
    for tcp in tcps:
        df.append(analysis_utils.agg_tcp_wise_data(tcp=tcp, filters=filters, data_type="median"))
    df = pd.concat(df, axis=0)
    return df

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

    # check for normality: most of the data is not normal, pvalue<0.001
    for t in data:
        print("Shapiro", t[0], len(t[1]), stats.shapiro(t[1]))
    print("All Shapiro", stats.shapiro([item for sublist in data for item in sublist[1]]))


    # get f-oneway
    print("F-oneway", stats.f_oneway(*[x[1] for x in data]).pvalue)

    with open("tukey.csv", "w") as f:
        f.write("tcp,score\n")
        for d in data:
            for val in d[1]:
                f.write(f"{d[0]},{val}\n")
    os.system("Rscript tukey.R tukey.csv tukey_group.csv")
    df = pd.read_csv("tukey_group.csv")
    groups = {}
    for idx, row in df.iterrows():
        groups[idx] = row["groups"].upper()
    return groups


    # get fridman result, all pvalue<0.001
    print("Friedman", stats.friedmanchisquare(*[x[1] for x in data]).pvalue)

    # conduct the Nemenyi post-hoc test
    # nemenyi = sp.posthoc_nemenyi_friedman(np.array([x[1] for x in data]).T)
    # new_names = {i: tcps[i] for i in range(len(tcps))}
    # nemenyi = nemenyi.rename(columns=new_names, index=new_names)

    pvalues = {}
    for i, tcp1 in enumerate(tcps):
        for j, tcp2 in enumerate(tcps):
            assert tcp1 == data[i][0]
            assert tcp2 == data[j][0]
            # use tukey
            # pvalue = stats.tukey_hsd(data[i][1], data[j][1]).pvalue[0, 1]
            # print("tukey", i, j, tcp1, tcp2, pvalue)
            # use nemeyi
            # pvalue = nemenyi.loc[tcp1, tcp2]
            pvalue = sp.posthoc_nemenyi_friedman(np.array([data[i][1], data[j][1]]).T).loc[0, 1]
            # print("nemenyi", i, j, tcp1, tcp2, pvalue)
            if tcp1 not in pvalues:
                pvalues[tcp1] = {}
            pvalues[tcp1][tcp2] = pvalue

    groups = []
    left_tcps = set(tcps)
    for i, tcp1 in enumerate(tcps):
        if tcp1 in left_tcps:
            subgroups = []
            for j, tcp2 in enumerate(left_tcps):
                # null hypthesis is true, these two tcps are in the same group
                pvalue = pvalues[tcp1][tcp2]
                assert pvalues[tcp1][tcp2] == pvalues[tcp2][tcp1]
                if pvalue > PVALUE:
                    print(tcp2, pvalue)
                    subgroups.append(tcp2)
            left_tcps = left_tcps - set(subgroups)
            groups.append(subgroups)

    letters = {}
    for i, group in enumerate(groups):
        letter =  chr(ord('A') + i)
        for tcp in group:
            letters[tcp] = letter

    return letters


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


def evaluation_table(filters):
    basic_tcps = marco.TRAD_TCPS + marco.IR_TCPS + marco.ML_TCPS + marco.RL_TCPS
    basic_tcps = list(set(basic_tcps))

    plotting_tcps = [
        (marco.TRAD_TCPS, "Traditional"),
        (marco.IR_TCPS, "IR"),
        (marco.ML_TCPS, "ML"),
        (marco.RL_TCPS, "RL"),
        (basic_tcps, "ALL")
    ]
    sorting_metric = marco.METRIC_NAMES[0]
    table = []
    sorted_tcps = []
    for tcps, group_name in plotting_tcps:
        print("\n\n", group_name)
        # collect mean
        df = plot_eval_outcome.collect_data(tcps, filters)
        tcps = plot_eval_outcome.sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=False)
        df = df[["tcp", sorting_metric]].rename(columns={sorting_metric: "metric"})
        means = get_mean(tcps, df)
        letters = get_nemenyi_test_group(tcps, df)
        # letters = assign_group_letters(tcps, groups)
        
        # df = collect_data_by_median(tcps, filters)
        # df = df[["tcp", sorting_metric]].rename(columns={sorting_metric: "metric"})
        medians = get_median(tcps, df)
        if group_name == "ALL":
            tcps = sorted(tcps, key=lambda x: sorted_tcps.index(x), reverse=False)
        for tcp in tcps:
            row = [marco.MARCOS[tcp], round(means[tcp], 3), round(medians[tcp], 3), letters[tcp]]
            print(",".join([str(x) for x in row]))
            table.append(row)
        sorted_tcps += tcps
    return table


def evaluation_table_for_IR(filters):
    basic_tcps = marco.TRAD_TCPS + marco.IR_TCPS + marco.ML_TCPS + marco.RL_TCPS
    basic_tcps = list(set(basic_tcps))

    plotting_tcps = [
        (marco.TIME_TCPS, "Time"),
        (marco.HIST_TCPS, "History"),
        (marco.IR_TCPS, "IR"),
    ]
    sorting_metric = marco.METRIC_NAMES[0]
    table = []
    sorted_tcps = []
    for tcps, group_name in plotting_tcps:
        print("\n\n", group_name)
        # collect mean
        df = plot_eval_outcome.collect_data(tcps, filters)
        tcps = plot_eval_outcome.sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=False)
        df = df[["tcp", sorting_metric]].rename(columns={sorting_metric: "metric"})
        means = get_mean(tcps, df)
        means = [x for x in means.values()]
        print(group_name, f", {round(np.array(means).mean(), 3)}, {round(min(means), 3)}-{round(max(means), 3)}")
    return table


def get_row_values_for_hybrid_evaluation_tables(tcp, model, data):
    ret = [
        data[model]["means"][model+tcp] if model+tcp in data[model]["means"] else "-",
        # data[model]["medians"][model+tcp] if model+tcp in data[model]["medians"] else "-",
        # data[model]["letters"][model+tcp] if model+tcp in data[model]["letters"] else "-",
    ]
    ret = [round(x, 3) if isinstance(x, float) else x for x in ret]

    if model != "":
        if ret[0] != "-":
            basic = data[""]["means"][tcp]
            new = ret[0]
            improvement = 100 * (new - basic) / basic
            improvement = f"{int(improvement)}\%"
            # return [ret[0], improvement, ret[1]]
            return [ret[0], improvement]
        else:
            # return [ret[0], "-", ret[1]]
            return [ret[0], "-"]
    return ret



def hybrid_evaluation_table_per_group(filters):
    # basic_tcps = marco.TRAD_TCPS + marco.IR_TCPS + marco.ML_TCPS
    # basic_tcps = list(set(basic_tcps))
    models = ["", marco.COST_PREFIX, marco.HISTCOST_PREFIX]

    plotting_tcps = [
        (marco.TRAD_TCPS, "Traditional"),
        (marco.IR_TCPS, "IR"),
        (marco.ML_TCPS, "ML"),
        # (marco.RL_TCPS, "RL"),
        # (basic_tcps, "ALL")
    ]
    sorting_metric = marco.METRIC_NAMES[0]

    for tcps, group_name in plotting_tcps:
        basic_tcps = tcps.copy()
        table = {}
        for model in models:
            if model == "":
                tcps = basic_tcps
            elif model == marco.COST_PREFIX:
                no_cost_model_tcps = [marco.RANDOM_TCP, marco.QTF_TCP]
                tcps = [model + x for x in basic_tcps if x not in no_cost_model_tcps]
            elif model == marco.HISTCOST_PREFIX:
                no_costhist_model_tcps = [marco.RANDOM_TCP, marco.FC_TCP, marco.QTF_TCP]
                tcps = [model + x for x in basic_tcps if x not in no_costhist_model_tcps]

            df = plot_eval_outcome.collect_data(tcps, filters)
            tcps = plot_eval_outcome.sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=False)
            df = df[["tcp", sorting_metric]].rename(columns={sorting_metric: "metric"})

            means = get_mean(tcps, df)
            medians = get_median(tcps, df)
            letters = get_nemenyi_test_group(tcps, df)
            # letters = assign_group_letters(tcps, groups)

            table[model] = {"means": means, "medians": medians, "letters": letters}

        # print table
        tcps_order_by_basic = plot_eval_outcome.sort_tcp_by_mean(
            plot_eval_outcome.collect_data(basic_tcps, filters)[["tcp", sorting_metric]],
            sorting_metric, ascending=False)
        rows = []
        for tcp in tcps_order_by_basic:
            basic = get_row_values_for_hybrid_evaluation_tables(tcp, "", table)
            cost = get_row_values_for_hybrid_evaluation_tables(tcp, marco.COST_PREFIX, table)
            histcost = get_row_values_for_hybrid_evaluation_tables(tcp, marco.HISTCOST_PREFIX, table)
            row = [marco.MARCOS[tcp]] + basic + cost + histcost
            rows.append(row)
            # convert_row_to_latex_format(row)
        # get column wise mean
        for row in rows:
            print(",".join([str(x) for x in row]))


def compare_over_dataset_helper(filters):
    # get tcp orders for table
    all_tcps = [marco.TRAD_TCPS, marco.IR_TCPS, marco.ML_TCPS, marco.RL_TCPS]
    if marco.FILTER_FIRST in filters:
        all_tcps = [marco.TRAD_TCPS, marco.IR_TCPS]
    
    basic_tcps = []
    sorting_metric = marco.METRIC_NAMES[0]
    for tcps in all_tcps:
        df = plot_eval_outcome.collect_data(tcps, filters)
        tcps = plot_eval_outcome.sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=False)
        basic_tcps += tcps

    plotting_tcps = [
        (basic_tcps, "ALL")
    ]
    table = []

    for tcps, group_name in plotting_tcps:
        print("\n\n", group_name)
        # collect mean
        df = plot_eval_outcome.collect_data(tcps, filters)
        # tcps = plot_eval_outcome.sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=False)
        df = df[["tcp", sorting_metric]].rename(columns={sorting_metric: "metric"})
        means = get_mean(tcps, df)
        letters = get_nemenyi_test_group(tcps, df)
        # letters = assign_group_letters(tcps, groups)
        
        # df = collect_data_by_median(tcps, filters)
        # df = df[["tcp", sorting_metric]].rename(columns={sorting_metric: "metric"})
        medians = get_median(tcps, df)

        for tcp in tcps:
            row = [marco.MARCOS[tcp], round(means[tcp], 3), round(medians[tcp], 3), letters[tcp]]
            table.append(row)
    return table

def highlight_top_k(orders, k=5):
    ranked = sorted(orders, key=lambda x: x[1], reverse=True)
    for i in range(k):
        top_i_tcp = ranked[i][0]
        for i in range(len(orders)):
            if orders[i][0] == top_i_tcp:
                orders[i] = [orders[i][0], f"\\textbf{{{orders[i][1]}}}", orders[i][2], f"\\textbf{{{orders[i][-1]}}}"]
    pass

def compare_over_datasets():
    meta = []
    for filters in marco.FILTER_COMBOS:
        data = compare_over_dataset_helper(filters)
        meta.append([filters, data])
    
    # sort all dataset based on the first version
    # print(meta)
    # ranking = sorted(meta[0][1], key=lambda x: x[1], reverse=True)
    # ranking = {tup[0]: idx for idx, tup in enumerate(ranking)}
    ranking = {tup[0]: idx for idx, tup in enumerate(meta[0][1])}
    print(ranking)
    for filters, orders in meta:
        # table[1] = [str(x) for x in table[1]]
        print("\n" + "_".join(filters))
        highlight_top_k(orders)
        orders = sorted(orders, key=lambda x: ranking[x[0]], reverse=False)
        for tcp in orders:
            print("{},{},{}".format(tcp[0], tcp[1], tcp[-1]))

    pass

if __name__ == "__main__":
    # print(marco.FILTER_COMBOS[0])
    evaluation_table(marco.FILTER_COMBOS[0])
    # evaluation_table_for_IR(marco.FILTER_COMBOS[0])
    # hybrid_evaluation_table_per_group(marco.FILTER_COMBOS[0])
    # compare_over_datasets()
    pass