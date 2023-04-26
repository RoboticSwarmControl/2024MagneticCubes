import time
from pymunk import Vec2d
import json

from sim.simulation import Simulation
from com.state import *
from plan.plan import *
from plan.globalp import *
import com.factory as factory
from com.motion import Rotation, PivotWalk


def jsonTest():
    data = {
        "results": [
            {
                "seed": 0,
                "time": 12.3,
                "pos": (2,3)
            },
            {
                "seed": 1,
                "time": 112.3
            },
            {
                "seed": 2,
                "time": 10.5
            }
        ]
    }
    with open('../results/json_data.json', 'w') as outfile:
        json.dump(data, outfile, indent=4)

    with open('../results/json_data.json', 'r') as openfile:
        json_dict = json.load(openfile)
    print(type(json_dict))
    print(json_dict)
    


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

def twoCutTest():
    poly = factory.randomPoly(10)
    twoCuts = twoCutSubassemblies(poly)
    for tc in twoCuts:
        print(tc)
    print(f"For:\n\n{poly}\nare {len(twoCuts)} possible two-cuts.")

def twoCutGraphTest():
    polys = PolyCollection([Polyomino(Cube(1)),Polyomino(Cube(1)),Polyomino(Cube(1)),Polyomino(Cube(1))])
    p = factory.linePolyVert(4, 0)
    g = TwoCutSubassemblyGraph(p)
    print(g)
    notes = g.getNextCollections(polys)
    print(g.__node_edges)
    for adj in notes:
        print(f"How to get to {repr(adj)}:")
        print(f"{g.getTranslatedConnections(polys, adj)}\n")

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
        save0 = singleUpdate(config)
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


if __name__ == "__main__":
    jsonTest()