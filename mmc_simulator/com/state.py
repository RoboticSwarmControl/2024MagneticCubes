"""
Holds the Configuration class

@author: Aaron T Becker, Kjell Keune
"""
import math
from enum import Enum
from queue import Queue
from pymunk import Vec2d

from com.motion import PivotWalk, Tilt


class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def inv(self):
        """
        Returns the inverse direction.
        """
        return Direction((self.value + 2) % 4)
    
    def vec(self, magAngle=0):
        """
        Retruns a vector point into this direction depending on the angle of the magnetic field.
        """
        if self == Direction.NORTH:
            return Vec2d(-math.cos(magAngle), -math.sin(magAngle))
        elif self == Direction.SOUTH:
            return Vec2d(math.cos(magAngle), math.sin(magAngle))
        elif self == Direction.EAST:
            return Vec2d(math.sin(magAngle), -math.cos(magAngle))
        else:
            return Vec2d(-math.sin(magAngle), math.cos(magAngle))
        
    @staticmethod    
    def list():
        return [Direction(i) for i in range(4)]

class Cube:
    """
    A unique cube object storing the cube type
    """
    nextid = 0
    
    TYPE_RED = 0
    TYPE_BLUE = 1

    MAG_FORCE = 25000000 # force of the magnets
    MRAD = 15  # distance of magnet from center of cube
    RAD = 20  # half length of side of cube
    MAG_DISTANCE_MIN = 5 * RAD

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
        if self.type == Cube.TYPE_BLUE:
            typeChar = 'b'
        else:
            typeChar = 'r'
        return f"[{typeChar}]"

    def __repr__(self):
        return f"Cube{self.id}"

    def __eq__(self, __o: object) -> bool:
        if not type(__o) is Cube:
            return False
        return self.id == __o.id

    def __hash__(self) -> int:
        return hash(self.id)

    @staticmethod
    def magForce1on2(pos1, pos2, ori1, ori2) -> Vec2d:  # https://en.wikipedia.org/wiki/Magnetic_moment
        # rhat = unitvector pointing from magnet 1 to magnet 2 and r is the distance
        pos1 = Vec2d(pos1[0], pos1[1])
        r = pos1.get_distance(pos2)
        if r < 2*(Cube.RAD-Cube.MRAD):
            r = 2*(Cube.RAD-Cube.MRAD)  # limits the amount of force applied
        # r̂ is the unit vector pointing from magnet 1 to magnet 2
        rhat = ((pos2[0]-pos1[0])/r, (pos2[1]-pos1[1])/r)
        m1r = ori1[0]*rhat[0] + ori1[1]*rhat[1]  # m1 dot rhat
        m2r = ori2[0]*rhat[0] + ori2[1]*rhat[1]  # m2 dot rhat
        m1m2 = ori1[0]*ori2[0] + ori1[1]*ori2[1]  # m1 dot m2
        # print(repr([r,rhat,m1r,m2r,m1m2]))
        f = Vec2d(Cube.MAG_FORCE*1/r**4 * (ori2[0]*m1r + ori1[0]*m2r + rhat[0]*m1m2 - 5*rhat[0]*m1r*m2r),
             Cube.MAG_FORCE*1/r**4 * (ori2[1]*m1r + ori1[1]*m2r + rhat[1]*m1m2 - 5*rhat[1]*m1r*m2r))
        # print( "force is " + repr(f) )
        # print(repr(f) )
        return f


