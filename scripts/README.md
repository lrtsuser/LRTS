# ARTIFACT


Each sub-directory has a README that provides more information.

### Collecting more builds for existing projects

Scripts at this directory level are used for collecting pull-request build data (test report, code change, build metadata, build log) from Jenkins CI and Github for the listed project (See `const.py` for the project list, and see `run.sh` for more description). 
Before running the scripts, you need to add your github api tokens to `token_pool.py`. 

Then, run `./run.sh` to start collecting more PR builds. It will create these folders: 
- `./metadata` to store csv-formatted metadata of each collected PR build per project
- `./prdata` to store per-PR metadata in JSON
- `./shadata` to store code change info per build 
- `./testdata` to store test reports and stdout logs per build
- `./history` to host the cloned codebase for the project
- `processed_test_result` to store parsed test results 

It will also generate `metadata/omin_init.csv` which lists metadata for all collected PR builds.

After running `./run.sh`, we can run `python3 build_omin.py` to create a metadata csv for the collected dataset, where each row is a test-suite run that can be used to evaluate TCP techniques. After that, we can also run `python3 extract_filtered_test_result.py` to create processed test results where failures of inspected flaky tests, frequently failing tests, and first failure of a test, will be labeled.