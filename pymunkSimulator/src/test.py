

import time
from pymunk import Vec2d
from sim.handling import Renderer

from sim.simulation import Simulation
from sim.state import *
import plan.local as local
from plan.plan import *
import plan.factory as factory
from sim.motion import Rotation, PivotWalk

def vecAngleTest():
    a = Vec2d(1, 0)
    b = Vec2d(1, 1)
    angCross = math.asin(a.cross(b) / (a.length * b.length))
    angDot = math.acos(a.dot(b) / (a.length * b.length))
    angPymunk = a.get_angle_degrees_between(b)
    print(f"Dot: {math.degrees(angDot)}")
    print(f"Cross: {math.degrees(angCross)}")
    print(f"Pymunk: {angPymunk}")

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

def directPolyAngCalc():
    seed = 1
    factory.generator.seed(seed)
    p1 = factory.linePolyVert(3, vertical=True)
    c1ref = p1.getCubes()[0]
    p2 = factory.linePolyVert(6, vertical=False)
    c2ref = p2.getCubes()[0]
    cf = factory.configWithPolys((800,800), math.radians(90), [p1,p2],[(300,400),(600,400)])
    cf = local.singleUpdate(cf)
    p1 = cf.getPolyominoes().getForCube(c1ref)
    p2 = cf.getPolyominoes().getForCube(c2ref)
    
    step = 5
    rotAng = step
    angDiff = {}
    while rotAng < 360:
        r1 = cf.getPosition(c1ref) - cf.getCOM(p1)
        r2 = cf.getPosition(c2ref) - cf.getCOM(p2)
        r1 = r1.rotated_degrees(step)
        r2 = r2.rotated_degrees(step)
        rotAng += step


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
        c1,c2,e2 = factory.randomConnection(p1,p2)
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
        polys.append(factory.linePolyVert(10, 1, False))
    polys = PolyCollection(polys)
    print(polys)



#-------------------------------------------------------------------------------------------------------------------



def motionAnalysis():
    maxSize = 10
    sim = Simulation(False, False)
    pWalk = PivotWalk(PivotWalk.RIGHT, PivotWalk.DEFAULT_PIVOT_ANG)
    rot10 = Rotation(math.radians(10))
    rot20 = Rotation(math.radians(20))
    rot45 = Rotation(math.radians(45))
    rot90 = Rotation(math.radians(90))
    rot180 = Rotation(math.radians(180))
    for size in range(1,maxSize+1):
        #size = 4
        config = factory.configWithPolys((1000,1000), math.radians(90), [factory.linePolyVert(size)], [(400,600)])
        refCube = config.getCubes()[0]
        save0 = local.singleUpdate(config)
        sim.loadConfig(save0)
        t0 = time.time()
        sim.start()
        sim.executeMotion(pWalk)
        sim.stop()
        t1 = time.time()
        save1 = sim.saveConfig()
        poly0 = save0.getPolyominoes().getForCube(refCube)
        poly1 = save1.getPolyominoes().getForCube(refCube)
        displacementIdeal = save0.getPivotWalkingVec(poly0, pWalk.pivotAng, pWalk.direction)
        displacement = save1.getCOM(poly1) - save0.getCOM(poly0)
        angDiff = displacement.get_angle_degrees_between(displacementIdeal)
        lenDiff = (displacement.length / displacementIdeal.length) * 100
        print(f"Poly size {size}:")
        print(f"[{pWalk}] Time: {round(t1 -t0, 4)}s, AngDiff: {round(angDiff,3)}°, LenOfIdeal: {round(lenDiff, 3)}%")
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

def holeConnectionTest():
    cubeA = Cube(0)
    cubeB = Cube(1)
    edgeB = Direction.WEST
    polyA = Polyomino(cubeA)
    cube1 = Cube(1)
    cube2 = Cube(1)
    polyA.connect(cube1, cubeA, Direction.NORTH)
    polyA.connect(Cube(0), cube1, Direction.EAST)
    polyA.connect(cube2, cubeA, Direction.SOUTH)
    polyA.connect(Cube(0), cube2, Direction.EAST)
    polyB = Polyomino(cubeB)
    print(polyA)
    config = factory.randomConfigWithPolys((800,800), [polyA,polyB])
    plan = local.planCubeConnect(config, cubeA, cubeB, edgeB)
    print(plan)

def twoCostumCubeConnect():
    c1 = Cube(1) #red
    p1 = (304, 528)
    c2 = Cube(0) #blue
    p2 = (397, 487)
    ed2 = Direction.NORTH
    ang = math.radians(52)
    config = Configuration((800,800),ang,{c1: p1, c2: p2})
    t0 = time.time()
    plan = local.planCubeConnect(config,c1,c2,ed2)
    t1 = time.time()
    print(f"{plan.state}: {round(plan.cost(),2)}rad in {round(t1 - t0, 2)}s")
    print(f"{c1.type} at {config.getPosition(c1)} --{ed2}-> {c2.type} at {config.getPosition(c2)}. Ang={round(math.degrees(ang))}")
    plan.execute()


def twoCubeConnect():
    #----------------------
    seed = 12
    samples = 20
    #----------------------
    plans = {}
    globalTime = 0
    for _ in range(samples):
        factory.generator.seed(seed)
        config = factory.randomConfigWithCubes((800,800), 2, 1)
        c1 = config.getCubes()[0]
        c2 = config.getCubes()[1]
        ed = Direction(factory.generator.randint(0,3))
        t0 = time.time()
        plan = local.planCubeConnect(config, c1, c2, ed)
        t1 = time.time()
        dt = t1 -t0
        globalTime += dt
        plans[seed] = plan
        print(f"[{seed}] {plan}: {round(plan.cost(),2)}rad in {round(dt, 2)}s")
        #print(f"{c1.type} at {config.getPosition(c1)} --{ed}-> {c2.type} at {config.getPosition(c2)}. Ang={round(math.degrees(config.magAngle))}")
        seed += 1
    fails = []
    for key, plan in plans.items():
        if plan.state != PlanState.SUCCESS:
            fails.append(key)
    print(f"Time summed: {round(globalTime, 2)}s, {len(fails)}/{samples} FAILURES: {fails}")
    while True:
        inp = input("Select seed to play:")
        plans[int(inp)].execute()


