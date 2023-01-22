"""
Holds the Configuration class

@author: Aaron T Becker, Kjell Keune
"""

class Configuration:
    """
    A Configuration consits of cubes and the orientation of the magnetic field.

    Can be used to store configuration data or can be loaded into a Simulation
    where it will be updated according to changes in the magnetic field.

    It also stores additional information about the magnetic connections and polyominoes present 
    if it was loaded and updated by a simulation
    """

    def __init__(self, ang=0, elev=0, cubes: dict={}):
        """
        creates configuration

        Parameters:
            ang: orientation of magnetic field (in radians)
            elev: elevation of magnetic field
            cubes: dictionary with key=cube value=postion (x,y)
        """
        self.cubes = cubes
        self.magAngle = ang  #orientation of magnetic field (in radians)
        self.magElevation = elev
        self.polyominoes = []

    def addCube(self, cube, pos):
        self.cubes[cube] = pos

    def removeCube(self, cube):
        del self.cubes[cube]

    def getCubes(self):
        return list(self.cubes.keys())

    def getPosition(self, cube):
        if not cube in self.cubes:
            return
        return self.cubes[cube] 
