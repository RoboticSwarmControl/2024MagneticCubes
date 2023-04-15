import time

from sim.state import *
from plan.plan import *
import plan.factory as factory
import plan.globa as globa

def customTargetAssembly(target: Polyomino, seed=0, samples=1):
    plans = {}
    globalTime = 0
    for _ in range(samples):
        factory.generator.seed(seed)
        config = factory.randomConfigWithCubes((800,800), target.size(), target.nred())
        t0 = time.time()
        plan = globa.planTargetAssembly(config, target)
        t1 = time.time()
        dt = t1 -t0
        globalTime += dt
        plans[seed] = plan
        print(f"[{seed}] {plan}with {round(plan.cost(),2)}rad in {round(dt, 2)}s\n")
        seed += 1
    fails = []
    for key, plan in plans.items():
        if plan.state != PlanState.SUCCESS:
            fails.append(key)
    print(f"Time summed: {round(globalTime, 2)}s, {len(fails)}/{samples} FAILURES: {fails}")
    while True:
        inp = input("Select seed to play:")
        plans[int(inp)].execute()
        
def randomTargetAssembly(ncubes, seed=0, samples=1):
    plans = {}
    globalTime = 0
    for _ in range(samples):
        factory.generator.seed(seed)
        target = factory.randomPoly(ncubes)
        print(f"Polyomino to assemble:\n{target}")
        config = factory.randomConfigWithCubes((800,800), target.size(), target.nred())
        t0 = time.time()
        plan = globa.planTargetAssembly(config, target)
        t1 = time.time()
        dt = t1 -t0
        globalTime += dt
        plans[seed] = plan
        print(f"[{seed}] {plan}with {round(plan.cost(),2)}rad in {round(dt, 2)}s\n")
        seed += 1
    fails = []
    for key, plan in plans.items():
        if plan.state != PlanState.SUCCESS:
            fails.append(key)
    print(f"Time summed: {round(globalTime, 2)}s, {len(fails)}/{samples} FAILURES: {fails}")
    while True:
        inp = input("Select seed to play:")
        plans[int(inp)].execute()

if __name__ == "__main__":
    customTargetAssembly(factory.threeByThreeRing(), 1, 1)