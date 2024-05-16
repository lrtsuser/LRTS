import pandas as pd
import json
import zipfile
import os
import glob
import multiprocessing as mp
import gzip

import const
import evaluation.eval_const as eval_const

"""filter out 
1. flaky test classes/methods
2. frequently failing tests
"""

FFDIR = "filter_tests"
os.makedirs(FFDIR, exist_ok=True)


def compute_fail_freq_for_test_classes():
    project_stages = pd.read_csv(const.DATASET_FILE)
    project_stages = project_stages[["project", "stage_id"]].drop_duplicates().values.tolist()
    freq = {}
    for project, stage in project_stages:
        key = project + ",, " + stage
        freq[key] = {}
        # get all builds of this stage
        testresult_csvs = glob.glob(f"{eval_const.trdir}/{project}/*/stage_{stage}/{eval_const.TEST_CLASS_CSV}")
        print("running", project, stage, "#files", len(testresult_csvs))
        for csv in testresult_csvs:
            df = pd.read_csv(csv)
            # get failed test classes
            failed_tests = df[df["outcome"] == 1]["testclass"].values.tolist()
            for test in failed_tests:
                if test not in freq[key]:
                    freq[key][test] = 0
                freq[key][test] += 1
    # construct dataframe for test class failure frequency
    ret = []
    for key in freq:
        for test, num_fail in freq[key].items():
            project, stage = key.split(",, ")
            ret.append([project, stage, test, num_fail])
    ret = pd.DataFrame(ret, columns=["project", "stage", "test", "fail_freq"])
    ret.to_csv(os.path.join(FFDIR, "test_fail_freq.csv"), index=False)


def get_no_fail_test_classes():
    project_stages = pd.read_csv(const.DATASET_FILE)
    project_stages = project_stages[["project", "stage_id"]].drop_duplicates().values.tolist()
    freq = {}
    for project, stage in project_stages:
        key = project + ",, " + stage
        freq[key] = {}
        # get all builds of this stage
        testresult_csvs = glob.glob(f"{eval_const.trdir}/{project}/*/stage_{stage}/{eval_const.TEST_CLASS_CSV}")
        print("running", project, stage, "#files", len(testresult_csvs))
        for csv in testresult_csvs:
            df = pd.read_csv(csv)
            # get failed test classes
            tests = df[["testclass", "outcome"]].values.tolist()
            for test, outcome in tests:
                if test not in freq[key]:
                    freq[key][test] = 0
                freq[key][test] += outcome
    # construct dataframe for test class failure frequency
    ret = []
    for key in freq:
        for test, num_fail in freq[key].items():
            project, stage = key.split(",, ")
            if num_fail == 0:
                ret.append([project, stage, test])
    ret = pd.DataFrame(ret, columns=["project", "stage", "test"])
    ret.to_csv(os.path.join(FFDIR, "no_fail_test.csv"), index=False)


def get_test_classes_exec_count():
    """get number of times a test executed"""
    freq = {}
    num_tsrs = {}
    for project in const.PROJECTS:
        freq[project] = {}
        # get all builds of this stage
        testresult_csvs = glob.glob(f"{eval_const.trdir}/{project}/*/stage_*/{eval_const.TEST_CLASS_CSV}")
        num_tsrs[project] = len(testresult_csvs)
        print("running", project, "#files", len(testresult_csvs))
        for csv in testresult_csvs:
            df = pd.read_csv(csv)
            for test in df["testclass"].values.tolist():
                if test not in freq[project]:
                    freq[project][test] = 0
                freq[project][test] += 1
    # construct dataframe for test class failure frequency
    ret = []
    for project in freq:
        for test, exec_count in freq[project].items():
                ret.append([project, test, exec_count, num_tsrs[project]])
    ret = pd.DataFrame(ret, columns=["project", "test", "exec_count", "test_suite_runs"])
    ret.to_csv(os.path.join(FFDIR, "test_exec_count.csv"), index=False)


