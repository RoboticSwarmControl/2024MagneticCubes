"""
Here you can find documented examples on how to use the framework to write your own control programs
using local and global planner.

@author: Kjell Keune
"""
import math
from com.state import Configuration, Cube
from com.motion import PivotWalk, Rotation
from sim.simulation import Simulation
from plan.globalp import planTargetAssembly
import com.factory as fac

def mmc_video():
    # initial cubes
    cubes = {
            Cube(1): (17 *Cube.RAD, 1.3 * Cube.RAD),
            Cube(1): (1.3 *Cube.RAD, 11 * Cube.RAD),
            Cube(0): (8.5 *Cube.RAD, 11 * Cube.RAD),
            Cube(0): (11 *Cube.RAD, 19 * Cube.RAD)
    }
    # motions
    motions = []
    for i in range(15):
        motions.append(PivotWalk(PivotWalk.LEFT, math.radians(15)))
    motions.append(Rotation(-math.radians(90)))
    for i in range(11):
        motions.append(PivotWalk(PivotWalk.LEFT, math.radians(15)))
    # sequence like video
    config = Configuration((22 * Cube.RAD, 22 * Cube.RAD), math.radians(90), cubes)
    sim = Simulation()
    sim.loadConfig(config)
    for motion in motions:
        sim.executeMotion(motion)

def mmc_video_plan():
    # initial cubes
    cubes = {
            Cube(1): (17 *Cube.RAD, 1.3 * Cube.RAD),
            Cube(1): (1.3 *Cube.RAD, 11 * Cube.RAD),
            Cube(0): (8.5 *Cube.RAD, 11 * Cube.RAD),
            Cube(0): (11 *Cube.RAD, 19 * Cube.RAD)
    }
    config = Configuration((22 * Cube.RAD, 22 * Cube.RAD), math.radians(90), cubes)
    plan = planTargetAssembly(config, fac.fourCube_LShape())
    plan.execute()

def main():
    mmc_video()

if __name__ == "__main__":
    main()