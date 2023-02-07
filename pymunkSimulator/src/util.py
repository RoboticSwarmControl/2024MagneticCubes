from enum import Enum
import math

DEBUG = True

def distance(p1,p2):
    return math.sqrt( (p2[1]-p1[1])**2 + (p2[0]-p1[0])**2  )

def norm(p):
    return math.sqrt( p[1]**2 + p[0]**2  )

def angle(p1,p2):
    return math.atan2((p2[1]-p1[1]),     (p2[0]-p1[0])  )

def rotateVecbyAng(vec, ang):  #rotate a vector in 2D by angle ang
    (x,y) = vec
    return ( math.cos(ang)*x - math.sin(ang)*y, math.sin(ang)*x + math.cos(ang)*y)


class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def __str__(self) -> str:
        return self.name

    def inv(self):
        return Direction((self.value + 2) % 4)


class Color():
    BLACK = (0, 0, 0,100)
    WHITE = (255, 255, 255, 100)
    DARKGREY = (90, 90, 90, 100)
    LIGHTGRAY = (170, 170, 170, 100)
    RED = (195, 0, 0, 100)
    GREEN = (0, 195, 0,100)
    LIGHTBROWN = (201, 165, 129, 100)
    #https://sashamaps.net/docs/resources/20-colors/
    SASHACOLORS = ((230, 25, 75,100), (60, 180, 75,100), (255, 225, 25,100), (0, 130, 200,100), (245, 130, 48,100), (145, 30, 180,100), (70, 240, 240,100), (240, 50, 230,100), (210, 245, 60,100), (250, 190, 212,100), (0, 128, 128,100), 
                (220, 190, 255,100), (170, 110, 40,100), (255, 250, 200,100), (128, 0, 0,100), (170, 255, 195,100), (128, 128, 0,100), (255, 215, 180,100), (0, 0, 128,100), (128, 128, 128,100), (255, 255, 255,100), (0, 0, 0,100))