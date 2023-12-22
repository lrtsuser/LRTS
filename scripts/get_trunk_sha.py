import lzma
import pandas as pd
import os
import re
import subprocess
import multiprocessing as mp
from subprocess import Popen, PIPE


import const

"""get trunk sha from build log"""


def clean_extracted_sha(s):
    s = s.strip().split(" ")
    for t in s:
        if len(t) == 40:
            return t


def tvm_corner_case(content):
    trunk_pattern = r'git -c user.name=TVM-Jenkins -c user.email=jenkins@tvm.apache.org merge (.*)\n'
    head_pattern = r'Obtained Jenkinsfile from (.*)\n'
    trunk_matches = re.findall(trunk_pattern, content)
    head_matches = re.findall(head_pattern, content)
    print(f"#matches for pattern-tvm", len(trunk_matches), len(head_matches))
    if len(trunk_matches) and len(head_matches):
        trunk_sha = clean_extracted_sha(trunk_matches[0])
        head_sha = clean_extracted_sha(head_matches[0])
        return [trunk_sha, head_sha]
    return []


def get_trunk_sha_via_build_log_regex_corner_case(project, content):
    if project in [const.TVM, const.TVM_GPU]:
        return tvm_corner_case(content)
    return []


def get_trunk_sha_via_build_log_regex(project, log_file):
    """
    get the trunk sha via regexing, i.e.,
    Merging remotes/origin/main commit A into PR head commit B
    """
    patterns = [
        r'Merging remotes/origin/.* commit (.*) into PR head commit (.*)',
        r'Loading trusted files from base branch \w+ (.*) rather than (.*)\n'
    ]

    try:
        with lzma.open(log_file, "rt", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            # lines = [x for x in content.split("\n")]
            # print(lines[:20])
            for index, pattern in enumerate(patterns):
                matches = re.findall(pattern, content)
                print(f"#matches for pattern-{index}", len(matches))
                # return the first instance, [trunk, prhead]
                if len(matches) > 0 and len(matches[0]) == 2:
                    trunk_sha = clean_extracted_sha(matches[0][0])
                    head_sha = clean_extracted_sha(matches[0][1])
                    return [trunk_sha, head_sha]
            
            # corner case checking
            matches = get_trunk_sha_via_build_log_regex_corner_case(project, content)
            if len(matches) == 2:
                return matches
    except Exception as e:
        print("[ERROR]", str(e))
    return []


def get_trunk_sha_via_nearest_trunk_commit(project, pr_base_branch, build_timestamp, build_head_sha):
    """
    get the timestamp of the build taking place
    find the nearest commit from trunk repo that happens before the timestamp
    """
    # git log --before=1673142654.245 -n 1 --pretty=format:"%H;%at"

    # convert to second, minus 8 hours, empirically, there is delay
    build_timestamp = build_timestamp

    trunk_dir = os.path.join(const.historydir, project, f"{project}_trunk")
    current_dir = os.path.dirname(os.path.realpath(__file__))
    os.chdir(trunk_dir)
    
    # in corner case, the return sha is the same as build head sha
    # most in jackrabbit e.g., jackrabbit-oak/PR-520_build1
    # in this case, go further back in time until retrive a different sha
    trunk_sha = build_head_sha
    start_timestamp = build_timestamp
    while trunk_sha == build_head_sha:
        try:
            output = subprocess.check_output(
                f"git log {pr_base_branch} --before={start_timestamp} -n 1 --pretty=format:\"%H;%at\"", 
                shell=True)
            output = output.decode("utf-8", errors="ignore")
            trunk_sha, trunk_sha_timestamp = output.split(";")
        except Exception as e:
            print(f"ERROR for checkout branch {pr_base_branch}", str(e))
            print("falling back to default branch")
            output = subprocess.check_output(
                f"git log --before={start_timestamp} -n 1 --pretty=format:\"%H;%at\"", 
                shell=True)
            output = output.decode("utf-8", errors="ignore")
            trunk_sha, trunk_sha_timestamp = output.split(";")
        trunk_sha_timestamp = int(trunk_sha_timestamp)
        start_timestamp -= 60
    os.chdir(current_dir)

    return trunk_sha, trunk_sha_timestamp


def get_trunk_sha(index, project, pr_name, pr_base_branch, build_id, build_timestamp, build_head_sha):
    """
    find it from log, 
    if unfound, get the nearest commit before the build from trunk based on build timestamp
    """
    # return trunk_sha, build_head_sha_from_log, trunk_sha_timestamp, source
    print("processing", index, build_head_sha)

    # extract from log file first
    log_file = os.path.join(const.testdir, project, "PR", pr_name, f"console_build{build_id}.txt.xz")
    if os.path.exists(log_file):
        print("checking log", log_file)
        match = get_trunk_sha_via_build_log_regex(project, log_file)
        if len(match) == 2:
            trunk_sha, build_head_sha_from_log = match
            if build_head_sha_from_log == build_head_sha:
                return trunk_sha, None, "build_log"
            else:
                print(f"[STRANGE] head sha unmatch", log_file)
        else:
            if project != const.HIVE:
                print("[STRANGE] no match from log")
    
    # if failed, extract the nearest commit from trunk git log
    print(f"checking trunk, branch: {pr_base_branch}")
    trunk_sha, trunk_sha_timestamp = get_trunk_sha_via_nearest_trunk_commit(
        project, pr_base_branch, build_timestamp, build_head_sha)
    return trunk_sha, trunk_sha_timestamp, "nearest_commit"


def run_get_trunk_sha(project):
    # get the trunk sha for each pr head build sha from metadata csv
    metadata = pd.read_csv(os.path.join(const.metadir, project, const.BUILDSTATS_FILE))
    metadata = metadata[["pr_name", "pr_base_branch", "build_id", "build_timestamp", "build_head_sha"]]
    metadata = metadata.dropna().values.tolist()
    print("#shas", project, len(metadata))

    df = []
    for index, (pr_name, pr_base_branch, build_id, build_timestamp, build_head_sha) in enumerate(metadata):
        trunk_sha, trunk_sha_timestamp, trunk_sha_source = get_trunk_sha(
            index, project, pr_name, pr_base_branch, build_id, build_timestamp, build_head_sha
        )
        df.append([
            pr_name, pr_base_branch, build_id, build_timestamp, trunk_sha_timestamp,
            build_head_sha, trunk_sha, trunk_sha_source
            ])

    df = pd.DataFrame(df, columns=[
        "pr_name", "pr_base_branch", 
        "build_id", "build_timestamp", "trunk_sha_timestamp_sec", "build_head_sha",
        "trunk_sha", "trunk_sha_source"])
    df.to_csv(os.path.join(const.metadir, project, const.TRUNK_PRHEAD_MAP_FILE), index=False)
    pass

if __name__ == "__main__":
    for project in const.PROJECTS:
        run_get_trunk_sha(project)
    pass