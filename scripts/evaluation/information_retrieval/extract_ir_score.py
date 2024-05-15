import pandas as pd
import os
import sys
import time
import json
import gzip
import multiprocessing as mp

script_dir = os.path.dirname(__file__)
grandparent_dir = os.path.join(script_dir, "..", "..")
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "information_retrieval")
sys.path.append(grandparent_dir)
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const
import ir_const
import eval_const
import extract_ir_body

from ir_utility import low_tokenization, tfidf_model, tfidf_score, bm25_model,  bm25_score

"""
extract data object from the test body file
extract query object from diff body file
tokenize them, put them into bm25 model
"""


def process_testbody_file(testbody_fpath):
    # read body per test, tokenization
    # return [(test, testbody), ...]
    ret = {}
    with gzip.open(testbody_fpath+".gz", "rt", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)
        for test, path_to_body in data.items():
            ret[test] = ""
            for body in path_to_body.values():
                ret[test] += body
    ret = [(k, low_tokenization(v)) for k, v in ret.items()]
    return ret


def process_diffbody_file(diffbody_path, diff_fpath):
    # read diff body, tokenization
    # provide 0 context query, whole context query body
    with gzip.open(diffbody_path+".gz", "rt", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)
        zero_context = " ".join(data["changed_lines"])
        zero_context = low_tokenization(zero_context)
        whole_file = " ".join(data["whole_files"].values())
        whole_file = low_tokenization(whole_file)

    # get diff context query, tokenization
    with open(diff_fpath, "rt", encoding="utf-8", errors="ignore") as f:
        diff = low_tokenization(f.read())
    
    return zero_context, diff, whole_file


def get_bm25_ir_score_per_build(project, index, pr_name, build_id, overwrite=True):
    # file to store ir scores
    feature_build_dir = os.path.join(eval_const.feadir, project, f"{pr_name}_build{build_id}")
    os.makedirs(feature_build_dir, exist_ok=True)
    ir_score_file = os.path.join(feature_build_dir, eval_const.IRSCORE_BM25_FILE)

    # tokenized data
    ir_build_dir = os.path.join(ir_const.irdata_dir, project, f"{pr_name}_build{build_id}")
    tk_ir_object_file = os.path.join(ir_build_dir, ir_const.IROBJ_FILE)
    print("running", project, index, pr_name, build_id)

    if overwrite or not os.path.exists(ir_score_file):
        with gzip.open(tk_ir_object_file + ".gz", "rt") as f:
            ir_data = json.load(f)

        train_model, model_time = bm25_model([x[1] for x in ir_data["data_objects"]])
        zero_context_scores, zero_context_time = bm25_score(train_model, ir_data["zero_context"])
        diff_scores, diff_time = bm25_score(train_model, ir_data["diff"])
        whole_file_scores, whole_file_time = bm25_score(train_model, ir_data["whole_file"])
        
        tests = [x[0] for x in ir_data["data_objects"]]
        df = pd.DataFrame({
            "testclass": tests,
            "zero_context": zero_context_scores,
            "git_diff": diff_scores,
            "whole_file": whole_file_scores,
        })

        df.to_csv(ir_score_file, index=False)
        print("processing", project, index, pr_name, build_id, 
              "BM25 time(second)", model_time, zero_context_time, diff_time, whole_file_time,
              "writing", ir_score_file)
        sys.stdout.flush()


