import datetime
import numpy as np
import os.path
import random
import pandas as pd
import sys
import gzip
import json

script_dir = os.path.dirname(__file__)
main_dir = os.path.join(script_dir, "..", "..")
eval_dir = os.path.join(script_dir, "..")
sys.path.append(main_dir)
sys.path.append(eval_dir)


import eval_const


rand = random.Random(10)


DEFAULT_NO_SCENARIOS = 1000
DEFAULT_NO_ACTIONS = 100
# DEFAULT_HISTORY_LENGTH = 5
DEFAULT_HISTORY_LENGTH = 10
DEFAULT_STATE_SIZE = DEFAULT_HISTORY_LENGTH + 1
DEFAULT_LEARNING_RATE = 0.05
DEFAULT_EPSILON = 0.2
DEFAULT_DUMP_INTERVAL = 100
DEFAULT_VALIDATION_INTERVAL = 100
DEFAULT_PRINT_LOG = False
DEFAULT_PLOT_GRAPHS = False
DEFAULT_NO_HIDDEN_NODES = (12, 12, )
DEFAULT_TODAY = datetime.datetime.today()


def preprocess_continuous(state, scenario_metadata, histlen):
    if scenario_metadata['maxExecTime'] > scenario_metadata['minExecTime']:
        time_since = (scenario_metadata['maxExecTime'] - state['LastRun']) / (
            scenario_metadata['maxExecTime'] - scenario_metadata['minExecTime'])
    else:
        time_since = 0

    history = [1 if res else 0 for res in state['LastResults'][0:histlen]]

    if len(history) < histlen:
        history.extend([1] * (histlen - len(history)))

    row = [
        state['Duration'] / scenario_metadata['totalTime'], # test duration / test suite duration
        time_since # the time it was last executed
    ]
    row.extend(history)

    return tuple(row)


def preprocess_discrete(state, scenario_metadata, histlen):
    if scenario_metadata['maxDuration'] > scenario_metadata['minDuration']:
        # (longest test duration in this suite - this test duration) / (longest - shortest)
        duration = (scenario_metadata['maxDuration'] - state['Duration']) / (
            scenario_metadata['maxDuration'] - scenario_metadata['minDuration'])
    else:
        duration = 0

    if duration > 0.66:
        duration_group = 2
    elif duration > 0.33:
        duration_group = 1
    else:
        duration_group = 0

    if scenario_metadata['maxExecTime'] > scenario_metadata['minExecTime']:
        time_since = (scenario_metadata['maxExecTime'] - state['LastRun']) / (
            scenario_metadata['maxExecTime'] - scenario_metadata['minExecTime'])
    else:
        time_since = 0

    if time_since > 0.66:
        time_group = 2
    elif time_since > 0.33:
        time_group = 1
    else:
        time_group = 0

    history = [1 if res else 0 for res in state['LastResults'][0:histlen]]

    if len(history) < histlen:
        history.extend([1] * (histlen - len(history)))

    row = [
        duration_group,
        time_group
    ]
    row.extend(history)

    return tuple(row)


def get_build_metadata(tests, history, build_timestamp):
    # execTimes are dates of last run of each test, if not exist, use a random value
    # durations are approximated duration of each test, if not exist, use a random value
    execTimes, durations = [], []
    for test in tests:
        name = test["Name"]
        if name in history:
            last_durations = history[name]["LastDurations"]
            approx_duration = sum(last_durations) / len(last_durations)
            last_run = history[name]["LastRun"]
        else:
            approx_duration = rand.randint(180, 1200)
            last_run = build_timestamp - 60 * 60 * rand.randint(1, 24)
        
        durations.append(approx_duration)
        execTimes.append(last_run)

        # update test data as well
        test["LastRun"] = last_run
        test["LastResults"] = history[name]["LastResults"] if name in history else []
        test["Duration"] = approx_duration

    metadata = {
        'totalTime': sum(durations), # max time limit allow for the test suite run, sum of test durations of this build
        'minExecTime': min(execTimes), # oldest date of LastRun of a test in this suite
        'maxExecTime': max(execTimes), # most recent date of LastRun of a test in this suite
        'minDuration': min(durations), # smallest duration of the tests in this suite
        'maxDuration': max(durations)
    }

    return metadata


