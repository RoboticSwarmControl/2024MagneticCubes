from enum import Enum
from pymunk import Vec2d
import math

DEBUG = True

class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def __str__(self) -> str:
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
            return Vec2d(math.sin(magAngle), math.cos(magAngle))
        else:
            return Vec2d(-math.sin(magAngle), -math.cos(magAngle))
        
def distance(p1,p2):
    return math.sqrt( (p2[1]-p1[1])**2 + (p2[0]-p1[0])**2  )

def norm(p):
    return math.sqrt( p[1]**2 + p[0]**2  )

def rotateVecbyAng(vec, ang):  #rotate a vector in 2D by angle ang
    (x,y) = vec
    return ( math.cos(ang)*x - math.sin(ang)*y, math.sin(ang)*x + math.cos(ang)*y)

class Color():
    BLACK = (0, 0, 0,100)
    WHITE = (255, 255, 255, 100)
    DARKGREY = (90, 90, 90, 100)
    LIGHTGRAY = (170, 170, 170, 100)
    RED = (195, 0, 0, 100)
    LIGHTRED = (250, 150, 150, 100)
    BLUE = (0, 0, 195, 100)
    LIGHTBLUE = (150, 150, 250, 100)
    LIGHTBROWN = (201, 165, 129, 100)
    PURPLE = (151, 0, 196, 100)