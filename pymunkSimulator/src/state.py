"""
Holds the Configuration class

@author: Aaron T Becker, Kjell Keune
"""
from queue import Queue
import random

from util import *

class Cube:
    """
    A unique cube object storing the cube type
    """
    nextid = 0
    
    TYPE_RED = 0
    TYPE_BLUE = 1

    MAG_FORCE = 20000000  # force of the magnets
    MRAD = 15  # distance of magnet from center of cube
    RAD = 20  # half length of side of cube

    def __init__(self, type):
        self.type = type
        self.magnetPos = [(-Cube.MRAD, 0), (0, -Cube.MRAD), (Cube.MRAD, 0), (0, Cube.MRAD)]
        if type == Cube.TYPE_RED:
            self.magnetOri = [(1, 0), (0, 1), (1, 0), (0, -1)]
        elif type == Cube.TYPE_BLUE:
            self.magnetOri = [(1, 0), (0, -1), (1, 0), (0, 1)]
        self.id = Cube.nextid
        Cube.nextid += 1

    def __str__(self):
        return f"Cube{self.id}[{self.type}]"

    def __repr__(self):
        return f"Cube{self.id}[{self.type}]"

    def __hash__(self) -> int:
        return hash(self.id)

    @staticmethod
    def magForce1on2(pos1, pos2, ori1, ori2):  # https://en.wikipedia.org/wiki/Magnetic_moment
        # rhat = unitvector pointing from magnet 1 to magnet 2 and r is the distance
        r = distance(pos1, pos2)
        if r < 2*(Cube.RAD-Cube.MRAD):
            r = 2*(Cube.RAD-Cube.MRAD)  # limits the amount of force applied
        # r̂ is the unit vector pointing from magnet 1 to magnet 2
        rhat = ((pos2[0]-pos1[0])/r, (pos2[1]-pos1[1])/r)
        m1r = ori1[0]*rhat[0] + ori1[1]*rhat[1]  # m1 dot rhat
        m2r = ori2[0]*rhat[0] + ori2[1]*rhat[1]  # m2 dot rhat
        m1m2 = ori1[0]*ori2[0] + ori1[1]*ori2[1]  # m1 dot m2
        # print(repr([r,rhat,m1r,m2r,m1m2]))
        f = (Cube.MAG_FORCE*1/r**4 * (ori2[0]*m1r + ori1[0]*m2r + rhat[0]*m1m2 - 5*rhat[0]*m1r*m2r),
             Cube.MAG_FORCE*1/r**4 * (ori2[1]*m1r + ori1[1]*m2r + rhat[1]*m1m2 - 5*rhat[1]*m1r*m2r))
        # print( "force is " + repr(f) )
        # print(repr(f) )
        return f



