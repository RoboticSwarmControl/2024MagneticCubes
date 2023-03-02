"""
Holds the Simulation class

@author: Aaron T Becker, Kjell Keune
"""

import pygame
import pymunk.pygame_util
import pymunk
import math
from threading import Thread, Event
from util import Color, DEBUG
from state import *
from sim.handling import *
from motion import PivotWalk, Rotation 


class Simulation:
    """
    Top-level class for interacting with the Simulation
    """
    FPS = 144  # Determines the visual speed of the simulation has no effect when drawing is disabled

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

        self.stopped = Event()
        self.started = Event()

        self.polyManager = PolyManager()
        self.stateHandler = StateHandler(width, height, self.polyManager)
        self.motionController = MotionController(self.polyManager)

        self.pygameInit = False
        self.window = None
        self.clock = None
        self.drawOpt = None

    def loadConfig(self, newConfig: Configuration) -> Configuration:
        """
        Notifies the simulation to load a new configuration on the next update.
        """
        self.stateHandler.loadConfig(newConfig)
        if DEBUG:
            print("Configuration loaded.")

    def saveConfig(self):
        """
        Returns the configuration the simulation currently has.
        """
        save = self.stateHandler.saveConfig()
        if DEBUG:
            print("Configuration saved.")
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
        if DEBUG:
            print("Added cube" + str(cube) + "to current configuration")

    def removeCube(self, cube: Cube):
        """
        Removes a cube from the current configuration

        Parameters:
            cube: cube to be removed
        """
        config = self.stateHandler.saveConfig()
        config.removeCube(cube)
        self.stateHandler.loadConfig(config)
        if DEBUG:
            print("Removed cube" + str(cube) + "from current configuration")

    def pivotWalk(self, direction) -> bool:
        """
        Notifies the simulation to do one pivot walking cycle and returns when the motion finished executing.

        Parameters:
            direction: direction of pivot walk. Either PivotWalk.LEFT (-1) or PivotWalk.RIGHT (1)
        """
        motion = PivotWalk(direction)
        self.motionController.add(motion)
        motion.executed.wait()

    def rotate(self, angle) -> bool:
        """
        Notifies the simulation to do a rotation and returns when the motion finished executing.

        Parameters:
            angle: rotation angle in radians. Negativ values for rotation counterclockwise.
        """
        motion = Rotation(angle)
        self.motionController.add(motion)
        motion.executed.wait()

    def pivotWalk_nowait(self, direction):
        """
        Notifies the simulation to do one pivot walking cycle and returns immediately.

        Parameters:
            direction: direction of pivot walk. Either PivotWalk.LEFT (-1) or PivotWalk.RIGHT (1)
        """
        self.motionController.add(PivotWalk(direction))

    def rotate_nowait(self, angle):
        """
        Notifies the simulation to do a rotation and returns immediately.

        Parameters:
            angle: rotation angle in radians. Negativ values for rotation counterclockwise.
        """
        self.motionController.add(Rotation(angle))

    def start(self):
        """
        Starts the simulation on a new thread. The new thread initializes pygame if drawing is activ. Returns when initialization is done.
        """
        if (self.started.isSet()):
            print("Simulation already running.")
            return
        thread = Thread(target=self.__run__, daemon=False)
        thread.start()
        self.stopped.clear()
        self.started.wait(1)
        if DEBUG:
            print("Simulation started.")

    def start_onMac(self, callable=None):
        """
        Starts the simulation on this thread and executes the callable on a new thread.
        Only use this function when using macOS, because macOS only allows pygame to run on the main thread.
        Once you started you can only stop but not restart, because of this disable/enableDrawing wont work.
        You can set the drawing option when initializing the Simulation.

        Parameters:
            callable: this function gets called on a new thread this simulation gets passed as parameter
        """
        if (self.started.isSet()):
            print("Simulation already running.")
            return
        if not callable == None:
            controllThread = Thread(target=callable, args=[self], daemon=True)
            controllThread.start()
        self.stopped.clear()
        if DEBUG:
            print("Simulation started.")
        self.__run__()

    def stop(self):
        """
        Stops the Simulation. Returns when simulation is stopped.
        """
        if (self.stopped.isSet()):
            print("Simulation is not running.")
            return
        self.started.clear()
        self.stopped.wait(1)
        if DEBUG:
            print("Simulation stopped.")

    def terminate(self) -> Configuration:
        """
        Terminates the simulation. Also terminates pygame when drawing was activated once during runtime.
        This simulation wont be callable anymore after this method,
        so one last configuration of the system is returned.
        """
        self.stop()
        config = self.saveConfig()
        if self.pygameInit:
            pygame.quit()
        del self
        if DEBUG:
            print("Simulation terminated.")
        return config

    def disableDraw(self):
        """
        Disables drawing. If the simulation is running it will be restarted.
        """
        wasRunning = self.started.is_set()
        if wasRunning:
            self.stop()
        self.drawingActive = False
        if wasRunning:
            self.start()

    def enableDraw(self):
        """
        Enables drawing. If the simulation is running it will be restarted.
        """
        wasRunning = self.started.is_set()
        if wasRunning:
            self.stop()
        self.drawingActive = True
        if wasRunning:
            self.start()

    def __pygameInit__(self):
        pygame.init()
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("magnetic cube simulator")
        self.drawOpt = pymunk.pygame_util.DrawOptions(self.window)
        self.drawOpt.flags = pymunk.SpaceDebugDrawOptions.DRAW_CONSTRAINTS
        self.clock = pygame.time.Clock()
        self.pygameInit = True

    def __run__(self):
        # initialisation
        if self.drawingActive and not self.pygameInit:
            self.__pygameInit__()
        self.started.set()
        # Simulation loop
        while self.started.isSet():
            if (self.userInputsActive and self.drawingActive):
                self.__userInputs__()
            step = self.motionController.nextStep()
            self.stateHandler.update(step.angChange, step.elevChange)
            if self.drawingActive:
                self.__draw__()
                self.clock.tick(Simulation.FPS)
        self.stopped.set()

    def __draw__(self):
        self.window.fill(Color.WHITE)
        # draw the walls
        for shape in self.stateHandler.getBoundaries():
            pygame.draw.line(self.window, Color.DARKGREY, shape.body.local_to_world(
                shape.a), shape.body.local_to_world(shape.b), StateHandler.BOUNDARIE_RAD)
        # draw the cubes with magnets and CenterOfGravity
        for cube in self.stateHandler.getCubes():
            shape = self.stateHandler.getShape(cube)
            verts = [shape.body.local_to_world(lv) for lv in shape.get_vertices()]
            pygame.draw.polygon(self.window, shape.color, verts)
            pygame.draw.lines(self.window, Color.DARKGREY, True, verts, 2)
            if shape in self.stateHandler.frictionpoints:
                pygame.draw.circle(self.window, Color.BLACK, self.stateHandler.frictionpoints[shape], 6)
            for i, magP in enumerate(cube.magnetPos):
                if 0 < magP[0]*cube.magnetOri[i][0]+magP[1]*cube.magnetOri[i][1]:
                    magcolor = Color.BLUE
                else:
                    magcolor = Color.RED
                pygame.draw.circle(
                    self.window, magcolor, shape.body.local_to_world(magP), 4)
        # draw the connections
        for i, poly in enumerate(self.polyManager.getPolyominoes()):
            for cube in poly.getCubes():
                connects = poly.getConnections(cube)
                for cubeCon in connects:
                    if cubeCon == None:
                        continue
                    pygame.draw.line(self.window, Color.PURPLE, self.stateHandler.getShape(cube).body.local_to_world(
                        (0, 0)), self.stateHandler.getShape(cubeCon).body.local_to_world((0, 0)), 4)
        # draw the compass
        pygame.draw.circle(self.window, Color.LIGHTGRAY,  (12, 12), 12)
        pygame.draw.circle(self.window, Color.LIGHTBROWN,  (12, 12), 10)
        pygame.draw.line(self.window, Color.BLUE,   (12, 12), (12+12*math.cos(
            self.stateHandler.magAngle), 12+12*math.sin(self.stateHandler.magAngle)), 3)
        pygame.draw.line(self.window, Color.RED, (12, 12), (12-12*math.cos(
            self.stateHandler.magAngle), 12-12*math.sin(self.stateHandler.magAngle)), 3)
        # debug draw
        self.stateHandler.space.debug_draw(self.drawOpt)
        # update the screen
        pygame.display.update()
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
                elif event.key == 105:  # 'i' info
                    #print(len(self.stateHandler.connectJoints))
                    pass
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if event.button == 1:  # 'left click' places cube TYPE_RED
                    config = self.stateHandler.saveConfig()
                    config.addCube(Cube(Cube.TYPE_RED), mouse_pos)
                    self.stateHandler.loadConfig(config)
                elif event.button == 3:  # 'right click' places cube TYPE_BLUE
                    config = self.stateHandler.saveConfig()
                    config.addCube(Cube(Cube.TYPE_BLUE), mouse_pos)
                    self.stateHandler.loadConfig(config)
            elif event.type == pygame.QUIT:
                thread = Thread(target=self.terminate, daemon=False)
                thread.start()
                break
