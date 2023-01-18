"""
Holds the Cube class and the constants FMAG, RAD and MRAD which apply for all cubes

@author: Aaron T Becker, Kjell Keune
"""

FMAG = 1000 #magnetic force
MRAD = 15  #distance of magnet from center of cube
RAD = 20 #half length of side of cube

class Cube:
    """
    A unique cube object storing the cube type
    """

    def __init__(self, type):
        self.type = type