def get_tfidf_ir_score_per_build(project, index, pr_name, build_id, overwrite=True):
    # file to store ir scores
    feature_build_dir = os.path.join(eval_const.feadir, project, f"{pr_name}_build{build_id}")
    os.makedirs(feature_build_dir, exist_ok=True)
    ir_score_file = os.path.join(feature_build_dir, eval_const.IRSCORE_TFIDF_FILE)

    # tokenized data
    ir_build_dir = os.path.join(ir_const.irdata_dir, project, f"{pr_name}_build{build_id}")
    tk_ir_object_file = os.path.join(ir_build_dir, ir_const.IROBJ_FILE)
    print("running", project, index, pr_name, build_id)

    if overwrite or not os.path.exists(ir_score_file):
        with gzip.open(tk_ir_object_file + ".gz", "rt") as f:
            ir_data = json.load(f)

        train_model, train_data_matrix, model_time = tfidf_model([x[1] for x in ir_data["data_objects"]])
        zero_context_scores, zero_context_time = tfidf_score(train_model, train_data_matrix, ir_data["zero_context"])
        diff_scores, diff_time = tfidf_score(train_model, train_data_matrix, ir_data["diff"])
        whole_file_scores, whole_file_time = tfidf_score(train_model, train_data_matrix, ir_data["whole_file"])
        
        tests = [x[0] for x in ir_data["data_objects"]]
        df = pd.DataFrame({
            "testclass": tests,
            "zero_context": zero_context_scores,
            "git_diff": diff_scores,
            "whole_file": whole_file_scores,
        })

        df.to_csv(ir_score_file, index=False)
        print("processing", project, index, pr_name, build_id, 
              "TFIDF time(second)", model_time, zero_context_time, diff_time, whole_file_time,
              "writing", ir_score_file)
        sys.stdout.flush()


def process_raw_ir_data_per_build(project, index, pr_name, build_id, overwrite=True):
    """extract data object, query and tokenize them"""
    ir_build_dir = os.path.join(ir_const.irdata_dir, project, f"{pr_name}_build{build_id}")
    testbody_file = os.path.join(ir_build_dir, ir_const.TESTBODY_FILE)
    diffbody_file = os.path.join(ir_build_dir, ir_const.DIFFBODY_FILE)
    diff_file = os.path.join(const.shadir, project, const.DIFF_DIR, f"{pr_name}_build{build_id}.diff")

    tk_ir_object_file = os.path.join(ir_build_dir, ir_const.IROBJ_FILE)
    
    if overwrite or not os.path.exists(tk_ir_object_file + ".gz"):
        # extract original file
        start = time.time()
        # get data objects, and queries
        data_objects = process_testbody_file(testbody_file)
        zero_context, diff, whole_file = process_diffbody_file(diffbody_file, diff_file)
        ir_data = {
            "data_objects": data_objects, 
            "zero_context": zero_context, "diff": diff, "whole_file": whole_file
        }
        with open(tk_ir_object_file, "w") as f:
            json.dump(ir_data, f)
        print("writing", project, index, pr_name, build_id, 
            time.time() - start, tk_ir_object_file)
        sys.stdout.flush()

        # compress original file
        extract_ir_body.compress_file(tk_ir_object_file)



def process_raw_ir_data(project):
    # only do IR on builds with failed tests
    df = pd.read_csv(const.DATASET_FILE)
    df = df[df["project"] == project]
    df = df[["pr_name", "build_id"]].drop_duplicates().values.tolist()

    pool = mp.Pool(mp.cpu_count())
    args = [(project, index, pr_name, build_id) for index, (pr_name, build_id) in enumerate(df)]
    pool.starmap(process_raw_ir_data_per_build, args)


def get_ir_score(project):
    os.makedirs(os.path.join(eval_const.feadir, project), exist_ok=True)
    
    df = pd.read_csv(const.DATASET_FILE)
    df = df[df["project"] == project]
    # different stages of the same build is based on the same change
    # get all tests' score relative to the change from all stages
    # extracted ir body file already include all the tests
    df = df[["pr_name", "build_id"]].drop_duplicates().values.tolist()

    pool = mp.Pool(mp.cpu_count())
    args = [(project, index, pr_name, build_id) for index, (pr_name, build_id) in enumerate(df)]
    pool.starmap(get_tfidf_ir_score_per_build, args)
    pool.starmap(get_bm25_ir_score_per_build, args)


if __name__ == "__main__":
    for project in const.PROJECTS:
        process_raw_ir_data(project)
        get_ir_score(project)
    pass