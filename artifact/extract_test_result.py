import pandas as pd
import json
import zipfile
import os
import glob
import multiprocessing as mp

import const
import evaluation.eval_const as eval_const

"""
for each project, 
- extract the running time of each test case
- extract the running time of each test class
- extract the current and last outcome of each test class

keep the first stage execution for projects that only runs one stage per test suite
keep all stage executions of the same build for project with multiple stages (e.g., JDK 8 and JDK 11)
"""


def parse_enclosing_blockname(s):
    s = "_".join(s)
    s = s.replace(" ", "_")
    s = s.replace(",", ";")
    s = s.replace(":", "")
    return s

# ------------ TEST METHOD --------

def get_test_method_results(filepath):
    filepath_base = os.path.basename(filepath.replace(".zip", ""))
    testdata = json.load(zipfile.ZipFile(filepath, "r").open(filepath_base))

    ret = []
    for suite in testdata["suites"]:
        if "name" in suite:
            suite_duration = suite["duration"]
            classname_from_suite = suite["name"]
            enclosing_blockname = parse_enclosing_blockname(suite["enclosingBlockNames"])
            
            if "cases" in suite:
                for case in suite["cases"]:
                    classname_from_case = case["className"]
                    method_status = case["status"]
                    method_duration = case["duration"]
                    method_name = case["name"]
                    ret.append([
                        enclosing_blockname,
                        classname_from_suite,
                        classname_from_case,
                        suite_duration,
                        method_name,
                        method_duration,
                        method_status])
                    
    ret = pd.DataFrame(
        data=ret, columns=["stage_id", 
                           "suite_classname", "case_classname", "suite_duration", 
                           "method_name", "method_duration", "method_status"])
    return ret


def extract_test_method_results_from_rawfile(project, pr_name, build_id, overwrite=False):
    output_dir = os.path.join(eval_const.trdir, project, f"{pr_name}_build{build_id}")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, eval_const.TEST_REPORT_CSV)
    if overwrite or not os.path.exists(output_path):
        input_path = os.path.join(const.testdir, project, f"PR/{pr_name}/testReport_build{build_id}.json.zip")
        print("extracting test method results", project, pr_name, build_id, input_path)
        df = get_test_method_results(input_path)
        df.to_csv(output_path, index=False)


def extract_test_method_results_per_project(project):
    """extract test results at method level into csv"""
    os.makedirs(os.path.join(eval_const.trdir, project), exist_ok=True)

    df = pd.read_csv(const.DATASET_INIT_FILE)
    df = df[df["project"] == project]
    args = df[["project", "pr_name", "build_id"]].values.tolist()
    pool = mp.Pool(mp.cpu_count())
    pool.starmap(extract_test_method_results_from_rawfile, args)


# ------------ TEST CLASS --------

def get_test_class_outcome(df_slice):
    # test class outcome is computed based on test method outcomes
    outcomes = df_slice["method_status"].values.tolist()
    for outcome in outcomes:
        # if any method fails, the class is marked failed
        if outcome in [const.FAILED, const.REGRESSION]:
            return eval_const.FAIL
    return eval_const.PASS


def get_test_class_duration(df_slice):
    # test class duration is computed by summing test method durations
    # test class duration in suite_duration from `suite` sometimes are not accurate
    return round(sum(df_slice["method_duration"]), 3)


def filter_tests(project, df):
    # remove tests of invalid format
    if project.startswith(const.TVM):
        pass
    else:
        # invalid patterns: TEST-*, *.xml
        df = df[~df["case_classname"].str.startswith(("Gradle ", "TEST", "["))]

    # remove skipped tests
    df = df[df["method_status"] != const.SKIPPED]
    return df


def parse_testnames(project, df):
    if project.startswith(const.TVM):
        for idx, row in df.iterrows():
            suffix = row["case_classname"].split(".")[-1]
            if not suffix.islower():
                # e.g., ctypes.tests.python.relay.test_op_level3.TestArange
                df.loc[idx, "method_name"] = suffix + row["method_name"]
                df.loc[idx, "case_classname"] = ".".join(row["case_classname"].split(".")[:-1])
    elif project in [const.JAMES]:
        # replace case name with suite name
        # ./PR-1640_build3/test_report.csv:Stable_Tests,org.apache.james.jmap.memory.cucumber.MemoryUploadCucumberTest,Feature: An upload endpoint
        for idx, row in df.iterrows():
            if not row["case_classname"].startswith("org."):
                df.loc[idx, "case_classname"] = row["suite_classname"]
    elif project in [const.LOG4J, const.HIVE]:
        # replace case name with suite name
        # ./PR-717_build1/test_report.csv:Ubuntu_Test,org.apache.logging.log4j.taglib.TagUtilsLevelTest,TagUtilsLevelTest
        # ./PR-4510_build1/test_report.cs:vorg.apache.hadoop.hive.ql.parse.type.TestTypeCheckProcFactory,TestTypeCheckProcFactory
        for idx, row in df.iterrows():
            if not row["case_classname"].startswith("org."):
                df.loc[idx, "case_classname"] = row["suite_classname"]
    else:
        pass
    return df


