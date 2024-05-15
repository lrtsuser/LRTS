import os, json
import pandas as pd
import multiprocessing as mp
import glob
import const
import evaluation.eval_const as eval_const


def stage_statistics(class_df):
    # total testing duration by summing test class duration
    stage_duration = class_df["duration"].sum()

    # test class level pass and fail
    num_pass_class = len(class_df[class_df["outcome"] == eval_const.PASS].index)
    num_fail_class = len(class_df[class_df["outcome"] == eval_const.FAIL].index)

    return [stage_duration, num_pass_class, num_fail_class]


def process_test_result(project, pr_name, build_id):
    """collect statistics for all stages of a build"""
    print(project, pr_name, build_id)
    stage_class_csv_files = glob.glob(
        os.path.join(eval_const.trdir, project, 
                     f"{pr_name}_build{build_id}", "stage_*", eval_const.TEST_CLASS_CSV))
    
    rows = []
    for stage_class_csv_file in stage_class_csv_files:
        stage = stage_class_csv_file.split("/")[-2].replace("stage_", "")
        stage_class_df = pd.read_csv(stage_class_csv_file)
        stage_stats = stage_statistics(stage_class_df)
        rows.append([project, pr_name, build_id, stage] + stage_stats)
    return rows


def get_omni_file():
    df = pd.read_csv(os.path.join(const.metadir, const.DATASET_INIT_FILE))
    df = df[df["has_trunk_head_diff_data"] == True]
    df = df[df["build_timestamp"].notnull()]
    args = df[["project", "pr_name", "build_id"]].values.tolist()

    pool = mp.Pool(mp.cpu_count())
    ret = pool.starmap(process_test_result, args)
    ret = [l for ls in ret for l in ls]
    ret = pd.DataFrame(ret, columns=[
        "project", "pr_name", "build_id", "stage_id",
        "test_suite_duration_s", "num_pass_class", "num_fail_class",
    ])
    df = pd.merge(df, ret, "left", on=["project", "pr_name", "build_id"])
    
    # remove useless cols, now all builds in this csv have diff data
    df = df.drop(
        labels=[
            "trunk_sha_timestamp_sec", "has_trunk_head_diff_data",
            # info from raw test report
            "ts_duration", "passcount", "failcount", "skipcount",
            ],
        axis=1)
    # sort by project, and time from oldest to newest
    df = df.sort_values(by=["project", "build_timestamp"], ascending=True)

    df.to_csv(os.path.join(const.DATASET_FILE), index=False)

if __name__ == "__main__":
    get_omni_file()