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
    # 1:1, A =~ 0.5M, 1M, 1.5M
    (700,700),
    (1000,1000),
    (1300,1300),
    # 2:1, A =~ 0.5M, 1M, 1.5M
    (1000,500),
    (1400,700),
    (1800,900),
    # 3:1, A =~ 0.5M, 1M, 1.5M
    (1200,400),
    (1800,600),
    (2100,700)
]

SHAPES = {
    "3x3": factory.threeByThree(),
    "5x2": factory.fiveByTwo(),
    "2x5": factory.twoByFive(),
    "10x1": factory.linePolyVert(10,10),
    "1x10": factory.linePolyHori(10,0)
    #"3x3_Ring": factory.threeByThreeRing()
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
def randomTargetAssembly(path, seed, ncubes, nred, boardSize, sorting):
    sorting = OptionSorting(sorting)
    boardSize = tuple(boardSize)
    factory.generator.seed(seed)
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


def assemblyForTargetShape(path, startSeed, samplesPerSize, shapes: list, optionSortings: list):
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


def assemblyForTargetSize(path, startSeed, samplesPerSize, startSize, endSize, optionSortings: list):
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


def main():
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
    # Put the experiments to execute here
    #assemblyForTargetSize(path, 100, 150, 12, 12, OptionSorting.list())
    #assemblyForBoardSize(path, 100, 100, BOARDSIZES, [OptionSorting.GROW_SMALLEST])
    assemblyForTargetShape(path, 100, 2, SHAPES.keys(), [OptionSorting.MIN_DIST])
    #TCSA_analysis(path, 0, 200, 5, 12)


if __name__ == "__main__":
    main()