def process_build(agent, tests, preprocess, history, build_timestamp):
    """run prio agent on a build, obtain priorization result"""

    # obtain current build metadata based on history
    # obtain test state
    build_metadata = get_build_metadata(tests, history, build_timestamp)
    
    # run tcp: compute ranking of testcases one by one
    for test in tests:
        # Build input vector: preprocess the observation
        x = preprocess(test, build_metadata, agent.histlen)
        action = agent.get_action(x)
        test['CalcPrio'] = action  # Store prioritization
    # larger CalcPrio means prioritized
    sorted_tests = sorted(tests, key=lambda x: (x['CalcPrio'], rand.random()), reverse=True)

    # compute metrics
    # original: [detected_failures, undetected_failures, ttf, napfd, recall, avg_precision, detection_ranks]
    detection_ranks = []
    detected_failures = 0
    for idx, test in enumerate(sorted_tests):
        if test["Verdict"] == 1:
            detection_ranks.append(idx+1)
            detected_failures += 1

    return [detected_failures, detection_ranks], sorted_tests


class PrioLearning(object):
    def __init__(self, agent, reward_function, preprocess_function, build_df, stage_id):
        self.agent = agent
        self.reward_function = reward_function
        self.preprocess_function = preprocess_function
        self.build_df = build_df
        self.stage_id = stage_id
        self.history = {}


    def update_history(self, tests, build_timestamp):
        # update each test's last run date, duration, and outcomes
        for test in tests:
            name, duration, verdict = test["Name"], test["CurrentDuration"], test["Verdict"]
            if name not in self.history:
                self.history[name] = {
                    "LastRun": None,
                    "LastDurations": [],
                    "LastResults": [],
                }
            self.history[name]["LastRun"] = build_timestamp
            self.history[name]["LastDurations"].append(duration)
            self.history[name]["LastResults"].append(verdict)

            # store only window history
            histlen = self.agent.histlen
            self.history[name]["LastDurations"] = self.history[name]["LastDurations"][0:histlen]
            self.history[name]["LastResults"] = self.history[name]["LastResults"][0:histlen]


    def train(self, seed, reward_name):
        # step through oldest to latest build
        self.build_df = self.build_df.sort_values("build_timestamp", ascending=True)

        for idx, build_row in self.build_df.iterrows():
            project = build_row["project"]
            pr_name = build_row["pr_name"]
            build_id = build_row["build_id"]
            build_timestamp = build_row["build_timestamp"]

            # load test results for this build of this stage
            # columns: testclass,duration,outcome
            tests = pd.read_csv(os.path.join(
                eval_const.trdir, project, f"{pr_name}_build{build_id}", "stage_" + self.stage_id, eval_const.TEST_CLASS_CSV))
            tests["duration"] = tests["duration"] + 0.001
            tests = tests.rename(columns={"testclass": "Name", "duration": "CurrentDuration", "outcome": "Verdict"})
            # print(f" evaluating {pr_name}, {build_id}, {len(tests)}")
            # convert each row (test) to a dict
            tests = tests.to_dict(orient="records")

            # run tcp for build, train agent, return sorted tests
            result, sorted_tests = process_build(self.agent, tests, self.preprocess_function, self.history, build_timestamp)
            reward = self.reward_function(result, sorted_tests)
            self.agent.reward(reward)

            # update history
            self.update_history(tests, build_timestamp)

            # save prioritization outcome
            df = pd.DataFrame.from_records(data=sorted_tests)
            df = df[["Name", "CalcPrio"]]
            df = {row["Name"]: row["CalcPrio"] for idx, row in df.iterrows()}
            build_stage_dir = os.path.join(eval_const.rldatadir, project, f"{pr_name}_build{build_id}", "stage_" + self.stage_id)
            output_path = os.path.join(build_stage_dir, eval_const.RL_FILE.format(self.agent.name, reward_name, seed))
            os.makedirs(build_stage_dir, exist_ok=True)
            with gzip.open(output_path, "wt") as f:
                json.dump(df, f)



