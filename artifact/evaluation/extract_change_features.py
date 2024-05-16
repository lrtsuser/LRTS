import pandas as pd
import os
import sys
import json
import multiprocessing as mp
from nltk.metrics.distance import edit_distance
import re

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import eval_const
import eval_utils



def tokenize(s):
    s = s.lower()
    return re.findall(r'[A-Za-z]+', s)

def get_distances(project, index, total_jobs, mytest, myfile):
    test = mytest.lower()
    file = myfile.lower()
    if index % 10000 == 0:
        print(project, index, total_jobs)
    file_path_dist = edit_distance(test, file)
    file_path_tok_sim = len(set(tokenize(test)).intersection(set(tokenize(file))))
    file_name_dist = edit_distance(test.split(".")[-1].split("_")[-1], os.path.basename(file))
    return [mytest, myfile, file_path_dist, file_path_tok_sim, file_name_dist]


def extract_change_based_features_per_build(
        project, index, pr_name, build_id, 
        changeinfo, file_path_dists, file_path_tok_sims, file_name_dists, overwrite=True):
    print("processing", project, index, pr_name, build_id)

    build_dir = os.path.join(eval_const.feadir, project, f"{pr_name}_build{build_id}")
    os.makedirs(build_dir, exist_ok=True)
    change_feature_file = os.path.join(build_dir, eval_const.CHANGEFEA_FILE)

    if overwrite or not os.path.exists(change_feature_file):
        tests = eval_utils.gather_test_classes_from_all_suites(project, pr_name, build_id)
        
        # change info for this build
        build_change = changeinfo[f"{pr_name}_build{build_id}"]
        changeset = set(build_change["changed_files"])
        
        features = []
        # get feature for each test in this build
        for test in tests:
            # (test, file) similarity on the change of this build
            min_file_path_distance = min([file_path_dists[test][x] for x in changeset]) if len(changeset) else 0
            max_file_path_tok_sim = max([file_path_tok_sims[test][x] for x in changeset]) if len(changeset) else 0
            min_file_name_distance = min([file_name_dists[test][x] for x in changeset]) if len(changeset) else 0
            # change features
            distinct_authors = len(set(build_change["authors"]))
            changeset_size = len(changeset)
            commit_count = build_change["commit_count"]
            distinct_extensions = len(set([x.split(".")[-1] for x in changeset]))


            features.append([
                test, min_file_path_distance, max_file_path_tok_sim, min_file_name_distance,
                distinct_authors, changeset_size, commit_count, distinct_extensions,
            ])

        # save the per build feature data
        features = pd.DataFrame(features, columns=[
            "testclass", "min_file_path_distance", "max_file_path_tok_sim", "min_file_name_distance",
            "distinct_authors", "changeset_size", "commit_count", "distinct_extensions",
        ])

        features.to_csv(change_feature_file, index=False)


def add_to_dict(test, file, value, dict):
    if test not in dict:
        dict[test] = {}
    dict[test][file] = value
    return dict


def load_existing_data(changedistance_fpath):
    if os.path.exists(changedistance_fpath):
        with open(changedistance_fpath, "r") as f:
            data = json.load(f)
            file_path_dists = data["file_path_dists"]
            file_path_tok_sims = data["file_path_tok_sims"]
            file_name_dists = data["file_name_dists"]
            return file_path_dists, file_path_tok_sims, file_name_dists
    return {}, {}, {}


def prune_existing_data(test_file_set, dist_dict):
    # keep only test in the new test file set
    dist_dict = {test: dist_dict[test] for test in test_file_set.keys() if test in dist_dict}
    for test in dist_dict:
        # keep only file in the new test file set for each test
        dist_dict[test] = {file: dist_dict[test][file] for file in test_file_set[test] if file in dist_dict[test]}
    return dist_dict


