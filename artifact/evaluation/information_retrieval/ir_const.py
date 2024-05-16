import os
import sys

script_dir = os.path.dirname(__file__)
grandparent_dir = os.path.join(script_dir, "..", "..")
parent_dir = os.path.join(script_dir, "..")
local_dir = os.path.join(script_dir, "..", "information_retrieval")
sys.path.append(grandparent_dir)
sys.path.append(parent_dir)
sys.path.append(local_dir)

import const

repo_dir = os.path.join(script_dir, "repo")
os.makedirs(repo_dir, exist_ok=True)

irdata_dir = os.path.join(script_dir, "ir_data")
os.makedirs(irdata_dir, exist_ok=True)
for project in const.PROJECTS:
    os.makedirs(os.path.join(irdata_dir, project), exist_ok=True)

# per project, per build, under the irdata dir
# QUERY_DIR = "query"
# TESTBODY_DIR = "testbody"
TESTPATH_FILE = "testpath.json"
TESTBODY_FILE = "testbody.json"
DIFFBODY_FILE = "diffbody.json"

IROBJ_FILE = "ir_object.json"