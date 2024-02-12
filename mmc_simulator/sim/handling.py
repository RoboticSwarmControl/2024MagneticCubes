
"""
Holds the StateHandler class

@author: Aaron T Becker, Kjell Keune
"""
import time
import json
import os
import pymunk
from pymunk.vec2d import Vec2d
import math
from threading import Lock
from com.motion import Tilt
from com.state import Cube, Configuration, PolyCollection, Direction, Polyomino

class Timer:

    def __init__(self) -> None:
        self.__total_time = 0
        self.__task_time = {}

    def addToTotal(self,dt):
        self.__total_time += dt

    def addToTask(self, task, dt):
        if task in self.__task_time:
            self.__task_time[task] += dt
        else:
            self.__task_time[task] = dt

    def reset(self):
        self.__total_time = 0
        self.__task_time.clear()

    def printTimeStats(self):
        print(f"Total time: {round(self.__total_time, 2)}s")
        for task, time in self.__task_time.items():
            portion = (time / self.__total_time) * 100
            print(f"    {task}: {round(portion, 2)}%")
    
    def writeTimeStats(self, path):
        data = {"total": self.__total_time, "tasks": self.__task_time}
        n = 1
        filePath = os.path.join(path, "time-stats.json")
        while(os.path.exists(filePath)):
            filePath = os.path.join(path, f"time-stats-{n}.json")
            n += 1
        with open(filePath, 'w') as file:
            json.dump(data, file, indent=4)
        print(f"Stats written to: {filePath}")


