import os
import sys
import numpy as np

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import eval_const
import eval_utils


# ------------ APTD, APTDc ------------
"""
Each metric has 4 variates, because each cause type (fault, or fix) can have 2 mappings
In total, there are 8 metric implementations

all_to_one: all transitions are due to the same root cause, denoted as same*
    i.e., FFMAP_S in "Evaluating Test-Suite Reduction in Real Software Evolution"
one_to_one: all transitions are due to a unique root cause, denoted as unique*
    i.e., FFMAP_U in "Evaluating Test-Suite Reduction in Real Software Evolution"
"""


def is_pass_to_fail(test):
    if test.last_outcome == eval_const.PASS and test.outcome == eval_const.FAIL:
        return True
    return False


def is_fail_to_pass(test):
    if test.last_outcome == eval_const.FAIL and test.outcome == eval_const.PASS:
        return True
    return False


def add_TF(TFis, pos, mapping):
    if mapping == "sameBug":
        if len(TFis["Bug"]) == 0:
            TFis["Bug"].append(pos)
    elif mapping == "uniqueBug":
        TFis["Bug"].append(pos)
    elif mapping == "sameFix":
        if len(TFis["Fix"]) == 0:
            TFis["Fix"].append(pos)
    elif mapping == "uniqueFix":
        TFis["Fix"].append(pos)
    return TFis

def convert_TFis_to_list(TFis):
    ret = []
    for k, v in TFis.items():
        ret += v
    return ret

class TransDetectionMetric:
    def __init__(self, tests, bug_mapping, fix_mapping, 
                 ts_duration, num_pass_to_fail, num_fail_to_pass):
        self.tests = tests
        self.num_tests = len(tests)
        self.ts_duration = ts_duration
        self.num_trans_tests = num_pass_to_fail + num_fail_to_pass
        self.num_trans_causes = self.count_num_trans_causes(
            bug_mapping, fix_mapping, num_pass_to_fail, num_fail_to_pass)
        self.TFis = self.compute_TFis(bug_mapping, fix_mapping)


    def count_num_trans_causes(
            self, bug_mapping, fix_mapping, num_pass_to_fail, num_fail_to_pass):
        if bug_mapping == "sameBug" and fix_mapping == "sameFix":
            # measure effectiveness on detecting the 1st FtP and/or the 1st PtF
            # in case one type of the transition is not presented
            return min(num_pass_to_fail, 1) + min(num_fail_to_pass, 1)
        elif bug_mapping == "sameBug" and fix_mapping == "uniqueFix":
            return 1 + num_fail_to_pass
        elif bug_mapping == "uniqueBug" and fix_mapping == "sameFix":
            return num_pass_to_fail + 1
        elif bug_mapping == "uniqueBug" and fix_mapping == "uniqueFix":
            return num_pass_to_fail + num_fail_to_pass

    def compute_TFis(self, bug_mapping, fix_mapping):
        TFis = {"Bug": [], "Fix": []}
        for pos, test in enumerate(self.tests):
            if is_fail_to_pass(test):
                # detect fail to pass due to fix
                TFis = add_TF(TFis, pos + 1, fix_mapping)
            elif is_pass_to_fail(test):
                # detect pass to fail due to fault
                TFis = add_TF(TFis, pos + 1, bug_mapping)
        # print(bug_mapping, fix_mapping, "num_trans", num_trans, "TFis", TFis)
        TFis = convert_TFis_to_list(TFis)
        return TFis

    def APTD(self):
        # for test suite that dont have transition test, return nan
        if self.num_trans_tests <= 0:
            return np.nan
        
        ret = sum(self.TFis) / (self.num_trans_causes * self.num_tests)
        ret = 1 - ret + (1 / (2 * self.num_tests))
        return ret


    def APTDc(self):
        # for test suite that dont have transition test, return nan
        if self.num_trans_tests <= 0:
            return np.nan

        # compute cost for each detected transition
        TF_costs = []
        for pos in self.TFis:
            TF_costs.append(sum(self.ts_duration[pos - 1:]) - (self.ts_duration[pos - 1] / 2))

        worst_case_cost = self.num_trans_causes * sum(self.ts_duration)
        return sum(TF_costs) / worst_case_cost


# ------------ APFD, APFDc ------------

"""each metric has two variate, one per mapping"""


def has_fail_tests(tests):
    failed = [1 for t in tests if t.outcome == eval_const.FAIL]
    if len(failed) > 0:
        return True
    return False


