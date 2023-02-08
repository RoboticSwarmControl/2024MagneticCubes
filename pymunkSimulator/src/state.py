"""
Holds the Configuration class

@author: Aaron T Becker, Kjell Keune
"""
import random

from util import *


class Cube:
    """
    A unique cube object storing the cube type
    """
    nextid = 0

    MAG_FORCE = 20000000  # force of the magnets
    MRAD = 15  # distance of magnet from center of cube
    RAD = 20  # half length of side of cube

    def __init__(self, type):
        self.type = type
        self.id = Cube.nextid
        Cube.nextid += 1

    def __str__(self):
        return "Cube:" + str(self.id)

    def __repr__(self):
        return "Cube:" + str(self.id)

    @staticmethod
    def magForce1on2(p1, p2, m1, m2):  # https://en.wikipedia.org/wiki/Magnetic_moment
        # rhat = unitvector pointing from magnet 1 to magnet 2 and r is the distance
        r = distance(p1, p2)
        if r < 2*(Cube.RAD-Cube.MRAD):
            r = 2*(Cube.RAD-Cube.MRAD)  # limits the amount of force applied
        # r̂ is the unit vector pointing from magnet 1 to magnet 2
        rhat = ((p2[0]-p1[0])/r, (p2[1]-p1[1])/r)
        m1r = m1[0]*rhat[0] + m1[1]*rhat[1]  # m1 dot rhat
        m2r = m2[0]*rhat[0] + m2[1]*rhat[1]  # m2 dot rhat
        m1m2 = m1[0]*m2[0] + m1[1]*m2[1]  # m1 dot m2
        # print(repr([r,rhat,m1r,m2r,m1m2]))
        f = (Cube.MAG_FORCE*1/r**4 * (m2[0]*m1r + m1[0]*m2r + rhat[0]*m1m2 - 5*rhat[0]*m1r*m2r),
             Cube.MAG_FORCE*1/r**4 * (m2[1]*m1r + m1[1]*m2r + rhat[1]*m1m2 - 5*rhat[1]*m1r*m2r))
        # print( "force is " + repr(f) )
        # print(repr(f) )
        return f


class Polyomino:

    def __init__(self, root: Cube):
        self.posCube = {(0, 0): root}
        self.cubePos = {root: (0, 0)}
        self.valid = True
        # The root should allways be the most left most bottom cube.

    def connect(self, cubeA: Cube, cubeB: Cube, edgeB: Direction):
        # check if cubes exist
        if not cubeB in self.cubePos:
            return False
        if cubeA in self.cubePos:
            return False
        # determine postion of cubeA
        posB = self.cubePos[cubeB]
        if edgeB == Direction.NORTH:
            posA = (posB[0], posB[1] + 1)
        elif edgeB == Direction.EAST:
            posA = (posB[0] + 1, posB[1])
        elif edgeB == Direction.SOUTH:
            posA = (posB[0], posB[1] - 1)
        elif edgeB == Direction.WEST:
            posA = (posB[0] - 1, posB[1])
        # check if conection is possible
        if posA in self.posCube:
            return False
        # add cubeA
        self.cubePos[cubeA] = posA
        self.posCube[posA] = cubeA
        # update the root
        if posA[0] < 0 or (posA[0] == 0 and posA[1] < 0):
            self.__updateRoot__(cubeA)
        # check for illegal side connection
        neighborW = self.getConnection(cubeA, Direction.WEST)
        neighborE = self.getConnection(cubeA, Direction.EAST)
        if (neighborW != None and neighborW.type == cubeA.type) or (neighborE != None and neighborE.type == cubeA.type):
            self.valid == False
        return True

    def remove(self, cube: Cube):
        pos = self.cubePos[cube]
        # remove if polyomino doesnt break
        return

    def getConnections(self, cube: Cube):
        connects = []
        for i in range(4):
            connects.append(self.getConnection(cube, Direction(i)))
        return connects

    def getConnection(self, cube: Cube, edge: Direction) -> Cube:
        pos = self.cubePos[cube]
        if edge.value % 2 == 0:
            dx = 0
            dy = edge.value - 1
        else:
            dx = edge.value - 2
            dy = 0
        try:
            adj = self.posCube[(pos[0] - dx, pos[1] - dy)]
        except KeyError:
            adj = None
        return adj

    def getCubes(self):
        return list(self.cubePos.keys())

    def isTrivial(self) -> bool:
        return len(self.cubePos) == 1

    def isIllegal(self):
        return not self.valid

    def size(self) -> int:
        return len(self.cubePos)

    def contains(self, cube):
        return cube in self.cubePos

    def __updateRoot__(self, newRoot):
        self.posCube.clear()
        posUpdate = self.cubePos[newRoot]
        for cube in self.getCubes():
            posOld = self.cubePos[cube]
            posNew = (posOld[0] - posUpdate[0], posOld[1] - posUpdate[1])
            self.posCube[posNew] = cube
            self.cubePos[cube] = posNew

    def __eq__(self, __o: object) -> bool:
        if not type(__o) is Polyomino:
            return False
        if self.size() != __o.size():
            return False
        for cubeT in self.getCubes():
            posT = self.cubePos[cubeT]
            try:
                if cubeT.type != __o.posCube[posT].type:
                    return False
            except KeyError:
                return False
        return True

    def __hash__(self) -> int:
        toHash = [(p, c.type) for p, c in self.posCube.items()]
        toHash.sort(key=lambda t: t[0])
        return hash(tuple(toHash))

    def __getRoot__(self):
        return self.posCube[(0, 0)]

    def __str__(self) -> str:
        return "Polyomino: " + str(self.cubePos)

    def __repr__(self) -> str:
        return "Polyomino: " + str(self.cubePos)


