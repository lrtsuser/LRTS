import numpy as np
import os
import sys

script_dir = os.path.dirname(__file__)
main_dir = os.path.join(script_dir, "..", "..")
eval_dir = os.path.join(script_dir, "..")
sys.path.append(main_dir)
sys.path.append(eval_dir)


import eval_const
import eval_metric


def failcount(result, sc=None):
    """the number of failed test cases"""
    return float(result[0])


def timerank(result, tests):
    """
    return a list of rewards, ordered by the original, unprioritized test order
    """
    if result[0] == 0:
        return 0.0

    total = result[0]
    # rank_idx are the index of the failed testcases in this test suite run
    rank_idx = np.array(result[-1])-1
    no_scheduled = len(tests)

    rewards = np.zeros(no_scheduled)
    rewards[rank_idx] = 1
    rewards = np.cumsum(rewards)  # Rewards for passed testcases
    rewards[rank_idx] = total  # Rewards for failed testcases

    return rewards


def tcfail(result, tests):
    """the test case's verdict as each test case's individual reward."""
    if result[0] == 0:
        return 0.0

    rank_idx = np.array(result[-1])-1
    no_scheduled = len(tests)

    rewards = np.zeros(no_scheduled)
    rewards[rank_idx] = 1

    return rewards
