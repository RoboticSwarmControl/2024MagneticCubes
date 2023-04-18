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
     
    def __init__(self, targetSize, targetNred, targetShape, boardSize, planOption, planData=None) -> None:
        self.targetSize = targetSize
        self.targetNred = targetNred
        self.targetShape = targetShape
        self.boardSize = boardSize
        self.planOption = planOption
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
def batchTargetAssemblyForSize(startSeed, startSize, endSize, samplesPerSize, planOptions):
    dateTime = datetime.now()
    dirPath = os.path.join(RESULT_DIR, dateTime.strftime("%m-%d-%H-%M-%S") + "-TAFS")
    os.mkdir(dirPath)
    boardSize = (1000,1000)
    for ncubes in range(startSize, endSize + 1):
        nred = math.floor(ncubes / 2)
        for optVal in planOptions:
            planOption = PlanOption(optVal)
            expData = ExperimentData(ncubes, nred, "random", boardSize, planOption.name)
            for seed in range(startSeed, startSeed + samplesPerSize):
                factory.generator.seed(seed)
                target = factory.randomPoly(ncubes, nred)
                initial = factory.randomConfigWithCubes(boardSize, ncubes, nred)
                t0 = time.time()
                plan = globalp.planTargetAssembly(initial, target, planOption)
                dt = time.time() - t0
                if plan.state == PlanState.SUCCESS:
                    success = True
                else:
                    success = False
                planData = PlanData(seed, success, dt, plan.cost(), plan.nconfig, plan.nlocal, plan.ntcsa, len(plan.actions))
                expData.planData.append(planData)
            writeExperiment(expData, os.path.join(dirPath, f"{ncubes}-{planOption.name}.json"))


if __name__ == "__main__":
    batchTargetAssemblyForSize.distribute(0, 5, 10, 10, [PlanOption.MIN_DIST.value])