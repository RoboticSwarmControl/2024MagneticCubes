from queue import Queue
from config.cube import Cube
from util.direction import Direction

class Polyomino:

    def __init__(self, root: Cube):
        self.connectionMap = {root: [None] * 4}
        self.postionMap = {root: (0,0)}
        #The root should allways be the most left most bottom cube.
        self.root = root

    def connect(self, cubeA: Cube, cubeB: Cube, edgeB: Direction):
        #determine if connection is possible
        if not cubeB in self.connectionMap:
            print(str(cubeB) + " not in polyomino")
            return False
        if cubeA in self.connectionMap:
            print(str(cubeA) + " already in polyomino")
            return False
        if self.connectionMap[cubeB][edgeB.value] != None:
            print("Edge of " + str(cubeB) + "already has a connection")
            return False
        if (edgeB == Direction.EAST or edgeB == Direction.WEST) and (cubeA.type == cubeB.type):
            print(str(cubeA) + " and " + str(cubeB) + "are same type. Cant connect sideways.")
            return False
        #Add new connections
        self.connectionMap[cubeB][edgeB.value] = cubeA
        self.connectionMap[cubeA] = [None] * 4
        self.connectionMap[cubeA][edgeB.inv().value] = cubeB
        #determine postion of cubeA
        posB = self.postionMap[cubeB]
        if edgeB == Direction.NORTH:
            posA = (posB[0], posB[1] + 1)
        elif edgeB == Direction.WEST:
            posA = (posB[0] + 1, posB[1])
        elif edgeB == Direction.SOUTH:
            posA = (posB[0], posB[1] - 1)
        elif edgeB == Direction.EAST:
            posA = (posB[0] - 1, posB[1])
        self.postionMap[cubeA] = posA
        #update the root 
        if posA[0] < 0 or (posA[0] == 0 and posA[1] < 0):
            self.__updateRoot__(cubeA)
        return True
    
    def getConnections(self, cube: Cube):
        return self.connectionMap[cube]
    
    def getCubes(self):
        return list(self.connectionMap.keys())
    
    def isTrivial(self):
        return len(self.connectionMap) == 1
    
    def contains(self, cube):
        return cube in self.connectionMap
    
    def __updateRoot__(self, newRoot):
        posUpdate = self.postionMap[newRoot]
        for cube in self.getCubes():
            posOld = self.postionMap[cube]
            posNew = (posOld[0] - posUpdate[0], posOld[1] - posUpdate[1])
            self.postionMap[cube] = posNew
        self.root = newRoot

    def __str__(self) -> str:
        return "Polyomino: " + str(self.connectionMap)
    
    def __repr__(self) -> str:
        return "Polyomino: " + str(self.connectionMap)