def remove_tuples_with_existing_data(test_file_set, file_path_dists, file_path_tok_sims, file_name_dists):
    ret = []
    for test, file in test_file_set:
        if test in file_path_dists and file in file_path_dists[test]:
            continue
        if test in file_path_tok_sims and file in file_path_tok_sims[test]:
            continue
        if test in file_name_dists and file in file_name_dists[test]:
            continue
        ret.append((test, file))
    return ret


def extract_change_based_features(project, overwrite=True, reuse_existing_data=True):
    print("processing", project)
    os.makedirs(os.path.join(eval_const.feadir, project), exist_ok=True)

    df = pd.read_csv(const.DATASET_FILE)
    df = df[df["project"] == project]

    # sort the build from oldest to latest
    df = df.sort_values("build_timestamp", ascending=True)
    df = df[["pr_name", "build_id"]].drop_duplicates().values.tolist()

    # load changset info
    with open(os.path.join(eval_const.changeinfodir, f"{project}.json"), "r") as f:
        changeinfo = json.load(f)

    # collect distance for (test, file) tuples
    changedistance_fpath = os.path.join(eval_const.changeinfodir, f"{project}_distances.json")
    file_path_dists, file_path_tok_sims, file_name_dists = {}, {}, {}
    # gather (test, file) tuples
    if overwrite or not os.path.exists(changedistance_fpath):
        # gather all tests from all suites in a build
        test_file_set = {}
        for index, (pr_name, build_id) in enumerate(df):
            tests = eval_utils.gather_test_classes_from_all_suites(project, pr_name, build_id)
            changeset = changeinfo[f"{pr_name}_build{build_id}"]["changed_files"]
            for test in tests:
                if test not in test_file_set:
                    test_file_set[test] = set()
                for file in changeset:
                    test_file_set[test].add(file)

        if reuse_existing_data:
            file_path_dists, file_path_tok_sims, file_name_dists = load_existing_data(changedistance_fpath)
            print("reusing existing data", len(file_path_dists), len(file_path_tok_sims), len(file_name_dists))
            # prune old data
            file_path_dists = prune_existing_data(test_file_set, file_path_dists)
            file_path_tok_sims = prune_existing_data(test_file_set, file_path_tok_sims)
            file_name_dists = prune_existing_data(test_file_set, file_name_dists)
        
        test_file_set = [(test, file) for test in test_file_set for file in test_file_set[test]]
        if reuse_existing_data:
            print("distances to compute before reusing old data", len(test_file_set))
            # remove tuples that already have data
            test_file_set = remove_tuples_with_existing_data(
                test_file_set, file_path_dists, file_path_tok_sims, file_name_dists)

        # parallelize
        print("distances to compute", len(test_file_set))
        pool = mp.Pool(mp.cpu_count())
        args = [(project, i, len(test_file_set), x[0], x[1]) for i, x in enumerate(test_file_set)]
        results = pool.starmap(get_distances, args)
        for test, file, file_path_dist, file_path_tok_sim, file_name_dist in results:
            file_path_dists = add_to_dict(test, file, file_path_dist, file_path_dists)
            file_path_tok_sims = add_to_dict(test, file, file_path_tok_sim, file_path_tok_sims)
            file_name_dists = add_to_dict(test, file, file_name_dist, file_name_dists)
        
        with open(changedistance_fpath, "w") as f:
            json.dump({
                "file_path_dists": file_path_dists, 
                "file_path_tok_sims": file_path_tok_sims,
                "file_name_dists": file_name_dists}, f, indent=2)
    else:
        file_path_dists, file_path_tok_sims, file_name_dists = load_existing_data(changedistance_fpath)

    for index, (pr_name, build_id) in enumerate(df):
        extract_change_based_features_per_build(
            project, index, pr_name, build_id, 
            changeinfo, file_path_dists, file_path_tok_sims, file_name_dists)



if __name__ == "__main__":
    for project in const.PROJECTS:
        extract_change_based_features(project)
    pass

