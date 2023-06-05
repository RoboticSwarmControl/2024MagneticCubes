import matplotlib.ticker as tck
import matplotlib.pyplot as plt
import pandas as pd
import seaborn
import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score

from experiment import *
from com.state import Cube

FIGURE_DIR = "../thesis/figures/plots"

AXIS_LABELS = {
    "targetSize": "target polyomino size $n$",
    "targetNred": r"number of red cubes $n_{red}$",
    "targetShape": "target polyomino shape",
    "boardSize": "workspace",
    "time": "planning time [s]",
    "cost": "plan cost [rad]",
    "nconfig": "#config",
    "nlocal": "#local",
    "ntcsa": "number of TCSA nodes #nodes",
    "localsToGoal": "$|P|$",
    "timeout": "fraction timed out",
    "nodes": "number of TCSA nodes",
    "edges": "number of TCSA edges",
    "seed": "instance seed"
}

BOARDSIZES_LABELS = {
    (700,700): "S, 1:1",
    (1000,1000): "M, 1:1",
    (1300,1300): "L, 1:1",
    (1000,500): "S, 2:1",
    (1400,700): "M, 2:1",
    (1800,900): "L, 2:1",
    (1200,400): "S, 3:1",
    (1800,600): "M, 3:1",
    (2100,700): "L, 3:1"
}

TASK_COLORS = {
    "Load Configuration": "limegreen",
    "Pymunk-Step": "tab:blue",
    "Polyomino Detection": "coral",
    "Save Configuration": "forestgreen",
    "Calculate Magnetic Field Forces": "indianred",
    "Calculate Friction Forces": "lightcoral",
    "Calculate Magnet Forces": "tab:red",
    "Other": "tab:gray"
}

FONTSCALE = 2
LEGEND_SIZE = 15

def plot_alignFunctions():
    plt.rc('font', size=14)
    # example a)
    pa = factory.fourCube_LShape()
    ca = pa.getCube((1,0))
    pb = factory.linePolyHori(2, 0)
    cb = pb.getCube((0,0))
    eb = Direction.WEST
    config = factory.configWithPolys((350,350), math.radians(90), [pa,pb], [(100, 260),(220, 120)])
    sim = Simulation()
    #sim.renderer.markedCubes.add(ca)
    #sim.renderer.markedCubes.add(cb)
    sim.loadConfig(config)
    sim.start()
    time.sleep(0.1)
    sim.stop()
    input()
    config = sim.terminate()
    pa = config.getPolyominoes().getForCube(ca)
    pb = config.getPolyominoes().getForCube(cb)
    __alignFunction(config.getCOM(pa), config.getPosition(ca), config.getCOM(pb), config.getPosition(cb), eb, config.magAngle, "a)")
    # example b)
    pa = factory.linePolyVert(3, 3)
    ca = pa.getCube((0,2))
    pb = factory.linePolyVert(3,0)
    cb = pb.getCube((0,0))
    eb = Direction.WEST
    config = factory.configWithPolys((350,350), math.radians(90), [pa,pb], [(140, 190),(210, 210)])
    sim = Simulation()
    sim.loadConfig(config)
    #sim.renderer.markedCubes.add(ca)
    #sim.renderer.markedCubes.add(cb)
    sim.start()
    time.sleep(0.1)
    sim.stop()
    input()
    config = sim.terminate()
    pa = config.getPolyominoes().getForCube(ca)
    pb = config.getPolyominoes().getForCube(cb)
    __alignFunction(config.getCOM(pa), config.getPosition(ca), config.getCOM(pb), config.getPosition(cb), eb, config.magAngle, "b)")
    # plot 
    plt.xlabel(r"rotation angle $\beta$")
    plt.ylabel(r"aligning function $\delta(\beta)$")
    ax = plt.subplot()
    plt.xlim(xmin=-1, xmax=1)
    plt.ylim(ymin=0, ymax=1)
    ax.legend()
    ax.xaxis.set_major_formatter(tck.FormatStrFormatter('%g $\pi$'))
    ax.xaxis.set_major_locator(tck.MultipleLocator(base=1.0))
    ax.yaxis.set_major_formatter(tck.FormatStrFormatter('%g $\pi$'))
    ax.yaxis.set_major_locator(tck.MultipleLocator(base=0.25))
    plt.tight_layout()
    plt.show()

