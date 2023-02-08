
"""
Holds the StateHandler class

@author: Aaron T Becker, Kjell Keune
"""
import pymunk
import math
from threading import Lock
from queue import Queue

from util import *
from state import Configuration, Polyomino, Cube

class StateHandler:

    STEP_TIME = 0.02  #(in seconds) bigger steps make sim faster but unprecise/unstable 0.02 seems reasonable
    MAG_FORCE_FIELD = 1000 #magnetic force of the magnetic-field
    CONNECTION_FORCE_MIN = norm(Cube.magForce1on2( (0,0), (0,2*(Cube.RAD - Cube.MRAD)+5 ), (0,1), (0,1)))  #NS connection
    SENSOR_CTYPE = 1
    BOUNDARIE_RAD = 8

    def __init__(self, width, height):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)  # gravity doesn't exist
        self.space.damping = 0.2  # simulate top-down gravity with damping
        cHandler = self.space.add_collision_handler(StateHandler.SENSOR_CTYPE, StateHandler.SENSOR_CTYPE)
        def sensorCollision(arbiter: pymunk.Arbiter, space, data):
            cubei = self.sensor_cube[arbiter.shapes[0]]
            cubej = self.sensor_cube[arbiter.shapes[1]]
            self.__applyForceMagnets__(cubei, cubej)
            return False
        cHandler.pre_solve = sensorCollision

        self.bounds = self.__createBoundaries__(width, height)
        self.cube_shapes = {}
        self.sensor_cube = {}

        self.magAngle = 0  #orientation of magnetic field (in radians)
        self.magElevation = 0
        self.magConnect = {}
        self.polyominoes = []
        self.poly = []

        self.configToLoad = None
        self.updateLock = Lock()

    def loadConfig(self, newConfig: Configuration):
        self.configToLoad = newConfig

    def saveConfig(self) -> Configuration:
        self.updateLock.acquire()
        cube_pos = {}
        cube_meta = {}
        for cube, shapes in self.cube_shapes.items():
            cube_pos[cube] = shapes[0].body.position
            cube_meta[cube] = (shapes[0].body.angle, shapes[0].body.velocity)
        config = Configuration(self.magAngle, self.magElevation, cube_pos, cube_meta)
        config.polyominoes = self.polyominoes
        self.updateLock.release()
        return config

    def isRegistered(self, cube: Cube):
        return cube in self.cube_shapes

    def getShape(self, cube: Cube):
        return self.cube_shapes[cube][0]

    def getShapes(self):
        return list(shapes[0] for shapes in self.cube_shapes.values())

    def getCubes(self):
        return list(self.cube_shapes.keys())
    
    def getBoundaries(self):
        return self.bounds

    def getPolyominoes(self):
        return self.polyominoes

    def update(self, angChange, elevChange):
        """
        Updates the configuration by adding angChange and elevChange to the current magnetic field orientation.
        Also loads a new configuration if loadConfig got called.

        Parameters:
            angChange: angular change (in radians)
            elevChange: elevation change
        """
        self.updateLock.acquire()
        self.magAngle += angChange
        self.magElevation += elevChange
        #load new config if present
        if not self.configToLoad == None:
            self.__loadConfig__()
        #detect polyominos
        self.__detectPoly__()
        #is determining poly list and updates pivots remove when fiction is fixed 
        if len(self.cube_shapes) > 0:
            self.__detectPolyOld__()     
        self.__updatePivots__()
        for cube in self.getCubes():
            # Apply Force from magnetic-field
            self.__applyForceField__(cube)
            # zero out the connections
            self.magConnect[cube] = [None] * 4 
        self.updateLock.release()
        self.space.step(StateHandler.STEP_TIME)        

    def __applyForceField__(self, cube: Cube):
        shape = self.getShape(cube)
        ang = shape.body.angle
        shape.body.apply_force_at_local_point( (0,-math.sin(ang-self.magAngle) * StateHandler.MAG_FORCE_FIELD)  , ( Cube.MRAD, 0)  )
        shape.body.apply_force_at_local_point( (0, math.sin(ang-self.magAngle) * StateHandler.MAG_FORCE_FIELD)  , (-Cube.MRAD, 0)  )

    def __applyForceMagnets__(self, cubei: Cube, cubej: Cube):
        shapei = self.getShape(cubei)
        shapej = self.getShape(cubej)
        angi = shapei.body.angle
        angj = shapej.body.angle
        for k, pikL in enumerate(shapei.magnetPos):
            for n, pjnL  in enumerate(shapej.magnetPos):
                pik = shapei.body.local_to_world( pikL  )
                mik = rotateVecbyAng(shapei.magnetOri[k] , angi)
                #(xk,yk) = cubei.magnetOri[k] (xk,yk) = cubei.magnetOri[k] 
                #mik = ( math.cos(angi)*xk - math.sin(angi)*yk, math.sin(angi)*xk + math.cos(angi)*yk)
                pjn = shapej.body.local_to_world( pjnL  )
                mjn = rotateVecbyAng(shapej.magnetOri[n], angj)
                #(xn,yn) = cubej.magnetOri[n]
                #mjn = ( math.cos(angj)*xn - math.sin(angj)*yn, math.sin(angj)*xn + math.cos(angj)*yn)
                fionj = Cube.magForce1on2( pik, pjn, mik, mjn )  # magForce1on2( p1, p2, m1,m2)
                shapei.body.apply_force_at_world_point( (-fionj[0],-fionj[1]) , pik  )
                shapej.body.apply_force_at_world_point(  fionj ,                pjn  )
                #Determine magnet connections
                if norm(fionj) < StateHandler.CONNECTION_FORCE_MIN:
                    continue
                if pikL[0] < 0:
                    self.magConnect[cubei][Direction.NORTH.value] = cubej
                    self.magConnect[cubej][Direction.SOUTH.value] = cubei
                elif pikL[0] > 0:
                    self.magConnect[cubei][Direction.SOUTH.value] = cubej
                    self.magConnect[cubej][Direction.NORTH.value] = cubei
                elif pikL[1] < 0 and cubei.type != cubej.type:
                    self.magConnect[cubei][Direction.EAST.value] = cubej
                    self.magConnect[cubej][Direction.WEST.value] = cubei
                elif pikL[1] > 0 and cubei.type != cubej.type:
                    self.magConnect[cubei][Direction.WEST.value] = cubej
                    self.magConnect[cubej][Direction.EAST.value] = cubei 

    def __detectPoly__(self):
        self.polyominoes = []
        done = set()
        next = Queue()
        for cube in self.getCubes():
            if cube in done:
                continue
            polyomino = Polyomino(cube)
            done.add(cube)
            next.put(cube)
            while not next.empty():
                current = next.get()
                for i, adj in enumerate(self.magConnect[current]):
                    if (adj == None) or (adj in done):
                        continue
                    polyomino.connect(adj, current, Direction(i))
                    done.add(adj)
                    next.put(adj)
            if not polyomino.isTrivial():
                self.polyominoes.append(polyomino)
                              
    def __detectPolyOld__(self):
        cubes = self.getCubes()
        self.poly = list(range(0, len(cubes)))  #the unique polygon each cube belongs to.
        for i,cubei in enumerate(cubes):
            for j,cubej in enumerate(cubes):   #for j,cubej in enumerate(cubes,i):
                if i<=j:
                    continue
                #check to see if they are magnetically connected
                if cubej in self.magConnect[cubei]:
                    #if so, assign them to the same poly
                    piS = self.poly[i]
                    pjS = self.poly[j]
                    minP = min(piS,pjS)
                    self.poly[j] = minP
                    self.poly[i] = minP
                    if piS != pjS:
                        maxP = max(piS,pjS)
                        for k in range(len(self.cube_shapes)):  # never gets called!
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
                    (cx,cy) = shapes[0].body.world_to_local(cubei.body.local_to_world((-Cube.MRAD,0)) )
                    if round(cx/Cube.RAD) < round(minXyLyR[polyi][0] / Cube.RAD):
                        minXyLyR[polyi] = [cx,cy,cy] #this is the minimum row, so it is the pivot
                    elif round(cx/Cube.RAD) == round(minXyLyR[polyi][0]/Cube.RAD):
                        if round(cy/Cube.RAD) < round(minXyLyR[polyi][1]/Cube.RAD):
                            minXyLyR[polyi][1] = cy
                        elif round(cy/Cube.RAD) > round(minXyLyR[polyi][2]/Cube.RAD):
                            minXyLyR[polyi][2] = cy
                myYxLxR = minXyLyR
            else:
                maxXyLyR = [[-myInf, 0, 0] for _ in range(max(self.poly)+1)]
                for i,cubei in enumerate(shapes):
                    polyi = self.poly[i]
                    #change everything into local coordinate frame of cube[0]
                    (cx,cy) = shapes[0].body.world_to_local(cubei.body.local_to_world((Cube.MRAD,0)) )
                    if round(cx/Cube.RAD) > round(maxXyLyR[polyi][0]/Cube.RAD):
                        maxXyLyR[polyi] = [cx,cy,cy]
                    elif round(cx/Cube.RAD) == round(maxXyLyR[polyi][0]/Cube.RAD):
                        if round(cy/Cube.RAD) < round(maxXyLyR[polyi][1]/Cube.RAD):
                            maxXyLyR[polyi][1] = cy
                        elif round(cy/Cube.RAD) > round(maxXyLyR[polyi][2]/Cube.RAD):
                            maxXyLyR[polyi][2] = cy
                myYxLxR = maxXyLyR    
            for i,myYxLxRi in enumerate(myYxLxR):  #calculate the centroids
                    centroids[i] = shapes[0].body.local_to_world( (myYxLxRi[0],(myYxLxRi[1]+myYxLxRi[2])/2)  )    
            for i,cubei in enumerate(shapes):  #apply the centroids            
                cubei.body.center_of_gravity = cubei.body.world_to_local( centroids[self.poly[i]]  )
                pos = cubei.body.position
                cubei.body.position = (pos[0],pos[1]) #for some reason you need to assign this new position or it will jump when the COG is moved.

    def __loadConfig__(self):
        for cube in self.getCubes():
            self.__remove__(cube)
        self.magAngle = self.configToLoad.magAngle
        self.magElevation = self.configToLoad.magElevation
        self.polyominoes = self.configToLoad.getPolyominoes()
        for cube in self.configToLoad.getCubes():
            pos = self.configToLoad.getPosition(cube)
            ang = self.configToLoad.getAngle(cube)
            vel = self.configToLoad.getVelocity(cube)
            self.__add__(cube, pos, ang, vel)
        self.configToLoad = None

    def __remove__(self, cube: Cube):
        if not self.isRegistered(cube):
            if DEBUG: print("Removing failed. " + str(cube) + " is not registered.")
            return
        shapes = self.cube_shapes[cube]
        self.space.remove(shapes[0].body, shapes[0], shapes[1])
        del self.cube_shapes[cube]
        del self.magConnect[cube]
        del self.sensor_cube[shapes[1]]

    def __add__(self, cube: Cube, pos, ang, vel):
        if self.isRegistered(cube):
            if DEBUG: print("Adding failed. " + str(cube) + " is already registered.")
            return
        # create the cube body      
        body = pymunk.Body()
        body.position = pos
        body.angle = ang
        body.velocity = vel
        # create the cube shape
        shape = pymunk.Poly(body, [(-Cube.RAD,-Cube.RAD),(-Cube.RAD,Cube.RAD),(Cube.RAD,Cube.RAD),(Cube.RAD,-Cube.RAD)],radius = 1)
        shape.mass = 10
        shape.elasticity = 0.4
        shape.friction = 0.4
        shape.magnetPos = [(Cube.MRAD,0),(0,Cube.MRAD),(-Cube.MRAD,0),(0,-Cube.MRAD)]
        if cube.type == 0:
            shape.magnetOri = [(1,0),(0,1),(1,0),(0,-1)]
        else:
            shape.magnetOri = [(1,0),(0,-1),(1,0),(0,1)]
        # create sensor-shape that identifies a magnet attraction
        magSensor = pymunk.Circle(body, 3 * Cube.RAD)
        magSensor.collision_type = StateHandler.SENSOR_CTYPE
        magSensor.sensor = True
        # add to space and dictionarys
        self.space.add(body, magSensor, shape)
        self.cube_shapes[cube] = (shape, magSensor)
        self.magConnect[cube] = [None] * 4
        self.sensor_cube[magSensor] = cube

    def __createBoundaries__(self, width, height):
        r = StateHandler.BOUNDARIE_RAD
        w = width - StateHandler.BOUNDARIE_RAD / 4
        h = height - StateHandler.BOUNDARIE_RAD / 4
        bounds = [
            pymunk.Segment(self.space.static_body, (0,0), (w,0), r),
            pymunk.Segment(self.space.static_body, (w,0), (w, h), r),
            pymunk.Segment(self.space.static_body, (w, h), (0, h), r),
            pymunk.Segment(self.space.static_body, (0, h), (0,0), r)
        ]
        for wall in bounds:
            wall.elasticity = 0.4
            wall.friction = 0.5
            self.space.add(wall)
        return bounds
            




     
