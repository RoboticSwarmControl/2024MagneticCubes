"""
Holds the Configuration class

@author: Aaron T Becker, Kjell Keune
"""
import random

from util.direction import Direction
from config.cube import Cube
import util.func as util

class Configuration:
    """
    A Configuration consits of cubes and the orientation of the magnetic field.

    Can be used to store configuration data or can be loaded into a Simulation
    where it will be updated according to changes in the magnetic field.

    It also stores additional information about the polyominoes present 
    if it was loaded and updated by a simulation
    """

    def __init__(self, ang, elev, cube_pos):
        """
        creates configuration

        Parameters:
            ang: orientation of magnetic field (in radians)
            elev: elevation of magnetic field
            cube_pos: dictionary with key=cube value=postion (x,y)
        """
        self.cubePosMap = cube_pos
        self.magAngle = ang  #orientation of magnetic field (in radians)
        self.magElevation = elev
        self.polyominoes = []

    def addCube(self, cube, pos):
        self.cubePosMap[cube] = pos

    def removeCube(self, cube):
        del self.cubePosMap[cube]

    def getCubes(self):
        return list(self.cubePosMap.keys())

    def getPosition(self, cube):
        if not cube in self.cubePosMap:
            return
        return self.cubePosMap[cube] 
    
    def nearestWall(self, cube, size) -> Direction:
        if not cube in self.cubePosMap:
            return
        pos = self.cubePosMap[cube]
        dis = [pos[1], abs(size[0] - pos[0]), abs(size[1] - pos[1]), pos[0]]
        return Direction(dis.index(min(dis)))
    
def initRandomConfig(ncubes, size) -> Configuration:
        config = Configuration(0, 0, {})
        for _ in range(ncubes):
            newCube = Cube(random.randint(0,1))
            overlap = True
            pos = (0,0)
            while overlap:
                overlap = False
                x = random.randint(Cube.RAD, size[0] - Cube.RAD)
                y = random.randint(Cube.RAD, size[1] - Cube.RAD)
                pos = (x,y)
                for cube in config.getCubes():
                    #TODO dont compare in circle compare in rect
                    if util.distance(pos, config.getPosition(cube)) <= Cube.RAD * 1.5:
                        overlap = True
                        break
            config.addCube(newCube, pos)
        return config
                
            






                