class Polyomino:

    nextId = 0

    def __init__(self, root: Cube):
        self.__pos_cube = {(0, 0): root}
        self.__cube_pos = {root: (0, 0)}
        self.__xmin = 0
        self.__xmax = 0
        self.__ymin = 0
        self.__ymax = 0
        self.valid = True
        self.id = Polyomino.nextId
        Polyomino.nextId += 1
        # The root should allways be the most left most bottom cube.

    def connect(self, cubeA: Cube, cubeB: Cube, edgeB: Direction):
        if not self.contains(cubeB):
            return False
        # determine postion of cubeA
        posB = self.__cube_pos[cubeB]
        if edgeB == Direction.NORTH:
            posA = (posB[0], posB[1] + 1)
        elif edgeB == Direction.EAST:
            posA = (posB[0] + 1, posB[1])
        elif edgeB == Direction.SOUTH:
            posA = (posB[0], posB[1] - 1)
        elif edgeB == Direction.WEST:
            posA = (posB[0] - 1, posB[1])
        # check if conection is possible
        if posA in self.__pos_cube:
            return False
        # add cubeA
        self.__cube_pos[cubeA] = posA
        self.__pos_cube[posA] = cubeA
        # update the bounds
        self.__xmin = min(posA[0], self.__xmin)
        self.__xmax = max(posA[0], self.__xmax)
        self.__ymin = min(posA[1], self.__ymin)
        self.__ymax = max(posA[1], self.__ymax)
        # update coordinate-system if root changed
        if posA[0] < 0 or (posA[0] == 0 and posA[1] < 0):
            self.__updateCoordinates__(cubeA)
        # check for illegal side connection
        neighborW = self.getConnection(cubeA, Direction.WEST)
        neighborE = self.getConnection(cubeA, Direction.EAST)
        if (neighborW != None and neighborW.type == cubeA.type) or (neighborE != None and neighborE.type == cubeA.type):
            self.valid = False
        return True

    def remove(self, cube: Cube):
        pos = self.__cube_pos[cube]
        # remove if polyomino doesnt break
        return

    def getConnections(self, cube: Cube):
        connects = []
        for i in range(4):
            connects.append(self.getConnection(cube, Direction(i)))
        return connects

    def getConnection(self, cube: Cube, edge: Direction) -> Cube:
        pos = self.__cube_pos[cube]
        if edge.value % 2 == 0:
            dx = 0
            dy = edge.value - 1
        else:
            dx = edge.value - 2
            dy = 0
        try:
            adj = self.__pos_cube[(pos[0] - dx, pos[1] - dy)]
        except KeyError:
            adj = None
        return adj

    def getCubes(self):
        return list(self.__cube_pos.keys())

    def getBottomRow(self):
        return self.__getRow__(self.__ymin)

    def getTopRow(self):
        return self.__getRow__(self.__ymax)

    def __getRow__(self, y):
        cubes = []
        for x in range(self.__xmin, self.__xmax + 1):
            try:
                cubes.append(self.__pos_cube[(x, y)])
            except KeyError:
                continue
        return cubes

    def isTrivial(self) -> bool:
        return len(self.__cube_pos) == 1

    def size(self) -> int:
        return len(self.__cube_pos)

    def contains(self, cube: Cube):
        return cube in self.__cube_pos

    def bounds(self):
        return (self.__xmax - self.__xmin + 1, self.__ymax - self.__ymin + 1)

    def clone(self):
        clone = Polyomino(self.__getRoot__())
        for cube, pos in self.__cube_pos.items():
            clone.__cube_pos[cube] = pos
            clone.__pos_cube[pos] = cube
        clone.valid = self.valid
        clone.__xmax = self.__xmax
        clone.__xmin = self.__xmin
        clone.__ymax = self.__ymax
        clone.__ymin = self.__ymin
        return clone

    def __updateCoordinates__(self, newRoot):
        self.__pos_cube.clear()
        posUpdate = self.__cube_pos[newRoot]
        self.__xmin -= posUpdate[0]
        self.__xmax -= posUpdate[0]
        self.__ymin -= posUpdate[1]
        self.__ymax -= posUpdate[1]
        for cube in self.getCubes():
            posOld = self.__cube_pos[cube]
            posNew = (posOld[0] - posUpdate[0], posOld[1] - posUpdate[1])
            self.__pos_cube[posNew] = cube
            self.__cube_pos[cube] = posNew

    def __getRoot__(self):
        return self.__pos_cube[(0, 0)]

    def __eq__(self, __o: object) -> bool:
        if not type(__o) is Polyomino:
            return False
        if self.size() != __o.size():
            return False
        for cubeT in self.getCubes():
            posT = self.__cube_pos[cubeT]
            try:
                if cubeT.type != __o.__pos_cube[posT].type:
                    return False
            except KeyError:
                return False
        return True

    def __hash__(self) -> int:
        toHash = [(p, c.type) for p, c in self.__pos_cube.items()]
        toHash.sort(key=lambda t: t[0])
        return hash(tuple(toHash))

    def __str__(self) -> str:
        string = f""
        for y in range(self.__ymax, self.__ymin - 1, -1):
            for x in range(self.__xmin, self.__xmax + 1):
                try:
                    string += str(self.__pos_cube[(x,y)].type)
                except KeyError:
                    string += " "
            string += "\n"
        return string

    def __repr__(self) -> str:
        return f"Polyomino{self.id}"
    
    @staticmethod
    def connectPoly(polyA, cubeA: Cube, polyB, cubeB: Cube, edgeB: Direction):
        if ((not polyA.contains(cubeA)) or (not polyB.contains(cubeB))):
            return
        poly = polyB.clone()
        if not poly.connect(cubeA, cubeB, edgeB):
            return None
        done = set()
        next = Queue()
        done.add(cubeA)
        next.put(cubeA)
        while not next.empty():
            current = next.get()
            for i, adj in enumerate(polyA.getConnections(current)):
                if (adj == None) or (adj in done):
                    continue
                if not poly.connect(adj, current, Direction(i)):
                    return None
                done.add(adj)
                next.put(adj)
        return poly
            


