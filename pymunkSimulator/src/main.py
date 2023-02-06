"""
Magnetic cube simulator.

After creating a Simulation custom configurations can be loaded.
After start you can execute motions with rotate() and pivotWalk() or the _nowait equivalents.
Runtime user interaction is also possible. Look in simulation.py method __userInputs()__ for key bindings.

@author: Aaron T Becker, Kjell Keune
"""
import math
import time

from util import *
from sim.simulation import Simulation
from sim.motion import *
from state import Configuration, Cube

def sandbox():
    sim1 = Simulation()
    sim1.start()

def demo1():
    cube1 = Cube(0)
    pos1 = (150,50)
    cube2 = Cube(1)
    pos2 = (200, 150)
    t0 = time.time()
    sim = Simulation(drawing=False)
    sim.start()
    t1 = time.time()
    sim.loadConfig(Configuration(math.radians(90),0,{cube1: pos1,cube2: pos2}))
    d0 = distance(pos1, pos2)
    while True:
        sim.pivotWalk(PivotWalk.LEFT)
        sim.pivotWalk(PivotWalk.LEFT)
        config = sim.saveConfig()
        d = distance(config.getPosition(cube1), config.getPosition(cube2))
        if not abs(d - d0) < 5:
            break
    savepoiont = sim.saveConfig()
    sim.rotate(math.radians(-90))
    for i in range(4):
        sim.pivotWalk(PivotWalk.LEFT)
    sim.loadConfig(savepoiont)
    sim.rotate(math.radians(-90))
    for i in range(6):
        sim.pivotWalk(PivotWalk.RIGHT)      
    t2 = time.time()
    sim.enableDraw()
    print("Init time: ", (t1 - t0), "s")
    print("Execution time: ", (t2 - t1), "s")



if __name__ == "__main__":
    sandbox()
    

    