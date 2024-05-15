import pandas as pd
import os
import sys
import time
import random
import multiprocessing as mp
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.preprocessing import MinMaxScaler
import pickle
import gzip
import json

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "evaluation")
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import eval_const
import eval_main

N_SEEDS = 10

random.seed(10)

for project in const.PROJECTS:
    os.makedirs(os.path.join(eval_const.mldir, project), exist_ok=True)


def display_split_statistics(project, training_set, testing_set):
    num_train_fail = len(training_set[training_set["num_fail_class"] > 0])
    num_test_fail = len(testing_set[testing_set["num_fail_class"] > 0])
    print(project, 
    "#Training Fail", num_train_fail, 
    "#Testing Fail", num_test_fail, 
    # "%FAIL IN TRAINING / ALL", round(100 * (num_train_fail / (num_test_fail + num_train_fail)), 2)
    )

def get_train_test_split(split=0.75):
    # split is relative all builds
    df = pd.read_csv(os.path.join(const.metadir, const.DATASET_FILE))
    for project in const.PROJECTS:
        training_sets, testing_sets = [], []
        project_df = df[df["project"] == project]
        print("\n" + project, "Full Project Size", len(project_df))
        # collect stages per project
        stages = set(project_df["stage_id"].values.tolist())
        # in each stage, get 75% of the builds as training split
        for stage in stages:
            stage_df = project_df[project_df["stage_id"] == stage].copy().reset_index(drop=True)
            split_index = int(split * len(stage_df))
            print(project, stage, "Full Stage Size", len(stage_df), "Split Index", split_index)
            training_set = stage_df.iloc[:split_index]
            testing_set = stage_df.iloc[split_index:]
            
            display_split_statistics(project, training_set, testing_set)
            training_sets.append(training_set)
            testing_sets.append(testing_set)
        
        training_sets = pd.concat(training_sets, axis=0)
        testing_sets = pd.concat(testing_sets, axis=0)
        print(f"Training, Testing Set Size for {project} are {len(training_sets)}, {len(testing_sets)}")
        training_sets.to_csv(os.path.join(eval_const.mldir, project, eval_const.ML_TRAINING_SET), index=False)
        testing_sets.to_csv(os.path.join(eval_const.mldir, project, eval_const.ML_TESTING_SET), index=False)


def get_stage_id_enums(df):
    stage_ids = set(df["stage_id"].values.tolist())
    return {stage: index for index, stage in enumerate(sorted(stage_ids))}


def get_ml_dataset(project):
    """
    get the merged features csv for each test run
    F1: 
    - Failure count, Last failure, Transition count, Last transition, Avg. test duration
    F2: 
    - Max. (test, file)-failure freq., Max. (test, file)-failure freq. (rel.), 
    - Max. (test, file)-transition freq., Max. (test, file)-transition freq. (rel.) 
    F3:
    - Min. file path distance, Max. file path token similarity, Min. file name distance
    F4:
    - Distinct authors, Changeset cardinality, Amount of commits, Distinct file extensions
    Additional:
    - Stage ID (the same test testing the same change under different stage (JDK 8 vs 11) may have different results)
    """
    # gather features to build ml dataset
    df = pd.read_csv(os.path.join(const.metadir, const.DATASET_FILE))
    df = df[df["project"] == project]
    stage_id_enums = get_stage_id_enums(df)
    df = df[["pr_name", "build_id", "stage_id"]].values.tolist()

    for index, (pr_name, build_id, stage_id) in enumerate(df):
        print("processing", project, index, pr_name, build_id, stage_id)
        build_dir = os.path.join(eval_const.feadir, project, f"{pr_name}_build{build_id}")
        build_stage_dir = os.path.join(build_dir, "stage_" + stage_id)
        f1 = pd.read_csv(os.path.join(build_stage_dir, eval_const.HIST_FILE))
        f1 = f1[["testclass", "failure_count", "last_failure", "transition_count", "last_transition", "average_duration"]]
        f2 = pd.read_csv(os.path.join(build_stage_dir, eval_const.TF_HIST_FILE))
        f34 = pd.read_csv(os.path.join(build_dir, eval_const.CHANGEFEA_FILE))
        outcome = pd.read_csv(os.path.join(
            eval_const.trdir, project, f"{pr_name}_build{build_id}", "stage_" + stage_id, eval_const.TEST_CLASS_CSV))
        outcome = outcome[["testclass", "outcome"]]
        
        merged = pd.merge(f1, f2, "inner", "testclass")
        merged = pd.merge(merged, f34, "inner", "testclass")
        merged = pd.merge(merged, outcome, "inner", "testclass")
        merged.insert(0, "stage_id_enum", [stage_id_enums[stage_id]] * len(merged))

        merged.to_csv(os.path.join(build_stage_dir, eval_const.MLFEATURE_FILE), index=False)


