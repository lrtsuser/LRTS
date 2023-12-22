import os
dir_path = os.path.dirname(os.path.realpath(__file__))

# build info, build test results
testdir = os.path.join(dir_path, "testdata")
# repo zips
historydir = os.path.join(dir_path, "history")
# pr links, shas, other info, misc
metadir = os.path.join(dir_path, "metadata")
# sha data
shadir = os.path.join(dir_path, "shadata")
# pr data (via github api)
prdir = os.path.join(dir_path, "prdata")

HADOOP = "hadoop"
HIVE = "hive"
TVM = "tvm"
JACK = "jackrabbit-oak"
HBASE = "hbase"
KAFKA = "kafka"
ACTIVEMQ = "activemq"
JAMES = "james"
KARAF = "karaf"
LOG4J = "log4j"

PROJECTS = [
    ACTIVEMQ,
    HADOOP,
    HBASE,
    HIVE,
    JACK,
    JAMES,
    KAFKA,
    KARAF,
    LOG4J,
    TVM,
]

PROJECT_PRETTY = {
    ACTIVEMQ: "ActiveMQ",
    HADOOP: "Hadoop",
    HBASE: "HBase",
    HIVE: "Hive",
    JACK: "Jackrabbit Oak",
    JAMES: "James",
    KAFKA: "Kafka",
    KARAF: "Karaf",
    LOG4J: "Log4j 2",
    TVM: "TVM",
}

# project that runs a test suite on multiple flavors per build
MF_PROJECTS = [HBASE, JAMES, KAFKA, LOG4J, TVM]

for project in PROJECTS:
    os.makedirs(os.path.join(testdir, project), exist_ok=True)
    os.makedirs(os.path.join(historydir, project), exist_ok=True)
    os.makedirs(os.path.join(metadir, project), exist_ok=True)
    os.makedirs(os.path.join(shadir, project), exist_ok=True)

# folder for storing the pr links in the metadata folder
PRLINKS = "pr_links"

# for collect pr links
PROJECT_URLS = {
    HADOOP: "https://ci-hadoop.apache.org/job/hadoop-multibranch/view/change-requests/api/json",
    TVM: "https://ci.tlcpack.ai/job/tvm/view/change-requests/api/json",
    KAFKA: "https://ci-builds.apache.org/job/Kafka/job/kafka-pr/view/change-requests/api/json",
    JACK: "https://ci-builds.apache.org/job/Jackrabbit/job/oak-trunk-pr/view/change-requests/api/json",
    HIVE: "http://ci.hive.apache.org/job/hive-precommit/view/change-requests/api/json", 
    ACTIVEMQ: "https://ci-builds.apache.org/job/ActiveMQ/job/ActiveMQ/view/change-requests/api/json",
    HBASE: "https://ci-hbase.apache.org/job/HBase-PreCommit-GitHub-PR/view/change-requests/api/json",
    JAMES: "https://ci-builds.apache.org/job/james/job/ApacheJames/view/change-requests/api/json",
    KARAF: "https://ci-builds.apache.org/job/Karaf/job/karaf-runtime/view/change-requests/api/json",
    LOG4J: "https://ci-builds.apache.org/job/Logging/job/log4j/view/change-requests/api/json",
}


PROJECT_GITHUB = {
    HADOOP: "https://github.com/apache/hadoop.git",
    TVM: "https://github.com/apache/tvm.git",
    KAFKA: "https://github.com/apache/kafka.git",
    JACK: "https://github.com/apache/jackrabbit-oak.git",
    HIVE: "https://github.com/apache/hive.git", 
    ACTIVEMQ: "https://github.com/apache/activemq.git",
    HBASE: "https://github.com/apache/hbase.git",
    JAMES: "https://github.com/apache/james-project.git",
    KARAF: "https://github.com/apache/karaf.git",
    LOG4J: "https://github.com/apache/logging-log4j2.git",
}

PROJECT_MAIN_BRANCHES = {
    HADOOP: "trunk",
    TVM: "main",
    KAFKA: "trunk",
    JACK: "trunk",
    HIVE: "master", 
    ACTIVEMQ: "main",
    HBASE: "master",
    JAMES: "master",
    KARAF: "main",
    LOG4J: "2.x",
}

# get project slug
PROJECT_SLUG = {}
for project, link in PROJECT_GITHUB.items():
    PROJECT_SLUG[project] = link.replace(".git", "").split("/")[-2:]
    PROJECT_SLUG[project] = "/".join(PROJECT_SLUG[project])




# folder for storing the build statistics in the metadata folder
BUILDSTATS_FILE = "buildstats.csv"

# for trunk sha data
TRUNK_PRHEAD_MAP_FILE = "trunk_prhread_map.csv"
# store trunk sha data from github api
SINGLE_DIR = "single_commit"
# store trunk...prhead diff data from github api
COMPARE_DIR = "compare_commits"
# store the trunk...prhead patch data
PATCH_DIR = "patch"
# store the trunk...diff data
DIFF_DIR = "diff"


# test case status
# https://javadoc.jenkins.io/plugin/junit/hudson/tasks/junit/CaseResult.Status.html
PASSED = "PASSED"
# This test was skipped due to configuration or the failure or skipping of a method that it depends on.
SKIPPED = "SKIPPED"
FAILED = "FAILED"
# This test has been running OK, but now it failed.
REGRESSION = "REGRESSION"
# This test has been failing, but now it runs OK.
FIXED = "FIXED"


# Headers to mimic the browser
GENERAL_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
}
