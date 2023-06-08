"""
Magnetic cube simulator.

After creating a Simulation custom configurations can be loaded.
After start you can execute motions with rotate() and pivotWalk() or the _nowait equivalents.
Runtime user interaction is also possible. Look in simulation.py method __userInputs()__ for key bindings.

@author: Aaron T Becker, Kjell Keune
"""
import math
from com.state import Configuration, Cube
from com.motion import PivotWalk, Rotation
from sim.simulation import Simulation

def sandbox_onMac():
    sim1 = Simulation()
    sim1.start_onMac()

def sandbox():
    sim1 = Simulation()
    sim1.loadConfig(Configuration((1000,1000), 0, {}))
    sim1.start()

def mmc_video():
    sim = Simulation()
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
    sim.loadConfig(config)
    sim.start()
    sim.stop()
    input()
    sim.start()
    for motion in motions:
        sim.executeMotion(motion)
    

if __name__ == "__main__":
    mmc_video()