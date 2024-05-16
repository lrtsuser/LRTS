import sys
import os
import json
import subprocess
import requests

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..", "")
sys.path.append(parent_dir)
import const
from token_pool import TokenPool

TOKENPOOL = TokenPool()

"""collect flaky test from github"""

# case in-sensitive
keywords = ["flaky"]
# create folder for flaky test data collection
for project in const.PROJECTS:
    os.makedirs(os.path.join("data", project), exist_ok=True)

def search_repo():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    for project in const.PROJECTS:
        print(project)
        os.chdir(f"../evaluation/information_retrieval/repo/{project}_repo")
        outputs = ""
        for k in keywords:
            try:
                outputs += subprocess.check_output(f"grep -rli \"{k}\"", shell=True, stderr=subprocess.STDOUT).decode("utf-8")            
                outputs += "\n"
            except:
                pass
        os.chdir(current_dir)
        with open(f"data/{project}/repo_grep_search.txt", "w") as f:
            f.write(outputs)


def search_issue(project):
    # https://api.github.com/search/issues?q=flaky%20repo:apache/tvm&per_page=100&page=1
    url = "https://api.github.com/search/issues?q=flaky%20repo:{slug}&per_page=100&page={page}"
    # get the first page
    headers = TOKENPOOL.get_next_token()
    page = 1
    github_url = url.format(slug=const.PROJECT_SLUG[project], page=page)
    html_response = requests.get(url=github_url, headers=headers)
    info = json.loads(html_response.text)
    with open(f"data/{project}/github_issue_page{page}.json", "w") as outf:
        json.dump(info, outf, indent=2)
    
    # get other pages
    total_count = info["total_count"]
    obtained = len(info["items"])
    total_count -= obtained
    while total_count > 0:
        page += 1
        github_url = url.format(slug=const.PROJECT_SLUG[project], page=page)
        html_response = requests.get(url=github_url, headers=headers)
        info = json.loads(html_response.text)
        with open(f"data/{project}/github_issue_page{page}.json", "w") as outf:
            json.dump(info, outf, indent=2)
        obtained = len(info["items"])
        total_count -= obtained
    pass

if __name__ == "__main__":
    pass