class FaultDetectionMetric:
    def __init__(self, tests, bug_mapping, ts_duration, num_fail_tests):
        self.tests = tests
        self.num_tests = len(tests)
        self.ts_duration = ts_duration
        self.num_fail_tests = num_fail_tests
        self.num_bugs = self.count_num_bugs(bug_mapping)
        self.TFis = self.get_TFis(bug_mapping)
    
    def count_num_bugs(self, bug_mapping):
        if bug_mapping == "uniqueBug":
            num_bugs = self.num_fail_tests
        else:
            num_bugs = 1
        return num_bugs

    def get_TFis(self, bug_mapping):
        TFis = {"Bug": [], "Fix": []}
        for pos, test in enumerate(self.tests):
            if test.outcome == eval_const.FAIL:
                TFis = add_TF(TFis, pos + 1, bug_mapping)
        TFis = convert_TFis_to_list(TFis)    
        return TFis

    def APFD(self):
        # for test suite that dont have failed tests, return nan
        if self.num_fail_tests <= 0:
            return np.nan
        
        ret = sum(self.TFis) / (self.num_bugs * self.num_tests)
        ret = 1 - ret + (1 / (2 * self.num_tests))
        return ret

    def APFDc(self):
        # for test suite that dont have failed bugs, return nan
        if self.num_fail_tests <= 0:
            return np.nan

        # compute cost for each detected transition
        TF_costs = []
        for pos in self.TFis:
            TF_costs.append(sum(self.ts_duration[pos - 1:]) - (self.ts_duration[pos - 1] / 2))

        worst_case_cost = self.num_bugs * sum(self.ts_duration)
        return sum(TF_costs) / worst_case_cost


def other_metric(tests_for_fail):
    # time to first fail
    ttff = 0
    
    # time to all fail
    ttaf = 0
    
    # num test to first fail
    ntff = 0

    # num test to all fail
    ntaf = 0

    total_time = 0
    total_test = 0
    detected = 0
    for t in tests_for_fail:
        if t.outcome == eval_const.FAIL:
            if  detected == 0:
                ttff += t.duration
                ntff += 1
            ttaf += t.duration
            ntaf += 1
            detected += 1
        total_test += 1
        total_time += t.duration
    return ttff, ttaf, ntff, ntaf, total_time, total_test


def compute_metrics(tests, filtered_failed_tests=set(), filtered_trans_tests=set()):
    values = {}

    # compute APFD(c)
    bug_mappings = ["sameBug", "uniqueBug"]
    tests_for_fail = [t for t in tests if t.name not in filtered_failed_tests]
    ts_duration, num_fail_tests = [], 0
    for t in tests_for_fail:
        ts_duration.append(t.duration)
        if t.outcome == eval_const.FAIL:
            num_fail_tests += 1
    for bug_mapping in bug_mappings:
        fault_metric = FaultDetectionMetric(
            tests=tests_for_fail, bug_mapping=bug_mapping, 
            ts_duration=ts_duration, num_fail_tests=num_fail_tests)
        values[f"APFD_{bug_mapping}"] = fault_metric.APFD()
        values[f"APFDc_{bug_mapping}"] = fault_metric.APFDc()
    
    # compute APTD(c)
    fix_mappings = ["sameFix", "uniqueFix"]
    tests_for_trans = [t for t in tests if t.name not in filtered_trans_tests]
    ts_duration, num_pass_to_fail, num_fail_to_pass = [], 0, 0
    for t in tests_for_trans:
        ts_duration.append(t.duration)
        if is_pass_to_fail(t):
            num_pass_to_fail += 1
        if is_fail_to_pass(t):
            num_fail_to_pass += 1
    for bug_mapping in bug_mappings:
        for fix_mapping in fix_mappings:
            trans_metric = TransDetectionMetric(
                tests=tests_for_trans, bug_mapping=bug_mapping, 
                fix_mapping=fix_mapping, ts_duration=ts_duration, 
                num_pass_to_fail=num_pass_to_fail, num_fail_to_pass=num_fail_to_pass)
            values[f"APTD_{bug_mapping}_{fix_mapping}"] = trans_metric.APTD()
            values[f"APTDc_{bug_mapping}_{fix_mapping}"] = trans_metric.APTDc()

    ttff, ttaf, ntff, ntaf, totaltime, totaltest = other_metric(tests_for_fail)
    values["TTFF"] = ttff
    values["TTAF"] = ttaf
    values["NTFF"] = ntff
    values["NTAF"] = ntaf
    values["TotalTime"] = totaltime
    values["TotalTest"] = totaltest

    return values


def test_cases():
    tests = [
        eval_utils.Test("a", 1, 1, 0), # fail, trans
        eval_utils.Test("b", 2, 0, 1), # pass, trans
        eval_utils.Test("c", 4, 0, 0),
        eval_utils.Test("d", 3, 1, 0), # fail, trans
        eval_utils.Test("e", 2, 0, 1), # pass, trans
        ]
    for k, v in compute_metrics(tests).items():
        print(k, v)
    
if __name__ == "__main__":
    test_cases()
    pass