class PolyCollection:

    def __init__(self):
        self.__nonTrivial = []
        self.__trivial = []
        self.maxPolyWidth = 0
        self.maxPolyHeight = 0
        self.__poly_count = {}
        self.__cube_poly  = {}

    def detectPolyominoes(self, connects: dict):
        self.__clear__()
        done = set()
        next = Queue()
        for cube in connects.keys():
            if cube in done:
                continue
            polyomino = Polyomino(cube)
            done.add(cube)
            next.put(cube)
            while not next.empty():
                current = next.get()
                for i, adj in enumerate(connects[current]):
                    if (adj == None) or (adj in done):
                        continue
                    polyomino.connect(adj, current, Direction(i))
                    done.add(adj)
                    next.put(adj)
            self.__add__(polyomino)
            
    def setPolyominoes(self, polys):
        self.__clear__()
        for poly in polys:
            self.__add__(poly)

    def getPoly(self, cube: Cube):
        return self.__cube_poly[cube]

    def getAll(self):
        return self.getTrivial() + self.getNonTrivial()
    
    def getTrivial(self):
        return list(self.__trivial)

    def getNonTrivial(self):
        return list(self.__nonTrivial)

    def clone(self):
        clone = PolyCollection()
        for poly in self.getAll():
            clone.__add__(poly.clone())
        return clone

    def __add__(self, poly: Polyomino):
        if poly.isTrivial():
            self.__trivial.append(poly)
        else:
            self.__nonTrivial.append(poly)
        size = poly.bounds()
        self.maxPolyWidth = max(self.maxPolyWidth, size[0]) 
        self.maxPolyHeight = max(self.maxPolyHeight, size[1])
        if poly in self.__poly_count:
            self.__poly_count[poly] += 1
        else:
            self.__poly_count[poly] = 1
        for cube in poly.getCubes():
            self.__cube_poly[cube] = poly

    def __clear__(self):
        self.__nonTrivial.clear()
        self.__trivial.clear()
        self.maxPolyWidth = 0
        self.maxPolyHeight = 0
        self.__poly_count.clear()
        self.__cube_poly.clear()

    def __contains__(self, key):
        return key in self.__poly_count
    
    def __eq__(self, __o: object) -> bool:
        if not type(__o) is PolyCollection:
            return False
        return __o.__poly_count == self.__poly_count
    
    def __str__(self) -> str: 
        line = ""
        for i in range(self.maxPolyWidth):
            line += "-"
        line += "\n"
        string = line
        for poly, count in self.__poly_count.items():
            string += str(count) + " x:\n\n" + str(poly) + line
        return string
    
    def __repr__(self) -> str:
        return repr(self.__nonTrivial)




class Configuration:
    """
    A Configuration consits of cubes and the orientation of the magnetic field.

    Can be used to store configuration data or can be loaded into a Simulation
    where it will be updated according to changes in the magnetic field.

    It also stores additional information about the polyominoes present 
    if it was loaded and updated by a simulation
    """

    def __init__(self, boardSize, magAng, magElev, cube_pos, polyominoes: PolyCollection = None, cube_meta=None):
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
                meta = (magAng, (0, 0))
            else:
                meta = cube_meta[cube]
            self.__cube_data[cube] = (pos, meta[0], meta[1])
        self.magAngle = magAng  # orientation of magnetic field (in radians)
        self.magElevation = magElev
        self.boardSize = boardSize
        if polyominoes == None:
            self.polyominoes = PolyCollection()
        else:
            self.polyominoes = polyominoes

    def getCubes(self):
        return list(self.__cube_data.keys())

    def getPosition(self, cube: Cube):
        return self.__cube_data[cube][0]

    def getAngle(self, cube: Cube):
        return self.__cube_data[cube][1]

    def getVelocity(self, cube: Cube):
        return self.__cube_data[cube][2]

    def nearestWall(self, cube) -> Direction:
        if not cube in self.__cube_data:
            return
        pos = self.__cube_data[cube]
        dis = [pos[1], abs(self.boardSize[0] - pos[0]), abs(self.boardSize[1] - pos[1]), pos[0]]
        return Direction(dis.index(min(dis)))

    def addCube(self, cube, pos, ang=None, vel=(0,0)):
        if ang == None:
            ang = self.magAngle
        self.__cube_data[cube] = (pos, ang, vel)

    def __eq__(self, __o: object) -> bool:
        return hash(self) == hash(__o)

    def __hash__(self) -> int:
        toHash = [(d[0], c.type) for c, d in self.__cube_data.items()]
        toHash.sort()
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
            config.addCube(newCube, pos)
        return config
