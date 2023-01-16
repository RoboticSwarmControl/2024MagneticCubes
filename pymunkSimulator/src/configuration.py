"""
Holds the Configuration class

@author: Aaron T Becker, Kjell Keune
"""

import math
import util
from cube import RAD, FMAG, MRAD, Cube

CONNECTION_FORCE_MIN = util.calculate_norm(util.magForce1on2( (0,0), (0,2*(RAD - MRAD)+5 ), (0,1), (0,1)))  #NS connection

class Configuration:
    """
    A Configuration consits of cubes and the orientation of the magnetic field.

    Can be used to store configuration data or can be loaded into a Simulation
    where it will be updated according to changes in the magnetic field.

    It also stores additional information about the magnetic connections and polyominoes present 
    if it was loaded and updated by a simulation
    """

    def __init__(self, ang, elev, cubes):
        """
        creates configuration

        Parameters:
            ang: orientation of magnetic field (in radians)
            elev: elevation of magnetic field
            cubes: List of cubes
        """
        self.loaded = False
        self.cubes = cubes
        self.magAngle = ang  #orientation of magnetic field (in radians)
        self.magElevation = elev
        self.magConnect = [ [] for _ in range(len(self.cubes)) ]
        self.poly = []

    def duplicate(self):
        newCubes = []
        for cube in self.cubes:
            newCubes.append(Cube(cube.position, cube.type))
        newConfig = Configuration(self.magAngle, self.magElevation, newCubes)
        newConfig.magConnect = self.magConnect
        newConfig.poly = self.poly
        return newConfig

    def _update_(self, ang, elev):
        """
        Updates the configuration by changing the magnetic field to ang and elev.
        The update should always be handelt by a simulation not manually.

        Parameters:
            ang: new orientation of magnetic field (in radians)
            elev: new elevation of magnetic field
        """
        self.magAngle = ang
        self.magElevation = elev
        # zero out the connections
        self.magConnect = [ [] for _ in range(len(self.cubes)) ]
        # Apply forces from magnets
        self.__applyMagForce__()  
        #detect polyominos
        if len(self.cubes) > 0:
            self.__detectPoly__()         
        #place the pivot point to match the polyominoes
        self.__updatePivots__()
        #Store the pygame positions in the cube.position
        for cube in self.cubes:
            cube.position = cube.shape.body.position


    def __applyMagForce__(self):
        for i,cubei in enumerate(self.cubes):
            angi = cubei.shape.body.angle
            # Apply forces from magnet field  (torques)
            cubei.shape.body.apply_force_at_local_point( (0,-math.sin(angi-self.magAngle)*FMAG)  , ( MRAD, 0)  )
            cubei.shape.body.apply_force_at_local_point( (0, math.sin(angi-self.magAngle)*FMAG)  , (-MRAD, 0)  )
             # Apply forces from the magnets on other cubes
            for j,cubej in enumerate(self.cubes):
                if i<=j:
                    continue
                angj = cubej.shape.body.angle
                if util.calculate_distance(cubei.shape.body.position, cubej.shape.body.position) <= 4*RAD:
                    
                     for k, pikL in enumerate(cubei.shape.magnetPos):
                         for n, pjnL  in enumerate(cubej.shape.magnetPos):
                             pik = cubei.shape.body.local_to_world( pikL  )
                             mik = util.rotateVecbyAng(cubei.shape.magnetOri[k] , angi)
                             #(xk,yk) = cubei.shape.magnetOri[k] (xk,yk) = cubei.shape.magnetOri[k] 
                             #mik = ( math.cos(angi)*xk - math.sin(angi)*yk, math.sin(angi)*xk + math.cos(angi)*yk)
                             pjn = cubej.shape.body.local_to_world( pjnL  )
                             mjn = util.rotateVecbyAng(cubej.shape.magnetOri[n], angj)
                             #(xn,yn) = cubej.shape.magnetOri[n]
                             #mjn = ( math.cos(angj)*xn - math.sin(angj)*yn, math.sin(angj)*xn + math.cos(angj)*yn)
                             fionj = util.magForce1on2( pik, pjn, mik, mjn )  # magForce1on2( p1, p2, m1,m2)
                             cubei.shape.body.apply_force_at_world_point( (-fionj[0],-fionj[1]) , pik  )
                             cubej.shape.body.apply_force_at_world_point(  fionj ,                pjn  )
                             if util.calculate_norm(fionj) > CONNECTION_FORCE_MIN:
                                 self.magConnect[i].append(j)
                                 self.magConnect[j].append(i)

    def __detectPoly__(self):
        self.poly = list(range(0, len(self.cubes)))  #the unique polygon each cube belongs to.
        for i,cubei in enumerate(self.cubes):
            for j,cubej in enumerate(self.cubes,i):   #for j,cubej in enumerate(cubes,i):
                #check to see if they are magnetically connected
                if self.magConnect[i].count(j)>0:
                    #if so, assign them to the same poly
                    piS = self.poly[i]
                    pjS = self.poly[j]
                    minP = min(piS,pjS)
                    self.poly[j] = minP
                    self.poly[i] = minP
                    if piS != pjS:
                        maxP = max(piS,pjS)
                        for k in range(len(self.cubes)):  # never gets called!
                            if self.poly[k] == maxP:
                                #print("Found equiv")
                                self.poly[k] = minP #assign all polys that have pjS or piS to be the minimum value
        polyset = list(set(self.poly))  # unique ID numbers
        #print("poly = " + repr(poly))
        #print("polyset = " + repr(polyset))
        newIndices = list(range(len(polyset))) #how many IDs there are
        for i in newIndices:     # renumber the polys poly = [0,0,1,3,3,8,8,8] --> [0,0,1,2,2,3,3,3] 
            self.poly = [i if item == polyset[i] else item for item in self.poly]                        
        #print("poly = " + repr(poly))

    def __updatePivots__(self):
        #updates the COM
        if self.magElevation == 0:
            for cube in self.cubes:
                cube.shape.body.center_of_gravity = ( 0, 0)
                pos = cube.shape.body.position
                cube.shape.body.position = (pos[0],pos[1]) #for some reason you need to assign this new position or it will jump when the COG is moved.
        else:
            myInf = 100000
            centroids = [[0,0] for _ in range(max(self.poly)+1)]
            if self.magElevation > 0:
                minXyLyR = [[ myInf, 0, 0] for _ in range(max(self.poly)+1)]
                for i,cubei in enumerate(self.cubes):
                    polyi = self.poly[i]
                    #change everything into local coordinate frame of cube[0]
                    (cx,cy) = self.cubes[0].shape.body.world_to_local(cubei.shape.body.local_to_world((-MRAD,0)) )
                    if round(cx/RAD) < round(minXyLyR[polyi][0] / RAD):
                        minXyLyR[polyi] = [cx,cy,cy] #this is the minimum row, so it is the pivot
                    elif round(cx/RAD) == round(minXyLyR[polyi][0]/RAD):
                        if round(cy/RAD) < round(minXyLyR[polyi][1]/RAD):
                            minXyLyR[polyi][1] = cy
                        elif round(cy/RAD) > round(minXyLyR[polyi][2]/RAD):
                            minXyLyR[polyi][2] = cy
                myYxLxR = minXyLyR
            else:
                maxXyLyR = [[-myInf, 0, 0] for _ in range(max(self.poly)+1)]
                for i,cubei in enumerate(self.cubes):
                    polyi = self.poly[i]
                    #change everything into local coordinate frame of cube[0]
                    (cx,cy) = self.cubes[0].shape.body.world_to_local(cubei.shape.body.local_to_world((MRAD,0)) )
                    if round(cx/RAD) > round(maxXyLyR[polyi][0]/RAD):
                        maxXyLyR[polyi] = [cx,cy,cy]
                    elif round(cx/RAD) == round(maxXyLyR[polyi][0]/RAD):
                        if round(cy/RAD) < round(maxXyLyR[polyi][1]/RAD):
                            maxXyLyR[polyi][1] = cy
                        elif round(cy/RAD) > round(maxXyLyR[polyi][2]/RAD):
                            maxXyLyR[polyi][2] = cy
                myYxLxR = maxXyLyR    
            for i,myYxLxRi in enumerate(myYxLxR):  #calculate the centroids
                    centroids[i] = self.cubes[0].shape.body.local_to_world( (myYxLxRi[0],(myYxLxRi[1]+myYxLxRi[2])/2)  )    
            for i,cubei in enumerate(self.cubes):  #apply the centroids            
                cubei.shape.body.center_of_gravity = cubei.shape.body.world_to_local( centroids[self.poly[i]]  )
                pos = cubei.shape.body.position
                cubei.shape.body.position = (pos[0],pos[1]) #for some reason you need to assign this new position or it will jump when the COG is moved.
            




     
