
"""
Holds the StateHandler class

@author: Aaron T Becker, Kjell Keune
"""
import pygame
import pymunk.pygame_util
import pymunk
import math
from threading import Lock

from util import *
from state import *


class StateHandler:

    # (in seconds) bigger steps make sim faster but unprecise/unstable 0.04 seems reasonable
    STEP_TIME = 0.04
    MAG_FORCE_FIELD = 1000  # magnetic force of the magnetic-field
    CONNECTION_DISTANCE = 2 * (Cube.RAD - Cube.MRAD) + 4
    CONNECTION_FORCE_MIN = norm(Cube.magForce1on2(
        (0, 0), (0, CONNECTION_DISTANCE), (0, 1), (0, 1)))  # NS connection
    NOMINAL_FRICTION = 0.2
    FRICTION_DAMPING = 0.9
    ANG_VEL_DAMP = 0.95

    SENSOR_CTYPE = 1
    BOUNDARIE_RAD = 8
    DEFAULT_BOARDSIZE = (800,800)
    DEFAULT_CONFIG = Configuration(DEFAULT_BOARDSIZE, math.radians(90), 0, {})

    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)  # gravity doesn't exist
        self.space.damping = 1.0
        # simulate top-down gravity with damping  was 0.2.  0 makes things not move.  1.0 they bounce forever.
        # A value of 0.9 means that each body will lose 10% of its velocity per second. Defaults to 1. Like gravity, it can be overridden on a per body basis.
        cHandler = self.space.add_collision_handler(
            StateHandler.SENSOR_CTYPE, StateHandler.SENSOR_CTYPE)

        def sensorCollision(arbiter: pymunk.Arbiter, space, data):
            cubei = self.sensor_cube[arbiter.shapes[0]]
            cubej = self.sensor_cube[arbiter.shapes[1]]
            self.__applyForceMagnets__(cubei, cubej)
            return False
        cHandler.pre_solve = sensorCollision

        self.boardSize = StateHandler.DEFAULT_BOARDSIZE
        self.bounds = []
        self.cube_shapes = {}
        self.sensor_cube = {}

        self.magAngle = 0  # orientation of magnetic field (in radians)
        self.magElevation = 0

        self.magConnect = {}
        self.magConnect_pre = {}
        self.polyominoes = PolyCollection()

        self.configToLoad = StateHandler.DEFAULT_CONFIG
        self.updateLock = Lock()

        self.frictionpoints = {}
        # JOINTS
        # self.connectJoints = []
        # self.pivotJoints = []

    def getCubeShape(self, cube: Cube):
        return self.cube_shapes[cube][0]

    def getSensorShape(self, cube: Cube):
        return self.cube_shapes[cube][1]

    def getCubes(self):
        return list(self.cube_shapes.keys())

    def getBoundaries(self):
        return self.bounds

    def loadConfig(self, newConfig: Configuration):
        self.boardSize = newConfig.boardSize
        self.configToLoad = newConfig

    def saveConfig(self) -> Configuration:
        self.updateLock.acquire()
        cube_pos = {}
        cube_meta = {}
        for cube, shapes in self.cube_shapes.items():
            cube_pos[cube] = shapes[0].body.position
            cube_meta[cube] = (shapes[0].body.angle, shapes[0].body.velocity)
        config = Configuration(self.boardSize, self.magAngle, self.magElevation, cube_pos, self.polyominoes.clone(), cube_meta)
        self.updateLock.release()
        return config

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
        if not self.magConnect == self.magConnect_pre:
            self.polyominoes.detectPolyominoes(self.magConnect)
        self.magConnect_pre = self.magConnect
        self.magConnect = {}
        # JOINTS
        # self.__removePivotJoints__()
        self.frictionpoints.clear()
        for poly in self.polyominoes.getAll():
            # self.__updatePivotPiont__(poly)
            # self.__addPivotJoints__(poly)
            for cube in poly.getCubes():
                self.__applyForceField__(cube)
                self.__applyForceFriction__(cube, poly)
                self.magConnect[cube] = [None] * 4
        self.updateLock.release()

    def __applyForceField__(self, cube: Cube):
        shape = self.getCubeShape(cube)
        ang = shape.body.angle
        shape.body.apply_force_at_local_point(
            (0, -math.sin(ang-self.magAngle) * StateHandler.MAG_FORCE_FIELD), (Cube.MRAD, 0))
        shape.body.apply_force_at_local_point(
            (0, math.sin(ang-self.magAngle) * StateHandler.MAG_FORCE_FIELD), (-Cube.MRAD, 0))

    def __applyForceMagnets__(self, cubei: Cube, cubej: Cube):
        shapei = self.getCubeShape(cubei)
        shapej = self.getCubeShape(cubej)
        angi = shapei.body.angle
        angj = shapej.body.angle
        for i, magPosLi in enumerate(cubei.magnetPos):
            for j, magPosLj in enumerate(cubej.magnetPos):
                magPosi = shapei.body.local_to_world(magPosLi)
                mi = rotateVecbyAng(cubei.magnetOri[i], angi)
                magPosj = shapej.body.local_to_world(magPosLj)
                mj = rotateVecbyAng(cubej.magnetOri[j], angj)
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
        # JOINTS
        # self.__addConnectionJoint__(cubei, edgei, cubej, edgej)

    def __applyForceFriction__(self, cube: Cube, poly: Polyomino):
        shape = self.getCubeShape(cube)
        # calculate friction force without velocity yet
        force = -1 * StateHandler.FRICTION_DAMPING * shape.mass
        if self.magElevation == 0:
            # Apply full friction to cube, at COG
            force *= shape.body.velocity
            shape.body.apply_force_at_world_point(force, shape.body.position)
            # just for drawing
            self.frictionpoints[shape] = shape.body.position
        else:
            # define the cubes in poly the have the most friction and the frictionpoint
            if self.magElevation < 0:
                frictionCubes = set(poly.getTopRow())
                fricPoint = shape.body.local_to_world((-Cube.MRAD, 0))
            elif self.magElevation > 0:
                frictionCubes = set(poly.getBottomRow())
                fricPoint = shape.body.local_to_world((Cube.MRAD, 0))
            # apply partial friction to cube at the frictionpoint
            force *= shape.body.velocity_at_world_point(fricPoint)
            shape.body.apply_force_at_world_point(
                StateHandler.NOMINAL_FRICTION * force, fricPoint)
            if cube in frictionCubes:
                # apply the rest if it is a friction cube
                shape.body.apply_force_at_world_point(
                    (1 - StateHandler.NOMINAL_FRICTION) * force * poly.size() / len(frictionCubes), fricPoint)
                self.frictionpoints[shape] = fricPoint  # just for drawing
        # damp the angular velocity
        shape.body.angular_velocity *= StateHandler.ANG_VEL_DAMP

    def __loadConfig__(self):
        # clear space
        # JOINTS
        # self.__removePivotJoints__()
        # self.__removeConnectJoints__()
        self.__removeBoundaries__()
        for cube in self.getCubes():
            self.__removeCube__(cube)
        # grab values from configToLoad
        self.magAngle = self.configToLoad.magAngle
        self.magElevation = self.configToLoad.magElevation
        # add new objects to space
        self.__addBoundaries__()
        for cube in self.configToLoad.getCubes():
            pos = self.configToLoad.getPosition(cube)
            ang = self.configToLoad.getAngle(cube)
            vel = self.configToLoad.getVelocity(cube)
            self.__addCube__(cube, pos, ang, vel)
        # reset the loading flag
        self.configToLoad = None

    def __removeCube__(self, cube: Cube):
        if not cube in self.cube_shapes:
            if DEBUG:
                print("Removing failed. " + str(cube) + " is not registered.")
            return
        shapes = self.cube_shapes[cube]
        self.space.remove(shapes[0].body, shapes[0], shapes[1])
        del self.cube_shapes[cube]
        del self.magConnect[cube]
        del self.sensor_cube[shapes[1]]

    def __addCube__(self, cube: Cube, pos, ang, vel):
        if cube in self.cube_shapes:
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
        if cube.type == Cube.TYPE_RED:
            shape.color = Color.LIGHTRED
        else:
            shape.color = Color.LIGHTBLUE
        # create sensor-shape that identifies a magnet attraction
        magSensor = pymunk.Circle(body, 3 * Cube.RAD)
        magSensor.collision_type = StateHandler.SENSOR_CTYPE
        magSensor.sensor = True
        # add to space and dictionarys
        self.space.add(body, magSensor, shape)
        self.cube_shapes[cube] = (shape, magSensor)
        self.magConnect[cube] = [None] * 4
        self.sensor_cube[magSensor] = cube

    def __addBoundaries__(self):
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

    def __removeBoundaries__(self):
        for wall in self.bounds:
            self.space.remove(wall)
        self.bounds.clear()

