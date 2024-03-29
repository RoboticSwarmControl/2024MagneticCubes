"""
You can call a desired experiment with its parameters in the `main()` method.

When executing this script you can define an output folder with `python3 experiment.py -o yourOutputFolder`
The experiment data will be stored in `results/yourOutputFolder`.
If the output folder already exists, new instances will be added and existing ones will be skipped. 

@author: Kjell Keune
"""
import json
import math
import os
from datetime import datetime
from threading import Event, Thread
import time
import slurminade
import argparse

from com.state import *
from plan.plan import *
import com.factory as factory
import plan.globalp as globalp

RESULT_DIR = "../results"

BOARDSIZES = [
    (700,700),
    (1000,500),
    (1200,400),
    (1000,1000),
    (1400,700),
    (1800,600),
    (1300,1300),
    (1800,900),
    (2100,700)
]

SHAPES = {
    "3x3": factory.threeByThree(),
    "3x3cb": factory.threeByThreeCB(),
    "5x2": factory.fiveByTwo(),
    "5x2cb": factory.fiveByTwoCB(),
    "2x5": factory.twoByFive(),
    "2x5cb": factory.twoByFiveCB(),
    "10x1": factory.linePolyVert(10,10),
    "10x1cb": factory.tenByOneCB(),
    "1x10": factory.linePolyHori(10,0),
    "C": factory.letterC(),
    "S": factory.letterS(),
    "A": factory.letterA(),
    "O": factory.letterO(),
    "I": factory.letterI(),
    "H": factory.letterH(),
    "Plus": factory.letterPlus()
}


slurminade.update_default_configuration(
    partition="alg",
    constraint="alggen03",
    mail_user="k.keune@tu-braunschweig.de",
    mail_type="ALL",
)

BATCH_MAX_SIZE = 40

class PlanData:
     
    def __init__(self, seed, success, time, cost, nconfig, nlocal, ntcsa, localsToGoal) -> None:
        self.seed = seed
        self.success = success
        self.time = time
        self.cost = cost
        self.nconfig = nconfig
        self.nlocal = nlocal
        self.ntcsa = ntcsa
        self.localsToGoal = localsToGoal

class ExperimentData:
     
    def __init__(self, targetSize, targetNred, targetShape, boardSize, optionSorting) -> None:
        self.targetSize = targetSize
        self.targetNred = targetNred
        self.targetShape = targetShape
        self.boardSize = boardSize
        self.optionSorting = optionSorting


def writeData(path, data):
    with open(path, 'w') as file:
        json.dump(data, file, indent=4, default=lambda o: o.__dict__)

def loadPlanData(path) -> PlanData:
    with open(path, 'r') as file:
        data = json.load(file)
    return PlanData(**data)

def loadExperimentData(path) -> ExperimentData:
    with open(path, 'r') as file:
        data = json.load(file)
    data["boardSize"] = tuple(data["boardSize"])
    return ExperimentData(**data)

def loadExperimentSet(path) -> dict:
    exp_plan_data = {}
    for fn1 in os.listdir(path):
        filePath = os.path.join(path, fn1)
        if not os.path.isfile(filePath):
            continue
        exp = loadExperimentData(filePath)
        exp_plan_data[exp] = []
        dataPath = os.path.join(path, os.path.splitext(fn1)[0])
        for fn2 in os.listdir(dataPath):
            exp_plan_data[exp].append(loadPlanData(os.path.join(dataPath, fn2)))
    return exp_plan_data


def TCSA_analysis(path, startSeed, samplesPerSize, startSize, endSize):
    filePath = os.path.join(path, "TCSA.json")
    if os.path.exists(filePath):   
        with open(filePath, 'r') as file:
            data = json.load(file)
            print("Data loaded")
    else:
        data = {}
    t0 = time.monotonic()
    for ncubes in range(startSize, endSize + 1):
        print(f"targetSize = {ncubes}")
        endSeed = startSeed + samplesPerSize - 1
        nred = math.floor(ncubes / 2)
        if not str(ncubes) in data:
            data[str(ncubes)] = {}
        for seed in range(startSeed, endSeed + 1):
            if str(seed) in data[str(ncubes)]:
                print(f"skipping seed = {seed}")
                continue
            factory.generator.seed(seed)
            poly = factory.randomPoly(ncubes, nred)
            tcsa = globalp.TwoCutSubassemblyGraph(poly)
            data[str(ncubes)][str(seed)] = {"nodes": tcsa.nodeCount(), "edges": tcsa.edgeCount()}
    dt = time.monotonic() - t0
    print(f"execution time: {round(dt, 2)}s")
    with open(filePath, 'w') as file:
        json.dump(data, file, indent=4)  


