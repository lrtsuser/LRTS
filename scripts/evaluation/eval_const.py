import os
import sys

script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(script_dir, "..")
sys.path.append(parent_dir)


trdir = os.path.join(parent_dir, "processed_test_result")
TEST_REPORT_CSV = "test_report.csv.zip"
TEST_CLASS_CSV = "test_class.csv.zip"
# test files with filtering indictator
TEST_CLASS_FL_CSV = "test_class_filterlabel.csv.zip"
FILTER_TESTS_FILE = "filtered_tests.json.gz"

PASS = 0
FAIL = 1

# folders to store features for TCP
feadir = os.path.join(script_dir, "tcp_features")
os.makedirs(feadir, exist_ok=True)

# folders to training data, training test split record, and trained models
mldir = os.path.join(script_dir, "ml_data")
os.makedirs(mldir, exist_ok=True)
ML_TESTING_SET = "testing_builds.csv"
ML_TRAINING_SET = "training_builds.csv"
ML_TRAINING_DATA = "training_data.csv"
ML_MODEL_DIR = "model"


# folders to rl data
rldatadir = os.path.join(script_dir, "reinforcement_learning/rl_data")
os.makedirs(rldatadir, exist_ok=True)
# this folder is at (build, stage) level in tcp_features
rl_feature_dir = "rl_features"


# store readily usable historical feature per build, i.e., failure count, last transition, etc
HIST_FILE = "historical.csv"
# store IR bm25 score
IRSCORE_BM25_FILE = "ir_score_bm25.csv"
IRSCORE_TFIDF_FILE = "ir_score_tfidf.csv"
# max test file failure frequency, etc
TF_HIST_FILE = "test_file_occ.csv"
CHANGEFEA_FILE = "change_feature.csv"
MLFEATURE_FILE = "ml.csv"
# prediction results
ML_FILE = "ml_{}_{}.json.gz" # feature set name, seed
RL_FILE = "rl_{}_{}_{}.json.gz" # agent, reward, seed


# store meta info of changes per build against its base, change set, authors, commits, etc.
# can be used to extract features
changeinfodir = os.path.join(script_dir, "change_info")
os.makedirs(changeinfodir, exist_ok=True)


# evaluation
evaloutcomedir = os.path.join(script_dir, "eval_outcome")
# TCP techniques
RANDOM_TCP = "Random"

# Cost-only baseline ranking tests in ascending order by their last execution time
QTF_TCP = "QTF"
# Cost-only baseline ranking tests in ascending order by their average execution time
QTF_AVG_TCP = "QTF(Avg)"
# Cost-only baseline ranking tests in ascending order by their last execution time
LTF_TCP = "LTF"
# Cost-only baseline ranking tests in ascending order by their average execution time
LTF_AVG_TCP = "LTF(Avg)"


# Baseline ranking tests in ascending order by the time since the last failure
LF_TCP = "LastFail_Asc"
# Baseline ranking tests in descending order by the amount of historical failures
FC_TCP = "FailCount_Desc"
# Baseline ranking tests in ascending order by the time since the last transition
LT_TCP = "LastTrans_Asc"
# Baseline ranking tests in descending order by the amount of transitions
TC_TCP = "TransCount_Desc"


# ranking tests in descending order by the max co-occurance (test, file) failure frequency
TF_FAILFREQ_TCP = "TestFile_FailFreq"
# ranking tests in descending order by the max co-occurance (test, file) failure frequency (relative)
TF_FAILFREQ_REL_TCP = "TestFile_FailFreq_Rel"
# ranking tests in descending order by the max co-occurance (test, file) transition frequency
TF_TRANSFREQ_TCP = "TestFile_TransFreq"
# ranking tests in descending order by the max co-occurance (test, file) transition frequency (relative)
TF_TRANSFREQ_REL_TCP = "TestFile_TransFreq_Rel"


IR_NOCONTEXT_TCP = "IR_0Context"
IR_DIFF_TCP = "IR_GitDiff"
IR_WHOLEFILE_TCP = "IR_WholeFile"

IR_NOCONTEXT_TFIDF_TCP = "IR_0Context_tfidf"
IR_DIFF_TFIDF_TCP = "IR_GitDiff_tfidf"
IR_WHOLEFILE_TFIDF_TCP = "IR_WholeFile_tfidf"


ML1_TCP = "ML_f1"
ML2_TCP = "ML_f2"
ML3_TCP = "ML_f3"
ML4_TCP = "ML_f4"
MLALL_TCP = "ML_fall"


