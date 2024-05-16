import pandas as pd
import glob
import os
import sys
from datetime import datetime
import json

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
sys.path.append(parent_dir)

import const

def convert_time_to_timestamp(s):
    # 30/Jul/18 23:33
    d = datetime.strptime(s, "%d/%b/%y %H:%M")
    ts = datetime.timestamp(d)
    return ts

def get_issue_link(key):
    return f"https://issues.apache.org/jira/browse/{key}"


def extract_test_from_summary(summary):
    # heuristic: extract longest word with the word `test`
    tokens = summary.split()
    # longest_word = tokens[0]
    # for w in tokens:
    #     if len(w) > len(longest_word) and "test" in w.lower():
    #         longest_word = w
    # return longest_word
    tokens_w_test = [x for x in tokens if "test" in x.lower()]
    return tokens_w_test


def get_earliest_build_timestamp(project):
    df = pd.read_csv(const.DATASET_FILE)
    df = df[df["project"] == project]
    ts = df["build_timestamp"].min()
    print("earliest build: ", datetime.fromtimestamp(ts), ts)
    return ts

def is_flaky_issue(issue):
    if "labels" in issue:
        for label in issue["labels"]:
            if "flaky" in label["name"]:
                return True
    return False

def convert_ts_github(s):
    # 2023-07-03T10:25:52Z
    d = datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    ts = datetime.timestamp(d)
    return ts


def clean_issue(project, issue):
    ret = {}
    ret["project"] = project
    ret["flaky tests"] = []
    ret["issue type"] = ";".join([x["name"] for x in issue["labels"]]) if "labels" in issue else None
    ret["issue key"] = issue["number"]
    ret["url"] = issue["html_url"]
    ret["summary"] = issue["title"]
    ret["status"] = issue["state"]
    ret["resolution"] = None
    ret["created"] = issue["created_at"]
    ret["updated"] = issue["updated_at"]
    ret["created_ts"] = convert_ts_github(issue["created_at"])
    ret["updated_ts"] = convert_ts_github(issue["updated_at"])
    ret["inspection_source"] = None
    return ret


def parse_github_issues(project):
    # "project": "activemq",
    # "flaky tests": [
    #   "AdvisoryTests"
    # ],
    # "issue type": "Bug",
    # "issue key": "AMQ-9192",
    # "url": "https://issues.apache.org/jira/browse/AMQ-9192",
    # "summary": "Fix flaky AdvisoryTests causing CI failures",
    # "status": "Resolved",
    # "resolution": "Fixed",
    # "created": "10/Jan/23 11:28",
    # "updated": "11/Jan/23 05:13",
    # "created_ts": 1673378880.0,
    # "updated_ts": 1673442780.0
    print(project)
    files = glob.glob("raw_data/tvm/*.json")
    print("number of issues", len(files))
    issues = []
    for file in files:
        issues += json.load(open(file))["items"]
    print("number of issues", len(issues))
    # keep issues with tag test:flaky
    issues = [x for x in issues if is_flaky_issue(x)]
    print("number of issue after labeled flaky", len(issues))
    # keep close issues only
    issues = [x for x in issues if x["state"] == "closed"]
    print("number of issues after closed", len(issues))
    # remove issue closed before the earilest build in the dataset
    earliest_ts = get_earliest_build_timestamp(project)
    issues = [x for x in issues if convert_ts_github(x["updated_at"]) > earliest_ts]
    print("number of issues after the earliest build", len(issues))
    issues = [clean_issue(project, x) for x in issues]
    return issues


def clean_jira_csv(project, df):
    df.columns= df.columns.str.lower()
    df = df[["issue type", "issue key", "summary", "status", "resolution", "created", "updated"]]
    # keep fixed bug flaky issue only
    df = df[df["resolution"] == "Fixed"]
    # df = df[df["issue type"] == "Bug"]
    print("number of issue resolution==Fixed", len(df))
    # convert time format
    df["created_ts"] = df["created"].apply(lambda x: convert_time_to_timestamp(x))
    df["updated_ts"] = df["updated"].apply(lambda x: convert_time_to_timestamp(x))
    # remove flaky tests fixed before all the builds in the dataset
    earliest_ts = get_earliest_build_timestamp(project)
    df = df[df["updated_ts"] > earliest_ts]
    print("number of issues fixed after the earliest build", len(df))
    return df


def parse_jira_csv(project):
    print(project)
    # Issue Type,Issue key,Issue id,Parent id,Summary,Assignee,Reporter,Priority,Status,Resolution,Created,Updated,Due Date
    # Bug,YARN-8605,13175733,,TestDominantResourceFairnessPolicy.testModWhileSorting is flaky,wilfreds,wilfreds,Minor,Resolved,Fixed,30/Jul/18 23:33,25/Feb/20 23:29,
    filename = glob.glob(os.path.join("raw_data", project, "*.csv"))[0]
    df = pd.read_csv(filename)
    print("number of issues", len(df))
    df = clean_jira_csv(project, df)
    # get issue url
    df.insert(2, "url", df["issue key"].apply(lambda x: get_issue_link(x))) 
    # extract test name
    df.insert(0, "flaky tests", df["summary"].apply(lambda x: extract_test_from_summary(x)))
    df.insert(0, "project", [project] * len(df))
    df["inspection_source"] = None
    df = json.loads(df.to_json(orient="records"))
    return df

if __name__ == "__main__":
    pass