import math
import random
from com.state import *


generator = random.Random()


def configWithPolys(size, ang,  polys: list, positions: list) -> Configuration:
    config = Configuration(size, ang, {})
    vecNorth = Direction.NORTH.vec(ang)
    vecEast = Direction.EAST.vec(ang)
    for i, poly in enumerate(polys):
        cubePos = {}
        rootPos = positions[i]
        for cube in poly.getCubes():
            # add cubes based on root cube
            coords = poly.getLocalCoordinates(cube)
            pos = rootPos + (coords[0] * 2 * Cube.RAD) * vecEast + (coords[1] * 2 * Cube.RAD) * vecNorth
            cubePos[cube] = pos
            # if a cube ends up out of bounds or is overlapping with existing cubes config can not be created
            if (not config.posInBounds(pos)) or config.posCubeOverlap(pos):
                return None
        # if everything is valid add the cubes to config
        for cube, pos in cubePos.items():
            config.addCube(cube, pos)
    return config     


def randomConfigWithCubes(size, ncubes, nred=None) -> Configuration:
    ang = generator.random() * 2 * math.pi
    config = Configuration(size, ang, {})
    for _ in range(ncubes):
        # create random cube
        newCube = randomCube(ncubes, nred)
        ncubes -= 1
        if newCube.type == Cube.TYPE_RED and nred != None:
            nred -= 1
        # create random non overlapping posistion
        overlap = True
        while overlap:
            overlap = False
            pos = Vec2d(generator.randint(Cube.RAD, size[0] - Cube.RAD), generator.randint(Cube.RAD, size[1] - Cube.RAD))
            if config.posCubeOverlap(pos):
                overlap = True  
        config.addCube(newCube, pos)
    return config


def randomConfigWithPolys(size, polyominoes: list):
    ang = generator.random() * 2 * math.pi
    config = Configuration(size, ang, {})
    vecNorth = Direction.NORTH.vec(ang)
    vecEast = Direction.EAST.vec(ang)
    for poly in polyominoes:
        invalid = True
        while invalid:
            # create random position for root cube
            invalid = False
            rootPos = Vec2d(generator.randint(Cube.RAD, size[0] - Cube.RAD), generator.randint(Cube.RAD, size[1] - Cube.RAD))
            cubePos = {}
            for cube in poly.getCubes():
                # add cubes based on root cube
                coords = poly.getLocalCoordinates(cube)
                pos = rootPos + (coords[0] * 2 * Cube.RAD) * vecEast + (coords[1] * 2 * Cube.RAD) * vecNorth
                cubePos[cube] = pos
                # if a cube ends up out of bounds or is overlapping with existing cubes try new rootPos
                if (not config.posInBounds(pos)) or config.posCubeOverlap(pos):
                    invalid = True
                    break
        # if everything is valid add the cubes to config
        for cube, pos in cubePos.items():
            config.addCube(cube, pos)
    return config

def randomCube(ncubes=None, nred=None):
    if nred == None:
        return Cube(generator.randint(0, 1))
    rnd = generator.randint(1, ncubes)
    if rnd <= nred:
        return Cube(Cube.TYPE_RED)
    else:
        return Cube(Cube.TYPE_BLUE)
    
def randomConnection(polyA: Polyomino, polyB: Polyomino, connectPoss:bool, onlyValid:bool):
    itr = 0 
    while itr < 256:
        itr += 1
        cubeA = generator.choice(polyA.getCubes())
        cubeB = generator.choice(polyB.getCubes())
        edgesA = polyA.getFreeEdges(cubeA, cubeA.type == cubeB.type)
        edgesB = polyB.getFreeEdges(cubeB, cubeA.type == cubeB.type)
        possibleEdgesB = [edgeB for edgeB in edgesB if edgeB.inv() in edgesA]
        if len(possibleEdgesB) == 0:
            continue
        edgeB = generator.choice(possibleEdgesB)
        if connectPoss:
            target = polyA.connectPoly(cubeA, polyB, cubeB, edgeB)
            if target == None:
                continue
            if onlyValid and not target.isValid():
                continue
        return cubeA, cubeB, edgeB
    return None, None, None



