import pandas as pd
import json
import requests
import os


import const
from token_pool import TokenPool

"""get sha data from github api"""

# to get single commit -- pr head sha
SHA_URL = "https://api.github.com/repos/{slug}/commits/{sha}?page={page}"

# to get diff between pr head (head) and trunk (base)
# OLD SHA FIRST, NEW SHA SECOND
COMPARE_URL = "https://api.github.com/repos/{slug}/compare/{base}...{head}?page={page}"


TOKENPOOL = TokenPool()

def query_and_write(url, fpath):
    if not os.path.exists(fpath):
        headers = TOKENPOOL.get_next_token()
        html_response = requests.get(url=url, headers=headers)
        info = json.loads(html_response.text)
        with open(fpath, "w") as outf:
            json.dump(info, outf, indent=2)
        return info
    else:
        with open(fpath, "r") as inf:
            info = json.load(inf)
        return info


def get_sha_data(project, pr_name, build_id, sha):
    # create folder for this build
    build_dir = os.path.join(const.shadir, project, const.SINGLE_DIR, f"{pr_name}_build{build_id}")
    os.makedirs(build_dir, exist_ok=True)

    # download the 1st page first
    page = 1
    github_url = SHA_URL.format(slug=const.PROJECT_SLUG[project], sha=sha, page=page)
    sha_file = os.path.join(build_dir, f"{sha}_page{page}.json")
    info = query_and_write(github_url, sha_file)
        
    # if there are more commits, use pagination
    file_count = len(info["files"]) if "files" in info else 0
    while file_count >= 300:
        page += 1
        github_url = SHA_URL.format(slug=const.PROJECT_SLUG[project], sha=sha, page=page)
        print("file_count", file_count, "querying page", page, github_url)
        sha_file = os.path.join(build_dir, f"{sha}_page{page}.json")
        info = query_and_write(github_url, sha_file)
        file_count = len(info["files"]) if "files" in info else 0
    pass


def run_get_sha_data(project):
    # get the data of a single commit
    # https://docs.github.com/en/rest/commits/commits?apiVersion=2022-11-28#get-a-commit
    os.makedirs(os.path.join(const.shadir, project, const.SINGLE_DIR), exist_ok=True)
    
    # get the pr head sha from builds
    shas = pd.read_csv(os.path.join(const.metadir, project, const.BUILDSTATS_FILE))
    shas = shas[["pr_name", "build_id", "build_head_sha"]].dropna().values.tolist()
    print("#shas", len(shas), project)
    for index, (pr_name, build_id, sha) in enumerate(shas):
        print("processing", project, index, pr_name, build_id, sha)
        get_sha_data(project, pr_name, build_id, sha)


def compare_two_shas(project, pr_name, build_id, base, head):
    # create folder for this build
    build_dir = os.path.join(const.shadir, project, const.COMPARE_DIR, f"{pr_name}_build{build_id}")
    os.makedirs(build_dir, exist_ok=True)

    # download the 1st page first
    page = 1
    github_url = COMPARE_URL.format(slug=const.PROJECT_SLUG[project], base=base, head=head, page=page)
    sha_file = os.path.join(build_dir, f"{base}_{head}_page{page}.json")
    info = query_and_write(github_url, sha_file)
        
    # if there are more commits, use pagination
    total_commits = (info["total_commits"] - len(info["commits"])) if "commits" in info else 0
    while total_commits > 0:
        page += 1
        github_url = COMPARE_URL.format(slug=const.PROJECT_SLUG[project], base=base, head=head, page=page)
        print("total commits remains", total_commits, "querying page", page, github_url)
        sha_file = os.path.join(build_dir, f"{base}_{head}_page{page}.json")
        info = query_and_write(github_url, sha_file)
        total_commits = (total_commits - len(info["commits"])) if "commits" in info else 0
    pass


