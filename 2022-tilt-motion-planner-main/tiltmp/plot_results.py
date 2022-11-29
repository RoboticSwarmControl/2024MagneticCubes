import argparse
import cProfile
import json
import math
import os
from json import JSONDecodeError
from pprint import pprint
import io
from collections import Counter, defaultdict

import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn

from tiltmp.core.serialization import read_instance, decode_instance, write_instance
from tiltmp.mp.motionplanner import *
from tiltmp.run_experiment import SolutionData
from pandas import DataFrame
import re

FONTSCALE = 3
LEGENDSIZE = 30

SOLVER_HUE_ORDER = ["BFS", "GD", "AD", "GGD", "GAD", "WSD", "MMP", "MMPT", "DFP", "RRT"]

def main():

    parser = argparse.ArgumentParser(description='Plot various aspects of solution data in scatter plots')
    parser.add_argument("-x", type=str, default="tiles",
                        help="parameter that will be displayed on the x-axis of the plot. "
                             "Possible values: " + str(tuple(AXIS_FUNCTIONS.keys())))
    parser.add_argument("-y", type=str, default="time",
                        help="parameter that will be displayed on the y-axis of the plot. "
                        "Possible values: " + str(tuple(AXIS_FUNCTIONS.keys())))
    parser.add_argument("--pairplot", action="store_true", help="plot all possible combinations of features")
    parser.add_argument("--regex", "-r", type=str, default=".*", help="filter files names by regex")
    parser.add_argument('input', metavar="IN", nargs="+",
                    help='list of files or directories with data about solved instances '
                         'as produced by run_experiment.py')
    parser.add_argument("-i", "--instances", type=str, default=None,
                         help="original instances used for the experiment. used to create the bar charts")
    parser.add_argument("-v", "--violin", action="store_true")

    args = parser.parse_args()

    if args.x not in AXIS_FUNCTIONS or args.y not in AXIS_FUNCTIONS:
        parser.error("unknown axis function")
        exit(-1)

    data = []

    regex = re.compile(args.regex)

    for file_or_directory in args.input:
        solved_names = []
        dir_data = []
        if os.path.isdir(file_or_directory):
            for filename in os.listdir(file_or_directory):
                if not filename.endswith(".json"):
                    continue
                if not regex.match(filename):
                    continue
                solution = load_file(os.path.join(file_or_directory, filename))
                solved_names.append(filename.rsplit('_', 1)[0])
                if solution:
                    if "maze" in filename:
                        solution.board_type = "maze"
                    elif "cave" in filename:
                        solution.board_type = "cave"
                    solution.file_name = filename
                    dir_data.append(solution)
        elif os.path.isfile(file_or_directory):
            solution = load_file(file_or_directory)
            if solution:
                dir_data.append(solution)
        if dir_data:
            fixed_only = "dfp" in file_or_directory
            if args.instances and os.path.isdir(args.instances):
                dir_data += get_additional_instances(args.instances, regex, solved_names, fixed_only=fixed_only)
            data.append(dir_data)

    if not data:
        print("no solution data found in the provided paths")
        exit(-1)

    print(len(data))

    gad_by_filename = {instance.file_name: instance for instance in data[0]}
    mmpt_by_filename = {instance.file_name: instance for instance in data[1]}

    i = 0
    for filename, instance in gad_by_filename.items():
        if instance.control_sequence:
            if not mmpt_by_filename[filename].control_sequence:
                i += 1
                print(filename)
    print(i)

    #evaluate_solution_length_difference(data[0], data[1])
    #maze vs cave all
    #data = sum(data, [])
    #plot_maze_vs_cave(data, "all solvers", args.x, args.y, average=True)

    #plot_steps_to_goal(data, ["BFS", "GD", "AD", "GAD"], x_axis=args.x)

    solvers = [
        #"BFS",
        #"GD",
        #"AD",
        #"GGD",
        "GAD",
        #"WSD",
        "MMP",
        "MMPT",
        "DFP",
        "RRT"
    ]

    plot_box_plot_grouped_by_solver(data, solvers, args.x, args.y, outliers=False, average=True)

    # Maze vs cave
    #s = iter(solvers)
    #for dir_data in data:
    #    plot_maze_vs_cave(dir_data, next(s), args.x, args.y, average = True)

    # Number of glues
    #s = iter(solvers)
    #for dir_data in data:
    #    plot_number_of_glues(dir_data, next(s), args.x, args.y)

    # fixed vs notfixed
    #s = iter(solvers)
    #for dir_data in data:
    #    plot_fixed_vs_not_fixed(dir_data, next(s), args.x, args.y, average=True)

    # effect of extra tiles
    #plot_extra_tiles(data, solvers, args.x, args.y, average=True, outliers=True)

    #memory usage
    s = iter(solvers)
    for dir_data in data:
       plot_peak_memory(dir_data, next(s))

    if args.pairplot:
        for dir_data in data:
            pair_plot(dir_data, violin=args.violin)
    else:
        for dir_data in data:
            if args.violin:
                plot_violin(dir_data, args.x, args.y)
                plot_bars(dir_data, args.x)
            else:
                plot(dir_data, args.x, args.y)
    plt.show()

