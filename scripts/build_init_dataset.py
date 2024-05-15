import os, json
import pandas as pd

import const

def check_has_trunk_head_diff_data(project, pr_name, build_id, base, head):
    fpath = os.path.join(const.shadir, project, const.COMPARE_DIR, 
                         f"{pr_name}_build{build_id}", f"{base}_{head}_page1.json")
    if os.path.exists(fpath):
        with open(fpath) as f:
            data = json.load(f)
            if "message" in data and "Not Found" in data["message"]:
                return False
            elif "url" in data:
                return True
    return False


def get_init_omin_file_per_project(project):
    bstats = pd.read_csv(os.path.join(const.metadir, project, const.BUILDSTATS_FILE))
    # pr_name,pr_base_branch,build_id,build_timestamp,trunk_sha_timestamp_sec,build_head_sha,trunk_sha,trunk_sha_source
    shamap = pd.read_csv(os.path.join(const.metadir, project, const.TRUNK_PRHEAD_MAP_FILE))
    # remove duplicate columns
    cols_to_use = shamap.columns.difference(bstats.columns).values.tolist()
    id_cols = ["pr_name", "build_id"]
    df = pd.merge(bstats, shamap[cols_to_use + id_cols], "inner", on=id_cols)
    print("bstats, shamap, merged", len(bstats), len(shamap), len(df))

    # check if each build has a zip
    # check if each build has pr head commit data
    # check if each build has the trunk...prhead diff
    # df["has_head_zip"] = False
    # df["has_head_commit_data"] = False
    df["has_trunk_head_diff_data"] = False

    for index, row in df.iterrows():
        pr_name = row["pr_name"]
        build_id = row["build_id"]
        head = row["build_head_sha"]
        base = row["trunk_sha"]
        # df.loc[index, "has_head_commit_data"] = check_has_head_commit_data(
        #     project, pr_name, build_id, head)
        df.loc[index, "has_trunk_head_diff_data"] = check_has_trunk_head_diff_data(
            project, pr_name, build_id, base, head)
    return df


def get_init_omin_file():
    """
    merge buildstats.csv with trunk_prhead_map.csv
    does a build has:
        - a zip
        - a commit json on the prhead sha
        - a commit json between the trunk and prhead sha
    """
    dfs = [get_init_omin_file_per_project(x) for x in const.PROJECTS]
    df = pd.concat(dfs, axis=0)
    df.to_csv(const.DATASET_INIT_FILE, index=False)


if __name__ == "__main__":
    get_init_omin_file()
