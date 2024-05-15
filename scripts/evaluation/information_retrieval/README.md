# README

This folder contains implementation and evaluation scripts for IR-based TCP techniques using BM25 and TDIDF. We need the processed test results (`processed_test_result/`) and code change information (`shadata/`) to run these scripts.

Run `python3 extract_ir_body.py` to extract the tokenized test documents and query, transform them into IR objects, and store them in `ir_data/`.

Then, run `python3 extract_ir_score.py` to compute IR score per test for all test-suite runs in a specified projects (project list in `../../const.py`), save BM25 scores in `../tcp_features/[project]/*/ir_score_bm25.csv`, save TFIDF scores in `../tcp_features/[project]/*/ir_score_tfidf.csv` for each test-suite runs.

