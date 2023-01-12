"""
Magnetic cube simulator.

Right now it only creates a Simulation with two cubes.

TODO interaction with the simulation (pivotwalk, rotate) with user inputs
"""
import math
from simulation import Simulation
from configuration import Configuration
from cube import Cube
from motion import LEFT, RIGHT
import time

if __name__ == "__main__":
    sim1 = Simulation(800, 800, 60)
    sim1.loadConfig(Configuration(0, 0, [Cube((100,100),0), Cube((300,300),1)]))
    sim1.start()
    sim1.rotate_nowait(math.pi / 2)
    for i in range(5):
        sim1.pivotWalk_nowait(RIGHT)
    for i in range(5):
        sim1.pivotWalk_nowait(LEFT)
    input("Press Enter to exit:")
    sim1.stop()
    