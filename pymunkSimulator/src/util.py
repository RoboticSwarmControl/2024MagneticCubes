"""
Utility functions

@author: Aaron T Becker, Kjell Keune
"""

import math
from cube import RAD, MRAD

def magForce1on2( p1, p2, m1,m2): #https://en.wikipedia.org/wiki/Magnetic_moment 
    #rhat = unitvector pointing from magnet 1 to magnet 2 and r is the distance
    r = calculate_distance(p1,p2)
    if r < 2*(RAD-MRAD):
        r = 2*(RAD-MRAD)  #limits the amount of force applied
        
    rhat  = ((p2[0]-p1[0])/r, (p2[1]-p1[1])/r) #r̂ is the unit vector pointing from magnet 1 to magnet 2 
    
    m1r   = m1[0]*rhat[0] + m1[1]*rhat[1]  #m1 dot rhat
    m2r   = m2[0]*rhat[0] + m2[1]*rhat[1]  #m2 dot rhat
    m1m2  = m1[0]*m2[0]   + m1[1]*m2[1]     #m1 dot m2
    
    #print(repr([r,rhat,m1r,m2r,m1m2]))
    sc = 20000000
    
    f = (sc*1/r**4 * (m2[0]*m1r + m1[0]*m2r + rhat[0]*m1m2 - 5*rhat[0]*m1r*m2r),   
         sc*1/r**4 * (m2[1]*m1r + m1[1]*m2r + rhat[1]*m1m2 - 5*rhat[1]*m1r*m2r))
    #print( "force is " + repr(f) )
    #print(repr(f) )
    return f

def calculate_distance(p1,p2):
    return math.sqrt( (p2[1]-p1[1])**2 + (p2[0]-p1[0])**2  )

def calculate_norm(p):
    return math.sqrt( p[1]**2 + p[0]**2  )

def calculate_angle(p1,p2):
    return math.atan2((p2[1]-p1[1]),     (p2[0]-p1[0])  )

def rotateVecbyAng(vec, ang):  #rotate a vector in 2D by angle ang
    (x,y) = vec
    return ( math.cos(ang)*x - math.sin(ang)*y, math.sin(ang)*x + math.cos(ang)*y)