import json
import os
import pandas as pd
import glob
import multiprocessing as mp
import zipfile
from datetime import datetime

import const

"""
collect the metadata of builds with failed tests
pr, buildid, build duration, test suite duration, 
pr head sha (this will be used to download zip)
"""

def get_build_head_sha(builddata, pr_name):
    actions = builddata["actions"]
    sha = None
    for action in actions:
        if "buildsByBranchName" in action and pr_name in action["buildsByBranchName"]:
            sha = action["buildsByBranchName"][pr_name]["revision"]["branch"][0]["SHA1"]
            break
    return sha


def get_pr_base_branch(project, pr_name):
    fpath = os.path.join(const.prdir, project, "pr_info", f"{pr_name}.json")
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
            info = json.load(f)
            if "message" in info and info["message"] == "Not Found":
                return None
            branch = info["base"]["ref"]
            return branch
    return None


def process_testfile(filepath, project):
    # get pr name and build id
    # hadoop/PR/PR-2912/testReport_build1.json
    tokens = filepath.split("/")
    pr_name = tokens[-2]
    build_id = int(tokens[-1].split(".")[0].split("build")[-1])

    # get #pass, failed, skipped tests, and test suite duration
    filepath_base = os.path.basename(filepath.replace(".zip", ""))
    testdata = json.load(zipfile.ZipFile(filepath, "r").open(filepath_base))
    duration = testdata["duration"]
    failcount = testdata["failCount"]
    passcount = testdata["passCount"]
    skipcount = testdata["skipCount"]
    
    # get the build data, timestamp, etc
    buildfilepath = os.path.join(os.path.dirname(filepath), f"build{build_id}.json")
    builddata = json.load(open(buildfilepath))
    # convert ms to second
    build_duration = int(builddata["duration"] / 1000)
    build_timestamp = int(builddata["timestamp"] / 1000)
    build_result = builddata["result"]
    # get the build head sha from the build data
    build_head_sha = get_build_head_sha(builddata, pr_name)
    pr_base_branch = get_pr_base_branch(project, pr_name)

    # filtering
    if build_duration == 0 or build_timestamp == 0:
        build_duration = None
        build_timestamp = None

    if failcount + passcount > 1:
        return [project, pr_name, pr_base_branch, build_id, 
                build_duration, build_timestamp, build_result, build_head_sha,
                duration, passcount, failcount, skipcount]
    return None


def get_buildstats(project):
    print("\nPROCESSING", project)
    # get a list of downloaded test files
    testfiles = glob.glob(os.path.join(const.testdir, project, "PR", "*/testReport*.zip"))
    print("#files", len(testfiles))

    # processing the test files
    pool = mp.Pool(mp.cpu_count())
    result = pool.starmap(process_testfile, [(f, project) for f in  testfiles])
    # no None
    result = [x for x in result if x != None]
    
    # construct df
    df = pd.DataFrame(result, columns=[
        "project", "pr_name", "pr_base_branch", "build_id", 
        "build_duration", "build_timestamp", "build_result", "build_head_sha",
        "ts_duration", "passcount", "failcount", "skipcount"
    ])
    # data processing: add human readable date, sort by earliest to latest
    df["build_date"] = df["build_timestamp"].apply(
        lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d') if not pd.isna(x) else None)
    df = df.sort_values("build_timestamp", ascending=True)

    bsfile = os.path.join(const.metadir, project, const.BUILDSTATS_FILE)
    df.to_csv(bsfile, index=False)



if __name__ == "__main__":
    for project in const.PROJECTS:
        get_buildstats(project)
    pass
