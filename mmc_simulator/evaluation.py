
import matplotlib.ticker as tck
import matplotlib.pyplot as plt
import pandas as pd
import seaborn
import numpy as np

from experiment import *
from com.state import Cube

AXIS_LABELS = {
    "targetSize": "target size $n$",
    "targetNred": "number of red cubes in target",
    "targetShape": "target shape",
    "boardSize": "size of workspace",
    "time": "planning time [s]",
    "cost": "plan cost [rad]",
    "nconfig": "number of explored configurations",
    "nlocal": "number of local plans",
    "ntcsa": "number of TCSA nodes",
    "localsToGoal": "number of local plans to goal",
    "timeout": "fraction timed out"
}

FONTSCALE = 2
LEGEND_SIZE = 20

def plot_pivotAngleDistance():
    pAxisLengths = [Cube.RAD * 6, Cube.RAD * 4, Cube.RAD * 2]
    alpha = np.linspace(0, np.pi, 100)
    for a_p in pAxisLengths:
        d_p = 2 * np.sin(0.5 * alpha) * a_p
        plt.plot(alpha/np.pi, d_p/Cube.RAD, label=f"$a_p = ${round(a_p / Cube.RAD)} $r_C$")
    ax = plt.subplot()
    plt.xlabel(r'pivot walking angle $\alpha$')
    plt.ylabel('pivot walking distance $d_p$')
    plt.xlim(xmin=0, xmax=1)
    plt.ylim(ymin=0, ymax=12.5)
    ax.legend()
    ax.xaxis.set_major_formatter(tck.FormatStrFormatter('%g $\pi$'))
    ax.xaxis.set_major_locator(tck.MultipleLocator(base=0.25))
    ax.yaxis.set_major_formatter(tck.FormatStrFormatter('%g $r_C$'))
    ax.yaxis.set_major_locator(tck.MultipleLocator(base=1.0))
    plt.show()


def barplot_multipleSorting(expPath, xaxis, yaxis):
    exp_plan_data = loadExperimentSet(expPath)
    xaxisLabel = AXIS_LABELS[xaxis]
    yaxisLabel = AXIS_LABELS[yaxis]
    # each sorting option gets a dataframe
    sorting_data = {}
    for sorting in OptionSorting.list():
        data = {}
        data[xaxisLabel] = []
        data[yaxisLabel] = []
        data["option sorting"] = []
        sorting_data[sorting.name] = data
    # fil in the data form the experiment set
    for exp, plans in exp_plan_data.items():
        data = sorting_data[exp.optionSorting]
        timedout = 0
        for plan in plans:
            if not plan.success and plan.time > 600:
                timedout += 1
            data[xaxisLabel].append(exp.__dict__[xaxis])
            data["option sorting"].append(exp.optionSorting)
        if yaxis == "timeout":
            data[yaxisLabel].extend([timedout / len(plans)] * len(plans))
    # create pandas dataframe
    dataFrame = pd.concat([pd.DataFrame(data=d) for d in sorting_data.values()])
    # plot catplot bars
    seaborn.set(font_scale=FONTSCALE)
    seaborn.catplot(data=dataFrame, kind="bar", x=xaxisLabel, y=yaxisLabel, hue="option sorting",
                    errorbar='sd', legend_out=False)
    plt.legend(loc="upper left", prop={'size': LEGEND_SIZE})
    plt.show()


def boxplot_multipleSortings(expPath, xaxis, yaxis, showFliers=True, onlySuccess=False):
    exp_plan_data = loadExperimentSet(expPath)
    xaxisLabel = AXIS_LABELS[xaxis]
    yaxisLabel = AXIS_LABELS[yaxis]
    # each sorting option gets a dataframe
    sorting_data = {}
    for sorting in OptionSorting.list():
        data = {}
        data[xaxisLabel] = []
        data[yaxisLabel] = []
        data["option sorting"] = []
        sorting_data[sorting.name] = data
    # fil in the data form the experiment set
    for exp, plans in exp_plan_data.items():
        data = sorting_data[exp.optionSorting]
        for plan in plans:
            if onlySuccess and not plan.success:
                continue
            data[xaxisLabel].append(exp.__dict__[xaxis])
            data[yaxisLabel].append(plan.__dict__[yaxis])
            data["option sorting"].append(exp.optionSorting)
    # create pandas dataframe
    dataFrame = pd.concat([pd.DataFrame(data=d) for d in sorting_data.values()])
    # create seaborn boxplot
    seaborn.set(font_scale=FONTSCALE)
    seaborn.boxplot(x=xaxisLabel, y=yaxisLabel, data=dataFrame, hue="option sorting",
                    showmeans=True, meanprops={"marker": "o","markerfacecolor": "white","markeredgecolor": "black","markersize": "10"},
                    showfliers=showFliers, flierprops=dict(markerfacecolor='0.50', markersize=5))
    plt.legend(loc="upper left", prop={'size': LEGEND_SIZE})
    plt.show()
    
        
def main():
    #plot_pivotAngleDistance()
    #boxplot_multipleSortings(os.path.join(RESULT_DIR, "TAFS-experiments"), "targetSize", "time")
    #barplot_multipleSorting(os.path.join(RESULT_DIR, "TAFS-experiments"), "targetSize", "timeout")
    boxplot_multipleSortings(os.path.join(RESULT_DIR, "AFBS-experiments"), "boardSize", "time")

if __name__ == "__main__":
    main()