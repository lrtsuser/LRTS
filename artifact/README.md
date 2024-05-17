# ARTIFACT


Each sub-directory has a README that provides more information.

### Collecting more builds for existing projects

Scripts at this directory level are used for collecting pull-request build data (test report, code change, build metadata, build log) from Jenkins CI and Github for the listed project. See `const.py` for the project list, and see `collect_builds.sh` for more description. 
Before running the scripts, you need to add your github api tokens to `token_pool.py`. 

Then, run `./collect_builds.sh` to start collecting more PR builds (for starting, we can only include ACTIVEMQ and comment out other projects in `PROJECTS` in `const.py`). Running `collect_builds.sh` will create these folders: 
- `metadata/` to store csv-formatted metadata of each collected PR build per project
- `prdata/` to store per-PR metadata in JSON
- `shadata/` to store code change info per build 
- `testdata/` to store test reports and stdout logs per build
- `history/` to host the cloned codebase for the project
- `processed_test_result/` to store parsed test results, each test-suite run is stored in a `csv.zip`

It will also generate `metadata/dataset_init.csv` which lists metadata for all collected PR builds.

After running `./collect_builds.sh`, we can run `python3 build_dataset.py` to create a metadata csv for the collected dataset, where each row is a test-suite run (unique by its \<project, pr_name, build_id, stage_id\> tuple) that can be used to evaluate TCP techniques. After that, we can also run `python3 extract_filtered_test_result.py` to create processed test results in `csv.zip` format where failures of inspected flaky tests, frequently failing tests, and first failure of a test, are labeled.

### Running evaluation experiments in the processed dataset

`evaluation/` provides scripts to run evaluation experiments. To run experiments in the processed LRTS dataset, decompressed the downloaded dataset, move the `processed_test_result/` and `shadata/` to this folder; move the `dataset.csv` to `../metadata`. 

Run `extract_filtered_test_result.py` to create create processed test results where failures of inspected flaky tests, frequently failing tests, and first failure of a test, are labeled. 

### Producing plots and figures in the evaluation section

`./analysis_paper` provides scripts to produce figure and tables in our evaluation. `metadata/`, `change_info/`, and `eval_outcome/` provide corresponding experiment data to run these scripts in our evaluation. 