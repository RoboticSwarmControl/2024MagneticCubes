
"""
Holds the StateHandler class

@author: Aaron T Becker, Kjell Keune
"""
import pymunk
import math
from threading import Lock, Event
from queue import Queue

from util import *
from state import Configuration, Polyomino, Cube


class StateHandler:

    # (in seconds) bigger steps make sim faster but unprecise/unstable 0.02 seems reasonable
    STEP_TIME = 0.02
    MAG_FORCE_FIELD = 1000  # magnetic force of the magnetic-field
    CONNECTION_DISTANCE = 2 * (Cube.RAD - Cube.MRAD) + 4
    CONNECTION_FORCE_MIN = norm(Cube.magForce1on2(
        (0, 0), (0, CONNECTION_DISTANCE), (0, 1), (0, 1)))  # NS connection
    SENSOR_CTYPE = 1
    BOUNDARIE_RAD = 8

    def __init__(self, width, height):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)  # gravity doesn't exist
        self.space.damping = 0.2  # simulate top-down gravity with damping
        cHandler = self.space.add_collision_handler(
            StateHandler.SENSOR_CTYPE, StateHandler.SENSOR_CTYPE)

        def sensorCollision(arbiter: pymunk.Arbiter, space, data):
            cubei = self.sensor_cube[arbiter.shapes[0]]
            cubej = self.sensor_cube[arbiter.shapes[1]]
            self.__applyForceMagnets__(cubei, cubej)
            return False
        cHandler.pre_solve = sensorCollision

        self.bounds = self.__createBoundaries__(width, height)
        self.cube_shapes = {}
        self.sensor_cube = {}
        
        self.magAngle = 0  # orientation of magnetic field (in radians)
        self.magElevation = 0
        self.magConnect = {}
        self.polyominoes = []

        #JOINTS
        self.connectJoints = []
        self.pivotJoints = []

        self.configToLoad = None
        self.updateLock = Lock()
        self.loaded = Event()
        self.connectionChange = Event()

    def loadConfig(self, newConfig: Configuration):
        self.configToLoad = newConfig
        self.loaded.wait(1)

    def loadConfig_nowait(self, newConfig: Configuration):
        self.configToLoad = newConfig

    def saveConfig(self) -> Configuration:
        self.updateLock.acquire()
        cube_pos = {}
        cube_meta = {}
        for cube, shapes in self.cube_shapes.items():
            cube_pos[cube] = shapes[0].body.position
            cube_meta[cube] = (shapes[0].body.angle, shapes[0].body.velocity)
        config = Configuration(
            self.magAngle, self.magElevation, cube_pos, self.polyominoes, cube_meta)
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
        # load new config if present
        if not self.configToLoad == None:
            self.__loadConfig__()
        # let pymunk update the space this also creates the magnetic connections
        self.space.step(StateHandler.STEP_TIME)
        # apply the change
        self.magAngle += angChange
        self.magElevation += elevChange
        # detect polyominos based on the magnetic connections
        if self.connectionChange.isSet():
            self.__detectPoly__()
            self.connectionChange.clear()
        # update the pivot point for polyominoes
        #JOINTS
        #self.__removePivotJoints__()
        for poly in self.polyominoes:
            self.__updatePivotPiont__(poly)
            #JOINTS
            #self.__addPivotJoints__(poly)
        # Apply forces to the cubes
        for cube in self.getCubes():
            self.__applyForceField__(cube)
        self.updateLock.release()

    def __applyForceField__(self, cube: Cube):
        shape = self.getShape(cube)
        ang = shape.body.angle
        shape.body.apply_force_at_local_point(
            (0, -math.sin(ang-self.magAngle) * StateHandler.MAG_FORCE_FIELD), (Cube.MRAD, 0))
        shape.body.apply_force_at_local_point(
            (0, math.sin(ang-self.magAngle) * StateHandler.MAG_FORCE_FIELD), (-Cube.MRAD, 0))

    def __applyForceMagnets__(self, cubei: Cube, cubej: Cube):
        shapei = self.getShape(cubei)
        shapej = self.getShape(cubej)
        angi = shapei.body.angle
        angj = shapej.body.angle
        for i, magPosLi in enumerate(shapei.magnetPos):
            for j, magPosLj in enumerate(shapej.magnetPos):
                magPosi = shapei.body.local_to_world(magPosLi)
                mi = rotateVecbyAng(shapei.magnetOri[i], angi)
                magPosj = shapej.body.local_to_world(magPosLj)
                mj = rotateVecbyAng(shapej.magnetOri[j], angj)
                # magForce1on2( p1, p2, m1,m2)
                fionj = Cube.magForce1on2(magPosi, magPosj, mi, mj)
                shapei.body.apply_force_at_world_point(
                    (-fionj[0], -fionj[1]), magPosi)
                shapej.body.apply_force_at_world_point(
                    fionj,                magPosj)
                # Determine magnet connections
                if norm(fionj) >= StateHandler.CONNECTION_FORCE_MIN:
                    self.__connectMagnets__(
                        cubei, Direction(i), cubej, Direction(j))

    def __connectMagnets__(self, cubei: Cube, edgei: Direction, cubej: Cube, edgej: Direction):
        # check if there already is a connection
        if cubej in self.magConnect[cubei]:
            return
        # edges should in inverse of each other
        if edgei.inv() != edgej:
            return
        # prevent side connection of same cube type
        if (edgei in (Direction.WEST, Direction.EAST)) and cubei.type == cubej.type:
            return
        # connect the cubes by adding them to magConnect map
        self.magConnect[cubei][edgei.value] = cubej
        self.magConnect[cubej][edgej.value] = cubei
        #JOINTS
        self.__addConnectionJoint__(cubei, edgei, cubej, edgej)
        self.connectionChange.set()

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
            self.polyominoes.append(polyomino)

    def __updatePivotPiont__(self, poly: Polyomino):
        if self.magElevation == 0:
            for cube in poly.getCubes():
                shape = self.getShape(cube)
                shape.body.center_of_gravity = (0,0)
                pos = shape.body.position
                shape.body.position = (pos[0],pos[1])
        else:
            if self.magElevation < 0:
                edgeCubes = poly.getTopRow()
                edgePointL = (-Cube.MRAD,0)
            else:
                edgeCubes = poly.getBottomRow()
                edgePointL = (Cube.MRAD,0)
            pivotPoint = (0,0)
            for cube in edgeCubes:
                shape = self.getShape(cube)
                pivotPoint += shape.body.local_to_world(edgePointL)
            pivotPoint /= len(edgeCubes)
            for cube in poly.getCubes(): 
                shape = self.getShape(cube)
                shape.body.center_of_gravity = shape.body.world_to_local(pivotPoint)
                pos = shape.body.position
                shape.body.position = (pos[0],pos[1])

    def __loadConfig__(self):
        # clear space
        #JOINTS
        #self.__removePivotJoints__()
        self.__removeConnectJoints__()
        for cube in self.getCubes():
            self.__remove__(cube)
        # grab values from configToLoad
        self.magAngle = self.configToLoad.magAngle
        self.magElevation = self.configToLoad.magElevation
        # add the cubes
        for cube in self.configToLoad.getCubes():
            pos = self.configToLoad.getPosition(cube)
            ang = self.configToLoad.getAngle(cube)
            vel = self.configToLoad.getVelocity(cube)
            self.__add__(cube, pos, ang, vel)
        # force connection change so that polyominoes get evaluated
        self.connectionChange.set()
        # reset the loading flags
        self.configToLoad = None
        self.loaded.set()
        self.loaded.clear()

    def __remove__(self, cube: Cube):
        if not self.isRegistered(cube):
            if DEBUG:
                print("Removing failed. " + str(cube) + " is not registered.")
            return
        shapes = self.cube_shapes[cube]
        self.space.remove(shapes[0].body, shapes[0], shapes[1])
        del self.cube_shapes[cube]
        del self.magConnect[cube]
        del self.sensor_cube[shapes[1]]

    def __add__(self, cube: Cube, pos, ang, vel):
        if self.isRegistered(cube):
            if DEBUG:
                print("Adding failed. " + str(cube) + " is already registered.")
            return
        # create the cube body
        body = pymunk.Body()
        body.position = pos
        body.angle = ang
        body.velocity = vel
        # create the cube shape
        shape = pymunk.Poly(body, [(-Cube.RAD, -Cube.RAD), (-Cube.RAD, Cube.RAD),
                            (Cube.RAD, Cube.RAD), (Cube.RAD, -Cube.RAD)], radius=1)
        shape.mass = 10
        shape.elasticity = 0.4
        shape.friction = 0.4
        shape.magnetPos = [(-Cube.MRAD, 0), (0, -Cube.MRAD),
                           (Cube.MRAD, 0), (0, Cube.MRAD)]
        if cube.type == 0:
            shape.magnetOri = [(1, 0), (0, -1), (1, 0), (0, 1)]
        else:
            shape.magnetOri = [(1, 0), (0, 1), (1, 0), (0, -1)]
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
            pymunk.Segment(self.space.static_body, (0, 0), (w, 0), r),
            pymunk.Segment(self.space.static_body, (w, 0), (w, h), r),
            pymunk.Segment(self.space.static_body, (w, h), (0, h), r),
            pymunk.Segment(self.space.static_body, (0, h), (0, 0), r)
        ]
        for wall in bounds:
            wall.elasticity = 0.4
            wall.friction = 0.5
            self.space.add(wall)
        return bounds
    
    def __addPivotJoints__(self, poly: Polyomino):
        if self.magElevation == 0:
            return
        if self.magElevation < 0:
            edgeCubes = poly.getTopRow()
            edgePointL = (-Cube.MRAD, 0)
        else:
            edgeCubes = poly.getBottomRow()
            edgePointL = (Cube.MRAD, 0)
        pivotPoint = (0, 0)
        for cube in edgeCubes:
            shape = self.getShape(cube)
            pivotPoint += shape.body.local_to_world(edgePointL)
        pivotPoint /= len(edgeCubes)
        staticBody = pymunk.Body(body_type=pymunk.Body.STATIC)
        staticBody.position = pivotPoint
        self.pivotJoints.append(staticBody)
        self.space.add(staticBody)
        for cube in edgeCubes:
            shape = self.getShape(cube)
            joint = pymunk.PinJoint(shape.body, staticBody, edgePointL)
            self.pivotJoints.append(joint)
            self.space.add(joint)

    def __removePivotJoints__(self):
        for element in self.pivotJoints:
            self.space.remove(element)
        self.pivotJoints.clear()

    def __addConnectionJoint__(self, cubei: Cube, edgei: Direction, cubej: Cube, edgej: Direction):
        shapei = self.getShape(cubei)
        shapej = self.getShape(cubej)
        pinJoint = pymunk.SlideJoint(
            shapei.body, shapej.body, shapei.magnetPos[edgei.value], shapej.magnetPos[edgej.value], StateHandler.CONNECTION_DISTANCE - 2, StateHandler.CONNECTION_DISTANCE)
        self.connectJoints.append(pinJoint)
        self.space.add(pinJoint)

    def __removeConnectJoints__(self):
        for joint in self.connectJoints:
            self.space.remove(joint)
        self.connectJoints.clear()
