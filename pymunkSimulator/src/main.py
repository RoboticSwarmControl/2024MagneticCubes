"""
Magnetic cube simulator.

After creating a Simulation custom configurations can be loaded.
After start you can execute motions with rotate() and pivotWalk() or the _nowait equivalents.
Runtime user interaction is also possible. Look in simulation.py method __userInputs()__ for key bindings.

@author: Aaron T Becker, Kjell Keune
"""
import math
from simulation import Simulation
from configuration import Configuration
from cube import Cube
from motion import LEFT, RIGHT

if __name__ == "__main__":
    sim1 = Simulation()
    sim1.loadConfig(Configuration(0, 0, [Cube((100,100),0), Cube((300,300),1)]))
    sim1.start()
    sim1.rotate(math.radians(90))

    