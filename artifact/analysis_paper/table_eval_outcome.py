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


def get_tukey_test_group(tcps, df):
    data = [(t, df[df["tcp"] == t]["metric"].values.tolist()) for t in tcps]
    with open("tukey.csv", "w") as f:
        f.write("tcp,score\n")
        for d in data:
            for val in d[1]:
                f.write(f"{d[0]},{val}\n")
    os.system("python3 tukey.py tukey.csv tukey_group.csv")
    df = pd.read_csv("tukey_group.csv")
    groups = {}
    for _, row in df.iterrows():
        groups[row[0]] = row["groups"].upper()
    os.system("rm tukey.csv")
    os.system("rm tukey_group.csv")
    return groups


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
        letters = get_tukey_test_group(tcps, df)

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
    print("computing hybrid improvement for ", marco.DATASET_MARCO['_'.join(filters)])
    models = ["", marco.COST_PREFIX, marco.HISTCOST_PREFIX]

    plotting_tcps = [
        (marco.TRAD_TCPS, "Traditional"),
        (marco.IR_TCPS, "IR"),
        (marco.ML_TCPS, "ML"),
    ]
    sorting_metric = marco.METRIC_NAMES[0]

    main_table = []

    for tcps, group_name in plotting_tcps:
        basic_tcps = tcps.copy()
        table = {}
        for model in models:
            if model == "":
                tcps = basic_tcps
            elif model == marco.COST_PREFIX:
                no_cost_model_tcps = [marco.RANDOM_TCP, marco.QTF_TCP, marco.QTF_AVG_TCP]
                tcps = [model + x for x in basic_tcps if x not in no_cost_model_tcps]
            elif model == marco.HISTCOST_PREFIX:
                no_costhist_model_tcps = [marco.RANDOM_TCP, marco.FC_TCP, marco.QTF_TCP, marco.QTF_AVG_TCP]
                tcps = [model + x for x in basic_tcps if x not in no_costhist_model_tcps]

            df = plot_eval_outcome.collect_data(tcps, filters)
            tcps = plot_eval_outcome.sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=False)
            df = df[["tcp", sorting_metric]].rename(columns={sorting_metric: "metric"})

            means = get_mean(tcps, df)
            medians = get_median(tcps, df)
            letters = get_tukey_test_group(tcps, df)

            table[model] = {"means": means, "medians": medians, "letters": letters}

        # print table
        tcps_order_by_basic = plot_eval_outcome.sort_tcp_by_mean(
            plot_eval_outcome.collect_data(basic_tcps, filters)[["tcp", sorting_metric]],
            sorting_metric, ascending=False)
        for tcp in tcps_order_by_basic:
            basic = get_row_values_for_hybrid_evaluation_tables(tcp, "", table)
            cost = get_row_values_for_hybrid_evaluation_tables(tcp, marco.COST_PREFIX, table)
            histcost = get_row_values_for_hybrid_evaluation_tables(tcp, marco.HISTCOST_PREFIX, table)
            row = [marco.MARCOS[tcp]] + basic + cost + histcost
            main_table.append(row)
    return main_table


def get_tcp_performance_on_dataset(filters):
    print("computing basic tcp performance for dataset version", marco.DATASET_MARCO['_'.join(filters)])
    # get tcp orders for table
    all_tcps = [marco.TRAD_TCPS, marco.IR_TCPS, marco.ML_TCPS, marco.RL_TCPS]
    if marco.FILTER_FIRST in filters:
        all_tcps = [marco.TRAD_TCPS, marco.IR_TCPS]
    
    # sorted TCPs within each TCP category
    basic_tcps = []
    sorting_metric = marco.METRIC_NAMES[0]
    for tcps in all_tcps:
        df = plot_eval_outcome.collect_data(tcps, filters)
        tcps = plot_eval_outcome.sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=False)
        basic_tcps += tcps

    # get the performance group when considering each tcp category
    plotting_tcps = [
        (marco.TRAD_TCPS, "Traditional"),
        (marco.IR_TCPS, "IR"),
        (marco.ML_TCPS, "ML"),
        (marco.RL_TCPS, "RL"),
    ]
    within_category_group = {}
    for tcps, group_name in plotting_tcps:
        # collect mean
        df = plot_eval_outcome.collect_data(tcps, filters)
        # tcps = plot_eval_outcome.sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=False)
        df = df[["tcp", sorting_metric]].rename(columns={sorting_metric: "metric"})
        letters = get_tukey_test_group(tcps, df)
        for tcp in tcps:
            within_category_group[marco.MARCOS[tcp]] = letters[tcp]

    # get the performance group when considering all tcp
    plotting_tcps = [
        (basic_tcps, "ALL")
    ]
    table = []
    for tcps, group_name in plotting_tcps:
        # collect mean
        df = plot_eval_outcome.collect_data(tcps, filters)
        # tcps = plot_eval_outcome.sort_tcp_by_mean(df[["tcp", sorting_metric]], sorting_metric, ascending=False)
        df = df[["tcp", sorting_metric]].rename(columns={sorting_metric: "metric"})
        means = get_mean(tcps, df)
        letters = get_tukey_test_group(tcps, df)
        medians = get_median(tcps, df)

        for tcp in tcps:
            row = [marco.MARCOS[tcp], round(means[tcp], 3), round(medians[tcp], 3), letters[tcp]]
            table.append(row)
    return table, within_category_group


