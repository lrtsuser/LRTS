import os
import glob
import pandas as pd
import multiprocessing as mp

def copy_over():
    files = glob.glob("/Users/samcheng/Desktop/bigRT/processed_test_result/tvm2023/tvm*/PR*/stage*/test_class.csv.zip")
    print(len(files))
    print(files[0])
    # /Users/samcheng/Desktop/bigRT/processed_test_result/tvm2023/tvm-cpu/PR-13530_build5/stage_tvm-cpu/test_class.csv.zip
    for f in files:
        print(f)
        segments = f.split('/')
        stage = segments[7]
        pr_build = segments[8]
        # print(stage, pr_build)
        # exit(0)
        output_path = f"/Users/samcheng/Desktop/LRTS/scripts/processed_test_result/tvm/{pr_build}/stage_{stage}"
        os.makedirs(output_path, exist_ok=True)
        os.system(f"cp {f} {output_path}/")

def remove_file():
    files = glob.glob("processed_test_result/*/PR*/stage*/test_class_filterlabel.csv.zip")
    print(len(files))
    print(files[0])
    for file in files:
        print(file)
        os.system(f"rm {file}")
    pass

def check_number():
    for project in const.PROJECTS:
        files = glob.glob(f"processed_test_result/{project}/PR-*/stage*/test_class.csv.zip")
        print(len(files))

# def corner_case():
#     missing = [
#     "tvm_PR-13500_build2_cpu",
#     "tvm_PR-13500_build2_gpu",
#     "tvm_PR-13500_build2_hexagon",
#     "tvm_PR-13530_build5_cpu",
#     "tvm_PR-13530_build5_gpu",
#     "tvm_PR-13530_build5_hexagon",
#     "tvm_PR-13530_build6_cpu",
#     "tvm_PR-13530_build6_gpu",
#     "tvm_PR-13530_build6_hexagon",
#     "tvm_PR-13530_build7_cpu",
#     "tvm_PR-13530_build7_gpu",
#     "tvm_PR-13530_build7_hexagon",
#     "tvm_PR-13530_build8_cpu",
#     "tvm_PR-13530_build8_gpu",
#     "tvm_PR-13530_build8_hexagon"
#     ]
#     for m in missing:
#         segments = m.split('_')
#         pr = segments[1]
#         build = segments[2]
#         stage = segments[-1]
#         print(m)
#         fpath = f"/Users/samcheng/Desktop/bigRT/processed_test_result/tvm2023/tvm-{stage}/{pr}_{build}/stage_tvm-{stage}/test_class.csv.zip"
#         if os.path.exists(fpath):
#             output_path = f"processed_test_result/tvm/{pr}_{build}/stage_{stage}"
#             os.makedirs(output_path, exist_ok=True)
#             os.system(f"cp {fpath} {output_path}/")


def add_num_trans_class_helper(i, path):
    print(path)
    test_df = pd.read_csv(path)
    return i, (test_df["outcome"] - test_df["last_outcome"]).abs().sum()

def add_num_trans_class():
    df = pd.read_csv("/Users/samcheng/Desktop/data_LRTS/long_running_test_suites/dataset.csv")
    print(df.columns)
    args = []
    for i, row in df.iterrows():
        project, prname, build_id, stage = row['project'], row['pr_name'], row['build_id'], row['stage_id']
        path = f"/Users/samcheng/Desktop/data_LRTS/long_running_test_suites/processed_test_result/{project}/{prname}_build{build_id}/stage_{stage}/test_class.csv.zip"
        args.append([i, path])
    
    pool = mp.Pool(mp.cpu_count())
    ret = pool.starmap(add_num_trans_class_helper, args)
    df['num_trans_class'] = 0
    for i, val in ret:
        df.at[i, "num_trans_class"] = val
    df.to_csv("/Users/samcheng/Desktop/data_LRTS/long_running_test_suites/dataset_new.csv", index=False)
    pass

if __name__ == "__main__":
    add_num_trans_class()
    pass