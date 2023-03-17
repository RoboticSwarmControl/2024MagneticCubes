
"""
Holds the StateHandler class

@author: Aaron T Becker, Kjell Keune
"""
import pygame
import pymunk.pygame_util
import pymunk
import math
from threading import Lock
from sim.motion import Tilt

from sim.state import *


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

        self.magAngle = 0
        self.magElevation = 0

        self.magConnect = {}
        self.magConnect_pre = {}
        self.polyominoes = PolyCollection()

        self.configToLoad = StateHandler.DEFAULT_CONFIG
        self.updateLock = Lock()

        self.frictionpoints = {}
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
        self.boardSize = newConfig.boardSize
        self.configToLoad = newConfig

    def saveConfig(self) -> Configuration:
        self.updateLock.acquire()
        cube_pos = {}
        cube_meta = {}
        for cube, shapes in self.cube_shapes.items():
            cube_pos[cube] = shapes[0].body.position
            cube_meta[cube] = (shapes[0].body.angle, shapes[0].body.velocity)
        config = Configuration(self.boardSize, self.magAngle, cube_pos, cube_meta, self.polyominoes.getAll(), self.magElevation)
        self.updateLock.release()
        return config

    def update(self, angChange, elevation, dt):
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
        self.space.step(dt)
        # apply the change
        self.magAngle += angChange
        if elevation != 0:
            self.magElevation = elevation
        # detect polyominos based on the magnetic connections
        if not self.magConnect == self.magConnect_pre:
            self.polyominoes.detectPolyominoes(self.magConnect)
        # safe magnetic connections to _pre and clear this one
        self.magConnect_pre = self.magConnect
        self.magConnect = {}
        # apply forces from magneticfield to each cube in each poly
        self.frictionpoints.clear()
        for poly in self.polyominoes.getAll():
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
                magOrii = cubei.magnetOri[i]
                mi = Vec2d(magOrii[0],magOrii[1]).rotated(angi)
                magPosj = shapej.body.local_to_world(magPosLj)
                magOrij = cubej.magnetOri[j]
                mj = Vec2d(magOrij[0],magOrij[1]).rotated(angj)
                # magForce1on2( p1, p2, m1,m2)
                fionj = Cube.magForce1on2(magPosi, magPosj, mi, mj)
                shapei.body.apply_force_at_world_point(
                    (-fionj[0], -fionj[1]), magPosi)
                shapej.body.apply_force_at_world_point(
                    fionj,                magPosj)
                # Determine magnet connections
                if fionj.length >= StateHandler.CONNECTION_FORCE_MIN:
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
                shape.body.apply_force_at_world_point(
                    (1 - StateHandler.NOMINAL_FRICTION) * force * poly.size() / len(frictionCubes), fricPoint)
                self.frictionpoints[shape] = fricPoint  # just for drawing
        # damp the angular velocity
        shape.body.angular_velocity *= StateHandler.ANG_VEL_DAMP

    def __loadConfig__(self):
        # clear space
        # JOINTS
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
            return
        shapes = self.cube_shapes[cube]
        self.space.remove(shapes[0].body, shapes[0], shapes[1])
        del self.cube_shapes[cube]
        del self.magConnect[cube]
        del self.sensor_cube[shapes[1]]

    def __addCube__(self, cube: Cube, pos, ang, vel):
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

    BLACK = (0, 0, 0,100)
    WHITE = (255, 255, 255, 100)
    DARKGREY = (90, 90, 90, 100)
    LIGHTGRAY = (170, 170, 170, 100)
    RED = (195, 0, 0, 100)
    LIGHTRED = (250, 150, 150, 100)
    BLUE = (0, 0, 195, 100)
    LIGHTBLUE = (150, 150, 250, 100)
    LIGHTBROWN = (201, 165, 129, 100)
    PURPLE = (151, 0, 196, 100)
    YELLOW = (252, 214, 88, 100)

    def __init__(self, stateHandler: StateHandler, fps=128):
        self.__stateHandler = stateHandler
        self.__window = None
        self.__clock = None
        self.__drawOpt = None
        self.initialized = False
        self.markedCubes = set()
        self.pointsToDraw = []
        self.linesToDraw = []

    def pygameInit(self):
        if self.initialized:
            return
        pygame.init()
        self.__window = pygame.display.set_mode(self.__stateHandler.boardSize)
        pygame.display.set_caption("Magnetic Cube Simulator")
        self.__drawOpt = pymunk.pygame_util.DrawOptions(self.__window)
        self.__drawOpt.flags = pymunk.SpaceDebugDrawOptions.DRAW_CONSTRAINTS
        self.__clock = pygame.time.Clock()
        self.initialized = True

    def pygameQuit(self):
        if not self.initialized:
            return
        pygame.quit()
        self.__window = None
        self.__clock = None
        self.__drawOpt = None
        self.initialized = False

    def render(self, fps):
        if not self.initialized:
            return
        self.__window.fill(Renderer.WHITE)
        # draw the walls
        for shape in self.__stateHandler.getBoundaries():
            pygame.draw.line(self.__window, Renderer.DARKGREY, shape.body.local_to_world(
                shape.a), shape.body.local_to_world(shape.b), StateHandler.BOUNDARIE_RAD)
        # draw the cubes with magnets and frictionpoints
        for cube in self.__stateHandler.getCubes():
            shape = self.__stateHandler.getCubeShape(cube)
            verts = [shape.body.local_to_world(lv)
                     for lv in shape.get_vertices()]
            # draw cube rect
            if cube.type == Cube.TYPE_RED:
                cubeColor = Renderer.LIGHTRED
            else:
                cubeColor = Renderer.LIGHTBLUE
            pygame.draw.polygon(self.__window, cubeColor, verts)
            # draw cube outline
            if cube in self.markedCubes:
                outlineColor = Renderer.YELLOW
            else:
                outlineColor = Renderer.DARKGREY
            pygame.draw.lines(self.__window, outlineColor, True, verts, 2)
            # draw the magnets
            for i, magP in enumerate(cube.magnetPos):
                if 0 < magP[0]*cube.magnetOri[i][0]+magP[1]*cube.magnetOri[i][1]:
                    magcolor = Renderer.BLUE
                else:
                    magcolor = Renderer.RED
                pygame.draw.circle(
                    self.__window, magcolor, shape.body.local_to_world(magP), 4)
            # draw frictino points
            if shape in self.__stateHandler.frictionpoints:
                pygame.draw.circle(self.__window, Renderer.PURPLE,
                                   self.__stateHandler.frictionpoints[shape], 3)
        # polyomino drawing
        for i, poly in enumerate(self.__stateHandler.polyominoes.getAll()):
            for cube in poly.getCubes():
                connects = poly.getConnections(cube)
                for cubeCon in connects:
                    if cubeCon == None:
                        continue
                    pygame.draw.line(self.__window, Renderer.PURPLE, self.__stateHandler.getCubeShape(cube).body.local_to_world(
                        (0, 0)), self.__stateHandler.getCubeShape(cubeCon).body.local_to_world((0, 0)), 4)
        # draw user points and lines
        for point in self.pointsToDraw:
            pygame.draw.circle(self.__window, point[0], point[1], point[2])
        for line in self.linesToDraw:
            pygame.draw.line(self.__window, line[0], line[1], line[2], line[3])
        # draw the compass
        comPos = pymunk.Vec2d(12,12)
        pygame.draw.circle(self.__window, Renderer.LIGHTGRAY,  comPos, 12)
        pygame.draw.circle(self.__window, Renderer.LIGHTBROWN,  comPos, 10)
        pygame.draw.line(self.__window, Renderer.BLUE, comPos, comPos + 12 * Direction.SOUTH.vec(self.__stateHandler.magAngle), 3)
        pygame.draw.line(self.__window, Renderer.RED, comPos, comPos + 12 * Direction.NORTH.vec(self.__stateHandler.magAngle), 3)
        # debug draw
        self.__stateHandler.space.debug_draw(self.__drawOpt)
        # update the screen
        pygame.display.update()
        self.__clock.tick(fps)
