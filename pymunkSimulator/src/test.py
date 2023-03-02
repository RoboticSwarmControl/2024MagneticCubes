

from state import Cube, Polyomino, Configuration
from util import *
from sim.simulation import Simulation
import time

def polyTest():
    cube0 = Cube(0)
    cube1 = Cube(1)
    cube2 = Cube(1)
    cube3 = Cube(1)
    cube4 = Cube(1)
    cube5 = Cube(1)
    poly = Polyomino(cube0)
    poly.connect(cube1, cube0, Direction.EAST)
    poly.connect(cube2, cube1, Direction.SOUTH)
    print(poly)
    poly.connect(cube3, cube0, Direction.NORTH)
    print(poly)
    poly.connect(cube4, cube0, Direction.SOUTH)
    print(poly)
    poly.connect(cube5, cube0, Direction.WEST)
    print(poly)
    print(poly.getTopRow())
    print(poly.getBottomRow())

def polyEqualTest():
    c0 = Cube(0)
    c1 = Cube(1)
    c2 = Cube(1)
    c3 = Cube(0)
    c4 = Cube(1)
    c5 = Cube(1)
    p1 = Polyomino(c0)
    p1.connect(c1, c0, Direction.EAST)
    p1.connect(c2, c1, Direction.NORTH)
    p2 = Polyomino(c5)
    p2.connect(c4, c5, Direction.WEST)
    p2.connect(c3, c4, Direction.SOUTH)
    print("p1: " + str(p1))
    print("p2: " + str(p2))
    print("equal = " + str(p1 == p2))

def nearestWall():
    size = (500,500)
    cube1 = Cube(0)
    pos1 = (410,100)
    cube2 = Cube(1)
    pos2 = (50, 400)
    config = Configuration(0, 0, {cube1: pos1, cube2: pos2})
    nwallCube1 = config.nearestWall(cube1, size)
    nwallCube2 = config.nearestWall(cube2, size)
    print(str(cube1) + ": " + str(nwallCube1))
    print(str(cube2) + ": " + str(nwallCube2))
    
def randomConfig():
    width = 1000
    height = 1000
    ncubes = 10
    sim = Simulation(width, height)
    sim.start()
    while True:
        config = Configuration.initRandomConfig(ncubes, (width, height))
        sim.loadConfig(config)
        time.sleep(1)
        print("Registerd Cubes: \n" + str(sim.stateHandler.getCubes()))
        print("Polyominoes: \n" + str(sim.stateHandler.polyominoes))
        input()
        
def forceSideConect():
    sim = Simulation(500,500)
    sim.start()
    sim.loadConfig(Configuration(0,0,{Cube(1): (20,20), Cube(1): (20,60)}))
    print("Connects: \n" + str(sim.stateHandler.magConnect))
    print("Polyominoes: \n" + str(sim.stateHandler.polyominoes))
    time.sleep(0.25)
    print("Connects: \n" + str(sim.stateHandler.magConnect))
    print("Polyominoes: \n" + str(sim.stateHandler.polyominoes))

def polyToPolyConnect():
    c0 = Cube(0)
    c1 = Cube(1)
    c2 = Cube(1)
    c3 = Cube(0)
    c4 = Cube(1)
    c5 = Cube(1)
    p1 = Polyomino(c0)
    p1.connect(c1, c0, Direction.EAST)
    p1.connect(c2, c1, Direction.NORTH)
    p2 = Polyomino(c5)
    p2.connect(c4, c5, Direction.SOUTH)
    p2.connect(c3, c4, Direction.WEST)
    print(p1)
    print(p2)
    print(Polyomino.connectPoly(p2, c5, p1, c0, Direction.WEST))

def connectAndPoly():
    sim = Simulation(1000,1000)
    sim.start()
    while True:
        input("Press Enter for information:")
        print("Connects: \n" + str(sim.stateHandler.magConnect))
        print("Polyominoes: \n" + str(sim.stateHandler.polyominoes))

def configurationHash():
    c1 = Cube(0)
    c2 = Cube(0)
    c3 = Cube(0)
    c4 = Cube(0)
    con1 = Configuration(0,0,{c1:(100,100),c2:(200,100),c3:(300,100),c4:(400,100)})
    con2 = Configuration(0,0,{c3:(300,100),c2:(200,100),c1:(100,100),c4:(400,100)})
    print("Hash equality = " + str(hash(con1) == hash(con2)))

def configPoly():
    c0 = Cube(0)
    c1 = Cube(1)
    c2 = Cube(1)
    c3 = Cube(0)
    c4 = Cube(1)
    c5 = Cube(1)
    p1 = Polyomino(c0)
    p1.connect(c1, c0, Direction.EAST)
    p1.connect(c2, c1, Direction.NORTH)
    p2 = Polyomino(c5)
    p2.connect(c4, c5, Direction.SOUTH)
    p2.connect(c3, c4, Direction.WEST)
    con1 = Configuration(0,0,{},[p1, p2])
    print("contain p1:", con1.contains(p1))
    print("contain p2:", con1.contains(p2))

if __name__ == "__main__":
    polyTest()