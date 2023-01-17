
"""
Holds the ConfigHandler class

@author: Aaron T Becker, Kjell Keune
"""
import pymunk
import math
from threading import Event, Lock

from util.func import *
from util.color import LIGHTBROWN
from config.cube import RAD, FMAG, MRAD
from config.configuration import Configuration


CONNECTION_FORCE_MIN = calculate_norm(magForce1on2( (0,0), (0,2*(RAD - MRAD)+5 ), (0,1), (0,1)))  #NS connection

class ConfigHandler:

    def __init__(self):
        self.cubes = {}
        self.magAngle = 0  #orientation of magnetic field (in radians)
        self.magElevation = 0
        self.magConnect = [ [] for _ in range(len(self.cubes)) ]
        self.poly = []
        self.configToLoad = None
        self.loaded = Event()
        self.updateLock = Lock()

    def loadConfig(self, newConfig: Configuration):
        self.configToLoad = newConfig
        self.loaded.wait(2)

    def loadConfig_nowait(self, newConfig: Configuration):
        self.configToLoad = newConfig

    def saveConfig(self) -> Configuration:
        self.updateLock.acquire()
        cube_pos = {}
        for cube, shape in self.cubes.items():
            cube_pos[cube] = shape.body.position
        config = Configuration(self.magAngle, self.magElevation, cube_pos)
        config.poly = self.poly
        config.magConnect = self.magConnect
        self.updateLock.release()
        return config

    def isRegistered(self, cube):
        return cube in self.cubes

    def getShapes(self):
        return list(self.cubes.values())

    def getCubes(self):
        return list(self.cubes.keys())

    def update(self, angChange, elevChange, space):
        """
        Updates the configuration by adding angChange and elevChange to the current magnetic field orientation.
        Also loads a new configuration if loadConfig got called.

        Parameters:
            angChange: angular change (in radians)
            elevChange: elevation change
            space: pymunk space in with the changes occure
        """
        self.updateLock.acquire()
        self.magAngle += angChange
        self.magElevation += elevChange
        # zero out the connections
        self.magConnect = [ [] for _ in range(len(self.cubes)) ]
        # Apply forces from magnets
        self.__applyMagForce__()  
        #detect polyominos
        if len(self.cubes) > 0:
            self.__detectPoly__()         
        #place the pivot point to match the polyominoes
        self.__updatePivots__()
        if not self.configToLoad == None:
            self.__loadConfig__(space)
        self.updateLock.release()
        

    def __loadConfig__(self, space):
        for cube in self.getCubes():
            self.__remove__(cube, space)
        self.magAngle = self.configToLoad.magAngle
        self.magElevation = self.configToLoad.magElevation
        for cube, pos in self.configToLoad.cubes.items():
            self.__add__(cube, pos, space)
        self.configToLoad = None
        self.loaded.set()
        self.loaded.clear()

    def __remove__(self, cube, space):
        if not self.isRegistered(cube):
            print("Removing failed. " + str(cube) + " is not registered.")
            return
        shape = self.cubes[cube]
        space.remove(shape.body, shape)
        del self.cubes[cube]

    def __add__(self, cube, pos, space):
        if self.isRegistered(cube):
            print("Adding failed. " + str(cube) + " is already registered.")
            return          
        body = pymunk.Body()
        body.position = pos
        shape = pymunk.Poly(body, [(-RAD,-RAD),(-RAD,RAD),(RAD,RAD),(RAD,-RAD)],radius = 1)
        #shape = pymunk.Poly.create_box(body,(2*rad,2*rad), radius = 1)
        shape.mass = 10
        shape.elasticity = 0.4
        shape.friction = 0.4
        shape.color = LIGHTBROWN
        shape.magnetPos = [(MRAD,0),(0,MRAD),(-MRAD,0),(0,-MRAD)]
        if cube.type == 0:
            shape.magnetOri = [(1,0),(0,1),(1,0),(0,-1)]
        else:
            shape.magnetOri = [(1,0),(0,-1),(1,0),(0,1)]
        body.angle = self.magAngle
        space.add(body,shape)
        self.cubes[cube] = shape


    def __applyMagForce__(self):
        shapes = self.getShapes()
        for i,cubei in enumerate(shapes):
            angi = cubei.body.angle
            # Apply forces from magnet field  (torques)
            cubei.body.apply_force_at_local_point( (0,-math.sin(angi-self.magAngle)*FMAG)  , ( MRAD, 0)  )
            cubei.body.apply_force_at_local_point( (0, math.sin(angi-self.magAngle)*FMAG)  , (-MRAD, 0)  )
             # Apply forces from the magnets on other cubes
            for j,cubej in enumerate(shapes):
                if i<=j:
                    continue
                angj = cubej.body.angle
                if calculate_distance(cubei.body.position, cubej.body.position) <= 4*RAD:
                    
                     for k, pikL in enumerate(cubei.magnetPos):
                         for n, pjnL  in enumerate(cubej.magnetPos):
                             pik = cubei.body.local_to_world( pikL  )
                             mik = rotateVecbyAng(cubei.magnetOri[k] , angi)
                             #(xk,yk) = cubei.magnetOri[k] (xk,yk) = cubei.magnetOri[k] 
                             #mik = ( math.cos(angi)*xk - math.sin(angi)*yk, math.sin(angi)*xk + math.cos(angi)*yk)
                             pjn = cubej.body.local_to_world( pjnL  )
                             mjn = rotateVecbyAng(cubej.magnetOri[n], angj)
                             #(xn,yn) = cubej.magnetOri[n]
                             #mjn = ( math.cos(angj)*xn - math.sin(angj)*yn, math.sin(angj)*xn + math.cos(angj)*yn)
                             fionj = magForce1on2( pik, pjn, mik, mjn )  # magForce1on2( p1, p2, m1,m2)
                             cubei.body.apply_force_at_world_point( (-fionj[0],-fionj[1]) , pik  )
                             cubej.body.apply_force_at_world_point(  fionj ,                pjn  )
                             if calculate_norm(fionj) > CONNECTION_FORCE_MIN:
                                 self.magConnect[i].append(j)
                                 self.magConnect[j].append(i)

    def __detectPoly__(self):
        shapes = self.getShapes()
        self.poly = list(range(0, len(self.cubes)))  #the unique polygon each cube belongs to.
        for i,cubei in enumerate(shapes):
            for j,cubej in enumerate(shapes,i):   #for j,cubej in enumerate(cubes,i):
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
        shapes = self.getShapes()
        #updates the COM
        if self.magElevation == 0:
            for cube in shapes:
                cube.body.center_of_gravity = ( 0, 0)
                pos = cube.body.position
                cube.body.position = (pos[0],pos[1]) #for some reason you need to assign this new position or it will jump when the COG is moved.
        else:
            myInf = 100000
            centroids = [[0,0] for _ in range(max(self.poly)+1)]
            if self.magElevation > 0:
                minXyLyR = [[ myInf, 0, 0] for _ in range(max(self.poly)+1)]
                for i,cubei in enumerate(shapes):
                    polyi = self.poly[i]
                    #change everything into local coordinate frame of cube[0]
                    (cx,cy) = shapes[0].body.world_to_local(cubei.body.local_to_world((-MRAD,0)) )
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
                for i,cubei in enumerate(shapes):
                    polyi = self.poly[i]
                    #change everything into local coordinate frame of cube[0]
                    (cx,cy) = shapes[0].body.world_to_local(cubei.body.local_to_world((MRAD,0)) )
                    if round(cx/RAD) > round(maxXyLyR[polyi][0]/RAD):
                        maxXyLyR[polyi] = [cx,cy,cy]
                    elif round(cx/RAD) == round(maxXyLyR[polyi][0]/RAD):
                        if round(cy/RAD) < round(maxXyLyR[polyi][1]/RAD):
                            maxXyLyR[polyi][1] = cy
                        elif round(cy/RAD) > round(maxXyLyR[polyi][2]/RAD):
                            maxXyLyR[polyi][2] = cy
                myYxLxR = maxXyLyR    
            for i,myYxLxRi in enumerate(myYxLxR):  #calculate the centroids
                    centroids[i] = shapes[0].body.local_to_world( (myYxLxRi[0],(myYxLxRi[1]+myYxLxRi[2])/2)  )    
            for i,cubei in enumerate(shapes):  #apply the centroids            
                cubei.body.center_of_gravity = cubei.body.world_to_local( centroids[self.poly[i]]  )
                pos = cubei.body.position
                cubei.body.position = (pos[0],pos[1]) #for some reason you need to assign this new position or it will jump when the COG is moved.
            




     
