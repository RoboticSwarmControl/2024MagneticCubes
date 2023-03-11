
import math
import random
from sim.state import *

generator = random.Random()

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
            connects = poly.getConnections(cube)
            indices = [i for i, x in enumerate(connects) if x == None]
            if newCube.type == cube.type:
                if Direction.WEST.value in indices:
                    indices.remove(Direction.WEST.value)
                if Direction.EAST.value in indices:
                    indices.remove(Direction.EAST.value)
            # connect at an random available edge
            save = poly.clone()
            while True:
                # if no edge is available try the next cube
                if len(indices) == 0:
                    currCubes.remove(cube)
                    break
                # check if the connection would create a non valid polyomino
                edge = Direction(generator.choice(indices))
                poly.connect(newCube, cube, edge)
                if poly.isValid():
                    placed = True
                    break
                else:
                    indices.remove(edge.value)
                    poly = save
    return poly


def randomConfig(size, ncubes, nred=None) -> Configuration:
    ang = generator.random() * 2 * math.pi
    config = Configuration(size, ang, 0, {})
    for _ in range(ncubes):
        # create random cube
        newCube = randomCube(ncubes, nred)
        ncubes -= 1
        if newCube.type == Cube.TYPE_RED and nred != None:
            nred -= 1
        # create random non overlapping posistion
        overlap = True
        pos = (0, 0)
        while overlap:
            overlap = False
            x = generator.randint(Cube.RAD, size[0] - Cube.RAD)
            y = generator.randint(Cube.RAD, size[1] - Cube.RAD)
            pos = Vec2d(x, y)
            for cube in config.getCubes():
                # TODO dont compare in circle compare in rect
                if pos.get_distance(config.getPosition(cube)) <= Cube.RAD * 1.5:
                    overlap = True
                    break
        config.addCube(newCube, pos)
    return config


def randomCube(ncubes=None, nred=None):
    if nred == None:
        return Cube(generator.randint(0, 1))
    rnd = generator.randint(1, ncubes)
    if rnd <= nred:
        return Cube(Cube.TYPE_RED)
    else:
        return Cube(Cube.TYPE_BLUE)
