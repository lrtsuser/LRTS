# LRTS: Dataset of Long-Running Test Suites


LRTS is the first, extensive dataset for test-case prioritization (TCP) focused on **long-running test suites**.

LRTS has 108,366 test-suite runs from 32,199 recent CI builds with **real** test failures (among which 49,674 test-suite runs from 22,763 CI builds have at least one failed test class), from **recent** codebases of 10 popular, large-scale, multi-PL, multi-module software projects: ActiveMQ, Hadoop, HBase, Hive, Jackrabbit Oak, James, Kafka, Karaf, Log4j 2, TVM. History of collected builds spans 2020 to 2024.

In LRTS, the average test-suite run duration is 6.75 hours, and at least 75% of the runs last >2 hours; the average number of executed test classes is 980. Among the failed test-suite runs, the average number of failed test classes is 5.
