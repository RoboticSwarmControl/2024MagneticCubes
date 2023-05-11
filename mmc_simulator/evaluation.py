
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
    "boardSize": "workspace area [Mpx], aspect ratio",
    "time": "planning time [s]",
    "cost": "plan cost [rad]",
    "nconfig": "number of explored configurations #config",
    "nlocal": "number of local plans #locals",
    "ntcsa": "number of TCSA nodes #nodes",
    "localsToGoal": "number of local plans in stack $|P|$",
    "timeout": "fraction timed out",
    "nodes": "number of TCSA nodes",
    "edges": "number of TCSA edges"
}

BOARDSIZES_LABELS = {
    (700,700): "0.5, 1:1",
    (1000,1000): "1.0, 1:1",
    (1300,1300): "1.5, 1:1",
    (1000,500): "0.5, 2:1",
    (1400,700): "1.0, 2:1",
    (1800,900): "1.5, 2:1",
    (1200,400): "0.5, 3:1",
    (1800,600): "1.0, 3:1",
    (2100,700): "1.5, 3:1"
}

FONTSCALE = 2
LEGEND_SIZE = 20

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
    plt.rc('font', size=14)
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
    

def pieplot_timeUse(filePath):
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
    task_colors = {
        "Load Configuration": "limegreen",
        "Pymunk-Step": "tab:blue",
        "Polyomino Detection": "coral",
        "Save Configuration": "forestgreen",
        "Calculate Magnetic Field Forces": "indianred",
        "Calculate Friction Forces": "lightcoral",
        "Calculate Magnet Forces": "tab:red",
        "Other": "tab:gray"
    }
    #plot
    plt.rc('font', size=14)
    ax = plt.subplot()
    ax.pie(task_time.values(), labels=task_time.keys(), colors=[task_colors[t] for t in task_time.keys()], autopct='%1.1f%%')
    plt.tight_layout()
    plt.show()


def boxplot_TCSA(path):
    filePath = os.path.join(path, "TCSA.json")
    with open(filePath, 'r') as file:
        exp_data = json.load(file)
    xaxisLabel = "target size $n$"
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
    seaborn.barplot(data=dataFrame, x=xaxisLabel, y=yaxisLabel1, errorbar=None,
                    color='darkorange', width=0.65)
    plt.subplot(1,2,2)
    seaborn.barplot(data=dataFrame, x=xaxisLabel, y=yaxisLabel2, errorbar=None,
                    color='green', width=0.65)
    #plt.tight_layout(pad=15)
    plt.subplots_adjust(wspace=0.5)
    plt.show()

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

def __expPlanData(expPath, xaxis):
    # fil in the data form the experiment set
    exp_plan_data = loadExperimentSet(expPath)
    # sort the xaxis 
    if xaxis == "boardSize":
        return dict(sorted(exp_plan_data.items(), key=lambda t: BOARDSIZES.index(t[0].boardSize)))
    if xaxis == "targetShape":
        return dict(sorted(exp_plan_data.items(), key=lambda t: list(SHAPES.keys()).index(t[0].targetShape)))
    return exp_plan_data

def barplot_multipleSorting(expPath, xaxis, yaxis):
    xaxisLabel = AXIS_LABELS[xaxis]
    yaxisLabel = AXIS_LABELS[yaxis]
    sorting_data = __emptySortingData(xaxisLabel, yaxisLabel)
    exp_plan_data = __expPlanData(expPath, xaxis)
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
            else:
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
    xaxisLabel = AXIS_LABELS[xaxis]
    yaxisLabel = AXIS_LABELS[yaxis]
    sorting_data = __emptySortingData(xaxisLabel, yaxisLabel)
    exp_plan_data = __expPlanData(expPath, xaxis)
    for exp, plans in exp_plan_data.items():
        data = sorting_data[exp.optionSorting]
        for plan in plans:
            if onlySuccess and not plan.success:
                continue
            if xaxis == "boardSize":
                data[xaxisLabel].append(BOARDSIZES_LABELS[exp.boardSize])
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
    plt.show()
    
        
def main():
    #---Thesis plots---
    #plot_alignFunctions()
    #plot_pivotAngleDistance()
    #plot_magnetForce()
    #pieplot_timeUse(os.path.join(RESULT_DIR, "Simulator-Time/time-stats.json"))
    #boxplot_TCSA(os.path.join(RESULT_DIR, "TCSA-experiments"))
    #---Result Plots---
    #boxplot_multipleSortings(os.path.join(RESULT_DIR, "TAFS-experiments-2"), "targetSize", "time", onlySuccess=False)
    #barplot_multipleSorting(os.path.join(RESULT_DIR, "TAFS-experiments-2"), "targetSize", "timeout")
    #boxplot_multipleSortings(os.path.join(RESULT_DIR, "AFBS-experiments"), "boardSize", "time", onlySuccess=False)
    #barplot_multipleSorting(os.path.join(RESULT_DIR, "AFBS-experiments"), "boardSize", "timeout")
    boxplot_multipleSortings(os.path.join(RESULT_DIR, "AFTS-experiments"), "targetShape", "time", onlySuccess=False)
    barplot_multipleSorting(os.path.join(RESULT_DIR, "AFTS-experiments"), "targetShape", "timeout")

if __name__ == "__main__":
    main()