def __alignFunction(comA: Vec2d, posA: Vec2d, comB: Vec2d, posB: Vec2d, edgeB: Direction, magAngle, label):
    step = math.radians(2)
    ang = magAngle - math.pi
    x = []
    y = []
    while ang < (magAngle + math.pi):
        rotAng = ang - magAngle
        if abs(rotAng) > math.pi:
            rotAng = -1 * (2 * math.pi - rotAng)
        rA = (posA - comA).rotated(rotAng)
        rB = (posB - comB).rotated(rotAng)
        vecBA = (comA + rA) - (comB + rB)
        vecEdgeB = edgeB.vec(ang)
        angDiff = abs(vecEdgeB.get_angle_between(vecBA))
        ang += step
        x.append(rotAng / math.pi)
        y.append(angDiff / math.pi)
    plt.plot(x, y, label=label)


def plot_pivotAngleDistance():
    plt.rc('font', size=16)
    plt.rc('text', usetex=True)
    plt.rc('text.latex', preamble=r'\usepackage{amsmath}')
    pAxisLengths = [Cube.RAD * 6, Cube.RAD * 4, Cube.RAD * 2]
    alpha = np.linspace(0, np.pi, 100)
    for a_p in pAxisLengths:
        d_p = 2 * np.sin(0.5 * alpha) * a_p
        plt.plot(alpha/np.pi, d_p/Cube.RAD, label=(r"$\lVert \vec{a} \rVert =" + f"{round(a_p / Cube.RAD)} r_C$"))
    ax = plt.subplot()
    plt.xlabel(r'pivot walking angle $\alpha$')
    plt.ylabel(r'pivot walking distance $\lVert\vec{d}\rVert$')
    plt.xlim(xmin=0, xmax=1)
    plt.ylim(ymin=0, ymax=12.5)
    ax.legend()
    ax.xaxis.set_major_formatter(tck.FormatStrFormatter('%g $\pi$'))
    ax.xaxis.set_major_locator(tck.MultipleLocator(base=0.25))
    ax.yaxis.set_major_formatter(tck.FormatStrFormatter('%g $r_C$'))
    ax.yaxis.set_major_locator(tck.MultipleLocator(base=1.0))
    plt.tight_layout()
    plt.show()


def plot_magnetForce():
    plt.rc('font', size=14)
    xmin = 2 * Cube.RAD
    xmax = 6 * Cube.RAD
    distance = np.linspace(xmin, xmax, 100)
    force = []
    for ydis in distance:
        f = Cube.magForce1on2(Vec2d(0,0 + Cube.MRAD), Vec2d(0, ydis - Cube.MRAD), (1,0), (1,0))
        force.append(f.length)
    max_force = max(force)
    for i in range(len(force)):
        force[i] /= max_force
    plt.plot(distance/Cube.RAD, force)
    ax = plt.subplot()
    ax.xaxis.set_major_formatter(tck.FormatStrFormatter('%g $r_C$'))
    ax.xaxis.set_major_locator(tck.MultipleLocator(base=1))
    plt.xlabel('distance of cubes')
    plt.ylabel('fraction of maximum force')
    plt.xlim(xmin=xmin/Cube.RAD, xmax=xmax/Cube.RAD)
    plt.ylim(ymin=0, ymax=max(force))
    plt.axvline(x=5, color='r')
    plt.text(4.8, 0.28, 'critical-distance', rotation=90, color="r")
    plt.tight_layout()
    plt.show()
    

def pieplot_timeUse(fileName):
    filePath = os.path.join(RESULT_DIR, "Simulator-Time", fileName)
    with open(filePath, 'r') as file:
        data = json.load(file)
    task_time: dict = data["tasks"]
    del task_time["Force Calculation"]
    del task_time["Polyomino Detection"]
    del task_time["Load Configuration"]
    del task_time["Save Configuration"]
    task_time["Pymunk-Step"] -= task_time["Calculate Magnet Forces"]
    timeOthers = data["total"]
    for time in task_time.values():
        timeOthers -= time
    task_time["Other"] = timeOthers
    task_time = {k: v for k, v in sorted(task_time.items(), key=lambda item: item[1], reverse=False)}
    #plot
    plt.rc('font', size=14)
    ax = plt.subplot()
    ax.pie(task_time.values(), labels=task_time.keys(), colors=[TASK_COLORS[t] for t in task_time.keys()], autopct='%1.1f%%')
    plt.tight_layout()
    plt.show()


