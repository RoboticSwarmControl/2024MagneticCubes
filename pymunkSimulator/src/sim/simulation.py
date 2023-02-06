"""
Holds the Simulation class

@author: Aaron T Becker, Kjell Keune
"""

import pygame
import pymunk
import pymunk.pygame_util
import math
from threading import Thread, Event
from util import Color
from state import Configuration, Cube
from sim.statehandler import StateHandler
from sim.motion import PivotWalk, Rotation, MotionController


class Simulation:
    """
    Top-level class for interacting with the Simulation
    """
    FPS = 120  # Determines the visual speed of the simulation has no effect when drawing is disabled
    STEP_TIME = 0.02  # bigger steps make sim faster but unprecise/unstable 0.02 seems reasonable
    DEBUG = True

    def __init__(self, width=800, height=800, drawing=True, userInputs=True):
        """
        creates a Simulation with empty configuration

        Parameters:
            width: screen width
            height: screen height
            drawing: if the simulation should draw
            userInputs: if user inputs are enabled
        """
        self.width = width
        self.height = height
        self.drawingActive = drawing
        self.userInputsActive = userInputs

        self.space = pymunk.Space()
        self.space.gravity = (0, 0)  # gravity doesn't exist
        self.space.damping = 0.2  # simulate top-down gravity with damping
        self.__createBoundaries__()
        self.window = None

        self.stopped = Event()
        self.started = Event()

        self.stateHandler = StateHandler(self.space)
        self.controller = MotionController()

    def loadConfig(self, newConfig: Configuration) -> Configuration:
        """
        Loads a new configuration. Returns when loading is done.
        """
        self.stateHandler.loadConfig(newConfig)
        if Simulation.DEBUG: print("Configuration loaded.")

    def saveConfig(self):
        """
        Returns the configuration the simulation currently has.
        """
        save = self.stateHandler.saveConfig()
        if Simulation.DEBUG: print("Configuration saved.")
        return save

    def addCube(self, cube: Cube, pos):
        """
        Adds a cube to the current configuration

        Parameters:
            cube: cube to be added
            pos: position of the cube
        """
        config = self.stateHandler.saveConfig()
        config.addCube(cube, pos)
        self.stateHandler.loadConfig(config)
        if Simulation.DEBUG: print("Added cube" + str(cube) + "to current configuration")

    def removeCube(self, cube: Cube):
        """
        Removes a cube from the current configuration

        Parameters:
            cube: cube to be removed
        """
        config = self.stateHandler.saveConfig()
        config.removeCube(cube)
        self.stateHandler.loadConfig(config)
        if Simulation.DEBUG: print("Removed cube" + str(cube) + "from current configuration")

    def pivotWalk(self, direction) -> bool:
        """
        Notifies the simulation to do one pivot walking cycle and returns when the motion finished executing.

        Parameters:
            direction: direction of pivot walk. Either motion.LEFT (-1) or motion.RIGHT (1)
        """
        motion = PivotWalk(direction)
        self.controller.add(motion)
        motion.executed.wait()

    def rotate(self, angle) -> bool:
        """
        Notifies the simulation to do a rotation and returns when the motion finished executing.

        Parameters:
            angle: rotation angle in radians. Negativ values for rotation counterclockwise.
        """
        motion = Rotation(angle)
        self.controller.add(motion)
        motion.executed.wait()

    def pivotWalk_nowait(self, direction):
        """
        Notifies the simulation to do one pivot walking cycle and returns immediately.

        Parameters:
            direction: direction of pivot walk. Either PivotWalk.LEFT (-1) or PivotWalk.RIGHT (1)
        """
        self.controller.add(PivotWalk(direction))

    def rotate_nowait(self, angle):
        """
        Notifies the simulation to do a rotation and returns immediately.

        Parameters:
            angle: rotation angle in radians. Negativ values for rotation counterclockwise.
        """
        self.controller.add(Rotation(angle))

    def start(self):
        """
        Starts the simulation on a new thread. The new thread initializes pygame. Returns when initialization is done.
        """
        if (self.started.isSet()):
            print("Simulation already running.")
            return
        thread = Thread(target=self.__run__, daemon=False)
        thread.start()
        self.stopped.clear()
        self.started.wait(1)
        if Simulation.DEBUG: print("Simulation started.")

    def stop(self):
        """
        Stops Simulation. pygame will also terminate. Retruns when terminated.
        """
        self.started.clear()
        self.stopped.wait(1)
        if Simulation.DEBUG: print("Simulation stopped.")

    def disableDraw(self):
        # Maybe do other stuff with the window thats why I have methodes
        self.drawingActive = False

    def enableDraw(self):
        # Maybe do other stuff with the window thats why I have methodes
        self.drawingActive = True

    def __run__(self):
        # initialisation
        pygame.init()
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("magnetic cube simulator")
        drawOptions = pymunk.pygame_util.DrawOptions(self.window)
        clock = pygame.time.Clock()
        self.started.set()
        # Simulation loop
        while self.started.isSet():
            if self.userInputsActive:
                self.__userInputs__()
            self.__update__()
            self.space.step(Simulation.STEP_TIME)
            if self.drawingActive:
                self.__draw__(drawOptions)
                clock.tick(Simulation.FPS)
        pygame.quit()
        self.stopped.set()

    def __update__(self):
        change = self.controller.nextStep()
        self.stateHandler.update(change[0], change[1])

    def __draw__(self, drawOptions):
        self.window.fill("white")
        self.space.debug_draw(drawOptions)
        # draw the magnets and CenterOfGravity-- for all cubes
        for cube in self.stateHandler.getShapes():  # COM
            pygame.draw.circle(self.window, Color.BLACK,  cube.body.local_to_world(
                cube.body.center_of_gravity), 7)

        for cube in self.stateHandler.getShapes():
            # magnets
            for i, magP in enumerate(cube.magnetPos):
                if 0 < magP[0]*cube.magnetOri[i][0]+magP[1]*cube.magnetOri[i][1]:
                    magcolor = Color.GREEN
                else:
                    magcolor = Color.RED
                pygame.draw.circle(self.window, magcolor,
                                   cube.body.local_to_world(magP), 5)

        # draw the connections
        for i, poly in enumerate(self.stateHandler.polyominoes):
            for cube in poly.getCubes():
                connects = poly.getConnections(cube)
                for cubeCon in connects:
                    if cubeCon == None:
                        continue
                    pygame.draw.line(self.window, Color.SASHACOLORS[i], self.stateHandler.getShape(cube).body.local_to_world(
                        (0, 0)), self.stateHandler.getShape(cubeCon).body.local_to_world((0, 0)), 3)

        # draw the compass
        pygame.draw.circle(self.window, Color.LIGHTBROWN,  (10, 10), 11)
        pygame.draw.line(self.window, "red",   (10, 10), (10+10*math.cos(
            self.stateHandler.magAngle), 10+10*math.sin(self.stateHandler.magAngle)), 3)
        pygame.draw.line(self.window, "green", (10, 10), (10-10*math.cos(
            self.stateHandler.magAngle), 10-10*math.sin(self.stateHandler.magAngle)), 3)

        pygame.display.update()  # draw to the screen
        return

    def __userInputs__(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == 119:  # 'w' pivotwalk right
                    self.pivotWalk_nowait(PivotWalk.RIGHT)
                elif event.key == 97:  # 'a' rotate ccw
                    self.rotate_nowait(-math.radians(10))
                elif event.key == 115:  # 's' pivotwalk left
                    self.pivotWalk_nowait(PivotWalk.LEFT)
                elif event.key == 100:  # 'd' rotate cw
                    self.rotate_nowait(math.radians(10))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if event.button == 1:  # 'left click' places cube type=0
                    config = self.stateHandler.saveConfig()
                    config.addCube(Cube(0), mouse_pos)
                    self.stateHandler.loadConfig_nowait(config)
                elif event.button == 3:  # 'right click' places cube type=1
                    config = self.stateHandler.saveConfig()
                    config.addCube(Cube(1), mouse_pos)
                    self.stateHandler.loadConfig_nowait(config)
            elif event.type == pygame.QUIT:
                self.started.clear()
                break

    def __createBoundaries__(self):
        walls = [
            pymunk.Segment(self.space.static_body, (0,0), (self.width,0), 5),
            pymunk.Segment(self.space.static_body, (self.width,0), (self.width, self.height), 5),
            pymunk.Segment(self.space.static_body, (self.width, self.height), (0, self.height), 5),
            pymunk.Segment(self.space.static_body, (0, self.height), (0,0), 5)
        ]
        for wall in walls:
            wall.elasticity = 0.4
            wall.friction = 0.5
            self.space.add(wall)
        
