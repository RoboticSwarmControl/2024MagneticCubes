from queue import Queue
from config.cube import Cube
from util.direction import Direction

class Polyomino:

    def __init__(self, root: Cube):
        self.posCube = {(0,0): root}
        self.cubePos = {root: (0,0)}
        self.valid = True
        #The root should allways be the most left most bottom cube.

    def connect(self, cubeA: Cube, cubeB: Cube, edgeB: Direction): 
        #check if cubes exist
        if not cubeB in self.cubePos:
            return False
        if cubeA in self.cubePos:
            return False
        #determine postion of cubeA
        posB = self.cubePos[cubeB]
        if edgeB == Direction.NORTH:
            posA = (posB[0], posB[1] + 1)
        elif edgeB == Direction.EAST:
            posA = (posB[0] + 1, posB[1])
        elif edgeB == Direction.SOUTH:
            posA = (posB[0], posB[1] - 1)
        elif edgeB == Direction.WEST:
            posA = (posB[0] - 1, posB[1])
        #check if conection is possible
        if posA in self.posCube:
            return False
        #add cubeA
        self.cubePos[cubeA] = posA
        self.posCube[posA] = cubeA
        #update the root 
        if posA[0] < 0 or (posA[0] == 0 and posA[1] < 0):
            self.__updateRoot__(cubeA)
        #check for illegal side connection
        neighborW = self.getConnection(cubeA, Direction.WEST)
        neighborE = self.getConnection(cubeA, Direction.EAST)
        if (neighborW != None and neighborW.type == cubeA.type) or (neighborE != None and neighborE.type == cubeA.type):
            self.valid == False
        return True
    
    def remove(self, cube: Cube):
        pos = self.cubePos[cube]
        #remove if polyomino doesnt break
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
    

    def __getRoot__(self):
        return self.posCube[(0, 0)]

    def __str__(self) -> str:
        return "Polyomino: " + str(self.cubePos)
    
    def __repr__(self) -> str:
        return "Polyomino: " + str(self.cubePos)
