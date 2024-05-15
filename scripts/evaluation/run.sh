#!/bin/bash

# extract historical features F1
python3 -u extract_hist_features.py

# extract test change data
python3 -u extract_change_info_from_raw_data.py

# extract test file cooccurance F2
python3 -u extract_test_file_occ_hist_features.py

# extract change features F3-4
python3 -u extract_change_features.py