def randomPoly(ncubes, nred=None):
    poly = None
    for _ in range(ncubes):
        # create random cube
        newCube = randomCube(ncubes, nred)
        ncubes -= 1
        if newCube.type == Cube.TYPE_RED and nred != None:
            nred -= 1
        # if first iteration create a poly
        if poly == None:
            poly = Polyomino(newCube)
            continue
        # connect the newCube
        currCubes = poly.getCubes()
        placed = False
        while not placed:
            # pick a random cube out of the current ones
            if len(currCubes) == 0:
                break
            cube = currCubes[generator.randint(0, len(currCubes) - 1)]
            # determin all possible open edges
            edgesAvail = poly.getFreeEdges(cube, newCube.type == cube.type)
            # connect at an random available edge
            save = poly.clone()
            while True:
                # if no edge is available try the next cube
                if len(edgesAvail) == 0:
                    currCubes.remove(cube)
                    break
                # check if the connection would create a non valid polyomino
                edge = generator.choice(edgesAvail)
                poly.connect(newCube, cube, edge)
                if poly.isValid():
                    placed = True
                    break
                else:
                    edgesAvail.remove(edge)
                    poly = save
    return poly

def linePolyVert(ncubes, nred=None):
    conEdge = Direction.NORTH
    poly = None
    lastCube = None
    for i in range(ncubes):
        # create random cube
        newCube = randomCube(ncubes, nred)
        ncubes -= 1
        if newCube.type == Cube.TYPE_RED and nred != None:
            nred -= 1
        # if first iteration create a poly
        if poly == None:
            poly = Polyomino(newCube)
            lastCube = newCube
            continue
        poly.connect(newCube, lastCube, conEdge)
        lastCube = newCube
    return poly

def linePolyHori(ncubes, firstType=None):
    if firstType == None:
        firstType = generator.randint(0,1)
    conEdge = Direction.EAST
    poly = None
    lastCube = None
    for i in range(ncubes):
        # create cube
        newCube = Cube(firstType)
        firstType = (firstType + 1) % 2
        # if first iteration create a poly
        if poly == None:
            poly = Polyomino(newCube)
            lastCube = newCube
            continue
        poly.connect(newCube, lastCube, conEdge)
        lastCube = newCube
    return poly

