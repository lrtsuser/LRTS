import pandas as pd
import os
import sys
import subprocess
import time
import json
import glob
import re

script_dir = os.path.dirname(__file__)
grandparent_dir = os.path.join(script_dir, "..", "..")
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "information_retrieval")
sys.path.append(grandparent_dir)
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import ir_const
import eval_utils


def download_trunk(project):
    print("processing", project)
    trunk = os.path.join(ir_const.repo_dir, f"{project}_repo")
    current_dir = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(trunk):
        link = const.PROJECT_GITHUB[project]
        os.chdir(ir_const.repo_dir)
        os.system(f"git clone {link} {project}_repo")
        os.chdir(current_dir)

    print("trunk downloaded, pulling")
    os.chdir(trunk)
    os.system("git branch")
    # go to default remote main branch
    # pull the latest change
    get_default_branch_cmd = "git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@'"
    ret = subprocess.run(get_default_branch_cmd, capture_output=True, shell=True)
    main_branch = ret.stdout.decode("utf-8", errors="ignore")
    os.system(f"git checkout {main_branch}")
    os.system("git pull")
    
    # get all branches needed for PRs
    df = pd.read_csv(const.DATASET_FILE)
    df = df[df["project"] == project]
    branches = set(df["pr_base_branch"].values.tolist())
    print("need to get branches", branches)
    for branch in branches:
        os.system(f"git checkout {branch}")
        os.system("git pull")
        # switch back to main branch
        os.system(f"git checkout {main_branch}")
    os.chdir(current_dir)


def get_filepaths(project, test, allfilepaths):
    testname = test.split("$")[0]
    if project.startswith(const.TVM):
        # python-based
        if testname.split(".")[-1].islower():
            testname = "/".join(testname.split(".")[-2:]) + "."
        else:
            testname = "/".join(testname.split(".")[-2:-1]) + "."
    else:
        if "." in test:
            # java
            testname = "/".join(testname.split(".")[-2:]) + "."
            if project in [const.HIVE]:
                # org.apache.hadoop.hive.cli.split2.TestCliDriver
                p = re.compile(r'split[0-9]+')
                if p.search(testname):
                    testname = "/" + testname.split("/")[-1]
        else:
            if project in [const.HADOOP]:
                testname = "/Test" + testname + ".cc"
            # otherwise: testname is often suffix of the file name (c file)
    matches = [x for x in allfilepaths if testname in x]

    return matches


def get_testclass_filepaths(testpath_file, project, tests, overwrite=False):
    # collect file if both the original and compressed file are missing
    if overwrite or not os.path.exists(testpath_file):
        data = {}
        start = time.time()
        # get a list of all test code files
        allfilepaths = glob.glob("**/*.java", recursive=True) + glob.glob("**/*.scala", recursive=True) \
            + glob.glob("**/*.py", recursive=True) + glob.glob("**/*.cc", recursive=True) \
                + glob.glob("**/*.c", recursive=True) + glob.glob("**/*.groovy", recursive=True)
        allfilepaths = [x for x in allfilepaths if "test" in x]
        for test in tests:
            data[test] = get_filepaths(project, test, allfilepaths)
        with open(testpath_file, "w") as f:
            json.dump(data, f, indent=2)
        os.system(f"echo [LRTS] SEARCH TIME FOR {len(tests)} TESTS: {time.time() - start}s")


def get_body(paths):
    path_to_body = {}
    for path in paths:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                path_to_body[path] = f.read()
    return path_to_body


def get_testclass_body(testpath_file, testbody_file):
    """load test path data, extract and save test body data"""
    # load path data
    with open(testpath_file, "r") as f:
        data = json.load(f)
    # extract body
    start = time.time()
    for test, paths in data.items():
        data[test] = get_body(paths)
    # dump body data
    with open(testbody_file, "w") as f:
        json.dump(data, f, indent=2)
    os.system(f"echo [LRTS] READ TIME FOR {len(data)} TESTS: {time.time() - start}s")


def get_diff_body(diffbody_file, change_file):
    start = time.time()
    # get changed file paths from .diff to get the whole file
    change_paths = []
    # get the + - lines only
    change_lines = []
    with open(change_file, "r") as f:
        for line in f.readlines():
            line = line.strip().strip("\n")
            if line.startswith("--- a") or line.startswith("+++ b"):
                change_paths.append(line.replace("--- a/", "").replace("+++ b/", ""))
            else:
                if line.startswith("+") or line.startswith("-"):
                    change_lines.append(line)
    change_paths = set(change_paths)

    # read whole changed files
    data = {
        "changed_lines": change_lines,
        "whole_files": {},
        # # i.e, deleted files
        # "unfound": [],
    }
    for path in change_paths:
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                data["whole_files"][path] = f.read()
        # else:
        #     data["unfound"].append(path)

    with open(diffbody_file, "w") as f:
        json.dump(data, f, indent=2)
    os.system(f"echo [LRTS] EXTRACT TIME FOR {len(change_paths)} CHANGED FILE: {time.time() - start}s")
    pass


