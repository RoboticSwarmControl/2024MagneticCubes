"""
Magnetic cube simulator.

Right now it only creates a Simulation with two cubes.

TODO interaction with the simulation (pivotwalk, rotate) with user inputs
"""

from simulation import Simulation
from configuration import Configuration
from cube import Cube
import time

if __name__ == "__main__":
    sim1 = Simulation(800, 800, 60)
    sim1.loadConfig(Configuration(0, 0, [Cube((100,100),0), Cube((300,300),1)]))
    sim1.start()
    input("Press Enter to exit:")
    sim1.stop()
    