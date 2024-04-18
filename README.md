# LRTS: Dataset of Long-Running Test Suites


LRTS is the first, extensive dataset for test-case prioritization (TCP) focused on **long-running test suites**.

LRTS has 100K+ test-suite runs from 30K+ recent CI builds with **real test failures**, from **recent** codebases of 10 popular, large-scale, multi-PL, multi-module software projects: ActiveMQ, Hadoop, HBase, Hive, Jackrabbit Oak, James, Kafka, Karaf, Log4j 2, TVM.


### Key Statistics
- 108,366 test-suite runs from 32,199 CI builds
- 49,674 *failed* test-suite runs from 22,763 CI builds (with at least one test failure)
- Build history span: 2020 to 2024
- Average test-suite run duration: 6.75 *hours*, with >75% runs last over 2 hours
- Average number of executed test class per run: 980
- Average number of failed test class per failed run: 5 