class Connection:

    def __init__(self, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> None:
        self.cubeA = cubeA
        self.cubeB = cubeB
        self.edgeB = edgeB

    def __eq__(self, __o: object) -> bool:
        if not type(__o) is Connection:
            return False
        tup = (self.cubeA, self.cubeB, self.edgeB)
        return tup == (__o.cubeA, __o.cubeB, __o.edgeB) or tup == (__o.cubeB, __o.cubeA, __o.edgeB.inv())
    
    def __hash__(self) -> int:
        if self.edgeB in (Direction.WEST, Direction.SOUTH):
            tup = (self.cubeB, self.cubeA, self.edgeB.inv())
        else:
            tup = (self.cubeA, self.cubeB, self.edgeB)
        return hash(tup)
    
    def __str__(self) -> str:
        return str((self.cubeA,self.cubeB,self.edgeB))
    
    def __repr__(self) -> str:
        return str((self.cubeA,self.cubeB,self.edgeB))


class Polyomino:

    nextId = 0

    def __init__(self, root: Cube):
        self.__pos_cube = {(0, 0): root}
        self.__cube_pos = {root: (0, 0)}
        self.xmin = 0
        self.xmax = 0
        self.ymin = 0
        self.ymax = 0
        self.__valid = True
        self.id = Polyomino.nextId
        Polyomino.nextId += 1
        # The root should allways be the most left most bottom cube.

    def connect(self, cubeA: Cube, cubeB: Cube, edgeB: Direction):
        if not self.contains(cubeB):
            return False
        if self.contains(cubeA):
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
        self.xmin = min(posA[0], self.xmin)
        self.xmax = max(posA[0], self.xmax)
        self.ymin = min(posA[1], self.ymin)
        self.ymax = max(posA[1], self.ymax)
        # update coordinate-system if root changed
        if posA[0] < 0 or (posA[0] == 0 and posA[1] < 0):
            self.__updateCoordinates__(cubeA)
        # check for illegal side connection
        neighborW = self.getConnectedAt(cubeA, Direction.WEST)
        neighborE = self.getConnectedAt(cubeA, Direction.EAST)
        if (neighborW != None and neighborW.type == cubeA.type) or (neighborE != None and neighborE.type == cubeA.type):
            self.__valid = False
        return True
    
    def getFreeEdges(self, cube: Cube, onlyNS:bool=False):
        edges = [Direction(i) for i, x in enumerate(self.getConnected(cube)) if x == None]
        if onlyNS:
            if Direction.WEST in edges:
                edges.remove(Direction.WEST)
            if Direction.EAST in edges:
                edges.remove(Direction.EAST)
        return edges

    def getConnected(self, cube: Cube):
        connects = []
        for i in range(4):
            connects.append(self.getConnectedAt(cube, Direction(i)))
        return connects

    def getConnectedAt(self, cube: Cube, edge: Direction) -> Cube:
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

    def getConnectionMap(self):
        map = {}
        for cube in self.getCubes():
            map[cube] = self.getConnected(cube)
        return map

    def getCubes(self):
        return list(self.__cube_pos.keys())

    def getCube(self, localCoords) -> Cube:
        try:
            return self.__pos_cube[localCoords]
        except KeyError:
            return None

    def getRoot(self):
        return self.getCube((0,0))

    def getLocalCoordinates(self, cube) -> Vec2d:
        return self.__cube_pos[cube]

    def getBottomRow(self):
        return self.__getRow__(self.ymin)

    def getTopRow(self):
        return self.__getRow__(self.ymax)

    def __getRow__(self, y):
        cubes = []
        for x in range(self.xmin, self.xmax + 1):
            try:
                cubes.append(self.__pos_cube[(x, y)])
            except KeyError:
                continue
        return cubes

    def __getColum__(self, x):
        cubes = []
        for y in range(self.ymin, self.ymax + 1):
            try:
                cubes.append(self.__pos_cube[(x, y)])
            except KeyError:
                continue
        return cubes

    def isTrivial(self) -> bool:
        return len(self.__cube_pos) == 1

    def isValid(self):
        return self.__valid

    def size(self) -> int:
        return len(self.__cube_pos)
    
    def nred(self) -> int:
        nred = 0
        for cube in self.__pos_cube.values():
            if cube.type == Cube.TYPE_RED:
                nred += 1
        return nred

    def contains(self, cube: Cube):
        return cube in self.__cube_pos

    def bounds(self):
        return (self.xmax - self.xmin + 1, self.ymax - self.ymin + 1)

    def connectPoly(self, cubeA: Cube, polyB, cubeB: Cube, edgeB: Direction):
        if ((not self.contains(cubeA)) or (not polyB.contains(cubeB))):
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
            for i, adj in enumerate(self.getConnected(current)):
                if (adj == None) or (adj in done):
                    continue
                if not poly.connect(adj, current, Direction(i)):
                    return None
                done.add(adj)
                next.put(adj)
        return poly
    
    def connectPolyPossible(self, cubeA: Cube, polyB, cubeB: Cube, edgeB: Direction, direction: Direction, target=None) -> bool:
        # check if connecting the polys creates a vaild target
        if target == None:
            target = self.connectPoly(cubeA, polyB, cubeB, edgeB)
        if target == None:
            return False
        # if we walk in from east then edgeB has to be west ang the other way around
        if edgeB == direction:
            return False
        if direction == Direction.EAST:
            end = target.xmin - 1
            step = -1
        elif direction == Direction.WEST:
            end = target.xmax + 1
            step = 1
        else:
            return False
        for cube in self.getCubes():
            posInTar = target.__cube_pos[cube]
            for x in range(posInTar[0], end, step):
                try:
                    cubeInTar = target.__pos_cube[(x,posInTar[1])]
                except KeyError:
                    continue
                if not self.contains(cubeInTar):
                    return False
        return True

    def clone(self):
        clone = Polyomino(self.getRoot())
        for cube, pos in self.__cube_pos.items():
            clone.__cube_pos[cube] = pos
            clone.__pos_cube[pos] = cube
        clone.__valid = self.__valid
        clone.xmax = self.xmax
        clone.xmin = self.xmin
        clone.ymax = self.ymax
        clone.ymin = self.ymin
        return clone

    def __updateCoordinates__(self, newRoot):
        self.__pos_cube.clear()
        posUpdate = self.__cube_pos[newRoot]
        self.xmin -= posUpdate[0]
        self.xmax -= posUpdate[0]
        self.ymin -= posUpdate[1]
        self.ymax -= posUpdate[1]
        for cube in self.getCubes():
            posOld = self.__cube_pos[cube]
            posNew = (posOld[0] - posUpdate[0], posOld[1] - posUpdate[1])
            self.__pos_cube[posNew] = cube
            self.__cube_pos[cube] = posNew

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
        for y in range(self.ymax, self.ymin - 1, -1):
            for x in range(self.xmin, self.xmax + 1):
                try:
                    string += str(self.__pos_cube[(x,y)])
                except KeyError:
                    string += "   "
            string += "\n"
        return string

    def __repr__(self) -> str:
        return f"Polyomino{self.id}"


   
class PolyCollection:

    def __init__(self, polys=None):
        self.maxWidth = 0
        self.maxHeight = 0
        self.maxSize = 0
        self.__valid = True
        self.__polyType_polys = {}
        self.cube_poly = {}
        if polys == None:
            return
        for poly in polys:
            self.__add__(poly)

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

    def getForCube(self, cube: Cube)-> Polyomino:
        return self.cube_poly[cube]

    def getForType(self, type: Polyomino) -> list:
        if not type in self:
            return []
        return self.__polyType_polys[type]

    def getTypes(self) -> list:
        return list(self.__polyType_polys.keys())

    def getAll(self) -> list:
        if len(self.__polyType_polys) == 0:
            return []
        values = list(self.__polyType_polys.values())
        polys = list(values[0])
        for i in range(1, len(values)):
            polys.extend(values[i])
        return polys

    def isEmpty(self) -> bool:
        return len(self.__polyType_polys) == 0

    def containsInvalid(self):
        return not self.__valid

    def __add__(self, poly: Polyomino):
        bounds = poly.bounds()
        self.maxWidth = max(self.maxWidth, bounds[0]) 
        self.maxHeight = max(self.maxHeight, bounds[1])
        self.maxSize = max(self.maxSize, poly.size())
        if not poly.isValid():
            self.__valid = False
        if poly in self.__polyType_polys:
            self.__polyType_polys[poly].append(poly)
        else:
            self.__polyType_polys[poly] = [poly]
        for cube in poly.getCubes():
            self.cube_poly[cube] = poly

    def __clear__(self):
        self.maxWidth = 0
        self.maxHeight = 0
        self.maxSize = 0
        self.__valid = True
        self.__polyType_polys.clear()
        self.cube_poly.clear()

    def polyCount(self):
        count = 0
        for value in self.__polyType_polys.values():
            count += len(value)
        return count

    def __contains__(self, key):
        return key in self.__polyType_polys
    
    def __eq__(self, __o: object) -> bool:
        if not type(__o) is PolyCollection:
            return False
        for key in self.__polyType_polys.keys():
            try:
                if len(__o.__polyType_polys[key]) != len(self.__polyType_polys[key]):
                    return False
            except KeyError:
                return False
        return True
    
    def __hash__(self) -> int:
        toHash = [(hash(k), len(v)) for k, v in self.__polyType_polys.items()]
        toHash.sort()
        return hash(tuple(toHash))

    def __str__(self) -> str: 
        strId = str(hex(id(self)))[-4:]
        string = f"PolyCollection{strId}:\n"
        for type, polys in self.__polyType_polys.items():
            string += f"--------{len(polys)}x--------\n{type}\n"
        return string
    
    def __repr__(self) -> str:
        strId = str(hex(id(self)))[-4:]
        return f"PolyCollection{strId}"


class Configuration:
    """
    A Configuration consits of cubes and the orientation of the magnetic field.

    Can be used to store configuration data or can be loaded into a Simulation
    where it will be updated according to changes in the magnetic field.

    It also stores additional information about the polyominoes present
    if it was loaded and updated by a simulation
    """

    def __init__(self, boardSize, magAng, cube_pos:dict, cube_meta:dict=None, polys:list=None,  magElev=Tilt.HORIZONTAL):
        self.magAngle = magAng  # orientation of magnetic field (in radians)
        self.magElevation = magElev
        self.boardSize = boardSize
        self.__cube_data = {}
        for cube, pos in cube_pos.items():
            if cube_meta == None:
                meta = (magAng, (0, 0))
            else:
                meta = cube_meta[cube]
            self.__cube_data[cube] = (pos, meta[0], meta[1])
        self.__poly_meta = {}
        if polys != None:
            for poly in polys:
                com = self.__calcCOM__(poly)
                pn = self.__calcPivotN__(poly)
                ps = self.__calcPivotS__(poly)
                self.__poly_meta[poly.id] = (com, pn, ps)
        self.__polyominoes = PolyCollection(polys)

    def getCubes(self):
        return list(self.__cube_data.keys())

    def getPosition(self, cube: Cube) -> Vec2d:
        pos = self.__cube_data[cube][0]
        return Vec2d(pos[0], pos[1])

    def getAngle(self, cube: Cube):
        return self.__cube_data[cube][1]

    def getVelocity(self, cube: Cube) -> Vec2d:
        vel = self.__cube_data[cube][2]
        return Vec2d(vel[0], vel[1])

    def getPolyominoes(self) -> PolyCollection:
        return self.__polyominoes

    def getCOM(self, poly: Polyomino) -> Vec2d:
        return self.__poly_meta[poly.id][0]

    def getPivotN(self, poly: Polyomino) -> Vec2d:
        return self.__poly_meta[poly.id][1]
    
    def getPivotS(self, poly: Polyomino) -> Vec2d:
        return self.__poly_meta[poly.id][2]

    def getPivotWalkingDistance(self, poly: Polyomino, pivotAng):
        axis = self.getPivotN(poly) - self.getPivotS(poly)
        return 2 * math.sin(pivotAng) * axis.length

    def getPivotWalkingVec(self, poly: Polyomino, pivotAng, direction) -> Vec2d:
        axis = self.getPivotN(poly) - self.getPivotS(poly)
        distWalk = 2 * math.sin(pivotAng) * axis.length
        vecWalk = axis.perpendicular().scale_to_length(distWalk)
        if direction == PivotWalk.LEFT:
            vecDir = Direction.WEST.vec(self.magAngle)
        else:
            vecDir = Direction.EAST.vec(self.magAngle)
        if vecWalk.dot(vecDir) < 0:
            vecWalk *= -1
        return vecWalk

    def nearestWall(self, cube) -> Direction:
        if not cube in self.__cube_data:
            return
        pos = self.__cube_data[cube]
        dis = [pos[1], abs(self.boardSize[0] - pos[0]), abs(self.boardSize[1] - pos[1]), pos[0]]
        return Direction(dis.index(min(dis)))

    def posInBounds(self, pos: Vec2d):
        return pos[0] < self.boardSize[0] and pos[0] >= 0 and pos[1] < self.boardSize[1] and pos[1] >= 0 

    def posCubeOverlap(self, pos: Vec2d):
        for cube in self.getCubes():
            # TODO dont compare in circle compare in rect
            if pos.get_distance(self.getPosition(cube)) <= Cube.RAD * 1.5:
                return True
        return False

    def __calcCOM__(self, poly: Polyomino) -> Vec2d:
        com = Vec2d(0,0)
        for cube in poly.getCubes():
            com += self.getPosition(cube)
        com /= poly.size()
        return com
        
    def __calcPivotN__(self, poly: Polyomino) -> Vec2d:
        pn = Vec2d(0,0)
        topRow = poly.getTopRow()
        for cube in topRow:
            pn += (self.getPosition(cube) + Cube.RAD * Direction.NORTH.vec(self.getAngle(cube)))
        pn /= len(topRow)
        return pn

    def __calcPivotS__(self, poly: Polyomino) -> Vec2d:
        ps = Vec2d(0,0)
        bottomRow = poly.getBottomRow()
        for cube in bottomRow:
            ps += (self.getPosition(cube) + Cube.RAD * Direction.SOUTH.vec(self.getAngle(cube)))
        ps /= len(bottomRow)
        return ps

    def __eq__(self, __o: object) -> bool:
        return hash(self) == hash(__o)

    def __hash__(self) -> int:
        toHash = [(d[0], c.type) for c, d in self.__cube_data.items()]
        toHash.sort()
        toHash.append(self.magAngle)
        return hash(tuple(toHash))
    
    def __str__(self) -> str:
        strId = str(hex(id(self)))[-4:]
        string = f"Config{strId}("
        for cube in self.getCubes():
            pos = self.getPosition(cube)
            pos = (round(pos.x), round(pos.y))
            string += f"{cube}: {pos}, "
        return string + ")"
    
    def __repr__(self) -> str:
        strId = str(hex(id(self)))[-4:]
        return f"Config{strId}"

    def addCube(self, cube, pos, ang=None, vel=(0,0)):
        if ang == None:
            ang = self.magAngle
        self.__cube_data[cube] = (pos, ang, vel)