def get_test_classes_fail_count():
    """get number of times a test executed"""
    freq = {}
    num_fail_tsrs = {}
    for project in const.PROJECTS:
        freq[project] = {}
        # get all builds of this stage
        testresult_csvs = glob.glob(f"{eval_const.trdir}/{project}/*/stage_*/{eval_const.TEST_CLASS_CSV}")
        num_fail_tsrs[project] = set()
        print("running", project, "#files", len(testresult_csvs))
        for csv in testresult_csvs:
            df = pd.read_csv(csv)
            for test, outcome in df[["testclass", "outcome"]].values.tolist():
                if test not in freq[project]:
                    freq[project][test] = 0
                freq[project][test] += outcome
                if outcome == eval_const.FAIL:
                    num_fail_tsrs[project].add(csv)
    # construct dataframe for test class failure frequency
    num_fail_tsrs = {k: len(v) for k, v in num_fail_tsrs.items()}
    
    ret = []
    for project in freq:
        for test, fail_count in freq[project].items():
                ret.append([project, test, fail_count, num_fail_tsrs[project]])
    ret = pd.DataFrame(ret, columns=["project", "test", "fail_count", "fail_test_suite_runs"])
    ret.to_csv(os.path.join(FFDIR, "test_fail_count.csv"), index=False)


def get_outlier():
    """
    get frequently failed (outlier) tests
    the number of failure bigger than mean + 3*std is marked as outlier
    """
    df = pd.read_csv(os.path.join(FFDIR, "test_fail_freq.csv"))
    stats = []
    # compute average fail freq across tests for each (project, stage)
    project_stages = df[["project", "stage"]].drop_duplicates().values.tolist()
    for project, stage in project_stages:
        fail_freqs = df[(df["project"] == project) & (df["stage"] == stage)]["fail_freq"]
        mean = round(fail_freqs.mean(), 2)
        std = round(fail_freqs.std(), 2)
        median = fail_freqs.median()
        row = [project, stage, len(fail_freqs), mean, std, median]
        stats.append(row)
    stats = pd.DataFrame(stats, columns=["project", "stage", "num_failed_tests", "mean", "std", "median"])
    print(stats)
    
    outlier = []
    stats["num_failed_tests_outlier"] = None
    for idx, row in stats.iterrows():
        project = row["project"]
        stage = row["stage"]
        current_outlier = df[(df["project"] == project) 
                             & (df["stage"] == stage)
                             & (df["fail_freq"] > row["mean"] + 3 * row["std"])]
        outlier.append(current_outlier)
        stats.loc[idx, "num_failed_tests_outlier"] = len(current_outlier)
    outlier = pd.concat(outlier, axis=0)
    stats.to_csv(f"{FFDIR}/test_fail_freq_stats.csv", index=False)
    outlier.to_csv(f"{FFDIR}/fail_freq_outliers.csv", index=False)


def process_jira_flaky_test_helper(test):
    # return [testclass, testmethod]
    tokens = test.split("#")
    if len(tokens) == 2:
        return tokens
    if "[" in tokens[0]:
        return [None, tokens[0]]
    return [tokens[0], None]


def process_jira_flaky_tests():
    df = pd.read_csv("flaky_test/flaky_tests.csv")
    cms = [process_jira_flaky_test_helper(t) for t in df["flaky_test"].values.tolist()]
    df.insert(2, "testclass", [x[0] for x in cms])
    df.insert(3, "testmethod", [x[1] for x in cms])
    df.to_csv(f"{FFDIR}/flaky_tests.csv", index=False)
    # get flaky test class per project
    df = df.sort_values(["project", "fix_timestamp"], ascending=True)
    df = df.drop(["flaky_test", "testmethod"], axis=1)
    df = df.drop_duplicates(subset=["project", "testclass"]).dropna()
    df.to_csv(f"{FFDIR}/flaky_testclasses.csv", index=False)
    print(df.groupby("project").count().reset_index())