def get_additional_instances(path, regex, solved_names, fixed_only=False):
    instances = []
    for filename in os.listdir(path):
        if not regex.match(filename) or not filename.endswith(".json"):
            continue
        if filename.rsplit('.', 1)[0] in solved_names:
            continue
        if fixed_only and "notfixed" in filename:
            continue
        i = read_instance(os.path.join(path, filename))
        s = SolutionData("", 1, instance=i)
        if "maze" in filename:
            s.board_type = "maze"
        elif "cave" in filename:
            s.board_type = "cave"
        s.file_name = filename.rsplit('.', 1)[0] + "_result.json"
        s.timed_out = True
        instances += [s]
    return instances


def load_file(file):
    with open(file) as f:
        data = json.load(f)
    for required in ["control_sequence", "time_needed"]:
        if required not in data:
            return None
    if "instance" in data:
        data["instance"] = decode_instance(data["instance"])
    solution = SolutionData("", 0)
    for key, value in data.items():
        try:
            setattr(solution, key, value)
        except AttributeError:
            pass
    return solution

def number_of_nodes(solution_data: SolutionData):
    try:
        return solution_data.number_of_nodes
    except AttributeError:
        return 0

def time_needed(solution_data: SolutionData):
    if solution_data.timed_out:
        return float("inf")
    return solution_data.time_needed

def target_shape_size(solution_data: SolutionData):
    return solution_data.instance.target_shape.size

def number_of_tiles(solution_data: SolutionData):
    return len(solution_data.instance.initial_state.get_tiles())

def board_size(solution_data: SolutionData):
    return np.prod(solution_data.instance.initial_state.concrete.size)

def solution_length(solution_data: SolutionData):
    if solution_data.control_sequence is None:
        return float("inf")
    return solution_data.control_sequence_length

def glue_types(solution_data: SolutionData):
     return len(solution_data.instance.initial_state.glue_rules.get_glues())

def is_fixed(solution_data: SolutionData):
    return hasattr(solution_data.instance.initial_state, "fixed_tiles")

def memory_usage(solution_data: SolutionData):
    return solution_data.max_mem_usage / 1000


def evaluate_solution_length_difference(data1, data2, compare_by=board_size):
    ratios = defaultdict(list)
    for instance in data1:
        instance2 = [i for i in data2 if i.file_name == instance.file_name][0]
        if instance.control_sequence_length and instance2.control_sequence_length:
            ratios[compare_by(instance)].append(instance2.control_sequence_length/ instance.control_sequence_length)
    for size, r in ratios.items():
        print(r)
        print(size, "average:", sum(r)/len(r))
        print("standard deviation", np.std(r, ddof=1))
        se = np.std(r, ddof=1) / np.sqrt(np.size(r))
        print("+/-", se)
    all = sum(ratios.values(), [])
    print("total", "average:", sum(all) / len(all))