@slurminade.slurmify()
def targetAssembly(path, seed, shapeName, boardSize, sorting):
    target = SHAPES[shapeName]
    sorting = OptionSorting(sorting)
    boardSize = tuple(boardSize)
    factory.generator.seed(seed)
    initial = factory.randomConfigWithCubes(boardSize, target.size(), target.nred())
    print(f"Assembling -> seed={seed}, shape={shapeName}, bsize={boardSize}, sorting={sorting.name}")
    t0 = time.monotonic()
    plan = globalp.planTargetAssembly(initial, target, sorting)
    dt = time.monotonic() - t0
    print("Done!")
    if plan.state == PlanState.SUCCESS:
        success = True
    else:
        success = False
    writeData(path, PlanData(seed, success, dt, plan.cost(), plan.nconfig, plan.nlocal, plan.ntcsa, len(plan.actions)))

@slurminade.slurmify()
def randomTargetAssembly(path, seed, ncubes, nred, boardSize, sorting, lineVert = False):
    sorting = OptionSorting(sorting)
    boardSize = tuple(boardSize)
    factory.generator.seed(seed)
    if lineVert:
        target = factory.linePolyVert(ncubes, nred)
    else:
        target = factory.randomPoly(ncubes, nred)
    initial = factory.randomConfigWithCubes(boardSize, ncubes, nred)
    print(f"Assembling -> seed={seed}, ncubes={ncubes}, nred={nred}, bsize={boardSize}, sorting={sorting.name}")
    t0 = time.monotonic()
    plan = globalp.planTargetAssembly(initial, target, sorting)
    dt = time.monotonic() - t0
    print("Done!")
    if plan.state == PlanState.SUCCESS:
        success = True
    else:
        success = False
    writeData(path, PlanData(seed, success, dt, plan.cost(), plan.nconfig, plan.nlocal, plan.ntcsa, len(plan.actions)))


def assemblyForTargetSize(path, startSeed, samplesPerSize, startSize, endSize, optionSortings: list):
    """
    Experiment for assembling random polyominoes with different target sizes.
    `samplesPerSize` instances will be solved for each target size from `startSize` to `endSize` and each option sorting.
    """
    boardSize = (1000,1000)
    assemblies = 0
    skipped = 0
    with slurminade.Batch(BATCH_MAX_SIZE):
        for ncubes in range(startSize, endSize + 1):
            nred = math.floor(ncubes / 2)
            for sorting in optionSortings:
                # create experiment data and a directory for the planning results
                dataPath = os.path.join(path, f"TAFS-{ncubes}-{sorting.name}")
                if not os.path.exists(dataPath):
                    os.mkdir(dataPath)
                    writeData(dataPath + ".json", ExperimentData(ncubes, nred, "random", boardSize, sorting.name))
                # distribute the planning samples
                endSeed = startSeed + samplesPerSize - 1
                for seed in range(startSeed, endSeed + 1):
                    assemblies += 1
                    filePath = os.path.join(dataPath, f"seed-{seed}.json")
                    if os.path.exists(filePath):
                        skipped += 1
                        continue
                    randomTargetAssembly.distribute(filePath, seed, ncubes, nred, boardSize, sorting.value)
    print(f"Submitted {assemblies - skipped}/{assemblies}.\nSkipped {skipped}.")


def assemblyForTargetShape(path, startSeed, samplesPerSize, shapes: list, optionSortings: list):
    """
    Experiment for assembling specific target shapes.
    `samplesPerSize` instances will be solved for each shape and each option sorting.
    """
    boardSize = (1000,1000)
    assemblies = 0
    skipped = 0
    with slurminade.Batch(BATCH_MAX_SIZE):
        for shapeName in shapes:
            target = SHAPES[shapeName]
            ncubes = target.size()
            nred = target.nred()
            for sorting in optionSortings:
                # create experiment data and a directory for the planning results
                dataPath = os.path.join(path, f"AFTS-{shapeName}-{sorting.name}")
                if not os.path.exists(dataPath):
                    os.mkdir(dataPath)
                    writeData(dataPath + ".json", ExperimentData(ncubes, nred, shapeName, boardSize, sorting.name))
                # distribute the planning samples
                endSeed = startSeed + samplesPerSize - 1
                for seed in range(startSeed, endSeed + 1):
                    assemblies += 1
                    filePath = os.path.join(dataPath, f"seed-{seed}.json")
                    if os.path.exists(filePath):
                        skipped += 1
                        continue
                    targetAssembly.distribute(filePath, seed, shapeName, boardSize, sorting.value)
    print(f"Submitted {assemblies - skipped}/{assemblies}.\nSkipped {skipped}.")