def barplot_TCSA(expName):
    filePath = os.path.join(RESULT_DIR, expName, "TCSA.json")
    with open(filePath, 'r') as file:
        exp_data = json.load(file)
    xaxisLabel = "target polyomino size $n$"
    yaxisLabel1 = AXIS_LABELS["nodes"]
    yaxisLabel2 = AXIS_LABELS["edges"]
    data = {}
    data[xaxisLabel] = []
    data[yaxisLabel1] = []
    data[yaxisLabel2] = []
    for n, seeds in exp_data.items():
        if int(n) > 11:
            continue
        for seed in seeds.values():
            data[xaxisLabel].append(n)
            data[yaxisLabel1].append(seed["nodes"])
            data[yaxisLabel2].append(seed["edges"])
    dataFrame = pd.DataFrame(data=data)
    seaborn.set(font_scale=4)
    plt.subplot(1,2,1)
    ax1 =seaborn.barplot(data=dataFrame, x=xaxisLabel, y=yaxisLabel1, errorbar=None,
                    color='darkorange', width=0.65)
    __fitExponential(ax1)
    plt.subplot(1,2,2)
    ax2 = seaborn.barplot(data=dataFrame, x=xaxisLabel, y=yaxisLabel2, errorbar=None,
                    color='green', width=0.65)
    __fitExponential(ax2)
    #plt.tight_layout(pad=15)
    plt.subplots_adjust(wspace=0.5)
    plt.show()

def __fitExponential(ax_bar):
    y = []
    for c in ax_bar.containers:
        for v in c:
           y.append(v.get_height())
    x = np.asarray(range(5,12))
    y = np.asarray(y)
    popt, pcov = curve_fit(lambda t, a, b: a * np.exp(b * t), x, y)
    a = popt[0]
    b = popt[1]
    x_fitted = np.linspace(np.min(x), np.max(x), 100)
    y_fitted = a * np.exp(b * x_fitted)
    #r2 = r2_score(y, y_fitted)
    #print(r2)
    plt.plot(x_fitted - 5, y_fitted, linewidth=4, color="black",
             label=(f"${round(a,2)}" + r"e^{" + f"{round(b,2)}" + r"n}$"))
    plt.legend(prop={'size': LEGEND_SIZE * 2.5})


def __emptySortingData(xaxisLabel, yaxisLabel):
    # each sorting option gets a dataframe
    sorting_data = {}
    for sorting in OptionSorting.list():
        data = {}
        data[xaxisLabel] = []
        data[yaxisLabel] = []
        data["option sorting"] = []
        sorting_data[sorting.name] = data
    return sorting_data

def __expPlanData(expName, xaxis):
    # fil in the data form the experiment set
    expPath = os.path.join(RESULT_DIR, expName)
    exp_plan_data = loadExperimentSet(expPath)
    # sort the xaxis 
    if xaxis == "boardSize":
        return dict(sorted(exp_plan_data.items(), key=lambda t: BOARDSIZES.index(t[0].boardSize)))
    if xaxis == "targetShape":
        return dict(sorted(exp_plan_data.items(), key=lambda t: list(SHAPES.keys()).index(t[0].targetShape)))
    return exp_plan_data

def barplot_multipleSortings(expName, xaxis, yaxis, outFile=None):
    xaxisLabel = AXIS_LABELS[xaxis]
    yaxisLabel = AXIS_LABELS[yaxis]
    sorting_data = __emptySortingData(xaxisLabel, yaxisLabel)
    exp_plan_data = __expPlanData(expName, xaxis)
    for exp, plans in exp_plan_data.items():
        data = sorting_data[exp.optionSorting]
        timedout = 0
        for plan in plans:
            if not plan.success and plan.time > 600:
                if plan.nlocal < 100:
                    print(f"{exp.__dict__[xaxis]}-{exp.optionSorting}-{plan.seed} sus with nlocal={plan.nlocal}!")
                timedout += 1
            if xaxis == "boardSize":
                data[xaxisLabel].append(BOARDSIZES_LABELS[exp.boardSize])
            elif xaxis == "seed":
                data[xaxisLabel].append(plan.__dict__[xaxis])
            else:
                data[xaxisLabel].append(exp.__dict__[xaxis])
            data["option sorting"].append(exp.optionSorting)
        if yaxis == "timeout":
            data[yaxisLabel].extend([timedout / len(plans)] * len(plans))
    # create pandas dataframe
    dataFrame = pd.concat([pd.DataFrame(data=d) for d in sorting_data.values()])
    # plot catplot bars
    seaborn.set(font_scale=FONTSCALE)
    g = seaborn.catplot(data=dataFrame, kind="bar", x=xaxisLabel, y=yaxisLabel, hue="option sorting",
                    errorbar=None, legend_out=False)
    # add zero labels if bar has no height
    ax = g.facet_axis(0, 0)
    for c in ax.containers:
        labels = []
        for v in c:
            if v.get_height() != 0:
                labels.append("")
            else:
                labels.append("0")
        ax.bar_label(c, labels=labels, label_type="edge")
    # ledgend and show
    plt.legend(loc="upper left", prop={'size': LEGEND_SIZE})
    if outFile == None:
        plt.show()
    else:
        figure = plt.gcf()
        figure.set_size_inches(16*1.15 ,9*1.15)
        plt.savefig(os.path.join(FIGURE_DIR, outFile), bbox_inches='tight') 
    plt.close()