def steps_to_goal(solution_data: SolutionData):
    board = solution_data.instance.initial_state
    target_shape = solution_data.instance.target_shape
    if len(board.get_tiles()) != target_shape.size:
        return None
    if hasattr(board, "fixed_tiles"):
        return None
    if solution_data.timed_out or solution_data.control_sequence is None:
        return None
    board = deepcopy(board)
    tile = next(iter(board.get_tiles()))
    i = 0
    while tile.parent.size != target_shape.size:
        board.step(solution_data.control_sequence[i])
        board.activate_glues()
        i += 1
    return len(solution_data.control_sequence) - i

def pair_plot(data, violin=False):
    d = {}
    for name, function in AXIS_FUNCTIONS.items():
        d[AXIS_LABELS[name]] = [function(instance) for instance in data]

    # set status depending on timeout or no timeout
    d["status"] = []
    for x in d["time[s]"]:
        d["status"].append("timed out" if x == float("inf") else "solved")

    data_frame = DataFrame(data=d)

    for key, values_list in data_frame.items():
        maximum = max(filter((float("inf")).__ne__, values_list))
        data_frame[key] = [maximum if x == float("inf") else x for x in values_list]

    # seaborn.pairplot(data_frame, dropna=True, hue="status", markers=["o", "X"], diag_kind="hist", hue_order=["solved", "timed out"])
    pairplot_stacked(data_frame, violin=violin)

def pairplot_stacked(df, violin=False):
    # below for the histograms on the diagonal

    g = seaborn.PairGrid(data=df, hue="status", hue_order=["solved", "timed out"])
    if violin:
        offdiag = seaborn.violinplot
        g.map_offdiag(offdiag, style=df["status"], markers={"solved": "o", "timed out": "X"}, cut=0, scale="count")
    else:
        offdiag = seaborn.scatterplot
        g.map_offdiag(offdiag, style=df["status"], markers={"solved": "o", "timed out": "X"})

    d = {}
    def func(x, **kwargs):
        ax = plt.gca()

        if not ax in d.keys():
            d[ax] = {"data": [], "color": []}
        d[ax]["data"].append(x)
        d[ax]["color"].append(kwargs.get("color"))

    g.map_diag(func)
    for ax, dic in d.items():
        ax.hist(dic["data"], color=dic["color"], histtype="barstacked")


def get_consistent_solver_colors(data_frame: DataFrame, base_color_palette="pastel"):
    used_hues = []
    color_palette = []
    full_palette = seaborn.color_palette(base_color_palette)
    for i, hue in enumerate(SOLVER_HUE_ORDER):
        if hue in data_frame["solver"].unique():
            used_hues += [hue]
            color_palette += [full_palette[i]]
    return color_palette, used_hues


def plot_steps_to_goal(solution_data_sets, dataset_labels, x_axis=None, average=True):
    seaborn.set(font_scale=FONTSCALE)
    data_frame = DataFrame()
    labels_iter = iter(dataset_labels)

    for data_set in solution_data_sets:
        data_set = [i for i in data_set if number_of_tiles(i) == target_shape_size(i)]
        d = {}
        d["status"] = ["timed out" if instance.timed_out else "terminated" for instance in data_set]
        solver_label = next(labels_iter)
        if x_axis is not None:
            x_function = AXIS_FUNCTIONS[x_axis]
            x_axis_label = AXIS_LABELS[x_axis]
            d[x_axis_label] = [x_function(instance) for instance in data_set]
            if x_axis == "size":
                d[x_axis_label] = [str(int(math.sqrt(size))) + "x" + str(int(math.sqrt(size))) for size in d[x_axis_label]]
        d["solver"] = [solver_label] * len(d["status"])
        d["steps to target"] = [steps_to_goal(instance) for instance in data_set]
        data_frame = data_frame.append(DataFrame(data=d))

    palette, hue_order = get_consistent_solver_colors(data_frame)

    dropped_nan = data_frame[data_frame["steps to target"].notnull()]
    seaborn.boxplot(x=None if x_axis is None else AXIS_LABELS[x_axis], y="steps to target", data=dropped_nan,
                    hue="solver", hue_order=hue_order, flierprops=dict(markerfacecolor='0.50', markersize=5),
                    palette=palette, showmeans=average,
                    meanprops={"marker": "o",
                               "markerfacecolor": "white",
                               "markeredgecolor": "black",
                               "markersize": "10"})
    plt.legend(loc="upper left", prop={'size': LEGENDSIZE})
    plt.show()


