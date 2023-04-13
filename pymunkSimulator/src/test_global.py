import time

from sim.state import *
from plan.plan import *
import plan.factory as factory
import plan.globa as globa

def fourCube_LShapeAssembly(seed = 0):
    factory.generator.seed(seed)
    target = factory.fourCube_LShape()
    config = factory.randomConfigWithCubes((800,800), target.size(), 2)
    t0 = time.time()
    plan = globa.planTargetAssembly(config, target)
    dt = time.time() - t0
    print(f"[{seed}] {plan}with {round(plan.cost(),2)}rad in {round(dt, 2)}s\n")
    while True:
        input("Play plan:")
        plan.execute()
        

if __name__ == "__main__":
    fourCube_LShapeAssembly(2)