def boxplot_multipleSortings(expName, xaxis, yaxis, outFile=None, showFliers=True, onlySuccess=False, onlyTimeout=False):
    xaxisLabel = AXIS_LABELS[xaxis]
    yaxisLabel = AXIS_LABELS[yaxis]
    sorting_data = __emptySortingData(xaxisLabel, yaxisLabel)
    exp_plan_data = __expPlanData(expName, xaxis)
    for exp, plans in exp_plan_data.items():
        data = sorting_data[exp.optionSorting]
        for plan in plans:
            if (onlySuccess and not plan.success) or (onlyTimeout and (plan.time < 600 or plan.success)):
                continue
            if xaxis == "boardSize":
                data[xaxisLabel].append(BOARDSIZES_LABELS[exp.boardSize])
            elif xaxis == "seed":
                data[xaxisLabel].append(plan.__dict__[xaxis])
            else:
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
    if outFile == None:
        plt.show()
    else:
        figure = plt.gcf()
        figure.set_size_inches(16, 9)
        plt.savefig(os.path.join(FIGURE_DIR, outFile), bbox_inches='tight') 
    plt.close()

def stripplot_multipleSortings(expName, xaxis, yaxis, outFile=None, onlySuccess=False):
    xaxisLabel = AXIS_LABELS[xaxis]
    yaxisLabel = AXIS_LABELS[yaxis]
    sorting_data = __emptySortingData(xaxisLabel, yaxisLabel)
    exp_plan_data = __expPlanData(expName, xaxis)
    for exp, plans in exp_plan_data.items():
        data = sorting_data[exp.optionSorting]
        for plan in plans:
            if onlySuccess and not plan.success:
                continue
            if xaxis == "seed":
                data[xaxisLabel].append(plan.__dict__[xaxis])
            else:
                data[xaxisLabel].append(exp.__dict__[xaxis])
            data[yaxisLabel].append(plan.__dict__[yaxis])
            data["option sorting"].append(exp.optionSorting)
    # create pandas dataframe
    dataFrame = pd.concat([pd.DataFrame(data=d) for d in sorting_data.values()])
    # create seaborn stripplot
    seaborn.set(font_scale=FONTSCALE)
    dfm = pd.melt(dataFrame, id_vars=[xaxisLabel])
    seaborn.stripplot(data=dataFrame, x=xaxisLabel, y=yaxisLabel, hue="option sorting", alpha=0.25, s=8, dodge=True, jitter=True)
    plt.legend(loc="upper right", prop={'size': LEGEND_SIZE})
    for x in range(0, len(dfm[xaxisLabel].unique())):
        plt.axvspan(x - 0.5, x + 0.5, facecolor='black', alpha=[0.033 if x%2 == 0 else 0][0])
    figure = plt.gcf()
    figure.set_size_inches(8, 13)
    if outFile == None:
        plt.show()
    else:
        plt.savefig(os.path.join(FIGURE_DIR, outFile), bbox_inches='tight') 
    plt.close()

def scatterplot_multipleSortings(expName, xaxis, yaxis, outFile=None, onlySuccess=False):
    xaxisLabel = AXIS_LABELS[xaxis]
    yaxisLabel = AXIS_LABELS[yaxis]
    sorting_data = __emptySortingData(xaxisLabel, yaxisLabel)
    exp_plan_data = __expPlanData(expName, xaxis)
    for exp, plans in exp_plan_data.items():
        data = sorting_data[exp.optionSorting]
        for plan in plans:
            if onlySuccess and not plan.success:
                continue
            if xaxis == "ntcsa":
                data[xaxisLabel].append(plan.__dict__[xaxis])
            else:
                data[xaxisLabel].append(exp.__dict__[xaxis])
            data[yaxisLabel].append(plan.__dict__[yaxis])
            data["option sorting"].append(exp.optionSorting)
    # create pandas dataframe
    dataFrame = pd.concat([pd.DataFrame(data=d) for d in sorting_data.values()])
    # create seaborn scatterplot
    seaborn.set(font_scale=FONTSCALE)
    seaborn.scatterplot(data=dataFrame, x=xaxisLabel, y=yaxisLabel, hue="option sorting")
    plt.legend(loc="upper right", prop={'size': LEGEND_SIZE})
    if outFile == None:
        plt.show()
    else:
        figure = plt.gcf()
        figure.set_size_inches(16*1.15 ,9*1.15)
        plt.savefig(os.path.join(FIGURE_DIR, outFile), bbox_inches='tight') 
    plt.close()


