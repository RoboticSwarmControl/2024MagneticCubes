import time

from com.state import *
from plan.plan import *
import com.factory as factory
import plan.globalp as globalp


def randomTargetAssembly(seed, ncubes, nred, boardSize, sorting: OptionSorting):
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

def customTargetAssembly(seed, target: Polyomino, boardSize, sorting: OptionSorting):
    factory.generator.seed(seed)
    initial = factory.randomConfigWithCubes(boardSize, target.size(), target.nred())
    print(f"Target to assemble:\n{target}\n")
    t0 = time.monotonic()
    plan = globalp.planTargetAssembly(initial, target, sorting)
    dt = time.monotonic() - t0
    print(f"{plan}with {round(plan.cost(),2)}rad in {round(dt, 2)}s\n")
    while True:
        input("Play plan:")
        plan.execute()

if __name__ == "__main__":
    customTargetAssembly(1, factory.threeByThreeRing(), (1000,1000), OptionSorting.MIN_DIST)
    #randomTargetAssembly(1, 10 ,5, (1000,1000), OptionSorting.GROW_SMALLEST)