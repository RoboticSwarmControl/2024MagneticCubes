import json
import math
import os
from datetime import datetime
from threading import Event, Thread
import time
import slurminade

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
     
    def __init__(self, targetSize, targetNred, targetShape, boardSize, optionSorting, planData=None) -> None:
        self.targetSize = targetSize
        self.targetNred = targetNred
        self.targetShape = targetShape
        self.boardSize = boardSize
        self.optionSorting = optionSorting
        if planData == None:
            self.planData = []
        else:
            self.planData = planData


def writeExperiment(data: ExperimentData, path):
    with open(path, 'w') as file:
        json.dump(data, file, indent=4, default=lambda o: o.__dict__)

def loadExperiment(path) -> ExperimentData:
    with open(path, 'r') as file:
        data = json.load(file)
    data["boardSize"] = tuple(data["boardSize"])
    planData = []
    for p in data["planData"]:
        planData.append(PlanData(**p))
    data["planData"] = planData
    return ExperimentData(**data)


@slurminade.slurmify()
def batchTargetAssemblyForSize(dirPath, startSeed, samplesPerSize, startSize, endSize, optionSortings: list):
    boardSize = (1000,1000)
    for ncubes in range(startSize, endSize + 1):
        nred = math.floor(ncubes / 2)
        for optVal in optionSortings:
            sorting = OptionSorting(optVal)
            print(f"size:{ncubes}, sorting={sorting.name}")
            filePath = os.path.join(dirPath, f"TAFS-{ncubes}-{sorting.name}.json")
            if os.path.exists(filePath):
                expData = loadExperiment(filePath)
            else:
                expData = ExperimentData(ncubes, nred, "random", boardSize, sorting.name)
            endSeed = startSeed + samplesPerSize - 1
            for seed in range(startSeed, endSeed + 1):
                factory.generator.seed(seed)
                target = factory.randomPoly(ncubes, nred)
                initial = factory.randomConfigWithCubes(boardSize, ncubes, nred)
                print(f"  seed:{seed}")
                t0 = time.monotonic()
                plan = globalp.planTargetAssembly(initial, target, sorting)
                dt = time.monotonic() - t0
                if plan.state == PlanState.SUCCESS:
                    success = True
                else:
                    success = False
                planData = PlanData(seed, success, dt, plan.cost(), plan.nconfig, plan.nlocal, plan.ntcsa, len(plan.actions))
                expData.planData.append(planData)
                # wirte results every 5 seeds
                if (seed - startSeed + 1) % 5 == 0 or seed == endSeed:
                    writeExperiment(expData, filePath)
            print("\n")


def main():
    dateTime = datetime.now()
    path = os.path.join(RESULT_DIR, dateTime.strftime("%m-%d-%H-%M-%S"))
    os.mkdir(path)
    
    batchTargetAssemblyForSize.distribute(path, 100, 50, 5, 7, [0, 1, 2])
    batchTargetAssemblyForSize.distribute(path, 150, 50, 5, 7, [0, 1, 2])

    batchTargetAssemblyForSize.distribute(path, 100, 25, 8, 9, [0, 1, 2])
    batchTargetAssemblyForSize.distribute(path, 125, 25, 8, 9, [0, 1, 2])
    batchTargetAssemblyForSize.distribute(path, 150, 25, 8, 9, [0, 1, 2])
    batchTargetAssemblyForSize.distribute(path, 175, 25, 8, 9, [0, 1, 2])

    batchTargetAssemblyForSize.distribute(path, 100, 25, 10, 10, [0, 1, 2])
    batchTargetAssemblyForSize.distribute(path, 125, 25, 10, 10, [0, 1, 2])
    batchTargetAssemblyForSize.distribute(path, 150, 25, 10, 10, [0, 1, 2])
    batchTargetAssemblyForSize.distribute(path, 175, 25, 10, 10, [0, 1, 2])

if __name__ == "__main__":
    main()