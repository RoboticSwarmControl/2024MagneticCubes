

import time
from pymunk import Vec2d

from sim.simulation import Simulation
from sim.state import *
from plan.local import LocalPlanner
from plan.plan import Plan, PlanState
import plan.factory as factory
from sim.motion import Rotation, PivotWalk

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

def nearestWallTest():
    size = (500,500)
    cube1 = Cube(0)
    pos1 = (410,100)
    cube2 = Cube(1)
    pos2 = (50, 400)
    config = Configuration(size, 0, {cube1: pos1, cube2: pos2})
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
        config = factory.randomConfigWithCubes((width, height), ncubes, ncubes)
        sim.loadConfig(config)
        input("New config:")

def connectPolyTest():
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
    print(p2.connectPoly(c5, p1, c0, Direction.WEST))

def connectPolyPossibleTest():
    sim = Simulation(True, False)
    seed = 0
    while True:
        factory.generator.seed(seed)
        p1 = factory.randomPoly(5)
        p2 = factory.randomPoly(5)
        c1,c2,e2 = factory.randomPossibleConnection(p1,p2)
        slideInEast = p1.connectPolyPossible(c1, p2, c2, e2, Direction.EAST)
        slideInWest = p1.connectPolyPossible(c1, p2, c2, e2, Direction.WEST)
        print(f"seed: [{seed}]")
        print(f"c1 --{e2}-> c2")
        print(f"p1 --EAST-> p2: {slideInEast}")
        print(f"p1 --WEST-> p2: {slideInWest}")
        config = factory.configWithPolys((1500, 800), math.radians(90),[p1,p2],[(300,500),(1000,500)])
        sim.renderer.markedCubes.add(c1)
        sim.renderer.markedCubes.add(c2)
        sim.loadConfig(config)
        sim.start()
        input("Next:")
        sim.stop()
        sim.renderer.markedCubes.clear()
        seed += 1

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

def randomPolyTest():
    samples = 5
    polys = []
    for _ in range(samples):
        polys.append(factory.linePoly(10, 1, False))
    polys = PolyCollection(polys)
    print(polys)


def motionAnalysis():
    maxSize = 10
    sim = Simulation(False, False)
    pl = LocalPlanner()
    pWalk = PivotWalk(PivotWalk.RIGHT, PivotWalk.DEFAULT_PIVOT_ANG)
    rot10 = Rotation(math.radians(10))
    rot20 = Rotation(math.radians(20))
    rot45 = Rotation(math.radians(45))
    rot90 = Rotation(math.radians(90))
    rot180 = Rotation(math.radians(180))
    for size in range(1,maxSize+1):
        #size = 4
        config = factory.configWithPolys((1000,1000), math.radians(90), [factory.linePoly(size)], [(400,600)])
        refCube = config.getCubes()[0]
        save0 = pl.singleUpdate(config)
        sim.loadConfig(save0)
        t0 = time.time()
        sim.start()
        sim.executeMotion(pWalk)
        sim.stop()
        t1 = time.time()
        save1 = sim.saveConfig()
        dt = t1 -t0
        poly0 = save0.getPolyominoes().getPoly(refCube)
        poly1 = save1.getPolyominoes().getPoly(refCube)
        displacementIdeal = save0.getPivotWalkingVec(poly0, pWalk.pivotAng, pWalk.direction)
        displacement = save1.getCOM(poly1) - save0.getCOM(poly0)
        angDiff = displacement.get_angle_degrees_between(displacementIdeal)
        lenDiff = (displacementIdeal.length - displacement.length) / (2 * Cube.RAD)
        print(f"Poly size {size}:")
        print(f"[{pWalk}] Time: {round(t1 -t0, 4)}s, AngDiff: {round(angDiff,3)}°, LenDiff: {round(lenDiff, 3)}ø")
        t0 = time.time()
        sim.start()
        sim.executeMotion(rot10)
        sim.stop()
        t1 = time.time()
        print(f"[{rot10}] Time: {round(t1 -t0, 4)}s")
        t0 = time.time()
        sim.start()
        sim.executeMotion(rot20)
        sim.stop()
        t1 = time.time()
        print(f"[{rot20}] Time: {round(t1 -t0, 4)}s")
        t0 = time.time()
        sim.start()
        sim.executeMotion(rot45)
        sim.stop()
        t1 = time.time()
        print(f"[{rot45}] Time: {round(t1 -t0, 4)}s")
        t0 = time.time()
        sim.start()
        sim.executeMotion(rot90)
        sim.stop()
        t1 = time.time()
        print(f"[{rot90}] Time: {round(t1 -t0, 4)}s")
        t0 = time.time()
        sim.start()
        sim.executeMotion(rot180)
        sim.stop()
        t1 = time.time()
        print(f"[{rot180}] Time: {round(t1 -t0, 4)}s\n")