def get_common_failed_tests():
    omni = pd.read_csv(const.DATASET_FILE)
    omni = omni.sort_values(["project", "build_timestamp"], ascending=True)
    omni = omni[["project", "pr_name", "build_id"]].drop_duplicates().values.tolist()
    ret = {}
    for idx, (project, pr_name, build_id) in enumerate(omni):
        failed_tests = []
        stage_files = glob.glob(os.path.join(
            eval_const.trdir, project, f"{pr_name}_build{build_id}/stage*/{eval_const.TEST_CLASS_CSV}"))
        for stage_file in stage_files:
            df = pd.read_csv(stage_file)
            stage_fails = df[df["outcome"] == eval_const.FAIL]["testclass"].values.tolist()
            failed_tests.append(set(stage_fails))
        # union = set().union(*failed_tests)
        intersection = list(set.intersection(*failed_tests))
        prev = ",, ".join([str(x) for x in omni[idx-1]]) if (idx >= 1 and omni[idx-1][0] == project) else None
        ret[",, ".join([project, pr_name, str(build_id)])] = {
            "intersection": intersection, 
            "prev": prev}
        if idx % 100 == 0:
            print(project, pr_name, build_id, len(intersection), prev)
    with gzip.open(f"{FFDIR}/common_failed_tests.json.gz", "wt") as f:
        json.dump(ret, f, indent=2)


####################### get dataset variants

def load_jira_flaky_tests_for_build(project, build_timestamp):
    df = pd.read_csv(f"{FFDIR}/flaky_testclasses.csv")
    df = df[df["project"] == project]
    # keep flaky test it is fixed after the build is created
    flaky = df[df["fix_timestamp"] > build_timestamp]["testclass"].values.tolist()
    return flaky

def load_common_failed_tests(project, pr_name, build_id):
    with gzip.open(f"{FFDIR}/common_failed_tests.json.gz", "rt") as f:
        data = json.load(f)
        key = ",, ".join([project, pr_name, str(build_id)])
        intersection = data[key]["intersection"]
        intersection_from_prev_build = []
        if data[key]["prev"] is not None:
            intersection_from_prev_build = data[key]["intersection"]
        return intersection, intersection_from_prev_build


def load_frequent_fail_tests_for_stage(project, stage):
    df = pd.read_csv(f"{FFDIR}/fail_freq_outliers.csv")
    ff = df[(df["project"] == project) & (df["stage"] == stage)]
    ff = ff["test"].values.tolist()
    return ff


def label_test(df, jira, common, prev_common, frequent):
    """
    label these tests when they failed or transitioned
    for fail: for apfd(c) computations
    for tran: for aptd(c) computations
    """
    df["jira_for_fail"] = 0
    df["stageunique_for_fail"] = 0
    df["freqfail_for_fail"] = 0
    df["jira_for_trans"] = 0
    df["stageunique_for_trans"] = 0
    df["freqfail_for_trans"] = 0
    for idx, row in df.iterrows():
        test = row["testclass"]
        outcome = row["outcome"]
        last_outcome = row["last_outcome"]
        # remove flaky and frequently fail test as transition or failure
        if outcome == eval_const.FAIL or outcome != last_outcome:
            if test.endswith(tuple(jira)):
                df.loc[idx, "jira_for_fail"] = 1
                df.loc[idx, "jira_for_trans"] = 1
            if test.endswith(tuple(frequent)):
                df.loc[idx, "freqfail_for_fail"] = 1
                df.loc[idx, "freqfail_for_trans"] = 1
        if outcome == eval_const.FAIL and not test.endswith(tuple(common)):
            df.loc[idx, "stageunique_for_fail"] = 1
        # unique stage failure from prev build transition in this build
        if last_outcome == eval_const.FAIL and outcome == eval_const.PASS and not test.endswith(tuple(prev_common)):
            df.loc[idx, "stageunique_for_trans"] = 1
    return df


def extract_dataset_with_filterlabel_helper(index, project, pr_name, build_id, build_timestamp):
    # get jira flaky tests for this build
    jira_flaky = load_jira_flaky_tests_for_build(project, build_timestamp)
    # get failed test intersection across stage of this build
    common_fails, prev_common_fails = load_common_failed_tests(project, pr_name, build_id)
    stage_files = glob.glob(os.path.join(
        eval_const.trdir, project, f"{pr_name}_build{build_id}/stage*/{eval_const.TEST_CLASS_CSV}"))
    for stage_file in stage_files:
        df = pd.read_csv(stage_file)
        stage = stage_file.split("/")[-2].replace("stage_", "")
        freq_fails = load_frequent_fail_tests_for_stage(project, stage)
        df = label_test(df, jira_flaky, common_fails, prev_common_fails, freq_fails)
        # save label file
        df.to_csv(f"{os.path.dirname(stage_file)}/{eval_const.TEST_CLASS_FL_CSV}", index=False)
        if index % 100 == 0:
            print(index, project, pr_name, build_id, stage, "original", len(df[df["outcome"] == eval_const.FAIL]),
                  "jira", len(jira_flaky), "common", len(common_fails), "ff", len(freq_fails))