def get_complementary(color):
    r, g, b = color
    r_comp = max(r,b,g) + min(r,b,g) - r
    g_comp = max(r,b,g) + min(r,b,g) - g
    b_comp = max(r,b,g) + min(r,b,g) - b
    return (r_comp, g_comp, b_comp)

def plot_maze_vs_cave(data_set, label, x_axis, y_axis, outliers=False, average=False):
    seaborn.set(font_scale=FONTSCALE)
    data_frame = DataFrame()

    x_function = AXIS_FUNCTIONS[x_axis]
    x_axis_label = AXIS_LABELS[x_axis]
    y_function = AXIS_FUNCTIONS[y_axis]
    y_axis_label = AXIS_LABELS[y_axis]

    d = {}
    d[x_axis_label] = [x_function(instance) for instance in data_set]
    if x_axis == "size":
        d[x_axis_label] = [str(int(math.sqrt(size))) + "x" + str(int(math.sqrt(size))) for size in d[x_axis_label]]
    d[y_axis_label] = [y_function(instance) for instance in data_set]
    d["status"] = ["timed out" if instance.timed_out else "terminated" for instance in data_set]
    d["board type"] = [instance.board_type + " (" + label + ")" for instance in data_set]
    d["solver"] = [label] * len(d[x_axis_label])

    data_frame = data_frame.append(DataFrame(data=d))

    terminated = data_frame[data_frame["status"] == "terminated"]

    hue_order = ["cave" " (" + label + ")", "maze" " (" + label + ")"]

    if y_axis_label == "solution length":
        solved = data_frame[data_frame["solution length"] != float("inf")]
        solved = solved[solved["solution length"] != 0]
        # seaborn.violinplot(x=x_axis_label, y=y_axis_label, data=solved, hue="solver", hue_order=hue_order
        #                   , palette=palette, scale="width", cut=0, dropna=True)
        seaborn.boxplot(x=x_axis_label, y=y_axis_label, data=solved, hue="board type", hue_order=hue_order,
                        palette="muted", flierprops=dict(markerfacecolor='0.50', markersize=5), showfliers=outliers,
                    showmeans=average,
                    meanprops={"marker": "o",
                               "markerfacecolor": "white",
                               "markeredgecolor": "black",
                               "markersize": "10"})
        plt.legend(loc="upper left", prop={'size': LEGENDSIZE})
    else:
        #seaborn.violinplot(x=x_axis_label, y=y_axis_label, data=terminated, hue="solver", hue_order=hue_order,x
        #                palette=palette, scale="width", cut = 0)
        seaborn.boxplot(x=x_axis_label, y=y_axis_label, data=terminated, hue="board type",
                        palette="muted", flierprops=dict(markerfacecolor='0.50', markersize=5), showfliers=outliers,
                    showmeans=average,
                    meanprops={"marker": "o",
                               "markerfacecolor": "white",
                               "markeredgecolor": "black",
                               "markersize": "10"})
        plt.legend(loc="upper left", prop={'size': LEGENDSIZE})
        plt.axhline(y=600, color="r", linestyle="dotted")

    plt.show()

    def fraction_solved(x):
        return x[x.str.contains("terminated")].count() / len(x)

    solved_counts = data_frame.groupby(["board type", x_axis_label])["status"].apply(fraction_solved)\
        .to_frame(name="fraction of instances").reset_index()

    seaborn.catplot(
        data=solved_counts, kind="bar",
        x=x_axis_label, y="fraction of instances", hue="board type",
        ci="sd", palette="muted", hue_order=hue_order, legend_out=False
    )

    plt.legend(loc="upper right", prop={'size': LEGENDSIZE})

    plt.show()