def get_test_class_results(project, df):
    # keep first stage
    df = parse_testnames(project, df)
    df = df.drop_duplicates(subset=["suite_classname", "case_classname", "method_name"])

    # obtain class level duration and outcome
    df_duration = df[["case_classname", "method_duration"
                      ]].groupby(["case_classname"]
                             ).apply(get_test_class_duration).reset_index()
    df_duration.columns = ["testclass", "duration"]
    df_outcome = df[["case_classname", "method_status"
                      ]].groupby(["case_classname"]
                             ).apply(get_test_class_outcome).reset_index()
    df_outcome.columns = ["testclass", "outcome"]
    merged = pd.merge(df_duration, df_outcome, "inner", ["testclass"])
    return merged


def get_stages(project, df):
    if project not in const.MF_PROJECTS:
        return ["single"]
    df["stage_id"] = df["stage_id"].fillna("nan_id")
    stages = set(df["stage_id"].values.tolist())
    # handling tvm
    if project.startswith(const.TVM):
        stages = list(set([s.split("_")[1].strip() for s in stages]))
        # stages = [s.replace(":", "") for s in stages]
    return stages


def extract_test_class_results_from_csv(project, pr_name, build_id, overwrite=False):
    report_dir = os.path.join(eval_const.trdir, project, f"{pr_name}_build{build_id}")
    input_df = pd.read_csv(os.path.join(report_dir, eval_const.TEST_REPORT_CSV))
    # filter invalid test and fill nan stage
    input_df = filter_tests(project, input_df)
    input_df["stage_id"] = input_df["stage_id"].fillna("nan_id")

    # get test report for different stages (same code under different envs) of the same build if any
    stages = get_stages(project, input_df)
    for stage in stages:
        stage_dir = os.path.join(report_dir, "stage_" + stage)
        os.makedirs(stage_dir, exist_ok=True)
        output_path = os.path.join(stage_dir, eval_const.TEST_CLASS_CSV)
        if overwrite or not os.path.exists(output_path):
            print("extracting test class results", project, pr_name, build_id, stage)
            stage_df = input_df if stage == "single" else input_df[input_df["stage_id"].str.contains(stage)]
            df = get_test_class_results(project, stage_df)
            df.to_csv(output_path, index=False)


def extract_test_class_results_per_project(project):
    """extract test class results from test method level csvs"""
    os.makedirs(os.path.join(eval_const.trdir, project), exist_ok=True)

    df = pd.read_csv(const.DATASET_INIT_FILE)
    df = df[df["project"] == project]
    args = df[["project", "pr_name", "build_id"]].values.tolist()
    
    # for project, pr_name, build_id in args:
    #     extract_test_class_results_from_csv(project, pr_name, build_id)
    pool = mp.Pool(mp.cpu_count())
    pool.starmap(extract_test_class_results_from_csv, args)


def amend_last_outcome(project):
    df = pd.read_csv(const.DATASET_INIT_FILE)
    df = df[df["project"] == project]
    df = df[df["build_timestamp"].notnull()]
    # sort tests from oldest to latest
    df = df.sort_values("build_timestamp", ascending=True)
    df = df[["pr_name", "build_id"]].values.tolist()

    history = {}

    for index, (pr_name, build_id) in enumerate(df):
        csv_paths = glob.glob(os.path.join(
            eval_const.trdir, project, f"{pr_name}_build{build_id}", "stage_*", eval_const.TEST_CLASS_CSV))
        for csv_path in csv_paths:
            stage = csv_path.split("/")[-2]
            print("walking", project, index, pr_name, build_id, stage)
            df = pd.read_csv(csv_path)
            # amend last outcome to df
            # assume test last outcome is 0 if it is the first time
            df["last_outcome"] = df["testclass"].apply(
                lambda x: history[x + stage] if x + stage in history else 0)
            # save results
            df.to_csv(csv_path, index=False)

            # update history with this build
            for _, row in df.iterrows():
                history[row["testclass"] + stage] = row["outcome"]

if __name__ == "__main__":
    for project in const.PROJECTS:
        extract_test_method_results_per_project(project)
        extract_test_class_results_per_project(project)
        amend_last_outcome(project)
    pass