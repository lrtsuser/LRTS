# LRTS: Dataset of Long-Running Test Suites


LRTS is the first, extensive dataset for test-case prioritization (TCP) focused on **long-running test suites**.

LRTS has 100K+ test-suite runs from 30K+ recent CI builds with **real test failures**, from **recent codebases** of 10 popular, large-scale, multi-PL, multi-module, **open-source software projects**: [ActiveMQ](https://github.com/apache/activemq), [Hadoop](https://github.com/apache/hadoop), [HBase](https://github.com/apache/hbase), [Hive](https://github.com/apache/hive), [Jackrabbit Oak](https://github.com/apache/jackrabbit-oak), [James](https://github.com/apache/james-project), [Kafka](https://github.com/apache/kafka), [Karaf](https://github.com/apache/karaf), [Log4j 2](https://github.com/apache/logging-log4j2), [TVM](https://github.com/apache/tvm).


### Key Statistics
- 108,366 test-suite runs from 32,199 CI builds
- 49,674 *failed* test-suite runs (with at least one test failure) from 22,763 CI builds
- Build history span: 2020 to 2024
- Average test-suite run duration: 6.75 *hours*, with at least 75% runs last over 2 hours
- Average number of executed test class per run: 980
- Average number of failed test class per failed run: 5 


## Dataset

Go to [this link](https://drive.google.com/file/d/12gVUIUiRpR53pzI3xGMOEqBXdsDP_dYS/view?usp=sharing) to download the processed LRTS. It contains the metadata of the dataset, test results at test class level, and code change data of each test-suite run. We are actively looking for online storage to host the raw version which takes ~100GBs.

## Scripts

`scripts` folder contains our code for downloading more builds from the listed projects, our TCP technique code implementation and experiment scripts.

**We are preparing and releasing our technique implement and experiment analysis code.**