# ------------------------------------DEPRECATED----------------------------------------------
    def __updatePivotPiont__(self, poly: Polyomino):
        if self.magElevation == 0:
            for cube in poly.getCubes():
                shape = self.getCubeShape(cube)
                shape.body.center_of_gravity = (0, 0)
                pos = shape.body.position
                shape.body.position = (pos[0], pos[1])
        else:
            if self.magElevation < 0:
                edgeCubes = poly.getTopRow()
                edgePointL = (-Cube.MRAD, 0)
            else:
                edgeCubes = poly.getBottomRow()
                edgePointL = (Cube.MRAD, 0)
            pivotPoint = (0, 0)
            for cube in edgeCubes:
                shape = self.getCubeShape(cube)
                pivotPoint += shape.body.local_to_world(edgePointL)
            pivotPoint /= len(edgeCubes)
            for cube in poly.getCubes():
                shape = self.getCubeShape(cube)
                shape.body.center_of_gravity = shape.body.world_to_local(
                    pivotPoint)
                pos = shape.body.position
                shape.body.position = (pos[0], pos[1])

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
            shape = self.getCubeShape(cube)
            pivotPoint += shape.body.local_to_world(edgePointL)
        pivotPoint /= len(edgeCubes)
        staticBody = pymunk.Body(body_type=pymunk.Body.STATIC)
        staticBody.position = pivotPoint
        self.pivotJoints.append(staticBody)
        self.space.add(staticBody)
        for cube in edgeCubes:
            shape = self.getCubeShape(cube)
            joint = pymunk.PinJoint(shape.body, staticBody, edgePointL)
            self.pivotJoints.append(joint)
            self.space.add(joint)

    def __removePivotJoints__(self):
        for element in self.pivotJoints:
            self.space.remove(element)
        self.pivotJoints.clear()

    def __addConnectionJoint__(self, cubei: Cube, edgei: Direction, cubej: Cube, edgej: Direction):
        shapei = self.getCubeShape(cubei)
        shapej = self.getCubeShape(cubej)
        pinJoint = pymunk.SlideJoint(
            shapei.body, shapej.body, cubei.magnetPos[edgei.value], cubej.magnetPos[edgej.value], StateHandler.CONNECTION_DISTANCE - 2, StateHandler.CONNECTION_DISTANCE)
        self.connectJoints.append(pinJoint)
        self.space.add(pinJoint)

    def __removeConnectJoints__(self):
        for joint in self.connectJoints:
            self.space.remove(joint)
        self.connectJoints.clear()
