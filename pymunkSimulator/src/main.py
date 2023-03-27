"""
Magnetic cube simulator.

After creating a Simulation custom configurations can be loaded.
After start you can execute motions with rotate() and pivotWalk() or the _nowait equivalents.
Runtime user interaction is also possible. Look in simulation.py method __userInputs()__ for key bindings.

@author: Aaron T Becker, Kjell Keune
"""
import math
import time
from pymunk import Vec2d

from sim.simulation import Simulation
from sim.motion import *
from sim.state import Configuration, Cube

def sandbox_onMac():
    sim1 = Simulation()
    sim1.start_onMac()

def sandbox():
    sim1 = Simulation()
    #sim1.loadConfig(Configuration((600,600), math.radians(90), {}))
    sim1.start()

def demo1():
    cube1 = Cube(0)
    pos1 = Vec2d(150,50)
    cube2 = Cube(1)
    pos2 = Vec2d(200, 150)
    pwLeft = PivotWalk(PivotWalk.LEFT)
    pwRight = PivotWalk(PivotWalk.RIGHT)
    rot90ccw = Rotation(math.radians(-90))
    d0 = pos1.get_distance(pos2)
    sim = Simulation(drawing=False)
    sim.loadConfig(Configuration((800,800), math.radians(90),{cube1: pos1,cube2: pos2}))
    t0 = time.time()
    while True:
        sim.start()
        sim.executeMotion(pwLeft)
        sim.executeMotion(pwLeft)
        sim.stop()
        config = sim.saveConfig()
        d = config.getPosition(cube1).get_distance(config.getPosition(cube2))
        if not abs(d - d0) < 5:
            break
    savepoint = sim.saveConfig()
    sim.start()
    sim.executeMotion(rot90ccw)
    for i in range(4):
        sim.executeMotion(pwLeft)
    sim.loadConfig(savepoint)
    sim.executeMotion(rot90ccw)
    for i in range(6):
        sim.executeMotion(pwRight)    
    t1 = time.time()
    print("Execution time: ", (t1 - t0), "s")
    sim.enableDraw()
    

if __name__ == "__main__":
    sandbox()