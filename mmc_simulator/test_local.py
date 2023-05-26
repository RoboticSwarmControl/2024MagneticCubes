import time

from com.state import *
import plan.localp as local
from plan.plan import *
import com.factory as factory


def connectionOptions():
    a = Cube(0)
    b = Cube(1)
    c = Cube(1)
    d = Cube(0)
    config = Configuration((350,350), math.radians(90), {a: (70,70), b:(280,70), d:(280, 190), c:(70,280)})
    # load initial
    sim = Simulation()
    print("inital config")
    sim.loadConfig(config)
    sim.start()
    time.sleep(0.1)
    sim.stop()
    input()
    sim.terminate()
    # 1 local plan
    p1 = local.planCubeConnect(config, a, b, Direction.WEST)
    print(f"after plan {p1}")
    sim = Simulation()
    sim.loadConfig(p1.goal)
    sim.start()
    time.sleep(0.1)
    sim.stop()
    input()
    sim.terminate()
    # 2 local plan
    p2 = local.planCubeConnect(config, a, c, Direction.WEST)
    print(f"after plan {p2}")
    sim = Simulation()
    sim.loadConfig(p2.goal)
    sim.start()
    time.sleep(0.1)
    sim.stop()
    input()
    sim.terminate()
    # 3 local plan
    p3 = local.planCubeConnect(config, d, b, Direction.WEST)
    print(f"after plan {p3}")
    sim = Simulation()
    sim.loadConfig(p3.goal)
    sim.start()
    time.sleep(0.1)
    sim.stop()
    input()
    sim.terminate()
    # 4 local plan
    p4 = local.planCubeConnect(config, d, c, Direction.WEST)
    print(f"after plan {p4}")
    sim = Simulation()
    sim.loadConfig(p4.goal)
    sim.start()
    time.sleep(0.1)
    sim.stop()
    input()
    sim.terminate()

def comicSequence():
    pB = factory.fourCube_LShape()
    pA = factory.linePolyHori(2,0)
    cB = pB.getCube((1,0))
    cA = pA.getCube((0,0))
    c = factory.configWithPolys((700,700),math.radians(90), [pB,pA], [(150,150), (350,300)])
    plan = local.planCubeConnect(c, cA, cB, Direction.SOUTH)

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


def twoCubeConnect(seed = 0, samples = 10):
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
        print(f"[{seed}] {plan}: {round(plan.cost(),2)}rad in {round(dt, 2)}\ns")
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
        print(f"[{seed}] {plan}: {round(plan.cost(),2)}rad in {round(dt, 2)}s\n")
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
        print(f"[{seed}] {plan}: {round(plan.cost(),2)}rad in {round(dt, 2)}s\n")
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
    twoPolyConnect(7836000,1, 7, False)