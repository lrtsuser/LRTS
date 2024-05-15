# README

### Extracting test features

To get test features for a project, we need to have processed test results and code change data (`processed_test_results/` and `shadata/`) generated from scripts from the parent folder (See README from parent folder).

Run `./run.sh` to extract test features. It will create a folder `tcp_features` that stores test features per test-suite run; in `tcp_features`, `change_feature.csv` stores code change related features, `historical.csv` and `test_file_occ.csv` store test duration, outcome, (test outcome, changed file) occurance features. These features will be used by the evaluated TCP techniques listed in `eval_const.py`. 

### Running TCP techniques

Run `python3 eval_main.py` to evaluate TCP techniques on specific projects in the dataset in test class granularity. 
We can configure the evaluating techniques (variable `EVAL_TCPS`) and evaluation metrics (variable `METRIC_NAMES`) in `eval_const.py`, and configure the evaluating projects in `../const.py`. The evaluation outcome will be saved in `eval_outcome/[project]/d_[filters]/[tcp_name].csv.zip`.

You can also specify the version of the dataset used for evaluation by applying different filters to keep or omit some of the builds that have failed tests in `eval_const.py` (variable FILTER_COMBOS): 
`FILTER_FIRST` keeps the builds that have failure of test that failed for the first time throughout the collected CI history; 
`FILTER_JIRA` omits test failures that are due to flaky tests identified from JIRA/Github issues; 
`FILTER_STAGEUNIQUE` omits tests that failed on only one stage when the build runs the same test suite on several stages that have different envrionments (e.g., JDK 8 vs JDK 11); 
`FILTER_FREQFAIL` omits tests that failed more frequently than failed tests using three sigma-rule-of-thumb. 
We can obtain the labeled version of the test results by running `../extract_filtered_test_result.py`.
