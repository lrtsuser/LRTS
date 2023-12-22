import os
import pandas as pd
import subprocess
import const

"""download the codebase zip wrt the merged build head sha"""
def download_possible_branches(project):
    df = pd.read_csv(os.path.join(const.metadir, project, const.BUILDSTATS_FILE))
    branches = set(df["pr_base_branch"].values.tolist())
    print("need to get branches", branches)
    for branch in branches:
        os.system(f"git checkout {branch}")
    pass

def download_trunk(project):
    print("processing", project)
    trunk_dir = os.path.join(const.historydir, project)
    os.makedirs(trunk_dir, exist_ok=True)
    trunk = os.path.join(trunk_dir, f"{project}_trunk")
    current_dir = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(trunk):
        link = const.PROJECT_GITHUB[project]
        os.chdir(trunk_dir)
        os.system(f"git clone {link} {project}_trunk")
        os.chdir(current_dir)

    print("trunk downloaded, pulling")
    current_dir = os.path.dirname(os.path.realpath(__file__))
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
    df = pd.read_csv(os.path.join(const.metadir, project, const.BUILDSTATS_FILE))
    branches = set(df["pr_base_branch"].values.tolist())
    print("need to get branches", branches)
    for branch in branches:
        os.system(f"git checkout {branch}")

    # switch back to main branch
    os.system(f"git checkout {main_branch}")
    os.chdir(current_dir)


if __name__ == "__main__":
    for project in const.PROJECTS:
        download_trunk(project)
    pass