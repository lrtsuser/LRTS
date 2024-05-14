import pandas as pd
import os
import sys
import json
import multiprocessing as mp

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import eval_const


"""
look at the change between the build head versus its base (i.e., commit it is merging into), extract:
- set of change files
- set of distinct authors
- number of commits
"""


def extract_change_info_per_build(project, pr_name, build_id, base, head):
    page = 1
    fpath = os.path.join(const.shadir, project, const.COMPARE_DIR, 
                         f"{pr_name}_build{build_id}", f"{base}_{head}_page{page}.json")
    
    ret = {
        "commit_count": 0,
        "authors": [],
        "changed_files": [],
    }
    
    while os.path.exists(fpath):
        print("loading", fpath)
        with open(fpath, "r") as f:
            data = json.load(f)
            # get set of changed files
            if "files" in data:
                ret["changed_files"] += [x["filename"] for x in data["files"]]
            if "commits" in data:
                ret["authors"] += [x["commit"]["author"]["email"] for x in data["commits"]]
                ret["commit_count"] += len(data["commits"])
                # for commit in data["commits"]:
                #     print(commit["commit"]["author"]["email"])
        page += 1
        fpath = os.path.join(const.shadir, project, const.COMPARE_DIR, 
                        f"{pr_name}_build{build_id}", f"{base}_{head}_page{page}.json")

    ret["authors"] = list(set(ret["authors"]))
    ret["changed_files"] = list(set(ret["changed_files"]))
    return ret


def extract_change_info(project):
    df = pd.read_csv(const.OMIN_FILE)
    df = df[df["project"] == project]
    # all stages of the same build is on top of the same change, no need to distinguish stages here
    df = df[["pr_name", "build_id", "trunk_sha", "build_head_sha"]].drop_duplicates().values.tolist()

    data = {}
    for pr_name, build_id, base, head in df:
        info = extract_change_info_per_build(project, pr_name, build_id, base, head)
        data[f"{pr_name}_build{build_id}"] = info
    with open(os.path.join(eval_const.changeinfodir, f"{project}.json"), "w") as f:
        json.dump(data, f, indent=2)
        

def extract_change_stats_per_build(project, pr_name, build_id, base, head):
    page = 1
    fpath = os.path.join(const.shadir, project, const.COMPARE_DIR, 
                         f"{pr_name}_build{build_id}", f"{base}_{head}_page{page}.json")
    # num changed files, added lines, deleted lines
    ret = {
        "num_changed_files": 0,
        "num_additions": 0,
        "num_deletions": 0,
    }
    while os.path.exists(fpath):
        print("loading", fpath)
        with open(fpath, "r") as f:
            data = json.load(f)
            # get set of changed files
            if "files" in data:
                ret["num_changed_files"] += len(data["files"])
                ret["num_additions"] += sum([x["additions"] for x in data["files"]])
                ret["num_deletions"] += sum([x["deletions"] for x in data["files"]])
        page += 1
        fpath = os.path.join(const.shadir, project, const.COMPARE_DIR, 
                        f"{pr_name}_build{build_id}", f"{base}_{head}_page{page}.json")

    return [ret["num_changed_files"], ret["num_additions"], ret["num_deletions"]]


def extract_change_stats(project):
    """get #changed files, #lines added, and #lines deleted per change/build"""
    df = pd.read_csv(const.OMIN_FILE)
    df = df[df["project"] == project]
    # all stages of the same build is on top of the same change, no need to distinguish stages here
    df = df[["pr_name", "build_id", "trunk_sha", "build_head_sha"]].drop_duplicates().values.tolist()

    data = []
    for pr_name, build_id, base, head in df:
        info = extract_change_stats_per_build(project, pr_name, build_id, base, head)
        data.append([project, pr_name, build_id] + info)
    return data


def extract_change_stats_runner():
    df = []
    for project in const.PROJECTS:
        rows = extract_change_stats(project)
        df = df + rows
    df = pd.DataFrame(df, columns=["project", "pr_name", "build_id", "num_changed_files", "num_addition", "num_deletion"])
    df.to_csv(os.path.join(eval_const.changeinfodir, f"change_stats.csv"), index=False)


if __name__ == "__main__":
    # for project in const.PROJECTS:
    #     extract_change_info(project)
    extract_change_stats_runner()
    pass