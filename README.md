# LRTS: Dataset of Long-Running Test Suites


LRTS is an extensive, large-scale dataset for test prioritization research.

LRTS curates historical CI builds with real CI failures from GitHub and Jenkins CI. LRTS currently has 21K CI builds with 57K test-suite runs from 10 popular, large- scale open-source projects. Builds span 2020 to 2023.

*We are including more collected builds and updating our docs/scripts. Please stay tune for more updates.*

| **Project** | **Software domain** | **Main PLs** | **Period (days)** | **#CI builds** | **#Test suite runs** | **#Failed test suite runs** |
|---|---|---:|---:|---:|---:|---:|
| [ActiveMQ](https://github.com/apache/activemq) | Message broker | Java | 827 | 207 | 207 | 109 |
| [Hadoop](https://github.com/apache/hadoop) | Big-data processing | Java | 1,094 | 1,299 | 1,299 | 543 |
| [HBase](https://github.com/apache/hbase) | Big-data storage | Java | 504 | 278 | 553 | 215 |
| [Hive](https://github.com/apache/hive) | Data warehouse | Java, HiveQL | 618 | 2,056 | 2,056 | 1,419 |
| [Jackrabbit Oak](https://github.com/apache/jackrabbit-oak) | Content repository | Java | 745 | 860 | 860 | 639 |
| [James](https://github.com/apache/james-project) | Mail server | Java, Scala | 786 | 2,404 | 3,147 | 1,399 |
| [Kafka](https://github.com/apache/kafka) | Stream processing | Java, Scala | 984 | 11,843 | 39,006 | 24,047 |
| [Karaf](https://github.com/apache/karaf) | Modulith runtime | Java, Scala | 959 | 620 | 620 | 174 |
| [Log4j 2](https://github.com/apache/logging-log4j2) | Logging API | Java | 436 | 270 | 528 | 162 |
| [TVM](https://github.com/apache/tvm) | Compiler stack | Python, C++ | 631 | 1,418 | 9,161 | 1,411 |
| **Total** |  |  |  | **21,255** | **57,437** | **30,118** |



Average statistics on the FAILED test suites by project (TC means test class, TM means test method):

| **Project** | **Avg #TC** | **Avg #Failed TC** | **Avg #TM** | **Avg #Failed TM** | **Avg duration (hours)** |
|---|---:|---:|---:|---:|---:|
| [ActiveMQ](https://github.com/apache/activemq) | 676 | 3 | 6,081 | 34 | 4.36 |
| [Hadoop](https://github.com/apache/hadoop) | 829 | 6 | 7,289 | 24 | 5.57 |
| [HBase](https://github.com/apache/hbase) | 1,061 | 2 | 6,369 | 3 | 9.28 |
| [Hive](https://github.com/apache/hive) | 1,273 | 9 | 40,921 | 83 | 26.12 |
| [Jackrabbit Oak](https://github.com/apache/jackrabbit-oak) | 1,897 | 12 | 19,699 | 107 | 3.27 |
| [James](https://github.com/apache/james-project) | 1,864 | 6 | 34,718 | 37 | 2.15 |
| [Kafka](https://github.com/apache/kafka) | 1,232 | 4 | 19,399 | 12 | 7.59 |
| [Karaf](https://github.com/apache/karaf) | 205 | 2 | 841 | 2 | 0.58 |
| [Log4j 2](https://github.com/apache/logging-log4j2) | 641 | 3 | 3,918 | 4 | 0.25 |
| [TVM](https://github.com/apache/tvm) | 526 | 3 | 8,564 | 37 | 4.83 |

## Dataset

You can download LRTS from Zenodo.org. Please see `dataset/README.md`

The LRTS dataset is organized as:

```
data/
    [project_id]/
        [pull_request_id]/
            meta_github.json
            meta_jenkins.json
            build_[build_id]/
                meta_jenkins.json
                test_report.json.zip
                change_github.diff
                stdout_log.txt.xz
                change_meta_github/page*.json
```


- `meta*.json` is the metadata file collected from Github or Jenkins CI for the respective PR/build.
- `test_report.json.zip` is the zipped test report of the Jenkins CI build
- `stdout_log.txt.xz` is the compressed stdout build log
- `change_github.diff` is the diff file of the change that the build is based on
- `change_meta_github/*` contains json files of the metadata (authors, diff statistics, changed files, etc) of the change from Github

## Scripts

The code/scripts for collecting build data from Jenkins CI projects is in `./scripts/`
