#!/bin/bash

# get pr links
python3 -u get_pr_links.py

# get pr info for pr with test reports from github api
# amend them to buildstats
python3 -u get_pr_data.py

# download test report and build log for prs
python3 -u get_build_testdata.py

# extract stats per build from the downloaded data
python3 -u build_buildstats.py

# git pull the repo from their main branch
python3 -u get_repo.py

# extract trunk sha for prs from build log or from the pulled repo
python3 -u get_trunk_sha.py

# download sha data and trunk...prhead per build from github api
python3 -u get_sha_data.py


# extract test results
python3 -u build_init_omin.py
python3 -u extract_test_result.py

