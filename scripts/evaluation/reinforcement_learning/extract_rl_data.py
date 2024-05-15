import multiprocessing as mp
import pandas as pd
import os
import sys

script_dir = os.path.dirname(__file__)
main_dir = os.path.join(script_dir, "..", "..")
eval_dir = os.path.join(script_dir, "..")
sys.path.append(main_dir)
sys.path.append(eval_dir)

import const
import agents
import retecs
import reward


N_SEEDS = 10
AGENT_AND_PREPROC_NAMES = [
    ("tableau", "preprocess_discrete"), 
    ("mlpclassifier", "preprocess_continuous")]
REWARD_NAMES = ["failcount", "timerank", "tcfail"]
SEEDS = [x for x in range(N_SEEDS)]

def get_agent_by_name(name):
    agent = None
    if name == "tableau":
        agent = agents.TableauAgent(
            histlen=retecs.DEFAULT_HISTORY_LENGTH, learning_rate=retecs.DEFAULT_LEARNING_RATE,
            state_size=retecs.DEFAULT_STATE_SIZE,
            action_size=retecs.DEFAULT_NO_ACTIONS, epsilon=retecs.DEFAULT_EPSILON)
    elif name == "mlpclassifier":
        agent = agents.NetworkAgent(
            histlen=retecs.DEFAULT_HISTORY_LENGTH, state_size=retecs.DEFAULT_STATE_SIZE, 
            action_size=1,
            hidden_size=retecs.DEFAULT_NO_HIDDEN_NODES)
    return agent


def get_preproc_by_name(name):
    preproc = None
    if name == "preprocess_discrete":
        preproc = retecs.preprocess_discrete
    elif name == "preprocess_continuous":
        preproc = retecs.preprocess_continuous
    return preproc


def get_reward_func_by_name(name):
    reward_func = None
    if name == "failcount":
        reward_func = reward.failcount
    elif name == "timerank":
        reward_func = reward.timerank
    elif name == "tcfail":
        reward_func = reward.tcfail
    return reward_func


def run_rl_on_project_stage(project, stage_id, agent_name, preproc_name, reward_name, seed):
    agent = get_agent_by_name(agent_name)
    reward_fun = get_reward_func_by_name(reward_name)
    preprocessor = get_preproc_by_name(preproc_name)
    
    # load builds of this stage in this project
    stage_df = pd.read_csv(const.OMIN_FILE)
    stage_df = stage_df[(stage_df["project"] == project) & (stage_df["stage_id"] == stage_id)]
    # sort the build from oldest to latest
    stage_df = stage_df.sort_values("build_timestamp", ascending=True)

    rl_learning = retecs.PrioLearning(agent=agent,
                                        reward_function=reward_fun,
                                        preprocess_function=preprocessor,
                                        build_df=stage_df,
                                        stage_id=stage_id)
        
    print(f"running {project}, {stage_id} ({len(stage_df)} builds),", 
          f"{agent_name} ({id(agent)}), {preproc_name} ({id(preprocessor)}),",
          f"{reward_name} ({id(reward_fun)}), rl_learning ({id(rl_learning)}) seed={seed}")
    # this will train and write results into csv
    rl_learning.train(seed=seed, reward_name=reward_name)


def run_rl_on_project(project):
    df = pd.read_csv(const.OMIN_FILE)
    df = df[df["project"] == project]
    
    # each stage/job has a seperate history, hence each stage has a seperate ai agent
    stage_ids = list(set(df["stage_id"].values.tolist()))    
    args = []
    for stage_id in stage_ids:
        for agent_name, preproc_name in AGENT_AND_PREPROC_NAMES:
            for reward_name in REWARD_NAMES:
                for seed in SEEDS:
                    args.append((project, stage_id, agent_name, preproc_name, reward_name, seed))
    
    pool = mp.Pool(mp.cpu_count())
    pool.starmap(run_rl_on_project_stage, args)


if __name__ == "__main__":
    for project in const.PROJECTS:
        run_rl_on_project(project)
    pass