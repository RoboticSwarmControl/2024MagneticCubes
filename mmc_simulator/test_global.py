import time

from com.state import *
from plan.plan import *
import com.factory as factory
import plan.globalp as globalp

def customTargetAssembly(target: Polyomino, seed=0, samples=1):
    plans = {}
    globalTime = 0
    for _ in range(samples):
        factory.generator.seed(seed)
        config = factory.randomConfigWithCubes((800,800), target.size(), target.nred())
        t0 = time.monotonic()
        plan = globalp.planTargetAssembly(config, target)
        t1 = time.monotonic()
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
        
def randomTargetAssembly(ncubes, seed=0, samples=1, halfRed=False):
    plans = {}
    globalTime = 0
    for _ in range(samples):
        factory.generator.seed(seed)
        if halfRed:
            target = factory.randomPoly(ncubes, round(ncubes / 2))
        else:
            target = factory.randomPoly(ncubes)
        print(f"Polyomino to assemble:\n{target}")
        config = factory.randomConfigWithCubes((800,800), target.size(), target.nred())
        t0 = time.monotonic()
        plan = globalp.planTargetAssembly(config, target)
        t1 = time.monotonic()
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


def singleTargetAssembly(seed, ncubes, nred, boardSize, sorting: OptionSorting):
    factory.generator.seed(seed)
    target = factory.randomPoly(ncubes, nred)
    initial = factory.randomConfigWithCubes(boardSize, ncubes, nred)
    print(f"Target to assemble:\n{target}\n")
    t0 = time.monotonic()
    plan = globalp.planTargetAssembly(initial, target, sorting)
    dt = time.monotonic() - t0
    print(f"{plan}with {round(plan.cost(),2)}rad in {round(dt, 2)}s\n")
    while True:
        input("Play plan:")
        plan.execute()


if __name__ == "__main__":
    singleTargetAssembly(1, 10 ,5, (1000,1000), OptionSorting.GROW_SMALLEST)