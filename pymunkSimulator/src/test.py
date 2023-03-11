import sys
sys.path.append("..")
import time
from pymunk import Vec2d

from sim.simulation import Simulation
from sim.state import *
from plan.local import LocalPlanner
from plan.plan import Plan, PlanState
from plan.factory import *

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
    
def randomConfigTest():
    width = 1000
    height = 1000
    ncubes = 10
    sim = Simulation()
    sim.start()
    while True:
        config = randomConfig((width, height), ncubes, ncubes)
        sim.loadConfig(config)
        input("New config:")
        
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
    c2 = Cube(1)
    c3 = Cube(0)
    c4 = Cube(0)
    c5 = Cube(1)
    c6 = Cube(0)
    con1 = Configuration(0,0,{c1:(100,100), c2:(200,200), c3:(300,300)})
    con2 = Configuration(0,0,{c5:(200,200), c6:(300,300), c4:(100,100)})
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

def simControlTest():
    sim = Simulation()
    sim.start()
    time.sleep(1)
    sim.loadConfig(Configuration((800,800), 0, 0, {Cube(0): (100,100)}))
    time.sleep(1)
    sim.loadConfig(Configuration((1000,400), 0, 0, {Cube(0): (500,100)}))
    time.sleep(1)
    sim.disableDraw()
    sim.loadConfig(Configuration((400,400), 0, 0, {Cube(0): (200,200)}))
    sim.enableDraw()

def randomPolyTest():
    samples = 50
    polys = []
    for _ in range(samples):
        polys.append(randomPoly(10, 5))
    polys = PolyCollection(polys)
    print(polys)

def localPlanner():
    planer = LocalPlanner(drawing=True)
    c1 = Cube(1) #red
    p1 = (485, 587)
    c2 = Cube(0) #blue
    p2 = (36, 34)
    ed2 = Direction.WEST
    ang = math.radians(150)
    #config = Configuration((800,800),math.radians(90),0,{cubeA: (50,400),cubeB: (150,300)})
    #connected to side failure case
    config = Configuration((800,800),ang, 0,{c1: p1, c2: p2})
    t0 = time.time()
    plan = planer.planCubeConnect(config,c1,c2,ed2)
    t1 = time.time()
    print(f"{plan.state}: {round(plan.cost(),2)}rad in {round(t1 - t0, 2)}s")
    print(f"{c1.type} at {config.getPosition(c1)} --{ed2}-> {c2.type} at {config.getPosition(c2)}. Ang={round(math.degrees(ang))}")

def randomTwoCubeConnect():
    planer = LocalPlanner()
    plans = {}
    globalTime = 0
    samples = 20
    for i in range(samples):
        config = randomConfig((800,800), 2, 1)
        c1 = config.getCubes()[0]
        c2 = config.getCubes()[1]
        ed = Direction(random.randint(0,3))
        t0 = time.time()
        plan = planer.planCubeConnect(config, c1, c2, ed)
        t1 = time.time()
        dt = t1 -t0
        globalTime += dt
        plans[i] = plan
        print(f"[{i}] {plan.state}: {round(plan.cost(),2)}rad in {round(dt, 2)}s")
        print(f"{c1.type} at {config.getPosition(c1)} --{ed}-> {c2.type} at {config.getPosition(c2)}. Ang={round(math.degrees(config.magAngle))}")
    fails = []
    for key, plan in plans.items():
        if plan.state == PlanState.FAILURE:
            fails.append(key)
    print(f"Time summed: {round(globalTime, 2)}, {len(fails)}/{samples} FAILURES")
    print(fails)
    while True:
        inp = input("Select index to play:")
        planer.executePlan(plans[int(inp)])


if __name__ == "__main__":
    randomTwoCubeConnect()