def fourCube_LShape() -> Polyomino:
    c = Cube(1)
    p = Polyomino(c)
    type_edge = [(0,Direction.WEST),(1,Direction.NORTH),(0,Direction.NORTH)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p

def twoByTwo() -> Polyomino:
    c = Cube(1)
    p = Polyomino(c)
    type_edge = [(0,Direction.NORTH),(1,Direction.EAST),(0,Direction.SOUTH)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p

def threeByThree() -> Polyomino:
    p1 = linePolyVert(3,3)
    p2 = linePolyVert(3,0)
    p3 = linePolyVert(3,3)
    c2 = p2.getCube((0,0))
    p: Polyomino = p1.connectPoly(p1.getCube((0,0)), p2, c2, Direction.WEST)
    p = p.connectPoly(c2, p3, p3.getCube((0,0)), Direction.WEST)
    return p

def fiveByTwo()-> Polyomino:
    pR = linePolyVert(5,5)
    pL = linePolyVert(5,0)
    cR = pR.getCube((0,0))
    cL = pL.getCube((0,0))
    return pR.connectPoly(cR, pL, cL, Direction.WEST)

def twoByFive()-> Polyomino:
    pT = linePolyHori(5,0)
    pB = linePolyHori(5,0)
    cT = pT.getCube((0,0))
    cB = pB.getCube((0,0))
    return pT.connectPoly(cT, pB, cB, Direction.NORTH)

def threeByThreeCB() -> Polyomino:
    m = Cube(0)
    l = Cube(1)
    r = Cube(1)
    p = Polyomino(m)
    p.connect(l, m, Direction.WEST)
    p.connect(r, m, Direction.EAST)
    p.connect(Cube(1), m, Direction.NORTH)
    p.connect(Cube(1), m, Direction.SOUTH)
    p.connect(Cube(0), l, Direction.NORTH)
    p.connect(Cube(0), l, Direction.SOUTH)
    p.connect(Cube(0), r, Direction.NORTH)
    p.connect(Cube(0), r, Direction.SOUTH)
    return p

def fiveByTwoCB()-> Polyomino:
    c = Cube(0)
    p = Polyomino(c)
    type_edge = [(1, Direction.NORTH),(0,Direction.NORTH),(1,Direction.NORTH),(0,Direction.NORTH),
                 (1,Direction.EAST),(0,Direction.SOUTH),(1,Direction.SOUTH),(0,Direction.SOUTH),(1,Direction.SOUTH)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p

def twoByFiveCB()-> Polyomino:
    c = Cube(1)
    p = Polyomino(c)
    type_edge = [(0,Direction.EAST),(1, Direction.EAST),(0,Direction.EAST),(1,Direction.EAST),(0,Direction.NORTH),
                 (1,Direction.WEST),(0,Direction.WEST),(1,Direction.WEST),(0,Direction.WEST)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p

def tenByOneCB()-> Polyomino:
    c = Cube(1)
    p = Polyomino(c)
    type_edge = [(0,Direction.NORTH),(1, Direction.NORTH),(0,Direction.NORTH),(1,Direction.NORTH),(0,Direction.NORTH),
                 (1,Direction.NORTH),(0,Direction.NORTH),(1,Direction.NORTH),(0,Direction.NORTH)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p

def letterC()-> Polyomino:
    c = Cube(1)
    p = Polyomino(c)
    type_edge = [(0,Direction.SOUTH),(1, Direction.WEST),(0,Direction.WEST),(1,Direction.NORTH),(0,Direction.NORTH),
                 (1,Direction.NORTH),(0,Direction.NORTH),(1,Direction.EAST),(0,Direction.EAST),(1,Direction.SOUTH)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p

def letterS()-> Polyomino:
    c = Cube(0)
    p = Polyomino(c)
    type_edge = [(1, Direction.EAST),(0,Direction.EAST),(1,Direction.NORTH),(0,Direction.NORTH),(1,Direction.WEST),
                 (0,Direction.WEST),(1,Direction.NORTH),(0,Direction.NORTH),(1,Direction.EAST),(0,Direction.EAST)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p

def letterA()-> Polyomino:
    c = Cube(1)
    p = Polyomino(c)
    p.connect(Cube(0), c, Direction.SOUTH)
    p.connect(Cube(0), c, Direction.EAST)
    type_edge = [(0,Direction.NORTH),(1,Direction.NORTH),(0,Direction.NORTH),(1,Direction.EAST),(0,Direction.EAST),
                 (1,Direction.SOUTH),(0,Direction.SOUTH),(1,Direction.SOUTH),(0,Direction.SOUTH)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p

def letterO()-> Polyomino:
    c = Cube(1)
    p = Polyomino(c)
    type_edge = [(0,Direction.NORTH),(1,Direction.NORTH),(0,Direction.NORTH),(1,Direction.EAST),(0,Direction.EAST),
                 (1,Direction.EAST),(0,Direction.SOUTH),(1,Direction.SOUTH),(0,Direction.SOUTH),(1,Direction.WEST),
                 (0,Direction.WEST)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p

def letterI()-> Polyomino:
    c = Cube(1)
    p = Polyomino(c)
    type_edge = [(0,Direction.EAST),(1,Direction.NORTH),(0,Direction.NORTH),(1,Direction.NORTH),(0,Direction.EAST),
                 (1,Direction.SOUTH),(0,Direction.SOUTH),(1,Direction.SOUTH),(0,Direction.EAST)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    p.connect(Cube(0), p.getCube((1,3)), Direction.WEST)
    p.connect(Cube(1), p.getCube((2,3)), Direction.EAST)
    return p

def letterH()-> Polyomino:
    c = Cube(1)
    p = Polyomino(c)
    type_edge = [(0,Direction.NORTH),(1,Direction.EAST),(0,Direction.EAST),(1,Direction.EAST),(0,Direction.NORTH),
                 (1,Direction.WEST),(0,Direction.WEST),(1,Direction.WEST),(0,Direction.NORTH)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    p.connect(Cube(0), p.getCube((3,1)), Direction.SOUTH)
    p.connect(Cube(1), p.getCube((3,2)), Direction.NORTH)
    return p

def letterPlus()-> Polyomino:
    c = Cube(1)
    p = Polyomino(c)
    type_edge = [(0,Direction.EAST),(1,Direction.NORTH),(0,Direction.EAST),(1,Direction.SOUTH),(0,Direction.EAST),
                 (1,Direction.SOUTH),(0,Direction.WEST),(1,Direction.SOUTH),(0,Direction.WEST),(1,Direction.NORTH),
                 (0,Direction.WEST)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p

def threeByThreeRing() -> Polyomino:
    c = Cube(0)
    p = Polyomino(c)
    type_edge = [(1,Direction.EAST),(0,Direction.EAST),(1,Direction.SOUTH),(0,Direction.SOUTH),(1,Direction.WEST),
                 (0,Direction.WEST),(1,Direction.NORTH)]
    for type, edge in type_edge:
        cnew = Cube(type)
        p.connect(cnew, c, edge)
        c = cnew
    return p