def extract_dataset_with_filterlabel():
    """
    generate test_class_filterlabel.csv where each FAILED test is also labeled whether they belongs to:
        1. jira flaky test
        2. not in intersection of failed test set across stage
        3. frequently failed test
    """
    df = pd.read_csv(const.DATASET_FILE)
    df = df[["project", "pr_name", "build_id", "build_timestamp"]].drop_duplicates().values.tolist()
    df = [(idx, proj, pr, build, ts) for idx, (proj, pr, build, ts) in enumerate(df)]
    pool = mp.Pool(mp.cpu_count())
    pool.starmap(extract_dataset_with_filterlabel_helper, df)



def update_first_history(project, stage, df, fail_hist, trans_hist):
    key = project + "_" + stage
    if key not in fail_hist:
        fail_hist[key] = set()
    if key not in trans_hist:
        trans_hist[key] = {"fail_to_pass": set(), "pass_to_fail": set()}

    test_outcomes = df[["testclass", "outcome", "last_outcome"]].values.tolist()
    first_failure = [0] * len(test_outcomes)
    first_trans = [0] * len(test_outcomes)
    for idx, (test, outcome, last_outcome) in enumerate(test_outcomes):
        # mark when the test fail for the first time
        if outcome == eval_const.FAIL:
            # test never failed before
            if test not in fail_hist[key]:
                fail_hist[key].add(test)
                # record the first build this test failed on
                first_failure[idx] = 1
        # mark when the test transition from fail to pass for the first time
        if last_outcome == eval_const.FAIL and outcome == eval_const.PASS:
            if test not in trans_hist[key]["fail_to_pass"]:
                trans_hist[key]["fail_to_pass"].add(test)
                first_trans[idx] = 1
        if last_outcome == eval_const.PASS and outcome == eval_const.FAIL:
            if test not in trans_hist[key]["pass_to_fail"]:
                trans_hist[key]["pass_to_fail"].add(test)
                first_trans[idx] = 1
    return first_failure, first_trans, fail_hist, trans_hist


def amend_first_failure_filter():
    omni = pd.read_csv(const.DATASET_FILE)
    # sort tests from oldest to latest
    omni = omni.sort_values(["project", "build_timestamp"], ascending=True)
    omni = omni[["project", "pr_name", "build_id"]].drop_duplicates().values.tolist()
    fail_hist, trans_hist = {}, {}

    for index, (project, pr_name, build_id) in enumerate(omni):
        stage_files = glob.glob(os.path.join(
            eval_const.trdir, project, f"{pr_name}_build{build_id}", "stage_*", eval_const.TEST_CLASS_FL_CSV))
        for stage_file in stage_files:
            stage = stage_file.split("/")[-2]
            print("walking", project, index, pr_name, build_id, stage)
            df = pd.read_csv(stage_file)
            # amend first failure filter to df
            first_failure, first_trans, fail_hist, trans_hist = update_first_history(
                project, stage, df, fail_hist, trans_hist)
            df["first_failure"] = first_failure
            df["first_trans"] = first_trans
            # save results
            df.to_csv(stage_file, index=False)


def get_num_fail_or_trans(tests, filters):
    df = tests.copy()
    for f in filters:
        df = df[df[f] == 1] if f.startswith(eval_const.FILTER_FIRST) else df[df[f] == 0]
    return len(df)