class StateHandler:

    MAG_FORCE_FIELD = 1000  # magnetic force of the magnetic-field
    CONNECTION_DISTANCE = 2 * (Cube.RAD - Cube.MRAD) + 4
    CONNECTION_FORCE_MIN = Cube.magForce1on2(
        (0, 0), (0, CONNECTION_DISTANCE), (0, 1), (0, 1)).length # NS connection
    NOMINAL_FRICTION = 0.35
    FRICTION_DAMPING = 0.9
    ANG_VEL_DAMP = 0.85

    SENSOR_CTYPE = 1
    BOUNDARIE_RAD = 8
    DEFAULT_BOARDSIZE = (800,800)
    DEFAULT_CONFIG = Configuration(DEFAULT_BOARDSIZE, math.radians(90), {})

    def __init__(self):
        self.space: pymunk.Space = None

        self.magAngle = 0
        self.magElevation = 0
        self.boardSize = StateHandler.DEFAULT_BOARDSIZE

        self.bounds = []
        self.cube_shapes = {}
        self.sensor_cube = {}
        self.cube_force = {}

        self.criticalCubePairs = []
        self.magConnect = {}
        self.magConnect_pre = {}
        self.polyominoes = PolyCollection() 

        self.timer = Timer()
        self.frictionpoints = {}

        self.loadConfig(StateHandler.DEFAULT_CONFIG)
        # JOINTS
        # self.connectJoints = []

    def getCubeShape(self, cube: Cube):
        return self.cube_shapes[cube][0]

    def getSensorShape(self, cube: Cube):
        return self.cube_shapes[cube][1]

    def getCubes(self):
        return list(self.cube_shapes.keys())

    def getBoundaries(self):
        return self.bounds

    def loadConfig(self, newConfig: Configuration):
        t0 = time.time()
        self.magAngle = newConfig.magAngle
        self.magElevation = newConfig.magElevation
        self.boardSize = newConfig.boardSize
        self.polyominoes = PolyCollection(newConfig.getPolyominoes().getAll())
        # JOINTS
        # self.__removeConnectJoints__()
        # clear space
        self.__resetSpace()
        # add new objects to space
        self.__addBoundaries()
        for cube in newConfig.getCubes():
            pos = newConfig.getPosition(cube)
            ang = newConfig.getAngle(cube)
            vel = newConfig.getVelocity(cube)
            self.__addCube(cube, pos, ang, vel)
        self.timer.addToTask("Load Configuration", time.time() - t0)

    def saveConfig(self) -> Configuration:
        t0 = time.time()
        cube_pos = {}
        cube_meta = {}
        for cube, shapes in self.cube_shapes.items():
            cube_pos[cube] = shapes[0].body.position
            cube_meta[cube] = (shapes[0].body.angle, shapes[0].body.velocity)
        config = Configuration(self.boardSize, self.magAngle, cube_pos, cube_meta, self.polyominoes.getAll(), self.magElevation)
        self.timer.addToTask("Save Configuration", time.time() - t0)
        return config

    def update(self, angChange, elevation, dt):
        """
        Updates the configuration by adding angChange and elevChange to the current magnetic field orientation.
        Also loads a new configuration if loadConfig got called.

        Parameters:
            angChange: angular change (in radians)
            elevChange: elevation change
        """
        # let pymunk update the space this also creates the magnetic connections
        t0 = time.time()
        self.space.step(dt)
        self.timer.addToTask("Pymunk-Step", time.time() - t0)
        # apply the change
        self.magAngle += angChange
        if elevation != 0:
            self.magElevation = elevation
        # apply magnet forces for cubes in critical-distance
        t0 = time.time()
        for cubei, cubej in self.criticalCubePairs:
            self.__applyForceMagnets(cubei, cubej)
        self.timer.addToTask("Force Calculation", time.time() - t0)
        self.criticalCubePairs.clear()
        # detect polyominos based on the magnetic connections
        t0 = time.time()
        if not self.magConnect == self.magConnect_pre:
            self.polyominoes.detectPolyominoes(self.magConnect)
        self.timer.addToTask("Polyomino Detection", time.time() - t0)
        # safe magnetic connections to _pre and clear this one
        self.magConnect_pre = self.magConnect
        self.magConnect = {}
        # apply forces from magneticfield to each cube in each poly
        self.frictionpoints.clear()
        t0 = time.time()
        for poly in self.polyominoes.getAll():
            for cube in poly.getCubes():
                self.__applyForceField(cube)
                self.__applyForceFriction(cube, poly)
                self.magConnect[cube] = [None] * 4
                self.cube_force[cube] = Vec2d(0,0)
        self.timer.addToTask("Force Calculation", time.time() - t0)

    def __applyForceField(self, cube: Cube):
        t0 = time.time()
        shape = self.getCubeShape(cube)
        ang = shape.body.angle
        # We need to apply world force to world point
        magPosN = shape.body.local_to_world(cube.magnetPos[Direction.NORTH.value])
        magPosS = shape.body.local_to_world(cube.magnetPos[Direction.SOUTH.value])
        force = Vec2d(0, math.sin(ang-self.magAngle) * StateHandler.MAG_FORCE_FIELD).rotated(ang)
        shape.body.apply_force_at_local_point(-force, magPosS)
        shape.body.apply_force_at_local_point( force, magPosN)
        #self.cube_force[cube] += force
        #self.cube_force[cube] += -force
        self.timer.addToTask("Calculate Magnetic Field Forces", time.time() - t0)

    def __sensorCollision(self, arbiter: pymunk.Arbiter, space, data): 
            cubei = self.sensor_cube[arbiter.shapes[0]]
            cubej = self.sensor_cube[arbiter.shapes[1]]
            #self.criticalCubePairs.append((cubei, cubej))
            self.__applyForceMagnets(cubei, cubej)
            return False

    def __applyForceMagnets(self, cubei: Cube, cubej: Cube):
        t0 = time.time()
        shapei = self.getCubeShape(cubei)
        shapej = self.getCubeShape(cubej)
        angi = shapei.body.angle
        angj = shapej.body.angle
        # determine which pairs to consider
        pairs = self.__magPairsMinDist(cubei, cubej)
        # calc magnetic force for the determined magnet pairs
        for i, j in pairs:
            magPosi = shapei.body.local_to_world(cubei.magnetPos[i])
            magOrii = cubei.magnetOri[i]
            mi = Vec2d(magOrii[0],magOrii[1]).rotated(angi)
            magPosj = shapej.body.local_to_world(cubej.magnetPos[j])
            magOrij = cubej.magnetOri[j]
            mj = Vec2d(magOrij[0],magOrij[1]).rotated(angj)
            fionj = Cube.magForce1on2(magPosi, magPosj, mi, mj)
            shapei.body.apply_force_at_world_point(-fionj, magPosi)
            shapej.body.apply_force_at_world_point(fionj, magPosj)
            # Determine magnet connections
            if fionj.length >= StateHandler.CONNECTION_FORCE_MIN:
                self.__connectMagnets(cubei, Direction(i), cubej, Direction(j))
            #self.cube_force[cubei] += -fionj
            #self.cube_force[cubej] += fionj
        self.timer.addToTask("Calculate Magnet Forces", time.time() - t0)

    def __magPairMinDist(self, cubei: Cube, cubej: Cube) -> list:
        # determine the magnetpair with the smallest distance. Only one pair is returned
        shapei = self.getCubeShape(cubei)
        shapej = self.getCubeShape(cubej)
        dismin = math.inf
        for i in range(4):
            magPosi = shapei.body.local_to_world(cubei.magnetPos[i])
            magPosi = Vec2d(magPosi[0], magPosi[1])
            for j in range(4):
                magPosj = shapej.body.local_to_world(cubej.magnetPos[j])
                dis = magPosi.get_distance(magPosj)
                if dis < dismin:
                    dismin = dis
                    pair = (i,j)
        return [pair]

    def __magPairsMinDist(self, cubei: Cube, cubej: Cube) -> list:
        # determine the magnetpairs with the smallest distance. In total 4 pairs are returned
        pairs = []
        shapei = self.getCubeShape(cubei)
        shapej = self.getCubeShape(cubej)
        for i in range(4):
            dismin = math.inf
            magPosi = shapei.body.local_to_world(cubei.magnetPos[i])
            magPosi = Vec2d(magPosi[0], magPosi[1])
            for j in range(4):
                magPosj = shapej.body.local_to_world(cubej.magnetPos[j])
                dis = magPosi.get_distance(magPosj)
                if dis < dismin:
                    dismin = dis
                    pair = (i,j)
            pairs.append(pair)
        return pairs

    def __magPairsAll(self, cubei: Cube, cubej: Cube) -> list:
        # returns all magnetpairs. 16 in total
        pairs = []
        for i in range(4):
            for j in range(4):
                pairs.append((i,j))
        return pairs

    def __connectMagnets(self, cubei: Cube, edgei: Direction, cubej: Cube, edgej: Direction):
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
        # JOINTS
        # self.__addConnectionJoint__(cubei, edgei, cubej, edgej)

    def __applyForceFriction(self, cube: Cube, poly: Polyomino):
        t0 = time.time()
        shape = self.getCubeShape(cube)
        # calculate friction force without velocity yet
        force = -1 * StateHandler.FRICTION_DAMPING * shape.mass
        if self.magElevation == Tilt.HORIZONTAL:
            # Apply full friction to cube, at COG
            force *= shape.body.velocity
            shape.body.apply_force_at_world_point(force, shape.body.position)
            # just for drawing
            self.frictionpoints[shape] = shape.body.position
        else:
            # define the cubes in poly the have the most friction and the frictionpoint
            if self.magElevation == Tilt.NORTH_DOWN:
                frictionCubes = set(poly.getTopRow())
                fricPoint = shape.body.local_to_world((-Cube.MRAD, 0))
            elif self.magElevation == Tilt.SOUTH_DOWN:
                frictionCubes = set(poly.getBottomRow())
                fricPoint = shape.body.local_to_world((Cube.MRAD, 0))
            # apply partial friction to cube at the frictionpoint
            force *= shape.body.velocity_at_world_point(fricPoint)
            shape.body.apply_force_at_world_point(
                StateHandler.NOMINAL_FRICTION * force, fricPoint)
            if cube in frictionCubes:
                # apply the rest if it is a friction cube
                #shape.body.apply_force_at_world_point(-self.cube_force[cube] / len(frictionCubes), fricPoint)
                shape.body.apply_force_at_world_point(
                    (1 - StateHandler.NOMINAL_FRICTION) * force * poly.size() / len(frictionCubes), fricPoint)
                self.frictionpoints[shape] = fricPoint  # just for drawing
        # damp the angular velocity
        shape.body.angular_velocity *= StateHandler.ANG_VEL_DAMP
        self.timer.addToTask("Calculate Friction Forces", time.time() - t0)

    def __resetSpace(self):
        # delete space and all dicts
        del self.space
        self.bounds.clear()
        self.cube_shapes.clear()
        self.sensor_cube.clear()
        self.cube_force.clear()
        self.magConnect.clear()
        # setup new space
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)  # gravity doesn't exist
        self.space.damping = 1.0
        # simulate top-down gravity with damping  was 0.2.  0 makes things not move.  1.0 they bounce forever.
        # A value of 0.9 means that each body will lose 10% of its velocity per second. Defaults to 1. Like gravity, it can be overridden on a per body basis.
        cHandler = self.space.add_collision_handler(
            StateHandler.SENSOR_CTYPE, StateHandler.SENSOR_CTYPE)
        cHandler.pre_solve = self.__sensorCollision

    def __addCube(self, cube: Cube, pos, ang, vel):
        if cube in self.cube_shapes:
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
        # create sensor-shape that identifies a magnet attraction
        magSensor = pymunk.Circle(body, Cube.MAG_DISTANCE_MIN / 2)
        magSensor.collision_type = StateHandler.SENSOR_CTYPE
        magSensor.sensor = True
        # add to space and dictionarys
        self.space.add(body, magSensor, shape)
        self.cube_shapes[cube] = (shape, magSensor)
        self.magConnect[cube] = [None] * 4
        self.cube_force[cube] = Vec2d(0,0)
        self.sensor_cube[magSensor] = cube

    def __addBoundaries(self):
        r = StateHandler.BOUNDARIE_RAD
        w = self.boardSize[0] - StateHandler.BOUNDARIE_RAD / 4
        h = self.boardSize[1] - StateHandler.BOUNDARIE_RAD / 4
        self.bounds = [
            pymunk.Segment(self.space.static_body, (0, 0), (w, 0), r),
            pymunk.Segment(self.space.static_body, (w, 0), (w, h), r),
            pymunk.Segment(self.space.static_body, (w, h), (0, h), r),
            pymunk.Segment(self.space.static_body, (0, h), (0, 0), r)
        ]
        for wall in self.bounds:
            wall.elasticity = 0.4
            wall.friction = 0.5
            self.space.add(wall)