def plot_number_of_glues(data_set, label, x_axis, y_axis, outliers=False, average=False):
    seaborn.set(font_scale=FONTSCALE)
    data_frame = DataFrame()

    title = "glue types" + " (" + label + ")"

    x_function = AXIS_FUNCTIONS[x_axis]
    x_axis_label = AXIS_LABELS[x_axis]
    y_function = AXIS_FUNCTIONS[y_axis]
    y_axis_label = AXIS_LABELS[y_axis]

    d = {}
    d[x_axis_label] = [x_function(instance) for instance in data_set]
    if x_axis == "size":
        d[x_axis_label] = [str(int(math.sqrt(size))) + "x" + str(int(math.sqrt(size))) for size in d[x_axis_label]]
    d[y_axis_label] = [y_function(instance) for instance in data_set]
    d["status"] = ["timed out" if instance.timed_out else "terminated" for instance in data_set]
    d["glue types"] = [glue_types(instance) for instance in data_set]
    d["solver"] = [label] * len(d[x_axis_label])

    data_frame = data_frame.append(DataFrame(data=d))

    terminated = data_frame[data_frame["status"] == "terminated"]

    hue_order = list(sorted(set(d["glue types"])))

    if y_axis_label == "solution length":
        solved = data_frame[data_frame["solution length"] != float("inf")]
        solved = solved[solved["solution length"] != 0]
        # seaborn.violinplot(x=x_axis_label, y=y_axis_label, data=solved, hue="solver", hue_order=hue_order
        #                   , palette=palette, scale="width", cut=0, dropna=True)
        seaborn.boxplot(x=x_axis_label, y=y_axis_label, data=solved, hue="glue types", hue_order=hue_order,
                        palette="muted", flierprops=dict(markerfacecolor='0.50', markersize=5), showfliers=outliers,
                    showmeans=average,
                    meanprops={"marker": "o",
                               "markerfacecolor": "white",
                               "markeredgecolor": "black",
                               "markersize": "10"})
        plt.legend(loc="upper left", prop={'size': LEGENDSIZE}, title=title)
    else:
        #seaborn.violinplot(x=x_axis_label, y=y_axis_label, data=terminated, hue="solver", hue_order=hue_order,x
        #                palette=palette, scale="width", cut = 0)
        seaborn.boxplot(x="glue types", y=y_axis_label, data=terminated, #hue="glue types",
                        palette="muted", flierprops=dict(markerfacecolor='0.50', markersize=5), showfliers=outliers,
                    showmeans=average,
                    meanprops={"marker": "o",
                               "markerfacecolor": "white",
                               "markeredgecolor": "black",
                               "markersize": "10"})
        plt.legend(loc="upper left", prop={'size': LEGENDSIZE}, title=title)
        #plt.axhline(y=600, color="r", linestyle="dotted")

    plt.show()


    def fraction_solved(x):
        return x[x.str.contains("terminated")].count() / len(x)

    solved_counts = data_frame.groupby(["glue types"])["status"].apply(fraction_solved)\
        .to_frame(name="fraction of instances").reset_index()

    seaborn.catplot(
        data=solved_counts, kind="bar",
        x="glue types", y="fraction of instances", #hue="glue types",
        ci="sd", palette="muted", legend_out=False
    )

    plt.legend(loc="upper right", prop={'size': LEGENDSIZE}, title=title, framealpha=0.5)

    plt.show()


