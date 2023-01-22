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
from config.cube import Cube
from config.polyomino import Polyomino
from util.direction import Direction
from util.func import *

def polyTest():
    cube0 = Cube(0)
    cube1 = Cube(1)
    cube2 = Cube(1)
    poly = Polyomino(cube0)
    poly.connect(cube1, cube0, Direction.EAST)
    poly.connect(cube2, cube1, Direction.SOUTH)
    print(poly.connectionMap)

def sandbox():
    sim1 = Simulation()
    sim1.start()

def demo1():
    sim = Simulation(drawing=True)
    cube1 = Cube(0)
    pos1 = (150,50)
    cube2 = Cube(1)
    pos2 = (200, 150)
    sim.start()
    sim.loadConfig(Configuration(math.radians(90),0,{cube1: pos1,cube2: pos2}))
    d0 = calculate_distance(pos1, pos2)
    while True:
        sim.pivotWalk(LEFT)
        sim.pivotWalk(LEFT)
        config = sim.saveConfig()
        d = calculate_distance(config.getPosition(cube1), config.getPosition(cube2))
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


if __name__ == "__main__":
    sandbox()
    

    