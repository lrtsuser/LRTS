import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.pylab as pylab

# params = {
#     # 'legend.fontsize': 'x-large',
#     # 'figure.figsize': (15, 5),
#     'axes.labelsize': 20,
#     'axes.titlesize': 20,
#     # 'font.family': "Times New Roman",
#     'xtick.labelsize': 15,
#     'ytick.labelsize': 15,
#          }
# pylab.rcParams.update(params)

# new_params = {"font.serif": "Times "}
# plt.rcParams.update(new_params)


def add_axis_line(ax0, vertical=True):
    if vertical:
        ax0.xaxis.grid(True, linestyle="-", which="major", color="lightgrey",
                        # alpha=0.5
                        )
    else:
        ax0.yaxis.grid(True, linestyle="-", which="major", color="lightgrey",
                       # alpha=0.5
                       )
    ax0.set_axisbelow(True)

def draw_metric_fig():
	# 1,2,3,4, p,f,f,p
    # 4,2,3,1, p,f,f,p
	data = [
		[
			# apmd, 0, test suite progress, fault detected
            [[0, 30, 60, 100], [0, 50, 100, 100], "t1-t2-t3-t4", "O1", "0.7"],
	        [[0, 30, 60, 100], [0, 50, 100, 100], "t4-t2-t3-t1", "O2", "0.7"],
			# [[0, 100/3, 200/3, 100], [0, 50, 100, 100], "t1-t2-t3", "O1", 67], #123
			# [[0, 100/3, 200/3, 100], [0, 50, 100, 100], "t2-t1-t3", "O2", 67], #213
			# [[0, 100/3, 200/3, 100], [0, 50, 50, 100], "t1-t3-t2", "O3", 50], #132
			# [[0, 100/3, 200/3, 100], [0, 0, 50, 100], "t3-t1-t2", "O4", 33], #312
		],
		[
			# apmdc
            [[0, 30, 60, 100], [0, 50, 100, 100], "t1-t2-t3-t4", "O1", "0.7"],
	        [[0, 60, 90, 100], [0, 50, 100, 100], "t4-t2-t3-t1", "O2", "0.475"],
			# [[0, 100/6, 300/6, 100], [0, 50, 100, 100], "t1-t2-t3", "O1", 79], #123
			# [[0, 200/6, 300/6, 100], [0, 50, 100, 100], "t2-t1-t3", "O2", 71], #213
			# [[0, 100/6, 400/6, 100], [0, 50, 50, 100], "t1-t3-t2", "O3", 54], #132
			# [[0, 300/6, 400/6, 100], [0, 0, 50, 100], "t3-t1-t2", "O4", 29], #312
		],
	]

	# colors = ["pink", "cornflowerblue"]
	# alphas = [1, 0.75, 0.5, 0.25] # transparence
	fig, axs = plt.subplots(nrows=2, ncols=2)
	fig.set_figheight(4)
	fig.set_figwidth(7)
	for i in range(2):
		for j in range(2):
			x, y, order, oid, auc = data[i][j]
			key = "APFD" if i == 0 else "APFDc"
			axs[i,j].plot(x, y, '-', color="black", linewidth=1)
			axs[i,j].vlines(x, 0, y, linestyle="dashed", linewidth=1, color="black") # dash test locations
			axs[i,j].fill_between(x, y, color="lightgrey") # color AOC
			axs[i,j].locator_params(axis="y", nbins=3) # only show 1, .5 and 0
			# plt.locator_params(axis="x", nbins=4) # only show 1, 0.6, 0.3 and 0
			axs[i,j].set_ylim(ymin=0, ymax=101)
			axs[i,j].set_xlim(xmin=0, xmax=101)
			# remove box
			axs[i,j].spines['top'].set_visible(False)
			axs[i,j].spines['right'].set_visible(False)
			axs[0,j].set_title("Prioritized order "+oid+": "+order, fontsize=13, pad=20)
			# axs[i,j].text(5, 70, "Area={}%\n{}={}".format(auc, key, auc/100), bbox=dict(facecolor='white'))
			axs[i,j].text(10, 80, "{}={}".format(key, auc), bbox=dict(facecolor='white'))
			axs[i,1].tick_params(labelleft=False)
			add_axis_line(axs[i, j], vertical=False)
			# label
			# axs[i, j].set_ylabel("Percentage Detected Misconfigurations")
			if i == 0:
				axs[i, j].set_xlabel("% Test suite executed", fontsize=12)
			elif i == 1:
				axs[i, j].set_xlabel("% Test suite cost incurred", fontsize=12)
	fig.supylabel("% Detected faults", x=0.01, fontsize=12)
	fig.tight_layout()
	fig.savefig("figures/metric.jpg")
	fig.savefig("figures/metric.pdf")
	plt.close()

if __name__ == '__main__':
	draw_metric_fig()