def twoPolyConnect(seed = 0, samples = 1, polyMaxSize = 4 ,forceMaxSize = True):
    plans = {}
    globalTime = 0
    for _ in range(samples):
        factory.generator.seed(seed)
        while True:
            if forceMaxSize:
                p1 = factory.randomPoly(polyMaxSize)
                p2 = factory.randomPoly(polyMaxSize)
            else:
                p1 = factory.randomPoly(factory.generator.randint(1,polyMaxSize))
                p2 = factory.randomPoly(factory.generator.randint(1,polyMaxSize))
            c1, c2, ed = factory.randomConnection(p1, p2, True, True)
            if c1 != None:
                break
        config = factory.randomConfigWithPolys((800,800),[p1,p2])
        t0 = time.time()
        plan = local.planCubeConnect(config, c1, c2, ed)
        t1 = time.time()
        dt = t1 -t0
        globalTime += dt
        plans[seed] = plan
        print(f"[{seed}] {plan}: {round(plan.cost(),2)}rad in {round(dt, 2)}s")
        #print(f"{c1.type} at {config.getPosition(c1)} --{ed}-> {c2.type} at {config.getPosition(c2)}. Ang={round(math.degrees(config.magAngle))}")
        seed += 1
    fails = []
    for key, plan in plans.items():
        if plan.state != PlanState.SUCCESS:
            fails.append(key)
    print(f"Time summed: {round(globalTime, 2)}s, {len(fails)}/{samples} FAILURES: {fails}")
    while True:
        inp = input("Select seed to play:")
        #print(f"Is plan valid? = {plans[int(inp)].validate()}")
        plans[int(inp)].execute()


def twoPolyConnect_othersOnBoard(seed = 0, samples = 1, polyMaxSize = 4 , others = 2):
    plans = {}
    globalTime = 0
    for _ in range(samples):
        factory.generator.seed(seed)
        while True:
            p1 = factory.randomPoly(factory.generator.randint(1,polyMaxSize))
            p2 = factory.randomPoly(factory.generator.randint(1,polyMaxSize))
            c1, c2, ed = factory.randomConnection(p1, p2, True, True)
            if c1 != None:
                break
        polys = [p1,p2]
        for _ in range(others):
            polys.append(factory.randomPoly(factory.generator.randint(1,polyMaxSize)))
        config = factory.randomConfigWithPolys((1000,1000),polys)
        t0 = time.time()
        plan = local.planCubeConnect(config, c1, c2, ed)
        t1 = time.time()
        dt = t1 -t0
        globalTime += dt
        plans[seed] = plan
        print(f"[{seed}] {plan}: {round(plan.cost(),2)}rad in {round(dt, 2)}s")
        #print(f"{c1.type} at {config.getPosition(c1)} --{ed}-> {c2.type} at {config.getPosition(c2)}. Ang={round(math.degrees(config.magAngle))}")
        seed += 1
    fails = []
    for key, plan in plans.items():
        if plan.state != PlanState.SUCCESS:
            fails.append(key)
    print(f"Time summed: {round(globalTime, 2)}s, {len(fails)}/{samples} FAILURES: {fails}")
    while True:
        inp = input("Select seed to play:")
        #print(f"Is plan valid? = {plans[int(inp)].validate()}")
        plans[int(inp)].execute()


def twoPolyConnect_ncubes(seed=0, samples=1, ncubes=10):
    plans = {}
    globalTime = 0
    for _ in range(samples):
        cubesLeft = ncubes
        factory.generator.seed(seed)
        while True:
            p1 = factory.randomPoly(factory.generator.randint(1, cubesLeft - 1))
            p2 = factory.randomPoly(factory.generator.randint(1, cubesLeft - p1.size()))
            c1, c2, ed = factory.randomConnection(p1, p2, True, True)
            if c1 != None:
                cubesLeft -= (p1.size() + p2.size())
                break
        polys = [p1,p2]
        while cubesLeft > 0:
            p = factory.randomPoly(factory.generator.randint(1,cubesLeft))
            polys.append(p)
            cubesLeft -= p.size()
        config = factory.randomConfigWithPolys((1000,1000),polys)
        t0 = time.time()
        plan = local.planCubeConnect(config, c1, c2, ed)
        t1 = time.time()
        dt = t1 -t0
        globalTime += dt
        plans[seed] = plan
        print(f"[{seed}] {plan}: {round(plan.cost(),2)}rad in {round(dt, 2)}s")
        #print(f"{c1.type} at {config.getPosition(c1)} --{ed}-> {c2.type} at {config.getPosition(c2)}. Ang={round(math.degrees(config.magAngle))}")
        seed += 1
    fails = []
    for key, plan in plans.items():
        if plan.state != PlanState.SUCCESS:
            fails.append(key)
    print(f"Time summed: {round(globalTime, 2)}s, {len(fails)}/{samples} FAILURES: {fails}")
    while True:
        inp = input("Select seed to play:")
        if inp == 'v':
            invalid = []
            for seed, plan in plans.items():
                if not plan.validate():
                    invalid.append(seed)
            print(f"{len(invalid)}/{samples} invalid: {invalid}")
        else:
            inp = int(inp)
            plans[inp].execute()

if __name__ == "__main__":
    vecAngleTest()