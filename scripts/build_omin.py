import os, json
import pandas as pd
import multiprocessing as mp
import glob
import const
import extract_test_result
import evaluation.eval_const as eval_const


def convert_method_status(status):
    if status in [const.FAILED, const.REGRESSION]:
        return eval_const.FAIL
    return eval_const.PASS


def get_test_class_outcome(df_slice):
    # test class outcome is computed based on test method outcomes
    outcomes = df_slice["method_status"].values.tolist()
    if eval_const.FAIL in outcomes:
        # if any method fails, the class is marked failed
        return eval_const.FAIL
    return eval_const.PASS


def stage_statistics(method_df, class_df):
    # total_suite_duration: sum of suite duration by executed suites
    stage_duration_by_suite_sum = method_df.drop_duplicates(subset=["suite_classname"])["suite_duration"].sum()
    # total testing duration by summing method duration
    stage_duration_by_method_sum = method_df["method_duration"].sum()

    # num_pass_method: number of executed passed test methods
    num_pass_method = len(method_df[method_df["method_status"] == eval_const.PASS].index)

    # num_fail_method: number of executed failed test methods
    num_fail_method = len(method_df[method_df["method_status"] == eval_const.FAIL].index)

    # test class level pass and fail
    num_pass_class = len(class_df[class_df["outcome"] == eval_const.PASS].index)
    num_fail_class = len(class_df[class_df["outcome"] == eval_const.FAIL].index)
    num_trans_class = (class_df["outcome"] - class_df["last_outcome"]).abs().sum()

    return [stage_duration_by_suite_sum, stage_duration_by_method_sum,
        num_pass_class, num_fail_class, num_trans_class,
        num_pass_method, num_fail_method]


def process_test_result(project, pr_name, build_id):
    """collect statistics for all stages of a build"""
    print(project, pr_name, build_id)
    df = pd.read_csv(os.path.join(
        eval_const.trdir, project, 
        f"{pr_name}_build{build_id}", eval_const.TEST_REPORT_CSV))
    
    # filter invalid test names and skipped tests
    df = extract_test_result.filter_tests(project, df)    
    # convert method status
    df["method_status"] = df["method_status"].apply(lambda x: convert_method_status(x))
    stage_class_csv_files = glob.glob(
        os.path.join(eval_const.trdir, project, 
                     f"{pr_name}_build{build_id}", "stage_*", eval_const.TEST_CLASS_CSV))
    
    rows = []
    for stage_class_csv_file in stage_class_csv_files:
        stage = stage_class_csv_file.split("/")[-2].replace("stage_", "")
        if project in [const.TVM, const.TVM_GPU]:
            stage_method_df = df if stage == "single" else df[df["stage_id"].str.contains(stage)]
        else:
            stage_method_df = df if stage == "single" else df[df["stage_id"] == stage]
        stage_class_df = pd.read_csv(stage_class_csv_file)
        stage_stats = stage_statistics(stage_method_df, stage_class_df)
        rows.append([project, pr_name, build_id, stage] + stage_stats)
    return rows


def get_omin_file():
    df = pd.read_csv(os.path.join(const.metadir, const.OMIN_INIT_FILE))
    df = df[df["has_trunk_head_diff_data"] == True]
    df = df[df["build_timestamp"].notnull()]
    args = df[["project", "pr_name", "build_id"]].values.tolist()

    pool = mp.Pool(mp.cpu_count())
    ret = pool.starmap(process_test_result, args)
    ret = [l for ls in ret for l in ls]
    ret = pd.DataFrame(ret, columns=[
        "project", "pr_name", "build_id", "stage_id",
        "stage_duration_by_suite_sum", "stage_duration_by_method_sum",
        "num_pass_class", "num_fail_class", "num_trans_class",
        "num_pass_method", "num_fail_method",
    ])
    df = pd.merge(df, ret, "left", on=["project", "pr_name", "build_id"])
    
    # remove useless cols, now all builds in this csv have diff data
    df = df.drop(
        labels=["trunk_sha_timestamp_sec", "has_trunk_head_diff_data"],
        axis=1)
    # sort by project, and time from oldest to newest
    df = df.sort_values(by=["project", "build_timestamp"], ascending=True)

    df.to_csv(os.path.join(const.OMIN_FILE), index=False)

if __name__ == "__main__":
    get_omin_file()