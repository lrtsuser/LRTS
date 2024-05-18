# README


To produce the plot that shows distribution of APFD(c) values for all techniques (Figure 2), run `python3 plot_eval_outcome.py`, figure is saved to `figures/eval-LRTS-DeConf.pdf`. 


To produce the table that compares the basic TCP techniques versus hybrid TCP (Table 8),  the table that shows controlled experiment results on IR TCP (Table 9), the table that compares basic TCP techniques across all dataset versions (Table 10), run `python3 table_eval_outcome.py`, tables are printed to stdout in csv format.

To produce a summary table of the dataset described in `../metadata/dataset.csv` (like Table 3), and the CDF plot that shows distributions of test suite duration (hours) and size per project (Figure 1), run `python3 viz_dataset.py`, results will be saved to `dataset_viz/`.

