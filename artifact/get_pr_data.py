import os
import glob
import multiprocessing as mp
import numpy as np
import json
import pandas as pd
import requests

import const
from token_pool import TokenPool
import get_pr_links

"""get the pr data for the test report we collected via github api"""

PR_URL = "https://api.github.com/repos/{slug}/pulls/{prid}"

TOKENPOOL = TokenPool()

def download_pr_info(project, pr):
    prid = pr.replace("PR-", "")
    github_url = PR_URL.format(slug=const.PROJECT_SLUG[project], prid=prid)
    pr_file = os.path.join(const.prdir, project, "pr_info", f"{pr}.json")
    if not os.path.exists(pr_file):
        headers = TOKENPOOL.get_next_token()
        html_response = requests.get(url=github_url, headers=headers)
        info = json.loads(html_response.text)
        with open(pr_file, "w") as outf:
            json.dump(info, outf, indent=2)
    pass


def get_pr_data(project):
    # get the trunk sha for each pr head build sha from metadata csv
    prs = get_pr_links.get_all_prs(project)
    prs = list(prs.keys())

    # create a folder to store the data
    os.makedirs(os.path.join(const.prdir, project, "pr_info"), exist_ok=True)

    # processing the test files
    for index, pr in enumerate(prs):
        print("processing", project, index, pr)
        download_pr_info(project, pr)
    pass


if __name__ == "__main__":
    for project in const.PROJECTS:
        get_pr_data(project)
    pass