def get_ml_training_dataset(project):
    # gather training features to build training dataset
    df = pd.read_csv(os.path.join(eval_const.mldir, project, eval_const.ML_TRAINING_SET))
    df = df[["pr_name", "build_id", "stage_id"]].values.tolist()

    for index, (pr_name, build_id, stage_id) in enumerate(df):
        print("processing", project, index, pr_name, build_id, stage_id)
        data = pd.read_csv(os.path.join(
            eval_const.feadir, project, f"{pr_name}_build{build_id}", "stage_" + stage_id, eval_const.MLFEATURE_FILE))
        # remove useless columns to save space
        # data.insert(0, "pr_name", pr_name)
        # data.insert(1, "build_id", build_id)
        # data.insert(2, "stage_id", stage_id)
        data = data.drop(columns=["testclass"])

        if index == 0:
            data.to_csv(os.path.join(
                eval_const.mldir, project, eval_const.ML_TRAINING_DATA), index=False)
        else:
            data.to_csv(os.path.join(
                eval_const.mldir, project, eval_const.ML_TRAINING_DATA),
                mode="a", index=False, header=False)


def train_ml_model(project, scale=True):
    os.makedirs(os.path.join(eval_const.mldir, project, eval_const.ML_MODEL_DIR), exist_ok=True)
    print("loading data for", project)
    data = pd.read_csv(os.path.join(eval_const.mldir, project, eval_const.ML_TRAINING_DATA))
    Y = data["outcome"]
    X = data.drop(columns=["outcome"])

    # for each feature set
    for feature_set, feature_names in eval_const.ML_FEATURE_SETS.items():
        # train 10 models with different random state
        print("processing", project, feature_set, feature_names)
        sys.stdout.flush()
        for i in range(N_SEEDS):
            start = time.time()
            X_subset = X[feature_names]
            if scale:
                scaler = MinMaxScaler()
                X_subset = scaler.fit_transform(X_subset)
            header = "scale" if scale else "noscale"

            # clf = HistGradientBoostingClassifier(
            #     learning_rate=0.1,
            #     random_state=i,
            # ).fit(X_subset, Y)
            # score = clf.score(X_subset, Y)
            # print("cls", "seed", i, "training accuracy", score, "took", time.time() - start)
            # with open(os.path.join(eval_const.mldir, project, "model", f"{header}_cls_{feature_set}_seed{i}.pkl"), "wb") as f:
            #     pickle.dump(clf, f)

            reg = HistGradientBoostingRegressor(
                learning_rate=0.1,
                random_state=i,
            ).fit(X_subset, Y)
            score = reg.score(X_subset, Y)
            print("reg", "seed", i, "training accuracy", score, "took", time.time() - start)
            sys.stdout.flush()
            model_file_path = os.path.join(eval_const.mldir, project, eval_const.ML_MODEL_DIR, f"{header}_reg_{feature_set}_seed{i}.pkl")
            with open(model_file_path, "wb") as f:
                pickle.dump(reg, f)


def predict_prob_helper(project, pr_name, build_id, stage_id):
    print("processing", project, pr_name, build_id, stage_id)
    sys.stdout.flush()
    # load test result of this build
    input_dir = os.path.join(
        eval_const.feadir, project, f"{pr_name}_build{build_id}", "stage_" + stage_id)
    input_path = os.path.join(input_dir, eval_const.MLFEATURE_FILE)
    df = pd.read_csv(input_path)
    testnames = df["testclass"].values.tolist()

    # make prediction using models of 10 different seeds times 5 different feature sets
    output_dir = os.path.join(
        eval_const.mldir, project, "prediction", f"{pr_name}_build{build_id}", "stage_" + stage_id)
    os.makedirs(output_dir, exist_ok=True)
    for feature_set_name in eval_const.ML_FEATURE_SETS:
        for seed in range(N_SEEDS):
            # load ml model of this seed
            model_path = os.path.join(
                eval_const.mldir, project, eval_const.ML_MODEL_DIR, f"scale_reg_{feature_set_name}_seed{seed}.pkl")
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            # preprocessing features
            X = df[eval_const.ML_FEATURE_SETS[feature_set_name]]
            scaler = MinMaxScaler()
            X = scaler.fit_transform(X)
            # predict
            # probs = model.predict_proba(X).tolist()
            # probs = [x[0] if max(x) == x[0] else x[1] for x in probs]
            probs = model.predict(X).tolist()
            output = {k: v for k, v in zip(testnames, probs)}
            output_path = os.path.join(output_dir, eval_const.ML_FILE.format(feature_set_name, seed))
            with gzip.open(output_path, "wt") as f:
                json.dump(output, f)


def predict_prob(project):
    """perform prediction on testing data"""
    # load to be predicted builds
    df = pd.read_csv(const.DATASET_FILE)
    df = df[df["project"] == project]
    # predict only failed or transitioned builds in testing split
    df = eval_main.filter_builds(df, [])
    df = eval_main.get_testing_split(project, df)
    df = df[["project", "pr_name", "build_id", "stage_id"]].values.tolist()
    print("project and #builds to be predicted", project, len(df))
    sys.stdout.flush()
    pool = mp.Pool(mp.cpu_count())
    pool.starmap(predict_prob_helper, df)


if __name__ == "__main__":
    # # split the builds into training and testing
    # get_train_test_split()
    # get ml features per build, aggregrate over builds to get dataset
    # for project in const.PROJECTS:
    #     get_ml_dataset(project)
    #     get_ml_training_dataset(project)
    # # train models of 10 seeds times 5 feature sets per project on the training split
    # for project in const.PROJECTS:
    #     train_ml_model(project)
    # predict probs with all trained models on the testing split
    for project in const.PROJECTS:
        predict_prob(project)