def plot_fixed_vs_not_fixed(data_set, label, x_axis, y_axis, outliers=False, average=False):
    seaborn.set(font_scale=FONTSCALE)
    data_frame = DataFrame()

    title = "problem type " + "(" + label + ")"

    x_function = AXIS_FUNCTIONS[x_axis]
    x_axis_label = AXIS_LABELS[x_axis]
    y_function = AXIS_FUNCTIONS[y_axis]
    y_axis_label = AXIS_LABELS[y_axis]

    d = {}
    d[x_axis_label] = [x_function(instance) for instance in data_set]
    if x_axis == "size":
        d[x_axis_label] = [str(int(math.sqrt(size))) + "x" + str(int(math.sqrt(size))) for size in d[x_axis_label]]
    d[y_axis_label] = [y_function(instance) for instance in data_set]
    d["status"] = ["timed out" if instance.timed_out else "terminated" for instance in data_set]
    d["fixed"] = ["seed tile" if is_fixed(instance) else "no seed tile" for instance in data_set]
    d["solver"] = [label] * len(d[x_axis_label])

    data_frame = data_frame.append(DataFrame(data=d))

    if y_axis_label == "solution length":
        data = data_frame[data_frame["solution length"] != float("inf")]
        data = data[data["solution length"] != 0]
    else:
        data = data_frame[data_frame["status"] == "terminated"]

    hue_order = ["seed tile", "no seed tile"]

    seaborn.boxplot(x=x_axis_label, y=y_axis_label, data=data, hue="fixed", hue_order=hue_order,
                    palette="muted", flierprops=dict(markerfacecolor='0.50', markersize=5), showfliers=outliers,
                    showmeans=average,
                    meanprops={"marker": "o",
                               "markerfacecolor": "white",
                               "markeredgecolor": "black",
                               "markersize": "10"})
    plt.legend(loc="upper left", prop={'size': LEGENDSIZE}, title=title)


    def fraction_solved(x):
        return x[x.str.contains("terminated")].count() / len(x)

    solved_counts = data_frame.groupby(["fixed", x_axis_label])["status"].apply(fraction_solved) \
        .to_frame(name="fraction of instances").reset_index()

    seaborn.catplot(
        data=solved_counts, kind="bar",
        x=x_axis_label, y="fraction of instances", hue="fixed",
        ci="sd", palette="muted", hue_order=hue_order, legend_out=False
    )

    plt.legend(loc="upper right", prop={'size': LEGENDSIZE}, title=title)

    plt.show()


def plot_peak_memory(data_set, label):
    seaborn.set(font_scale=FONTSCALE)
    data_frame = DataFrame()

    x_axis = "time"
    y_axis = "mem"

    x_function = AXIS_FUNCTIONS[x_axis]
    x_axis_label = AXIS_LABELS[x_axis]
    y_function = AXIS_FUNCTIONS[y_axis]
    y_axis_label = AXIS_LABELS[y_axis]

    data_set = [i for i in data_set if hasattr(i, "max_mem_usage")]
    d = {}
    d[x_axis_label] = [x_function(instance) for instance in data_set]
    if x_axis == "size":
        d[x_axis_label] = [str(int(math.sqrt(size))) + "x" + str(int(math.sqrt(size))) for size in d[x_axis_label]]
    d[y_axis_label] = [y_function(instance) for instance in data_set]
    d["status"] = ["timed out" if instance.timed_out else "terminated" for instance in data_set]
    d["fixed"] = ["seed tile" if is_fixed(instance) else "no seed tile" for instance in data_set]
    d["solver"] = [label] * len(d[x_axis_label])

    data_frame = data_frame.append(DataFrame(data=d))

    palette, hue_order = get_consistent_solver_colors(data_frame, base_color_palette="tab10")

    seaborn.scatterplot(x=x_axis_label, y=y_axis_label, data=data_frame, marker="o", s=175, palette=palette, hue_order=hue_order, hue="solver")
    plt.legend(loc="upper left", prop={'size': LEGENDSIZE})
    #plt.axvline(x=600, color="r", linestyle="dotted")
    plt.show()

