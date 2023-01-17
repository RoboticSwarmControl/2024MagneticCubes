"""
Magnetic cube simulator.

After creating a Simulation custom configurations can be loaded.
After start you can execute motions with rotate() and pivotWalk() or the _nowait equivalents.
Runtime user interaction is also possible. Look in simulation.py method __userInputs()__ for key bindings.

@author: Aaron T Becker, Kjell Keune
"""
import math

from sim.simulation import Simulation
from sim.motion import LEFT, RIGHT
from config.configuration import Configuration
from config.cube import Cube

def test1():
    sim1 = Simulation(drawing=True)
    sim1.start()
    sim1.loadConfig(Configuration(0, 0, {Cube(0): (100,100), Cube(1): (300,300)}))
    sim1.rotate(math.radians(90))
    configSave = sim1.saveConfig()
    sim1.rotate(math.radians(90))
    for i in range(5):
        sim1.pivotWalk(LEFT)
    sim1.loadConfig(configSave)
    sim1.stop()
    sim1.start()
    for i in range(5):
        sim1.pivotWalk(LEFT)
    sim1.drawingActive = True

def sandbox():
    sim1 = Simulation()
    sim1.start()

if __name__ == "__main__":
    sandbox()

    