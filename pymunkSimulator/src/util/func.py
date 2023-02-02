"""
Utility functions

@author: Aaron T Becker, Kjell Keune
"""
import math

def distance(p1,p2):
    return math.sqrt( (p2[1]-p1[1])**2 + (p2[0]-p1[0])**2  )

def norm(p):
    return math.sqrt( p[1]**2 + p[0]**2  )

def angle(p1,p2):
    return math.atan2((p2[1]-p1[1]),     (p2[0]-p1[0])  )

def rotateVecbyAng(vec, ang):  #rotate a vector in 2D by angle ang
    (x,y) = vec
    return ( math.cos(ang)*x - math.sin(ang)*y, math.sin(ang)*x + math.cos(ang)*y)