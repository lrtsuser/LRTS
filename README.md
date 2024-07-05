# Artifact for "Revisiting Test-Case Prioritization on Long-Running Test Suites" (ISSTA 2024)


This README is for the artifact of the research paper "Revisiting Test-Case Prioritization on Long-Running Test Suites" in ISSTA 2024. 
The ["Getting Start"](#getting-start) section provides a quick walkthrough on the general functionality (e.g., downloading and extracting data from more builds, running TCP techniques) of the artifact using one of the evaluated projects as an example. To use the full dataset we previously collected, please refer to the ["Detailed Description"](#detailed-description) section.

## Getting Start

### Environment Setup

#### Using Docker

Start with Docker by running:

```bash
docker pull lrts/lrts-issta-24:latest
docker run -it --name lrts-artifact-container lrts/lrts-issta-24:latest
```

#### Local setup

*(Skip this section if you are using Docker)*

Required OS: Linux

Create a new conda environment and install artifact requirements:

```bash
# (Optional) install conda if not installed
curl -O https://repo.anaconda.com/archive/Anaconda3-2024.06-1-Linux-x86_64.sh
bash Anaconda3-2024.06-1-Linux-x86_64.sh

# create a new conda environment
conda create -n lrts python=3.9 -y
# run conda init and restart the shell before activating the env if needed
conda activate lrts

# install python deps
pip install -r requirements.txt

# install R deps
sudo apt update
sudo apt install r-base r-base-dev -y
R -e "install.packages('agricolae',dependencies=TRUE, repos='http://cran.rstudio.com/')"
```

### Specify an example project for the artifact 

Go to the [`./artifact`](./artifact) folder to start running the artifact by following the steps below. \
If you are using Docker, the default working directory is `artifact`.


We will use one of the evaluated projects, `activemq`, to walk through the general functionality of the artifact. Go to [`const.py`](./artifact/const.py), locate variable `PROJECTS`, and comment out the other projects in `PROJECTS` except `ACTIVEMQ`. 

### Collect more builds from evaluated projects

We need a valid GitHub API token to query some build data from GitHub. Before running the artifact, please follow the [official documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) and [Github personal access tokens](https://github.com/settings/tokens) to get a GitHub API token, and put the token in `self.tokens` in [`token_pool.py`](./artifact/token_pool.py) as a string.

To collect data (e.g, test report, log, metadata) of more PR builds from the evaluated project, run:

```bash
# run scripts to collect raw data for more builds
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

Running `python3 build_dataset.py` creates a metadata csv for the collected dataset (`metadata/dataset.csv`), where each row is a test-suite run (unique by its \<project, pr_name, build_id, stage_id\> tuple). Note that the newly collected builds may all be passing and have not failed tests to be evaluated (see `num_fail_class` in the generated csv). In this case, please try another project.

Running `python3 extract_filtered_test_result.py` creates processed test results in `csv.zip` format where failures of inspected flaky tests, frequently failing tests, and first failure of a test, are labeled.


### Evaluating on collected builds

This artifact also provides code that implements and runs TCP techniques in the paper on the collected build data.

#### Test feature collection

To extract test features, e.g., test duration, go to the [`./artifact/evaluation`](./artifact/evaluation/) folder and run:

```bash
./extract_test_features.sh
```

Then, to get data for information retrieval TCP, go to [`./artifact/evaluation/information_retrieval`](./artifact/evaluation/information_retrieval/), and run:

```bash
python extract_ir_body.py
python extract_ir_score.py
```


To get data for supervised learning TCP (e.g., training-testing split, models), run:

```bash
python extract_ml_data.py
```


To get data for reinforcement learning TCP, go to [`./artifact/evaluation/reinforcement_learning`](./artifact/evaluation/reinforcement_learning/), run:

```bash
python extract_rl_data.py
```

#### Measure TCP technique performance

To evaluate TCP techniques on the collected data, run:

```bash
python eval_main.py
```

Evaluation results will be saved as `eval_outcome/[dataset_version]/[project_name]/[tcp_technique_name].csv.zip`, in which the columns are: project, TCP technique, PR name, build id, stage id, run seed, \[metric_value_1\], \[metric_value_2\], ..., \[metric_value_n\]. 

There are three automatically generated `[dataset_version]`s: `d_nofilter` (corresponding to LRTS-All), `d_jira_stageunique_freqfail` (LRTS-DeConf), and `d_first_jira_stageunique` (LRTS-FirstFail).


## Detailed Description

To help facilitating research in software testing, especially test prioritization, this repository provides:
1. steps to download and use the full dataset of Long-Running Test Suites (LRTS) we have collected
2. scripts to collect more builds from the evaluated projects
3. implementations of different categories of Test-Case Prioritization (TCP) algorithms (time-based, history-based, information-retrieval-based, ML-based, RL-based)
4. experiment scripts to evaluate the implemented TCP algorithms on the collected, extensible dataset


### Reproducing results in the paper

We provide the evaluation outcome data in the artifact such that one can reproduce results from the paper within a reasonable runtime. If you have run [`./artifact/eval_main.py`](./artifact/evaluation/eval_main.py) which produces new evaluation outcome data in the current repo, please run `git restore .` to restore the data before it is overwritten.

The steps below produce all tables (Table 8-10) and figures (Figure 2) presented and analyzed in the "Evaluation" section of the paper, and produce the dataset summary table and figure (Table 2 and Figure 1).

Go to [`./artifact/analysis_paper/`](./artifact/analysis_paper/) folder,

```bash

# produce the plot that shows distribution of APFD(c) values for all techniques (Figure 2)
# figure is saved to figures/eval-LRTS-DeConf.pdf
python plot_eval_outcome.py

# produce
#   1. the table that compares the basic TCP techniques versus hybrid TCP (Table 8)
#   2. the table that shows controlled experiment results on IR TCP (Table 9)
#   3. the table that compares basic TCP techniques across all dataset versions (Table 10)
# tables are printed to stdout in csv format
python table_eval_outcome.py

# produce 
#   1. dataset summary table (Table 2)
#   2. CDF plot that shows distributions of test suite duration (hours) and size per project (Figure 1)
# results will be saved to dataset_viz/
python viz_dataset.py
```

**To download and use the full dataset we collected, please refer to the descriptions below.**


### The full dataset: LRTS


LRTS is the first, extensive dataset for test-case prioritization (TCP) focused on **long-running test suites**.

LRTS has 100K+ test-suite runs from 30K+ recent CI builds with **real test failures**, from **recent codebases** of 10 popular, large-scale, multi-PL, multi-module, **open-source software projects**: [ActiveMQ](https://github.com/apache/activemq), [Hadoop](https://github.com/apache/hadoop), [HBase](https://github.com/apache/hbase), [Hive](https://github.com/apache/hive), [Jackrabbit Oak](https://github.com/apache/jackrabbit-oak), [James](https://github.com/apache/james-project), [Kafka](https://github.com/apache/kafka), [Karaf](https://github.com/apache/karaf), [Log4j 2](https://github.com/apache/logging-log4j2), [TVM](https://github.com/apache/tvm).


#### Key Statistics
- 108,366 test-suite runs from 32,199 CI builds
- 49,674 *failed* test-suite runs (with at least one test failure) from 22,763 CI builds
- Build history span: 2020 to 2024
- Average test-suite run duration: 6.75 *hours*, with at least 75% of the runs last over 2 hours
- Average number of executed test classes per run: 980
- Average number of failed test classes per failed run: 5 


#### Dataset

Go to [this link](https://drive.google.com/file/d/13vnCA0tY2BMY9irfn0nV01bJnST6z4kx/view?usp=sharing) to download the processed LRTS. It contains the metadata of the dataset, test results at the test class level, and code change data of each test-suite run. We are actively looking for online storage to host the raw version which takes ~100GBs.

#### Artifact

The [`./artifact`](./artifact) folder contains our code for downloading more builds from the listed projects, our TCP technique code implementation, and experiment scripts. To run our scripts on the processed dataset above, please refer to the instructions in the `artifact/README.md`. They can be used the same way as described in the ["Getting Start"](#getting-start) section above.



<!-- #### Requirement

Install python requirement via `requirements.txt`. Install `R` and `agricolae` library on `R`. -->
