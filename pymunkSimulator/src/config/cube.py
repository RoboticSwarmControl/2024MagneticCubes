"""
Holds the Cube class and the constants FMAG, RAD and MRAD which apply for all cubes

@author: Aaron T Becker, Kjell Keune
"""

import util.func as util

class Cube:
    """
    A unique cube object storing the cube type
    """
    nextid = 0
    
    MAG_FORCE = 20000000 #force of the magnets
    MRAD = 15  #distance of magnet from center of cube
    RAD = 20 #half length of side of cube

    def __init__(self, type):
        self.type = type
        self.id = Cube.nextid
        Cube.nextid += 1

    def __str__(self):
        return "Cube:" + str(self.id)
    
    def __repr__(self):
        return "Cube:" + str(self.id)
    
def magForce1on2( p1, p2, m1, m2): #https://en.wikipedia.org/wiki/Magnetic_moment 
    #rhat = unitvector pointing from magnet 1 to magnet 2 and r is the distance
    r = util.distance(p1,p2)
    if r < 2*(Cube.RAD-Cube.MRAD):
        r = 2*(Cube.RAD-Cube.MRAD)  #limits the amount of force applied
    rhat  = ((p2[0]-p1[0])/r, (p2[1]-p1[1])/r) #r̂ is the unit vector pointing from magnet 1 to magnet 2 
    m1r   = m1[0]*rhat[0] + m1[1]*rhat[1]  #m1 dot rhat
    m2r   = m2[0]*rhat[0] + m2[1]*rhat[1]  #m2 dot rhat
    m1m2  = m1[0]*m2[0]   + m1[1]*m2[1]     #m1 dot m2
    #print(repr([r,rhat,m1r,m2r,m1m2]))
    f = (Cube.MAG_FORCE*1/r**4 * (m2[0]*m1r + m1[0]*m2r + rhat[0]*m1m2 - 5*rhat[0]*m1r*m2r),   
         Cube.MAG_FORCE*1/r**4 * (m2[1]*m1r + m1[1]*m2r + rhat[1]*m1m2 - 5*rhat[1]*m1r*m2r))
    #print( "force is " + repr(f) )
    #print(repr(f) )
    return f
        