def run_compare_two_shas(project):
    # get the data of comparing two commits
    # https://docs.github.com/en/rest/commits/commits?apiVersion=2022-11-28#compare-two-commits
    os.makedirs(os.path.join(const.shadir, project, const.COMPARE_DIR), exist_ok=True)
    
    # get the pr head sha from builds
    shas = pd.read_csv(os.path.join(const.metadir, project, const.TRUNK_PRHEAD_MAP_FILE))
    shas = shas[["pr_name", "build_id", "build_head_sha", "trunk_sha"]].dropna().values.tolist()
    print("#shas", project, len(shas))
    for index, (pr_name, build_id, prhead, trunk) in enumerate(shas):
        print("processing", project, index, pr_name, build_id, prhead, trunk)
        compare_two_shas(project=project, 
                         pr_name=pr_name, build_id=build_id, 
                         base=trunk, head=prhead)


def get_patch_data(project):
    # create a folder to store patches
    os.makedirs(os.path.join(const.shadir, project, const.PATCH_DIR), exist_ok=True)
    # load all builds
    builds = pd.read_csv(os.path.join(const.metadir, project, const.TRUNK_PRHEAD_MAP_FILE))
    builds = builds[["pr_name", "build_id", "trunk_sha", "build_head_sha"]].dropna().values.tolist()

    for index, (pr_name, build_id, base, head) in enumerate(builds):
        compare_fpath = os.path.join(const.shadir, project, const.COMPARE_DIR, 
                                  f"{pr_name}_build{build_id}", f"{base}_{head}_page1.json")
        patch_fpath = os.path.join(const.shadir, project, const.PATCH_DIR, f"{pr_name}_build{build_id}.patch")
        if not os.path.exists(patch_fpath):
            # if base...head is downloaded
            if os.path.exists(compare_fpath):
                with open(compare_fpath, "r") as f:
                    diff = json.load(f)
                    # if data is valid
                    if "patch_url" in diff:
                        url = diff["patch_url"]
                        print("requesting", project, index, pr_name, build_id, url)
                        try:
                            html_response = requests.get(url=url, headers=const.GENERAL_HEADERS, timeout=30)
                            with open(patch_fpath, "w") as outf:
                                outf.write(html_response.text)
                            print(patch_fpath, "collected")
                        except Exception as e:
                            print(f"ERROR GETTING {url}")


def get_diff_data(project):
    # create a folder to store patches
    os.makedirs(os.path.join(const.shadir, project, const.DIFF_DIR), exist_ok=True)
    # load all builds
    builds = pd.read_csv(os.path.join(const.metadir, project, const.TRUNK_PRHEAD_MAP_FILE))
    builds = builds[["pr_name", "build_id", "trunk_sha", "build_head_sha"]].dropna().values.tolist()

    for index, (pr_name, build_id, base, head) in enumerate(builds):
        compare_fpath = os.path.join(const.shadir, project, const.COMPARE_DIR, 
                                  f"{pr_name}_build{build_id}", f"{base}_{head}_page1.json")
        diff_fpath = os.path.join(const.shadir, project, const.DIFF_DIR, f"{pr_name}_build{build_id}.diff")
        if not os.path.exists(diff_fpath):
            # if base...head is downloaded
            if os.path.exists(compare_fpath):
                with open(compare_fpath, "r") as f:
                    diff = json.load(f)
                    # if data is valid
                    if "diff_url" in diff:
                        url = diff["diff_url"]
                        print("requesting", project, index, pr_name, build_id, url)
                        try:
                            html_response = requests.get(url=url, headers=const.GENERAL_HEADERS, timeout=30)
                            with open(diff_fpath, "w") as outf:
                                outf.write(html_response.text)
                            print(diff_fpath, "collected")
                        except Exception as e:
                            print(f"ERROR GETTING {url}")

if __name__ == "__main__":
    # TOKENPOOL.check_limits()
    for project in const.PROJECTS:
        # run_get_sha_data(project)
        # get_patch_data(project)
        run_compare_two_shas(project)
        get_diff_data(project)
