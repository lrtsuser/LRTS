# Artifact for "Revisiting Test-Case Prioritization on Long-Running Test Suites" (ISSTA 2024)


This is the artifact README for the research paper "Revisiting Test-Case Prioritization on Long-Running Test Suites" in ISSTA 2024. 
The "Getting Start" section provides a quick walkthrough on the general functionality (e.g., downloading and extract data from more builds, running TCP techniques) of the artifact on one of the evaluated project. To use the dataset we collected, please refer to the "Detailed Description" section.

## Getting Start


### Artifact setup

Required OS: Linux

Create a new conda environemnt and install artifact requirements:

```bash
# create a new conda environment
conda create -n lrts python=3.9 -y
conda activate lrts

# install python deps
pip install -r requirements.txt

# install R deps
sudo apt update
sudo apt install r-base r-base-dev -y
R -e "install.packages('agricolae',dependencies=TRUE, repos='http://cran.rstudio.com/')"
```


go to `./artifact` folder to start running the artifact by following the instructions below.


#### Specify example project for the artifact 

We will use one of the evaluated projects, `activemq`, to walk through the general functionlity of the artifact. Go to `const.py`, locate variable `PROJECTS`, comment out the other projects in `PROJECTS` except `ACTIVEMQ`. 



### Collect more builds from evaluated projects

We need valid GitHub API token to query some build data from GitHub. Before running the artifact, please follow the [official documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) to get a GitHub API token. Put your token into the `token_pool.py`.

To collect data (e.g, test report, log, metadata) of more PR builds from the evaluated projects, run the following:

```bash
# run scripts to collect raw data of more builds
./collect_builds.sh

# gather metadata of the collected builds
python build_dataset.py

# created dataset with confounding test labels
python extract_filtered_test_result.py
```

Running `collect_builds.sh` creates these folders: 
- `metadata/`: csv-formatted metadata of each collected PR build per project
- `prdata/`: per-PR metadata in JSON
- `shadata/`: code change info per build 
- `testdata/`: test reports and stdout logs per build
- `history/`: cloned codebase for the project
- `processed_test_result/`: parsed test results, each test-suite run is stored in a `csv.zip`

It will also generate `metadata/dataset_init.csv` which lists metadata for all collected PR builds.

Running `python3 build_dataset.py` creates a metadata csv for the collected dataset, where each row is a test-suite run (unique by its \<project, pr_name, build_id, stage_id\> tuple). Note that the newly collected builds may all be passing and have not failed tests to be evaluated (see `num_fail_class` in the generated `metadata/dataset.csv`). In this case, please try another project.

Running `python3 extract_filtered_test_result.py` creates processed test results in `csv.zip` format where failures of inspected flaky tests, frequently failing tests, and first failure of a test, are labeled.


### Evaluating on collected builds

This artifact also provides code that implements and runs TCP techniques in the paper on the collected build data.

#### Test feature collection

To extract test features, e.g., test duration, go to `./evaluation` folder and run:

```bash
./extract_test_features.sh
```

Then, to get data for information retrieval TCP, go to `./evaluation/information_retrieval`, and run:

```bash
python extract_ir_body.py
python extract_ir_score.py
```


To get data for supervised learning TCP (e.g., training-testing split, models), run:

```bash
python extract_ml_data.py
```


To get data for reinforcement learning TCP, go to `./evaluation/reinforcement_learning`, run:

```bash
python extract_rl_data.py
```

#### Measure TCP technique performance

To evaluate TCP technique on the collected data, run:

```bash
python eval_main.py
```

Evaluation results will be saved as `eval_outcome/[dataset_version]/[project_name]/[tcp_technique_name].csv.zip`, in which the columns are: project, tcp technique, PR name, build id, stage id, run seed, \[metric_value_1\], \[metric_value_2\], ..., \[metric_value_n\]. 

There are three automatically generated `[dataset_version]`s: `d_nofilter` (corresponding to LRTS-All), `d_jira_stageunique_freqfail` (LRTS-DeConf), and `d_first_jira_stageunique` (LRTS-FirstFail).


## Detailed Description


We provide the evaluation outcome data in the artifact such that one can reproduce results from the paper within a reasonable runtime. If you have run `eval_main.py` which produces new evaluation outcome data in the current repo, you need to clone a new copy of the repo to run this section.


### Reproducing results in the paper


Go to `analysis_paper/` folder,

```bash

# produce the plot that shows distribution of APFD(c) values for all techniques (Figure 2)
# figure is saved to figures/eval-LRTS-DeConf.pdf
python plot_eval_outcome.py

# produce
#   1. the table that compares the basic TCP techniques versus hybrid TCP (Table 8)
#   2. the table that shows controlled experiment results on IR TCP (Table 9)
#   3. the table that compares basic TCP techniques across all dataset versions (Table 10)
# tables are print to stdout in csv format
python table_eval_outcome.py


# produce 
#   1. dataset summary table as Table 3
#   2. CDF plot that shows distributions of test suite duration (hours) and size per project (Figure 1)
# results will be saved to dataset_viz/
python viz_dataset.py
```

**To use the scripts on the entire dataset we collected, please refer to the descriptions below.**


### The full dataset: LRTS


LRTS is the first, extensive dataset for test-case prioritization (TCP) focused on **long-running test suites**.

LRTS has 100K+ test-suite runs from 30K+ recent CI builds with **real test failures**, from **recent codebases** of 10 popular, large-scale, multi-PL, multi-module, **open-source software projects**: [ActiveMQ](https://github.com/apache/activemq), [Hadoop](https://github.com/apache/hadoop), [HBase](https://github.com/apache/hbase), [Hive](https://github.com/apache/hive), [Jackrabbit Oak](https://github.com/apache/jackrabbit-oak), [James](https://github.com/apache/james-project), [Kafka](https://github.com/apache/kafka), [Karaf](https://github.com/apache/karaf), [Log4j 2](https://github.com/apache/logging-log4j2), [TVM](https://github.com/apache/tvm).


#### Key Statistics
- 108,366 test-suite runs from 32,199 CI builds
- 49,674 *failed* test-suite runs (with at least one test failure) from 22,763 CI builds
- Build history span: 2020 to 2024
- Average test-suite run duration: 6.75 *hours*, with at least 75% runs last over 2 hours
- Average number of executed test class per run: 980
- Average number of failed test class per failed run: 5 


### Dataset

Go to [this link](https://drive.google.com/file/d/13vnCA0tY2BMY9irfn0nV01bJnST6z4kx/view?usp=sharing) to download the processed LRTS. It contains the metadata of the dataset, test results at test class level, and code change data of each test-suite run. We are actively looking for online storage to host the raw version which takes ~100GBs.

### Artifact

`artifact` folder contains our code for downloading more builds from the listed projects, our TCP technique code implementation and experiment scripts. To run our scripts on the processed dataset above, please use instructions in the `artifact/README.md`.

<!-- #### Requirement

Install python requirement via `requirements.txt`. Install `R` and `agricolae` library on `R`. -->
