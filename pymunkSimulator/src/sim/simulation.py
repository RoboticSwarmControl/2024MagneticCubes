"""
Holds the Simulation class

@author: Aaron T Becker, Kjell Keune
"""

import pygame
import pymunk
import math
from threading import Thread, Event
from util import Color, DEBUG
from state import Configuration, Cube
from sim.statehandler import StateHandler
from sim.motion import PivotWalk, Rotation, MotionController


class Simulation:
    """
    Top-level class for interacting with the Simulation
    """
    FPS = 120  # Determines the visual speed of the simulation has no effect when drawing is disabled

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

        self.stateHandler = StateHandler(width, height)
        self.controller = MotionController()

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
        Stops Simulation. pygame will also terminate. Retruns when terminated.
        """
        if (self.stopped.isSet()):
            print("Simulation is not running.")
            return
        self.started.clear()
        self.stopped.wait(1)
        if DEBUG:
            print("Simulation stopped.")

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

    def __run__(self):
        # initialisation
        if self.drawingActive:
            pygame.init()
            window = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("magnetic cube simulator")
            clock = pygame.time.Clock()
        self.started.set()
        # Simulation loop
        while self.started.isSet():
            if (self.userInputsActive and self.drawingActive):
                self.__userInputs__()
            change = self.controller.nextStep()
            self.stateHandler.update(change[0], change[1])
            if self.drawingActive:
                self.__draw__(window)
                clock.tick(Simulation.FPS)
        if self.drawingActive:
            pygame.quit()
        self.stopped.set()

    def __draw__(self, window: pygame.Surface):
        window.fill(Color.WHITE)
        # draw the walls
        for shape in self.stateHandler.getBoundaries():
            pygame.draw.line(window, Color.DARKGREY, shape.body.local_to_world(
                shape.a), shape.body.local_to_world(shape.b), StateHandler.BOUNDARIE_RAD)
        # draw the cubes with magnets and CenterOfGravity
        for shape in self.stateHandler.getShapes():
            verts = [shape.body.local_to_world(lv) for lv in shape.get_vertices()]
            pygame.draw.polygon(window, Color.LIGHTBROWN, verts)
            pygame.draw.lines(window, Color.DARKGREY, True, verts, 2)
            pygame.draw.circle(window, Color.BLACK, shape.body.local_to_world(
                shape.body.center_of_gravity), 6)
            for i, magP in enumerate(shape.magnetPos):
                if 0 < magP[0]*shape.magnetOri[i][0]+magP[1]*shape.magnetOri[i][1]:
                    magcolor = Color.GREEN
                else:
                    magcolor = Color.RED
                pygame.draw.circle(
                    window, magcolor, shape.body.local_to_world(magP), 5)
        # draw the connections
        for i, poly in enumerate(self.stateHandler.getPolyominoes()):
            for cube in poly.getCubes():
                connects = poly.getConnections(cube)
                for cubeCon in connects:
                    if cubeCon == None:
                        continue
                    pygame.draw.line(window, Color.SASHACOLORS[i], self.stateHandler.getShape(cube).body.local_to_world(
                        (0, 0)), self.stateHandler.getShape(cubeCon).body.local_to_world((0, 0)), 3)
        # draw the compass
        pygame.draw.circle(window, Color.LIGHTGRAY,  (12, 12), 12)
        pygame.draw.circle(window, Color.LIGHTBROWN,  (12, 12), 10)
        pygame.draw.line(window, Color.GREEN,   (12, 12), (12+12*math.cos(
            self.stateHandler.magAngle), 12+12*math.sin(self.stateHandler.magAngle)), 3)
        pygame.draw.line(window, Color.RED, (12, 12), (12-12*math.cos(
            self.stateHandler.magAngle), 12-12*math.sin(self.stateHandler.magAngle)), 3)
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if event.button == 1:  # 'left click' places cube type=0
                    config = self.stateHandler.saveConfig()
                    config.addCube(Cube(0), mouse_pos)
                    self.stateHandler.loadConfig(config)
                elif event.button == 3:  # 'right click' places cube type=1
                    config = self.stateHandler.saveConfig()
                    config.addCube(Cube(1), mouse_pos)
                    self.stateHandler.loadConfig(config)
            elif event.type == pygame.QUIT:
                self.started.clear()
                break
