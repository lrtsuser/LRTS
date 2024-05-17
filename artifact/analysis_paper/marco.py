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

BASIC_TCPS = [
    RANDOM_TCP,
    
    QTF_TCP,
    QTF_AVG_TCP,

    LF_TCP,
    FC_TCP,
    LT_TCP,
    TC_TCP,

    TF_FAILFREQ_TCP,
    TF_TRANSFREQ_TCP,
    
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


TRAD_TCPS = [RANDOM_TCP, QTF_TCP, QTF_AVG_TCP, LF_TCP, FC_TCP, LT_TCP, TC_TCP, TF_FAILFREQ_TCP, TF_TRANSFREQ_TCP]
TIME_TCPS = [QTF_TCP, QTF_AVG_TCP]
HIST_TCPS = [LF_TCP, FC_TCP, LT_TCP, TC_TCP, TF_FAILFREQ_TCP, TF_TRANSFREQ_TCP]
IR_TCPS = [IR_NOCONTEXT_TCP, IR_DIFF_TCP, IR_WHOLEFILE_TCP, IR_NOCONTEXT_TFIDF_TCP, IR_DIFF_TFIDF_TCP, IR_WHOLEFILE_TFIDF_TCP]
ML_TCPS = [ML1_TCP, ML2_TCP, ML3_TCP, ML4_TCP, MLALL_TCP]
RL_TCPS = [RL_TAB_FC_TCP, RL_TAB_TC_TCP, RL_TAB_TR_TCP, RL_NN_FC_TCP, RL_NN_TC_TCP, RL_NN_TR_TCP]

MARCOS = {
    RANDOM_TCP: "Random",
    QTF_TCP: "QTF-Last",
    QTF_AVG_TCP: "QTF-Avg",
    LTF_TCP: "LTF-Last",
    LTF_AVG_TCP: "LTF-Avg",

    LF_TCP: "LatestFail",
    FC_TCP: "MostFail",
    LT_TCP: "LatestTrans",
    TC_TCP: "MostTrans",

    TF_FAILFREQ_TCP: "TF-FailFreq",
    TF_FAILFREQ_REL_TCP: "TF-FailFreq-Rel",
    TF_TRANSFREQ_TCP: "TF-TransFreq",
    TF_TRANSFREQ_REL_TCP: "TF-TransFreq-Rrl",
    
    IR_NOCONTEXT_TCP: "IR-NoContext (BM25)",
    IR_DIFF_TCP: "IR-GitDiff (BM25)",
    IR_WHOLEFILE_TCP: "IR-WholeFile (BM25)",

    IR_NOCONTEXT_TFIDF_TCP: "IR-NoContext (TF-IDF)",
    IR_DIFF_TFIDF_TCP: "IR-GitDiff (TF-IDF)",
    IR_WHOLEFILE_TFIDF_TCP: "IR-WholeFile (TF-IDF)",

    ML1_TCP: "LTR ($F_1$)",
    ML2_TCP: "LTR ($F_2$)",
    ML3_TCP: "LTR ($F_3$)",
    ML4_TCP: "LTR ($F_4$)",
    MLALL_TCP: "LTR ($F_{all}$)",

    RL_TAB_FC_TCP: "RTL (Tabl-FailCount)",
    RL_TAB_TC_TCP: "RTL (Tabl-TCFail)",
    RL_TAB_TR_TCP: "RTL (Tabl-TimeRank)",
    RL_NN_FC_TCP: "RTL (NN-FailCount)",
    RL_NN_TC_TCP: "RTL (NN-TCFail)",
    RL_NN_TR_TCP: "RTL (NN-TimeRank)",

    # metric
    "APFDc_sameBug": "APFDc-$FFMap_S$",
    "APFDc_uniqueBug": "APFDc-$FFMap_U$",
    "APTDc_uniqueBug_sameFix": "$APTDc_{US}$",
    "APTDc_uniqueBug_uniqueFix": "$APTDc_{UU}$",

    "APFD_sameBug": "APFD-$FFMap_S$",
    "APFD_uniqueBug": "APFD-$FFMap_U$",
    "APTD_uniqueBug_sameFix": "$APTD_{US}$",
    "APTD_uniqueBug_uniqueFix": "$APTD_{UU}$",
}

METRIC_NAMES = [
    "APFDc_uniqueBug",
    "APFDc_sameBug",
    "APTDc_sameBug_sameFix",
    "APTDc_sameBug_uniqueFix",
    "APTDc_uniqueBug_sameFix",
    "APTDc_uniqueBug_uniqueFix",

    "APFD_uniqueBug",
    "APFD_sameBug",
    "APTD_sameBug_sameFix",
    "APTD_sameBug_uniqueFix",
    "APTD_uniqueBug_sameFix",
    "APTD_uniqueBug_uniqueFix",
]

COST_PREFIX = "cbt_"
HIST_PREFIX = "hbt_"
HISTCOST_PREFIX = "hcbt_"
HYBRID_MARCOS = {
    COST_PREFIX: "CC",
    HIST_PREFIX: "H",
    HISTCOST_PREFIX: "CCH",
}


# to be removed tests
FILTER_FIRST = "first"
FILTER_JIRA = "jira"
FILTER_STAGEUNIQUE = "stageunique"
FILTER_FREQFAIL = "freqfail"
FILTER_COMBOS = [
    [FILTER_JIRA, FILTER_STAGEUNIQUE, FILTER_FREQFAIL],
    [],
    [FILTER_FIRST, FILTER_JIRA, FILTER_STAGEUNIQUE],
]

DATASET_MARCO = {
    "jira_stageunique_freqfail": "LRTS-DeConf",
    "first_jira_stageunique": "LRTS-FirstFail",
    "": "LRTS-All",
}