RL_TAB_FC_TCP = "RL_tableau_failcount"
RL_TAB_TC_TCP = "RL_tableau_tcfail"
RL_TAB_TR_TCP = "RL_tableau_timerank"
RL_NN_FC_TCP = "RL_mlpclassifier_failcount"
RL_NN_TC_TCP = "RL_mlpclassifier_tcfail"
RL_NN_TR_TCP = "RL_mlpclassifier_timerank"
# RL TCP cannot do hybrid
RL_TCPS = [
    RL_TAB_FC_TCP,
    RL_TAB_TC_TCP,
    RL_TAB_TR_TCP,
    RL_NN_FC_TCP,
    RL_NN_TC_TCP,
    RL_NN_TR_TCP,
]


BASIC_TCPS = [
    RANDOM_TCP,
    
    QTF_TCP,
    QTF_AVG_TCP,
    # LTF_TCP,
    # LTF_AVG_TCP,

    LF_TCP,
    FC_TCP,
    LT_TCP,
    TC_TCP,

    TF_FAILFREQ_TCP,
    # TF_FAILFREQ_REL_TCP,
    TF_TRANSFREQ_TCP,
    # TF_TRANSFREQ_REL_TCP,
    
    IR_NOCONTEXT_TCP,
    IR_DIFF_TCP,
    IR_WHOLEFILE_TCP,

    IR_NOCONTEXT_TFIDF_TCP,
    IR_DIFF_TFIDF_TCP,
    IR_WHOLEFILE_TFIDF_TCP,

    ML1_TCP,
    ML2_TCP,
    ML3_TCP,
    ML4_TCP,
    MLALL_TCP,
]


# More advance RTP
EVAL_TCPS = BASIC_TCPS.copy() + RL_TCPS.copy()
# # EVAL_TCPS = []
# # run time-break tie RTP
# EVAL_TCPS += ["cbt_" + x for x in BASIC_TCPS if x not in [RANDOM_TCP, QTF_TCP] + RL_TCPS]

# # # run failure count-break tie RTP
# # EVAL_TCPS += ["hbt_" + x for x in BASIC_TCPS if x not in [RANDOM_TCP, FC_TCP] + RL_TCPS]

# # run failure count / time-break tie RTP
# EVAL_TCPS += ["hcbt_" + x for x in BASIC_TCPS if x not in [RANDOM_TCP, FC_TCP, QTF_TCP] + RL_TCPS]


METRIC_NAMES = [
    "APFD_sameBug",
    "APFD_uniqueBug",
    "APFDc_sameBug",
    "APFDc_uniqueBug",
    # transition
    "APTD_sameBug_sameFix",
    "APTD_sameBug_uniqueFix",
    "APTD_uniqueBug_sameFix",
    "APTD_uniqueBug_uniqueFix",
    "APTDc_sameBug_sameFix",
    "APTDc_sameBug_uniqueFix",
    "APTDc_uniqueBug_sameFix",
    "APTDc_uniqueBug_uniqueFix",
    "NRPA",
    # "TTFF", "TTAF", "NTFF", "NTAF", "TotalTime", "TotalTest"
]


# # TODO: run historical based RTP with window
# EVAL_TCPS = []
# for window in WINDOW_SIZES:
#     EVAL_TCPS += [f"limhist{window}_" + x for x in [QTF_AVG_TCP, LTF_AVG_TCP, LF_TCP, FC_TCP, LT_TCP, TC_TCP]]


ML_FEATURE_SETS = {
    "f1": ["stage_id_enum"] + ["failure_count", "last_failure", "transition_count", "last_transition", "average_duration"],
    "f2": ["stage_id_enum"] + ["max_test_file_failure_frequency", "max_test_file_failure_frequency_relative", 
           "max_test_file_transition_frequency", "max_test_file_transition_frequency_relative"],
    "f3": ["stage_id_enum"] + ["min_file_path_distance", "max_file_path_tok_sim", "min_file_name_distance"],
    "f4": ["stage_id_enum"] + ["distinct_authors", "changeset_size", "commit_count", "distinct_extensions"],
}
fall = ["stage_id_enum"]
for value in ML_FEATURE_SETS.values():
    fall = fall + value[1:]
ML_FEATURE_SETS["fall"] = fall


# directory to store test order after prioritization
orderedtestdir = os.path.join(script_dir, "prioritized_tests")
os.makedirs(orderedtestdir, exist_ok=True)


# to be removed tests
FILTER_FIRST = "first"
FILTER_JIRA = "jira"
FILTER_STAGEUNIQUE = "stageunique"
FILTER_FREQFAIL = "freqfail"
FILTER_COMBOS = [
    [FILTER_JIRA, FILTER_STAGEUNIQUE, FILTER_FREQFAIL],
    # [FILTER_JIRA, FILTER_FREQFAIL],
    # [FILTER_FIRST, FILTER_JIRA],
    [FILTER_FIRST, FILTER_JIRA, FILTER_STAGEUNIQUE],
    [],
]