def assemblyForBoardSize(path, startSeed, samplesPerSize, boardSizes: list, optionSortings: list):
    """
    Experiment for assembling random polyominoes in different workspace sizes.
    `samplesPerSize` instances will be solved for each board size and each option sorting.
    """
    ncubes = 9
    nred = math.floor(ncubes / 2)
    assemblies = 0
    skipped = 0
    with slurminade.Batch(BATCH_MAX_SIZE):
        for boardSize in boardSizes:
            for sorting in optionSortings:
                # create experiment data and a directory for the planning results
                dataPath = os.path.join(path, f"AFBS-{boardSize[0]}x{boardSize[1]}-{sorting.name}")
                if not os.path.exists(dataPath):
                    os.mkdir(dataPath)
                    writeData(dataPath + ".json", ExperimentData(ncubes, nred, "random", boardSize, sorting.name))
                # distribute the planning samples
                endSeed = startSeed + samplesPerSize - 1
                for seed in range(startSeed, endSeed + 1):
                    assemblies += 1
                    filePath = os.path.join(dataPath, f"seed-{seed}.json")
                    if os.path.exists(filePath):
                        skipped += 1
                        continue
                    randomTargetAssembly.distribute(filePath, seed, ncubes, nred, boardSize, sorting.value)
    print(f"Submitted {assemblies - skipped}/{assemblies}.\nSkipped {skipped}.")


def assemblyForNred(path, startSeed, samplesPerSize, startNred, endNred, optionSortings: list):
    """
    Experiment for assembling random vertical line-polyominoes with different numbers of red-cubes.
    `samplesPerSize` instances will be solved for each number of red cubes from `startNred` to `endNred` and each option sorting.
    """
    boardSize = (1000,1000)
    ncubes = 10
    assemblies = 0
    skipped = 0
    with slurminade.Batch(BATCH_MAX_SIZE):
        for nred in range(startNred, endNred + 1):
            for sorting in optionSortings:
                # create experiment data and a directory for the planning results
                dataPath = os.path.join(path, f"AFNR-{nred}-{sorting.name}")
                if not os.path.exists(dataPath):
                    os.mkdir(dataPath)
                    writeData(dataPath + ".json", ExperimentData(ncubes, nred, "10x1", boardSize, sorting.name))
                # distribute the planning samples
                endSeed = startSeed + samplesPerSize - 1
                for seed in range(startSeed, endSeed + 1):
                    assemblies += 1
                    filePath = os.path.join(dataPath, f"seed-{seed}.json")
                    if os.path.exists(filePath):
                        skipped += 1
                        continue
                    randomTargetAssembly.distribute(filePath, seed, ncubes, nred, boardSize, sorting.value, True)
    print(f"Submitted {assemblies - skipped}/{assemblies}.\nSkipped {skipped}.")


def assemblyReliability(path, seeds: list, samples, shape, optionSortings: list):
    """
    Experiment to test reliability.
    Each instance seed will be solved `samples` times for each option sorting.
    The target shape stays the same for all instances.
    """
    boardSize = (1000,1000)
    target = SHAPES[shape]
    ncubes = target.size()
    nred = target.nred()
    assemblies = 0
    skipped = 0
    with slurminade.Batch(BATCH_MAX_SIZE):
        for seed in seeds:
            for sorting in optionSortings:
                dataPath = os.path.join(path, f"AR-{shape}-{seed}-{sorting.name}")
                if not os.path.exists(dataPath):
                    os.mkdir(dataPath)
                    writeData(dataPath + ".json", ExperimentData(ncubes, nred, shape, boardSize, sorting.name))
                for i in range(samples):
                    assemblies += 1
                    filePath = os.path.join(dataPath, f"sample-{i}.json")
                    if os.path.exists(filePath):
                        skipped += 1
                        continue
                    targetAssembly.distribute(filePath, seed, shape, boardSize, sorting.value)
    print(f"Submitted {assemblies - skipped}/{assemblies}.\nSkipped {skipped}.")


def main(path):
    """
    Call the experiment you want to execute here.
    When working with slurminade, the work will be automatically distributed on the cluster.
    Otherwise your local machine will do the calculations.
    `path` is the folder where the experiment data is stored, which will be located in `../results`.
    """
    assemblyForTargetSize(path, 0, 2, 5, 8, OptionSorting.list())
    #assemblyForBoardSize(path, 100, 100, BOARDSIZES, [OptionSorting.GROW_SMALLEST])
    #assemblyForTargetShape(path, 100, 100, ["O", "I", "H", "Plus"], OptionSorting.list())
    #assemblyForNred(path, 100, 100, 0, 5, OptionSorting.list())
    #assemblyReliability(path, [100], 100, "3x3", OptionSorting.list())
    #TCSA_analysis(path, 0, 200, 5, 12)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", type=str, help="The name of the output directory. If not specified a new one is created.")
    args = parser.parse_args()
    if not args.o:
        dateTime = datetime.now()
        path = os.path.join(RESULT_DIR, dateTime.strftime("%m-%d-%H-%M-%S"))
    else:
        path = os.path.join(RESULT_DIR, args.o)
    if not os.path.exists(path):
        os.mkdir(path)
    main(path)