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

slurminade.update_default_configuration(
    partition="alg",
    constraint="alggen03",
    mail_user="k.keune@tu-braunschweig.de",
    mail_type="ALL",
)

RESULT_DIR = "../results"
BATCH_MAX_SIZE = 35

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

@slurminade.slurmify()
def targetAssembly(path, seed, target: Polyomino, boardSize, sorting):
    factory.generator.seed(seed)
    initial = factory.randomConfigWithCubes(boardSize, target.size(), target.nred())
    print(f"  seed:{seed}")
    t0 = time.monotonic()
    plan = globalp.planTargetAssembly(initial, target, sorting)
    dt = time.monotonic() - t0
    if plan.state == PlanState.SUCCESS:
        success = True
    else:
        success = False
    filePath =  os.path.join(path, f"seed-{seed}.json")
    writeData(filePath, PlanData(seed, success, dt, plan.cost(), plan.nconfig, plan.nlocal, plan.ntcsa, len(plan.actions)))

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


def targetAssemblyForSize(path, startSeed, samplesPerSize, startSize, endSize, optionSortings: list):
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
    targetAssemblyForSize(path, 100, 50, 10, 10, [OptionSorting.MIN_DIST, OptionSorting.GROW_LARGEST, OptionSorting.GROW_SMALLEST])


if __name__ == "__main__":
    main()