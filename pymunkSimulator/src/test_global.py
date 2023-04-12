from sim.state import *
from plan.plan import *
import plan.factory as factory
import plan.globa as globa

def fourCube_LShapeAssembly(seed = 0):
    factory.generator.seed(seed)
    target = factory.fourCube_LShape()
    config = factory.randomConfigWithCubes((800,800), target.size(), 2)
    plan = globa.planTargetAssembly(config, target)
    plan.execute()

if __name__ == "__main__":
    fourCube_LShapeAssembly(1)