def plot_extra_tiles(solution_data_sets, dataset_labels, x_axis, y_axis, outliers=False, average=True):
    seaborn.set(font_scale=FONTSCALE)
    data_frame = DataFrame()

    x_function = AXIS_FUNCTIONS[x_axis]
    x_axis_label = AXIS_LABELS[x_axis]
    y_function = AXIS_FUNCTIONS[y_axis]
    y_axis_label = AXIS_LABELS[y_axis]

    labels_iter = iter(dataset_labels)

    for data_set in solution_data_sets:
        data_set = [i for i in data_set if target_shape_size(i)==10]
        d = {}
        d[x_axis_label] = [x_function(instance) for instance in data_set]
        if x_axis == "size":
            d[x_axis_label] = [str(int(math.sqrt(size))) + "x" + str(int(math.sqrt(size))) for size in d[x_axis_label]]
        d[y_axis_label] = [y_function(instance) for instance in data_set]
        d["status"] = ["timed out" if instance.timed_out else "terminated" for instance in data_set]
        solver_label = next(labels_iter)
        d["solver"] = [solver_label] * len(d[x_axis_label])
        d["extra tiles"] = [number_of_tiles(instance) - target_shape_size(instance) for instance in data_set]
        data_frame = data_frame.append(DataFrame(data=d))

    if y_axis_label == "solution length":
        data = data_frame[data_frame["solution length"] != float("inf")]
        data = data[data["solution length"] != 0]
    else:
        data = data_frame[data_frame["status"] == "terminated"]

    palette, hue_order = get_consistent_solver_colors(data)

    seaborn.boxplot(x="extra tiles", y=y_axis_label, data=data, hue="solver", hue_order=hue_order,
                    palette=palette, flierprops=dict(markerfacecolor='0.50', markersize=5), showfliers=outliers,
                    showmeans=average,
                    meanprops={"marker": "o",
                               "markerfacecolor": "white",
                               "markeredgecolor": "black",
                               "markersize": "10"})
    if y_axis_label == "time[s]":
        pass
        plt.axhline(y=600, color="r", linestyle="dotted")
    plt.legend(loc="upper left", prop={'size': LEGENDSIZE})

    plt.show()

    def fraction_solved(x):
        return x[x.str.contains("terminated")].count() / len(x)

    solved_counts = data_frame.groupby(["solver", "extra tiles"])["status"].apply(fraction_solved) \
        .to_frame(name="fraction of instances").reset_index()

    seaborn.catplot(
        data=solved_counts, kind="bar",
        x="extra tiles", y="fraction of instances", hue="solver",
        ci="sd", palette=palette, hue_order=hue_order, legend_out=False
    )

    plt.legend(loc="upper left", prop={'size': LEGENDSIZE})

    plt.show()


def plot_box_plot_grouped_by_solver(solution_data_sets, dataset_labels, x_axis, y_axis, outliers=False, average=False):
    seaborn.set(font_scale=FONTSCALE)
    data_frame = DataFrame()

    x_function = AXIS_FUNCTIONS[x_axis]
    x_axis_label = AXIS_LABELS[x_axis]
    y_function = AXIS_FUNCTIONS[y_axis]
    y_axis_label = AXIS_LABELS[y_axis]

    labels_iter = iter(dataset_labels)

    for data_set in solution_data_sets:
        d = {}
        d[x_axis_label] = [x_function(instance) for instance in data_set]
        if x_axis == "size":
            d[x_axis_label] = [str(int(math.sqrt(size))) + "x" + str(int(math.sqrt(size))) for size in d[x_axis_label]]
        d[y_axis_label] = [y_function(instance) for instance in data_set]
        d["status"] = ["timed out" if instance.timed_out else "terminated" for instance in data_set]
        solver_label = next(labels_iter)
        d["solver"] = [solver_label] * len(d[x_axis_label])

        data_frame = data_frame.append(DataFrame(data=d))


    if y_axis_label == "solution length":
        data = data_frame[data_frame["solution length"] != float("inf")]
        data = data[data["solution length"] != 0]

    else:
        data = data_frame[data_frame["status"] == "terminated"]

    palette, hue_order = get_consistent_solver_colors(data)

    seaborn.boxplot(x=x_axis_label, y=y_axis_label, data=data, hue="solver", hue_order=hue_order,
                    palette=palette, flierprops=dict(markerfacecolor='0.50', markersize=5), showfliers=outliers,
                    showmeans=average, #order=["40x40","80x80", "120x120"],
                    meanprops={"marker": "o",
                               "markerfacecolor": "white",
                               "markeredgecolor": "black",
                               "markersize": "10"})
    if y_axis_label == "time[s]":
        pass
        plt.axhline(y=600, color="r", linestyle="dotted")
    plt.legend(loc="upper left", prop={'size': LEGENDSIZE})
    plt.show()

    def fraction_solved(x):
        return x[x.str.contains("terminated")].count() / len(x)

    solved_counts = data_frame.groupby(["solver", x_axis_label])["status"].apply(fraction_solved)\
        .to_frame(name="fraction of instances").reset_index()

    seaborn.catplot(
        data=solved_counts, kind="bar",
        x=x_axis_label, y="fraction of instances", hue="solver",
        ci="sd", palette=palette, hue_order=hue_order, legend_out=False#, order=["40x40","80x80", "120x120"]
    )
    #plt.ylim(0, 1.0)
    plt.legend("", loc="upper right", prop={'size': 0}, framealpha=0.0)

    plt.show()