def highlight_top_k(orders, k=5):
    ranked = sorted(orders, key=lambda x: x[1], reverse=True)
    for i in range(k):
        top_i_tcp = ranked[i][0]
        for i in range(len(orders)):
            if orders[i][0] == top_i_tcp:
                orders[i] = [orders[i][0], f"\\textbf{{{orders[i][1]}}}", orders[i][2], f"\\textbf{{{orders[i][-1]}}}"]
    pass


def tab_comparsion_over_datasets():
    print("\nTable: Results Across Dataset Versions")
    meta = []
    for filters in marco.FILTER_COMBOS:
        data, _ = get_tcp_performance_on_dataset(filters)
        meta.append([filters, data])
    # sort all dataset based on the first version
    ranking = [tup[0] for tup in meta[0][1]]
    ranking_idx = {tup[0]: i for i, tup in enumerate(meta[0][1])}
    table = {tcp: [] for tcp in ranking}
    for filters, orders in meta:
        highlight_top_k(orders)
        orders = sorted(orders, key=lambda x: ranking_idx[x[0]], reverse=False)
        for tcp in orders:
            table[tcp[0]] += [tcp[1], tcp[-1]]
    header = ["TCP Techniques"]
    for filters in marco.FILTER_COMBOS:
        header.append(marco.DATASET_MARCO["_".join(filters)] + " " + marco.METRIC_NAMES[0])
        header.append(marco.DATASET_MARCO["_".join(filters)] + " Perf Group")
    print(",".join(header))
    for tcp in ranking:
        print(f"{tcp}," + ",".join([str(x) for x in table[tcp]] + ["-"] * (6 - len(table[tcp]))))
    pass


def tab_dataset_performance_with_hybrid_improvement(filters):
    print("\nTable: Results Between Basic and Hybrid TCP Techniques on ", marco.DATASET_MARCO['_'.join(filters)])
    basic_table, within_category_group = get_tcp_performance_on_dataset(filters)
    basic_table_dict = {row[0]: [row[1], row[-1]] for row in basic_table}
    hybrid_table = hybrid_evaluation_table_per_group(filters)
    hybrid_table_dict = {row[0]: row[2:] for row in hybrid_table}
    header = ["TCP Techniques"]
    header += ['Avg ' + marco.METRIC_NAMES[0], "Within Categoruy Perf Group", "Overall Perf Group"]
    header += [marco.HYBRID_MARCOS[marco.COST_PREFIX] + ' Avg ' + marco.METRIC_NAMES[0], 
               marco.HYBRID_MARCOS[marco.COST_PREFIX] + ' Improvement']
    header += [marco.HYBRID_MARCOS[marco.HISTCOST_PREFIX] + ' Avg ' + marco.METRIC_NAMES[0], 
               marco.HYBRID_MARCOS[marco.HISTCOST_PREFIX] + ' Improvement']
    print(",".join(header))
    for row in basic_table:
        tcp = row[0]
        vals = [basic_table_dict[tcp][0]] + [within_category_group[tcp]] + [basic_table_dict[tcp][1]] + hybrid_table_dict.get(tcp, ['-'] * 4)
        print(",".join([str(x) for x in [tcp] + vals]))


def tab_controlled_experiment_ir(filters):
    plotting_tcps = [
        # (marco.TIME_TCPS, "Time"),
        # (marco.HIST_TCPS, "History"),
        (marco.IR_TCPS, "IR"),
    ]
    sorting_metric = marco.METRIC_NAMES[0]
    for tcps, group_name in plotting_tcps:
        print("\nComputing controlled experiment results for TCP category:", group_name)
        print("Controlled Variable,<=Q1,Q1-Q2,Q2-Q3,>=Q3")
        for control in analysis_utils.IR_CTRLS:
            row = [control]
            for quantiles in analysis_utils.IR_CTRL_QUANTILES:
                # collect mean
                df = []
                for tcp in tcps:
                    df.append(analysis_utils.agg_tcp_wise_data_controlled(
                        tcp=tcp, filters=filters, data_type="mean", controlled_var=control, quantiles=quantiles))
                df = pd.concat(df, axis=0)
                df = df[["tcp", sorting_metric]].rename(columns={sorting_metric: "metric"})
                means = get_mean(tcps, df)
                means = [x for x in means.values()]
                # print(group_name, f", {round(np.array(means).mean(), 3)}, {round(min(means), 3)}-{round(max(means), 3)}")
                row.append(round(np.array(means).mean(), 3))
            print(",".join([str(x) for x in row]))


if __name__ == "__main__":
    tab_dataset_performance_with_hybrid_improvement(marco.FILTER_COMBOS[0])
    tab_controlled_experiment_ir(marco.FILTER_COMBOS[0])
    tab_comparsion_over_datasets()
    pass