class Configuration:
    """
    A Configuration consits of cubes and the orientation of the magnetic field.

    Can be used to store configuration data or can be loaded into a Simulation
    where it will be updated according to changes in the magnetic field.

    It also stores additional information about the polyominoes present 
    if it was loaded and updated by a simulation
    """

    def __init__(self, ang, elev, cube_pos, polyominoes=None, cube_meta=None):
        """
        creates configuration

        Parameters:
            ang: orientation of magnetic field (in radians)
            elev: elevation of magnetic field
            cube_pos: dictionary with key=cube value=postion (x,y)
        """
        self.__cube_data = {}
        for cube, pos in cube_pos.items():
            if cube_meta == None:
                meta = (ang, (0, 0))
            else:
                meta = cube_meta[cube]
            self.__cube_data[cube] = (pos, meta[0], meta[1])
        self.magAngle = ang  # orientation of magnetic field (in radians)
        self.magElevation = elev
        self.__poly_count = {}
        if polyominoes == None:
            self.__polyominoes = []
        else:
            self.__polyominoes = polyominoes
            for poly in polyominoes:
                if poly in self.__poly_count:
                    self.__poly_count[poly] += 1
                else:
                    self.__poly_count[poly] = 1

    def getCubes(self):
        return list(self.__cube_data.keys())

    def getPolyominoes(self):
        return self.__polyominoes

    def getPosition(self, cube: Cube):
        return self.__cube_data[cube][0]

    def getAngle(self, cube: Cube):
        return self.__cube_data[cube][1]

    def getVelocity(self, cube: Cube):
        return self.__cube_data[cube][2]

    def contains(self, polyomino: Polyomino):
        return polyomino in self.__poly_count

    def nearestWall(self, cube, size) -> Direction:
        if not cube in self.__cube_data:
            return
        pos = self.__cube_data[cube]
        dis = [pos[1], abs(size[0] - pos[0]), abs(size[1] - pos[1]), pos[0]]
        return Direction(dis.index(min(dis)))

    def addCube(self, cube, pos, ang=None, vel=(0,0)):
        if ang == None:
            ang = self.magAngle
        self.__cube_data[cube] = (pos, ang, vel)

    def __eq__(self, __o: object) -> bool:
        return hash(self) == hash(__o)

    def __hash__(self) -> int:
        toHash = [(c, d[0]) for c, d in self.__cube_data.items()]
        toHash.sort(key=lambda t: t[0].id)
        toHash.append(self.magAngle)
        return hash(tuple(toHash))

    @staticmethod
    def initRandomConfig(ncubes, size):
        config = Configuration(0, 0, {})
        for _ in range(ncubes):
            newCube = Cube(random.randint(0, 1))
            overlap = True
            pos = (0, 0)
            while overlap:
                overlap = False
                x = random.randint(Cube.RAD, size[0] - Cube.RAD)
                y = random.randint(Cube.RAD, size[1] - Cube.RAD)
                pos = (x, y)
                for cube in config.getCubes():
                    # TODO dont compare in circle compare in rect
                    if distance(pos, config.getPosition(cube)) <= Cube.RAD * 1.5:
                        overlap = True
                        break
            config.addCube(cube, pos)
        return config