def twoCostumCubeConnect():
    planer = LocalPlanner()
    c1 = Cube(1) #red
    p1 = (304, 528)
    c2 = Cube(0) #blue
    p2 = (397, 487)
    ed2 = Direction.NORTH
    ang = math.radians(52)
    config = Configuration((800,800),ang,{c1: p1, c2: p2})
    t0 = time.time()
    plan = planer.planCubeConnect(config,c1,c2,ed2)
    t1 = time.time()
    print(f"{plan.state}: {round(plan.cost(),2)}rad in {round(t1 - t0, 2)}s")
    print(f"{c1.type} at {config.getPosition(c1)} --{ed2}-> {c2.type} at {config.getPosition(c2)}. Ang={round(math.degrees(ang))}")
    planer.executePlan(plan)


def twoCubeConnect():
    seed = 12
    planer = LocalPlanner()
    plans = {}
    globalTime = 0
    samples = 2
    for i in range(samples):
        factory.generator.seed(seed)
        config = factory.randomConfigWithCubes((800,800), 2, 1)
        c1 = config.getCubes()[0]
        c2 = config.getCubes()[1]
        ed = Direction(factory.generator.randint(0,3))
        t0 = time.time()
        plan = planer.planCubeConnect(config, c1, c2, ed)
        t1 = time.time()
        dt = t1 -t0
        globalTime += dt
        plans[i] = plan
        print(f"Seed: {seed}")
        print(f"[{i}] {plan}: {round(plan.cost(),2)}rad in {round(dt, 2)}s")
        #print(f"{c1.type} at {config.getPosition(c1)} --{ed}-> {c2.type} at {config.getPosition(c2)}. Ang={round(math.degrees(config.magAngle))}")
        seed += 1
    fails = []
    for key, plan in plans.items():
        if plan.state != PlanState.SUCCESS:
            fails.append(key)
    print(f"Time summed: {round(globalTime, 2)}, {len(fails)}/{samples} FAILURES")
    print(fails)
    while True:
        inp = input("Select index to play:")
        planer.executePlan(plans[int(inp)])


def twoPolyConnect():
    #----------------------
    seed = 9
    size = 4
    #----------------------
    planer = LocalPlanner()
    plans = {}
    globalTime = 0
    samples = 1
    for i in range(samples):
        factory.generator.seed(seed)
        p1 = factory.randomPoly(size)
        p2 = factory.randomPoly(size)
        config = factory.randomConfigWithPolys((800,800),[p1,p2])
        c1, c2, ed = factory.randomPossibleConnection(p1, p2)
        t0 = time.time()
        plan = planer.planCubeConnect(config, c1, c2, ed)
        t1 = time.time()
        dt = t1 -t0
        globalTime += dt
        plans[i] = plan
        print(f"Seed: {seed}")
        print(f"[{i}] {plan}: {round(plan.cost(),2)}rad in {round(dt, 2)}s")
        #print(f"{c1.type} at {config.getPosition(c1)} --{ed}-> {c2.type} at {config.getPosition(c2)}. Ang={round(math.degrees(config.magAngle))}")
        seed += 1
    fails = []
    for key, plan in plans.items():
        if plan.state != PlanState.SUCCESS:
            fails.append(key)
    print(f"Time summed: {round(globalTime, 2)}, {len(fails)}/{samples} FAILURES")
    print(fails)
    while True:
        inp = input("Select index to play:")
        planer.executePlan(plans[int(inp)])


if __name__ == "__main__":
    twoPolyConnect()