# --------------------------------------------------------------------------------------------


class Renderer:

    def __init__(self, stateHandler: StateHandler, fps=128):
        self.stateHandler = stateHandler
        self.fps = fps
        self.window = None
        self.clock = None
        self.drawOpt = None
        self.initialized = False

    def pygameInit(self):
        if self.initialized:
            return
        pygame.init()
        self.window = pygame.display.set_mode(self.stateHandler.boardSize)
        pygame.display.set_caption("Magnetic Cube Simulator")
        self.drawOpt = pymunk.pygame_util.DrawOptions(self.window)
        self.drawOpt.flags = pymunk.SpaceDebugDrawOptions.DRAW_CONSTRAINTS
        self.clock = pygame.time.Clock()
        self.initialized = True

    def pygameQuit(self):
        if not self.initialized:
            return
        pygame.quit()
        self.window = None
        self.clock = None
        self.drawOpt = None
        self.initialized = False

    def draw(self):
        if not self.initialized:
            return
        self.window.fill(Color.WHITE)
        # draw the walls
        for shape in self.stateHandler.getBoundaries():
            pygame.draw.line(self.window, Color.DARKGREY, shape.body.local_to_world(
                shape.a), shape.body.local_to_world(shape.b), StateHandler.BOUNDARIE_RAD)
        # draw the cubes with magnets and CenterOfGravity
        for cube in self.stateHandler.getCubes():
            shape = self.stateHandler.getCubeShape(cube)
            verts = [shape.body.local_to_world(lv)
                     for lv in shape.get_vertices()]
            pygame.draw.polygon(self.window, shape.color, verts)
            pygame.draw.lines(self.window, Color.DARKGREY, True, verts, 2)
            if shape in self.stateHandler.frictionpoints:
                pygame.draw.circle(self.window, Color.BLACK,
                                   self.stateHandler.frictionpoints[shape], 6)
            for i, magP in enumerate(cube.magnetPos):
                if 0 < magP[0]*cube.magnetOri[i][0]+magP[1]*cube.magnetOri[i][1]:
                    magcolor = Color.BLUE
                else:
                    magcolor = Color.RED
                pygame.draw.circle(
                    self.window, magcolor, shape.body.local_to_world(magP), 4)
        # draw the connections
        for i, poly in enumerate(self.stateHandler.polyominoes.getAll()):
            for cube in poly.getCubes():
                connects = poly.getConnections(cube)
                for cubeCon in connects:
                    if cubeCon == None:
                        continue
                    pygame.draw.line(self.window, Color.PURPLE, self.stateHandler.getCubeShape(cube).body.local_to_world(
                        (0, 0)), self.stateHandler.getCubeShape(cubeCon).body.local_to_world((0, 0)), 4)
        # draw the compass
        comPos = pymunk.Vec2d(12,12)
        pygame.draw.circle(self.window, Color.LIGHTGRAY,  comPos, 12)
        pygame.draw.circle(self.window, Color.LIGHTBROWN,  comPos, 10)
        pygame.draw.line(self.window, Color.BLUE, comPos, comPos + 12 * Direction.SOUTH.vec(self.stateHandler.magAngle), 3)
        pygame.draw.line(self.window, Color.RED, comPos, comPos + 12 * Direction.NORTH.vec(self.stateHandler.magAngle), 3)
        # debug draw
        self.stateHandler.space.debug_draw(self.drawOpt)
        # update the screen
        pygame.display.update()
        self.clock.tick(self.fps)