def compress_file(filepath, overwrite=False):
    if  overwrite or (os.path.exists(filepath) and not os.path.exists(filepath+".gz")):
        print("COMPRESSING ", filepath)
        current_dir = os.path.dirname(os.path.realpath(__file__))
        dest_dir = os.path.dirname(filepath)
        zip_name = os.path.basename(filepath)
        os.chdir(dest_dir)
        os.system(f"gzip -f {zip_name}")
        os.chdir(current_dir)


def extract_test_and_diff_body_per_build(project, pr_name, branch, build_id, base, overwrite=False):
    """
    extract the test class body per test class per build 
    extract change file body
    """
    ir_build_dir = os.path.join(ir_const.irdata_dir, project, f"{pr_name}_build{build_id}")
    os.makedirs(ir_build_dir, exist_ok=True)
    testpath_file = os.path.join(ir_build_dir, ir_const.TESTPATH_FILE)
    testbody_file = os.path.join(ir_build_dir, ir_const.TESTBODY_FILE)
    diffbody_file = os.path.join(ir_build_dir, ir_const.DIFFBODY_FILE)
    
    if overwrite or not os.path.exists(testbody_file + ".gz") or not os.path.exists(diffbody_file + ".gz"):
        # get the tests
        tests = eval_utils.gather_test_classes_from_all_suites(project, pr_name, build_id)
        os.system(f"echo [LRTS] PROCESSING PR BUILD {project}, {pr_name}, {build_id}, {base}")

        # get the diff patch
        change_file = os.path.join(const.shadir, project, const.DIFF_DIR, f"{pr_name}_build{build_id}.diff")
        
        # checkout the base
        repo = os.path.join(ir_const.repo_dir, f"{project}_repo")
        current_dir = os.path.dirname(os.path.realpath(__file__))
        os.chdir(repo)

        os.system("echo [LRTS] CLEAN LOCAL CHANGES, RESET TO MAIN BRANCH")
        os.system("git reset --hard")
        os.system("git clean -fdx")
        os.system(f"git checkout {const.PROJECT_MAIN_BRANCHES[project]}")
        
        os.system(f"echo [LRTS] CHECKING OUT {branch}, {base}")
        os.system(f"git checkout {branch}")
        os.system(f"git checkout {base}")

        # apply patch
        os.system(f"echo [LRTS] APPLYING CHANGE {change_file}")
        os.system(f"git apply --reject --ignore-space-change --ignore-whitespace {change_file}")
        os.system("echo [LRTS] FINISHED APPLYING CHANGE")
        
        # extract test class body via file path search
        get_testclass_filepaths(testpath_file, project, tests)
        get_testclass_body(testpath_file, testbody_file)
        # extract changed file body
        get_diff_body(diffbody_file, change_file)

        # # revert the applied patch
        os.system(f"echo [LRTS] REVERSING CHANGE {change_file}")
        # os.system(f"git apply -R --reject --ignore-space-change --ignore-whitespace {change_file}")
        os.system("git reset --hard")
        os.system("git clean -fdx")
        # # checkout to the original branch head
        os.system(f"echo [LRTS] CHECKING OUT MAIN BRANCH")
        os.system(f"git checkout {const.PROJECT_MAIN_BRANCHES[project]}")
        os.chdir(current_dir)

        # compress file and remove original file
        # compress_file(testpath_file)
        compress_file(testbody_file)
        compress_file(diffbody_file)


def extract_ir_body(project):
    os.makedirs(os.path.join(ir_const.irdata_dir, project), exist_ok=True)
    
    # only do IR on builds with failed tests
    df = pd.read_csv(const.DATASET_FILE)
    df = df[df["project"] == project]
    df = df[["pr_name", "pr_base_branch", "build_id", "trunk_sha", "build_head_sha"]].drop_duplicates().values.tolist()
    print("PROCESSING #builds", len(df))
    for pr_name, branch, build_id, base, head in df:
        extract_test_and_diff_body_per_build(project, pr_name, branch, build_id, base)

if __name__ == "__main__":
    for project in const.PROJECTS:
        download_trunk(project)
        extract_ir_body(project)
    # project = sys.argv[1]
    # download_trunk(project)
    # extract_ir_body(project)
    pass