def calculate_dataset_variant_stats():
    """compute stats (#failed tests) per (stage, build) under different filtering conditions"""
    df = pd.read_csv(const.DATASET_FILE)
    # print(df.columns)
    jira_for_fail = "jira_for_fail"
    stageunique_for_fail = "stageunique_for_fail"
    freqfail_for_fail = "freqfail_for_fail"
    jira_for_trans = "jira_for_trans"
    stageunique_for_trans = "stageunique_for_trans"
    freqfail_for_trans = "freqfail_for_trans"
    first_failure = "first_failure"
    first_trans = "first_trans"
    fail_filter_combos = [
        [jira_for_fail], [freqfail_for_fail], # [jira_for_fail, stageunique_for_fail]
        [stageunique_for_fail], [first_failure],
    ]
    trans_filter_combos = [
        [jira_for_trans], [freqfail_for_trans],
        [stageunique_for_trans], [first_trans],
    ]
    for combo in fail_filter_combos:
        new_col_name = "num_fail_class+" + "+".join(combo)
        df[new_col_name] = 0
    for combo in trans_filter_combos:
        new_col_name = "num_trans_class+" + "+".join(combo)
        df[new_col_name] = 0
    
    for idx, row in df.iterrows():
        project = row["project"]
        pr_name = row["pr_name"]
        build_id = row["build_id"]
        stage_id = row["stage_id"]
        fpath = os.path.join(eval_const.trdir, project, 
                           f"{pr_name}_build{build_id}/stage_{stage_id}/{eval_const.TEST_CLASS_FL_CSV}")
        current = pd.read_csv(fpath)
        fails = current[current["outcome"] == eval_const.FAIL]
        trans = current[current.outcome != current.last_outcome]
        for combo in fail_filter_combos:
            new_col_name = "num_fail_class+" + "+".join(combo)
            df.loc[idx, new_col_name] = get_num_fail_or_trans(fails, combo)
        for combo in trans_filter_combos:
            new_col_name = "num_trans_class+" + "+".join(combo)
            df.loc[idx, new_col_name] = get_num_fail_or_trans(trans, combo)
        if idx % 1000 == 0:
            print(idx, project, pr_name, build_id, stage_id)
    df.to_csv(const.DATASET_FILTER_FILE, index=False)


def extract_filtered_tests_for_builds():
    """get the to be filtered tests in each filter for each build"""
    omni = pd.read_csv(const.DATASET_FILE)
    omni = omni[["project", "pr_name", "build_id", "stage_id"]].values.tolist()
    filters = [eval_const.FILTER_JIRA, eval_const.FILTER_STAGEUNIQUE, 
               eval_const.FILTER_FREQFAIL, eval_const.FILTER_FIRST]
    for idx, (project, pr_name, build_id, stage_id) in enumerate(omni):
        if idx % 1000 == 0:
            print(project, pr_name, build_id, stage_id)
        input_dir = os.path.join(eval_const.trdir, project, 
                                f"{pr_name}_build{build_id}", f"stage_{stage_id}")
        input_path = os.path.join(input_dir, eval_const.TEST_CLASS_FL_CSV)
        df = pd.read_csv(input_path)
        filtered_tests = {"for_fail": {}, "for_trans": {}}
        for f in filters:
            if f == eval_const.FILTER_FIRST:
                # tests not first failure/trans should be filtered
                not_first_fails = df[(df["first_failure"] == 0) & (df["outcome"] == eval_const.FAIL)]["testclass"].values.tolist()
                not_first_trans = df[(df["first_trans"] == 0) & (df["outcome"] != df["last_outcome"])]["testclass"].values.tolist()
                filtered_tests["for_fail"][f] = not_first_fails
                filtered_tests["for_trans"][f] = not_first_trans
            else:
                filtered_tests["for_fail"][f] = df[df[f+"_for_fail"] == 1]["testclass"].values.tolist()
                filtered_tests["for_trans"][f] = df[df[f+"_for_trans"] == 1]["testclass"].values.tolist()
        with gzip.open(os.path.join(input_dir, eval_const.FILTER_TESTS_FILE), "wt") as f:
            json.dump(filtered_tests, f)
    pass

if __name__ == "__main__":
    compute_fail_freq_for_test_classes()
    get_outlier()
    process_jira_flaky_tests()
    get_common_failed_tests()
    extract_dataset_with_filterlabel()
    amend_first_failure_filter()
    calculate_dataset_variant_stats()
    # extract_filtered_tests_for_builds()
    # get_no_fail_test_classes()
    # get_test_classes_exec_count()
    # get_test_classes_fail_count()
    pass
