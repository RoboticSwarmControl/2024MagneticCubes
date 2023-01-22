from config.cube import Cube
from util.direction import Direction

class Polyomino:

    def __init__(self, root: Cube):
        self.connectionMap = {root: [None] * 4}

    def connect(self, cubeA: Cube, cubeB: Cube, edgeB: Direction):
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
        self.connectionMap[cubeB][edgeB.value] = cubeA
        self.connectionMap[cubeA] = [None] * 4
        self.connectionMap[cubeA][edgeB.inv().value] = cubeB
        return True
    
    def getConnections(self, cube: Cube):
        return self.connectionMap[cube]
    
    def getCubes(self):
        return list(self.connectionMap.keys())
    
    def isTrivial(self):
        return len(self.connectionMap) == 1
    
    def contains(self, cube):
        return cube in self.connectionMap
    
    def __str__(self) -> str:
        return "Polyomino: " + str(self.connectionMap)
    
    def __repr__(self) -> str:
        return "Polyomino: " + str(self.connectionMap)