def createFigures():
    #TAFS
    boxplot_multipleSortings("TAFS-experiments-2", "targetSize", "time", "AFN_time.pdf", onlySuccess=True)
    boxplot_multipleSortings("TAFS-experiments-2", "targetSize", "cost", "AFN_cost.pdf", onlySuccess=True, showFliers=False)
    boxplot_multipleSortings("TAFS-experiments-2", "targetSize", "nlocal", "AFN_nlocal.pdf", onlySuccess=True, showFliers=False)
    boxplot_multipleSortings("TAFS-experiments-2", "targetSize", "nconfig", "AFN_nconfig.pdf", onlySuccess=True, showFliers=False)
    boxplot_multipleSortings("TAFS-experiments-2", "targetSize", "localsToGoal", "AFN_ltg.pdf", onlySuccess=True)
    barplot_multipleSortings("TAFS-experiments-2", "targetSize", "timeout", "AFN_timeout.pdf")
    #AFTS
    boxplot_multipleSortings("AFTS-experiments-cb", "targetShape", "time", "AFTS_cb_time.pdf", onlySuccess=True)
    barplot_multipleSortings("AFTS-experiments-cb", "targetShape", "timeout", "AFTS_cb_timeout.pdf")
    boxplot_multipleSortings("AFTS-experiments-sp", "targetShape", "time", "AFTS_sp_time.pdf", onlySuccess=True)
    barplot_multipleSortings("AFTS-experiments-sp", "targetShape", "timeout", "AFTS_sp_timeout.pdf")
    #AFBS
    boxplot_multipleSortings("AFBS-experiments", "boardSize", "time", "AFBS_time.pdf", onlySuccess=True)  
    barplot_multipleSortings("AFBS-experiments", "boardSize", "timeout", "AFBS_timeout.pdf")
    boxplot_multipleSortings("AFBS-experiments", "boardSize", "cost", "AFBS_cost.pdf", onlySuccess=True, showFliers=False)
    #AFNR
    boxplot_multipleSortings("AFNR-experiments", "targetNred", "time", "AFNR_time.pdf", onlySuccess=True, showFliers=False)
    barplot_multipleSortings("AFNR-experiments", "targetNred", "timeout", "AFNR_timeout.pdf")
    #AR
    stripplot_multipleSortings("AR-bestseeds", "seed", "time", "AR_time.pdf", onlySuccess=True)
    stripplot_multipleSortings("AR-bestseeds", "seed", "cost", "AR_cost.pdf", onlySuccess=True)


def main():
    #---Thesis plots---
    #plot_alignFunctions()
    #plot_pivotAngleDistance()
    #plot_magnetForce()
    #pieplot_timeUse("time-stats.json")
    #barplot_TCSA("TCSA-experiments")
    #---Result Plots---
    #boxplot_multipleSortings("TAFS-experiments-2", "targetSize", "time", onlySuccess=True)
    #barplot_multipleSortings("TAFS-experiments-2", "targetSize", "timeout")
    #boxplot_multipleSortings("AFBS-experiments", "boardSize", "time", onlySuccess=True, showFliers=False)
    #boxplot_multipleSortings("AFNR-experiments", "targetNred", "cost", onlySuccess=True, showFliers=False)
    #boxplot_multipleSortings("AFTS-experiments-sp", "targetShape", "cost", onlySuccess=True)
    #stripplot_multipleSortings("AR-bestseeds", "seed", "time", onlySuccess=True)
    #stripplot_multipleSortings("AR-bestseeds", "seed", "cost", onlySuccess=True)
    #boxplot_multipleSortings("AR-bestseeds", "seed", "time", onlySuccess=True)
    #boxplot_multipleSortings("AR-bestseeds", "seed", "cost", onlySuccess=True)
    #scatterplot_multipleSortings("TAFS-experiments-2", "ntcsa", "cost", onlySuccess=True)
    #---Create Figures---
    createFigures()

if __name__ == "__main__":
    main()