# ------------------------------------DEPRECATED----------------------------------------------
    # def __updatePivotPiont__(self, poly: Polyomino):
    #     if self.magElevation == 0:
    #         for cube in poly.getCubes():
    #             shape = self.getCubeShape(cube)
    #             shape.body.center_of_gravity = (0, 0)
    #             pos = shape.body.position
    #             shape.body.position = (pos[0], pos[1])
    #     else:
    #         if self.magElevation < 0:
    #             edgeCubes = poly.getTopRow()
    #             edgePointL = (-Cube.MRAD, 0)
    #         else:
    #             edgeCubes = poly.getBottomRow()
    #             edgePointL = (Cube.MRAD, 0)
    #         pivotPoint = (0, 0)
    #         for cube in edgeCubes:
    #             shape = self.getCubeShape(cube)
    #             pivotPoint += shape.body.local_to_world(edgePointL)
    #         pivotPoint /= len(edgeCubes)
    #         for cube in poly.getCubes():
    #             shape = self.getCubeShape(cube)
    #             shape.body.center_of_gravity = shape.body.world_to_local(
    #                 pivotPoint)
    #             pos = shape.body.position
    #             shape.body.position = (pos[0], pos[1])

    # def __addConnectionJoint__(self, cubei: Cube, edgei: Direction, cubej: Cube, edgej: Direction):
    #     shapei = self.getCubeShape(cubei)
    #     shapej = self.getCubeShape(cubej)
    #     pinJoint = pymunk.SlideJoint(
    #         shapei.body, shapej.body, cubei.magnetPos[edgei.value], cubej.magnetPos[edgej.value], StateHandler.CONNECTION_DISTANCE - 2, StateHandler.CONNECTION_DISTANCE)
    #     self.connectJoints.append(pinJoint)
    #     self.space.add(pinJoint)

    # def __removeConnectJoints__(self):
    #     for joint in self.connectJoints:
    #         self.space.remove(joint)
    #     self.connectJoints.clear()
# --------------------------------------------------------------------------------------------