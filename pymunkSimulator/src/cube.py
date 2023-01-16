"""
Holds the Cube class and the constants FMAG, RAD and MRAD which apply for all cubes

@author: Aaron T Becker, Kjell Keune
"""

FMAG = 1000 #magnetic force
MRAD = 15  #distance of magnet from center of cube
RAD = 20 #half length of side of cube

class Cube:
    """
    Stores the position and the cubeType.

    Also contains a pymunk.shape if it got simulated.
    The shape will be used by the simulation to apply forces and draw the cube
    """

    def __init__(self, pos, type):
        self.position = pos
        self.type = type
        self.shape = None
