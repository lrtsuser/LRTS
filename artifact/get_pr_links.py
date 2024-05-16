import requests
import json
import os
from datetime import datetime, date
import glob

import const

# Headers to mimic the browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}


def get_pr_links(project):
    # create folder if not exists
    prlinks_dir = os.path.join(const.metadir, project, const.PRLINKS)
    os.makedirs(prlinks_dir, exist_ok=True)
    
    # store links into json by date
    html_response = requests.get(url=const.PROJECT_URLS[project], headers=headers)
    today = datetime.today().strftime('%Y-%m-%d')
    prs_outf = f"{prlinks_dir}/{today}.json"
    if not os.path.exists(prs_outf):
        with open(prs_outf, "w") as outf:
            info = json.loads(html_response.text)
            json.dump(info, outf, indent=2)
        print("dump " + prs_outf)


def get_all_prs(project):
    # get all pr files by date
    prlinks_dir = os.path.join(const.metadir, project, const.PRLINKS)
    pr_files = glob.glob(os.path.join(prlinks_dir, "*.json"))
    print("#files", project, len(pr_files))
    
    # collect all pr links from all files
    ret = {}
    for pr_file in pr_files:
        prs = json.load(open(pr_file, "r"))["jobs"]
        for pr in prs:
            if pr["name"] not in ret:
                ret[pr["name"]] = pr["url"]
    print("#prs", project, len(ret))
    return ret


if __name__ == "__main__":
    for project in const.PROJECTS:
        get_pr_links(project)
    pass