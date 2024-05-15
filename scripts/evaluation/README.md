# README

### Extracting test features

To get test features for a project, we need to have processed test results and code change data (`processed_test_results/` and `shadata/`) generated from scripts from the parent folder (See README from parent folder).

Run `./run.sh` to extract test features. It will create a folder `tcp_features` that stores test features per test-suite run; in `tcp_features`, `change_feature.csv` stores code change related features, `historical.csv` and `test_file_occ.csv` store test duration, outcome, (test outcome, changed file) occurance features. These features will be used by the evaluated TCP techniques listed in `eval_const.py`. 