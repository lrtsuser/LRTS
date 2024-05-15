

import pandas as pd
import json
import os
import sys
import gzip
import multiprocessing as mp
from sklearn.preprocessing import MinMaxScaler
import pickle

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import eval_const

import random
import copy

rand = random.Random(10)

epsilon = 1 / 1000000

def extract_heuristic(df, col):
    # for techniques are order the score ascendingly
    ret = df[["testclass", col]].values.tolist()
    ret = {k: v + epsilon for k, v in ret}
    return ret


class TestPrioritization:
    """
    host a varity of class-level TCP techniques
    each technique consume a list of test objects and returns a re-ordered list
    """
    def __init__(self, tests, project, tcp, pr_name, build_id, stage_id):
        # tests is a list of Test class objects
        self.tests = tests
        self.tcp = tcp
        self.project = project
        self.pr_name = pr_name
        self.build_id = build_id
        self.stage_id = stage_id
        # random or cost breaktie
        self.use_hybrid = False
        self.load_heuristics()


    def run_tcp(self, seed=None):
        if self.tcp == eval_const.RANDOM_TCP:
            return self.random_tcp()
        elif self.tcp.startswith("QTF"):
            return self.qtf_tcp()
        elif self.tcp.startswith("LTF"):
            return self.ltf_tcp()
        elif self.tcp == eval_const.LF_TCP:
            return self.last_failure_tcp()
        elif self.tcp == eval_const.FC_TCP:
            return self.failure_count_tcp()
        elif self.tcp == eval_const.LT_TCP:
            return self.last_transition_tcp()
        elif self.tcp == eval_const.TC_TCP:
            return self.transition_count_tcp()
        elif self.tcp.startswith("IR"):
            return self.ir_tcp()
        elif self.tcp.startswith("TestFile"):
            return self.test_file_co_occurance_tcp()
        elif self.tcp.startswith("ML"):
            return self.ml_tcp(seed)
        elif self.tcp.startswith("RL"):
            return self.rl_tcp(seed)

    def load_heuristics(self):
        feature_dir = os.path.join(eval_const.feadir, self.project, f"{self.pr_name}_build{self.build_id}")
        stage_feature_dir = os.path.join(feature_dir, "stage_" + self.stage_id)
        
        # check whether it is hybrid break tie
        if self.tcp.startswith("cbt_"):
            self.tcp = self.tcp.replace("cbt_", "")
            self.use_hybrid = True
            df = pd.read_csv(os.path.join(stage_feature_dir, eval_const.HIST_FILE))
            self.hybrid_cost = extract_heuristic(df, "last_duration")
        elif self.tcp.startswith("hbt_"):
            self.tcp = self.tcp.replace("hbt_", "")
            self.use_hybrid = True
            df = pd.read_csv(os.path.join(stage_feature_dir, eval_const.HIST_FILE))
            self.hybrid_cost = extract_heuristic(df, "failure_count")
            # larger fail better, reverse because every algorithm is ascending order
            self.hybrid_cost = {k: 1 / v for k, v in self.hybrid_cost.items()}
        elif self.tcp.startswith("hcbt_"):
            self.tcp = self.tcp.replace("hcbt_", "")
            self.use_hybrid = True
            df = pd.read_csv(os.path.join(stage_feature_dir, eval_const.HIST_FILE))
            hybrid_cost = df[["testclass", "failure_count", "last_duration"]].values.tolist()
            hybrid_cost = [[x[0], x[1] + epsilon, x[2] + epsilon] for x in hybrid_cost]
            # larger fail/time better (smaller time or larger fail), but since it is always ascending, divde
            self.hybrid_cost = {x[0]: 1 / (x[1] / x[2]) for x in hybrid_cost}
            

        # load feature file
        if self.tcp.startswith("IR"):
            ir_file = eval_const.IRSCORE_TFIDF_FILE if self.tcp.endswith("_tfidf") else eval_const.IRSCORE_BM25_FILE
            fpath = os.path.join(feature_dir, ir_file)
        elif self.tcp.startswith("TestFile"):
            fpath = os.path.join(stage_feature_dir, eval_const.TF_HIST_FILE)
        elif self.tcp.startswith("ML"):
            # load data at run_tcp instead to account for different seeds
            return
        elif self.tcp.startswith("RL"):
            # load data at run_tcp instead to account for different seeds
            return
        else:
            fpath = os.path.join(stage_feature_dir, eval_const.HIST_FILE)
        df = pd.read_csv(fpath)

        # read corresponding features
        if self.tcp == eval_const.QTF_TCP:
            self.qtf_duration = extract_heuristic(df, "last_duration")
        elif self.tcp == eval_const.QTF_AVG_TCP:
            self.qtf_duration = extract_heuristic(df, "average_duration")
        elif self.tcp == eval_const.LTF_TCP:
            self.ltf_duration = extract_heuristic(df, "last_duration")
        elif self.tcp == eval_const.LTF_AVG_TCP:
            self.ltf_duration = extract_heuristic(df, "average_duration")
        elif self.tcp == eval_const.LF_TCP:
            self.last_failure = extract_heuristic(df, "last_failure")
        elif self.tcp == eval_const.FC_TCP:
            self.failure_count = extract_heuristic(df, "failure_count")
        elif self.tcp == eval_const.LT_TCP:
            self.last_transition = extract_heuristic(df, "last_transition")
        elif self.tcp == eval_const.TC_TCP:
            self.transition_count = extract_heuristic(df, "transition_count")
        elif "IR_0Context" in self.tcp:
            self.ir_score = extract_heuristic(df, "zero_context")
        elif "IR_GitDiff" in self.tcp:
            self.ir_score = extract_heuristic(df, "git_diff")
        elif "IR_WholeFile" in self.tcp:
            self.ir_score = extract_heuristic(df, "whole_file")
        elif self.tcp == eval_const.TF_FAILFREQ_TCP:
            self.tf_freq = extract_heuristic(df, "max_test_file_failure_frequency")
        elif self.tcp == eval_const.TF_FAILFREQ_REL_TCP:
            self.tf_freq = extract_heuristic(df, "max_test_file_failure_frequency_relative")
        elif self.tcp == eval_const.TF_TRANSFREQ_TCP:
            self.tf_freq = extract_heuristic(df, "max_test_file_transition_frequency")
        elif self.tcp == eval_const.TF_TRANSFREQ_REL_TCP:
            self.tf_freq = extract_heuristic(df, "max_test_file_transition_frequency_relative")


    def random_tcp(self):
        tests = copy.deepcopy(self.tests)
        for idx, t in enumerate(tests):
            tests[idx].update_scores(
                base_score=self.break_tie(),
                hybrid_score=1,
                tie_score=self.break_tie())
        # reverse=False means ascending
        tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
        return tests

    def qtf_tcp(self):
        """ranking tests in ascending order by the average or last duration"""
        tests = copy.deepcopy(self.tests)
        for idx, t in enumerate(tests):
            tests[idx].update_scores(
                base_score=self.qtf_heuristic(t),
                hybrid_score=self.hybrid_score(t),
                tie_score=self.break_tie())
        # reverse=False means ascending
        tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
        return tests
    
    
    def qtf_heuristic(self, test):
        if test.name in self.qtf_duration:
            return self.qtf_duration[test.name]
        # prioritize new test
        return epsilon
    

    def ltf_tcp(self):
        """ranking tests in descending order by the average or last duration"""
        tests = copy.deepcopy(self.tests)
        for idx, t in enumerate(tests):
            tests[idx].update_scores(
                base_score=1 / self.ltf_heuristic(t),
                hybrid_score=self.hybrid_score(t),
                tie_score=self.break_tie())
        # reverse=False means ascending
        tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
        return tests
    
    
    def ltf_heuristic(self, test):
        if test.name in self.ltf_duration:
            return self.ltf_duration[test.name]
        # prioritize new test
        return epsilon
    
    def last_failure_tcp(self):
        """ranking tests in ascending order by the time (#CI runs) since the last failure"""
        tests = copy.deepcopy(self.tests)
        for idx, t in enumerate(tests):
            tests[idx].update_scores(
                base_score=self.lf_heuristic(t),
                hybrid_score=self.hybrid_score(t),
                tie_score=self.break_tie())
        tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
        return tests

    def lf_heuristic(self, test):
        if test.name in self.last_failure:
            return self.last_failure[test.name]
        # prioritize new test
        return epsilon
    
    def failure_count_tcp(self):
        """ranking tests in descending order by the amount of historical failures"""
        tests = copy.deepcopy(self.tests)
        for idx, t in enumerate(tests):
            tests[idx].update_scores(
                base_score=1 / self.fc_heuristic(t),
                hybrid_score=self.hybrid_score(t),
                tie_score=self.break_tie())
        tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
        # tests.sort(key=lambda t: (self.fc_heuristic(t), self.break_tie()), reverse=True)
        return tests
    
    def fc_heuristic(self, test):
        if test.name in self.failure_count:
            return self.failure_count[test.name]
        # prioritize new test
        return 1e6
    
    def last_transition_tcp(self):
        """ranking tests in ascending order by the time (#CI runs) since the last transition"""
        tests = copy.deepcopy(self.tests)
        for idx, t in enumerate(tests):
            tests[idx].update_scores(
                base_score=self.lt_heuristic(t),
                hybrid_score=self.hybrid_score(t),
                tie_score=self.break_tie())
        tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
        return tests
    
    def lt_heuristic(self, test):
        if test.name in self.last_transition:
            return self.last_transition[test.name]
        # prioritize new test
        return epsilon
    

    def transition_count_tcp(self):
        """ranking tests in descending order by the amount of historical transitions"""
        tests = copy.deepcopy(self.tests)
        for idx, t in enumerate(tests):
            tests[idx].update_scores(
                base_score=1 / self.tc_heuristic(t),
                hybrid_score=self.hybrid_score(t),
                tie_score=self.break_tie())
        tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
        return tests
    
    def tc_heuristic(self, test):
        if test.name in self.transition_count:
            return self.transition_count[test.name]
        # prioritize new test
        return 1e6

    
    def ir_tcp(self):
        """ranking tests in descending order by IR score"""
        tests = copy.deepcopy(self.tests)
        for idx, t in enumerate(tests):
            tests[idx].update_scores(
                base_score=1 / self.ir_heuristic(t),
                hybrid_score=self.hybrid_score(t),
                tie_score=self.break_tie())
        tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
        return tests

    def ir_heuristic(self, test):
        if test.name in self.ir_score:
            return self.ir_score[test.name]
        # deprioritize tests with no ir info
        return epsilon
    

    def test_file_co_occurance_tcp(self):
        """ranking tests in descending order by (test, file) fail/trans frequency"""
        tests = copy.deepcopy(self.tests)
        for idx, t in enumerate(tests):
            tests[idx].update_scores(
                base_score=1 / self.co_occurance_heuristic(t),
                hybrid_score=self.hybrid_score(t),
                tie_score=self.break_tie())
        tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
        return tests
    
    def co_occurance_heuristic(self, test):
        if test.name in self.tf_freq:
            return self.tf_freq[test.name]
        # prioritize new tests
        return 1e6
    

    def ml_tcp(self, seed):
        """ranking tests in descending order by fail likelihood"""
        fpath = os.path.join(
            eval_const.mldir, self.project, "prediction", f"{self.pr_name}_build{self.build_id}", 
            f"stage_{self.stage_id}", f"{self.tcp.lower()}_{seed}.json.gz")
        with gzip.open(fpath, "rt") as f:
            probs = json.load(f)
            ml_scores = {}
            for test, prob in probs.items():
                if prob < 0:
                    ml_scores[test] = 0 + epsilon
                elif prob > 1:
                    ml_scores[test] = 1 + epsilon
                else:
                    ml_scores[test] = prob + epsilon
            # higher score is more likelihood to fail
            tests = copy.deepcopy(self.tests)
            for idx, t in enumerate(tests):
                tests[idx].update_scores(
                    base_score=1 / ml_scores[t.name],
                    hybrid_score=self.hybrid_score(t),
                    tie_score=self.break_tie())
            tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
            return tests
        

    def rl_tcp(self, seed):
        fpath = os.path.join(
            "reinforcement_learning/rl_data", self.project, f"{self.pr_name}_build{self.build_id}",
            f"stage_{self.stage_id}", f"{self.tcp.lower()}_{seed}.json.gz")
        with gzip.open(fpath, "rt") as f:
            rl_scores = json.load(f)
            tests = copy.deepcopy(self.tests)
            for idx, t in enumerate(tests):
                tests[idx].update_scores(
                    base_score=1 / (rl_scores[t.name] + epsilon),
                    hybrid_score=self.hybrid_score(t),
                    tie_score=self.break_tie())
            tests.sort(key=lambda t: (t.prio_score, t.tie_score), reverse=False)
            return tests


    def break_tie(self):
        # default is random
        return rand.uniform(0, 1)
    

    def hybrid_score(self, test):
        if self.use_hybrid:
            if test.name in self.hybrid_cost:
                return self.hybrid_cost[test.name]
            # prioritize test with no hybrid score
            return 0
        return 1
