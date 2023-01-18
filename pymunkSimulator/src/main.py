"""
Magnetic cube simulator.

After creating a Simulation custom configurations can be loaded.
After start you can execute motions with rotate() and pivotWalk() or the _nowait equivalents.
Runtime user interaction is also possible. Look in simulation.py method __userInputs()__ for key bindings.

@author: Aaron T Becker, Kjell Keune
"""
import math

import time
from sim.simulation import Simulation
from sim.motion import LEFT, RIGHT
from config.configuration import Configuration
from config.cube import Cube, RAD

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

def demo1():
    sim = Simulation(drawing=False)
    cube1 = Cube(0)
    pos1 = (150,50)
    cube2 = Cube(1)
    pos2 = (200, 150)
    sim.start()
    sim.loadConfig(Configuration(math.radians(90),0,{cube1: pos1,cube2: pos2}))
    d0 = dis(pos1, pos2)
    while True:
        sim.pivotWalk(LEFT)
        sim.pivotWalk(LEFT)
        config = sim.saveConfig()
        d = dis(config.getPosition(cube1), config.getPosition(cube2))
        if not abs(d - d0) < 5:
            break
    savepoiont = sim.saveConfig()
    sim.rotate(math.radians(-90))
    for i in range(5):
        sim.pivotWalk(LEFT)
    time.sleep(1)
    sim.loadConfig(savepoiont)
    sim.rotate(math.radians(-90))
    for i in range(5):
        sim.pivotWalk(RIGHT)
    sim.enableDraw()

    
def dis(a, b):
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)


if __name__ == "__main__":
    sandbox()

    