def plot_bars(data, x_axis):
    d = {}
    for instance in data:
        x = AXIS_FUNCTIONS[x_axis](instance)
        if x not in d.keys():
            d[x] = (0, 0)
        if instance.timed_out:
            d[x] = (d[x][0], d[x][1] + 1)
        else:
            d[x] = (d[x][0] + 1, d[x][1])

    labels = list(sorted(d.keys()))

    terminated = []
    timed_out = []

    for label in labels:
        total = d[label][0] + d[label][1]
        terminated += [d[label][0] / total]
        timed_out += [d[label][1] / total]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots()
    # rects1 = ax.bar(x, terminated, width, label='terminated')
    rects2 = ax.bar(x, timed_out, width, label='timed out')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel("Fraction of instances", fontsize=18)
    #ax.set_title("Fraction timed_out instances by " + AXIS_LABELS[x_axis])

    ax.set_xticks(x, labels)
    ax.legend()

    #def autolabel(rects):
    #    for rect in rects:
    #        height = rect.get_height()
    #        ax.annotate('{}'.format(height),
    #                    xy=(rect.get_x() + rect.get_width() / 2, height),
    #                    xytext=(0, 3),  # 3 points vertical offset
    #                    textcoords="offset points",
    #                    ha='center', va='bottom')

    #autolabel(rects1)
    #autolabel(rects2)

    fig.tight_layout()
    plt.show()

def plot_violin(data, x_axis, y_axis):
    x_function = AXIS_FUNCTIONS[x_axis]
    y_function = AXIS_FUNCTIONS[y_axis]
    x = [x_function(instance) for instance in data]
    y = [y_function(instance) for instance in data]

    data = defaultdict(list)
    for i in range(len(x)):
        if y[i] != float("inf"):
            data[x[i]] += [y[i]]

    x_values = []
    sorted_data = []
    for x_value in sorted(data.keys()):
        x_values += [x_value]
        sorted_data.append(data[x_value])

    plt.violinplot(sorted_data, x_values)
    plt.xlabel(AXIS_LABELS[x_axis])
    plt.ylabel(AXIS_LABELS[y_axis])

def plot(data, x_axis, y_axis):
    x_function = AXIS_FUNCTIONS[x_axis]
    y_function = AXIS_FUNCTIONS[y_axis]
    x = [x_function(instance) for instance in data]
    y = [y_function(instance) for instance in data]

    plt.scatter(x, y, marker='.')
    plt.xlabel(AXIS_LABELS[x_axis])
    plt.ylabel(AXIS_LABELS[y_axis])

    # represent float("inf") values with x at the edges of the plot
    _, max_x = plt.gca().get_xlim()
    _, max_y = plt.gca().get_ylim()

    highx = [(max_x, b) for a, b in zip(x, y) if a == float("inf")]
    highy = [(a, max_y) for a, b in zip(x, y) if b == float("inf")]
    points = highx + highy

    x = [a for a, _ in points]
    y = [b for _, b in points]

    plt.scatter(x, y, marker='x', alpha=0.3)

AXIS_FUNCTIONS = {
    "nodes": number_of_nodes,
    "time": time_needed,
    "tiles": number_of_tiles,
    "size": board_size,
    "solution_length": solution_length,
    "glues": glue_types,
    "target_size": target_shape_size,
    "mem": memory_usage
}

AXIS_LABELS = {
    "nodes": "number of nodes",
    "time": "time[s]",
    "tiles": "number of tiles",
    "size": "board size",
    "solution_length": "solution length",
    "glues": "glue types",
    "target_size": "target shape size",
    "mem": "peak memory usage[MB]"
}

if __name__ == '__main__':
    main()
