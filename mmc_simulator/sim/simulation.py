"""
Holds the Simulation class

@author: Aaron T Becker, Kjell Keune
"""
import time
import pygame
import math
from queue import Queue

from com.state import Configuration, Cube
from com.motion import PivotWalk, Rotation, Motion, Step, Tilt
from sim.handling import StateHandler
from sim.rendering import Renderer

DEBUG = False

KEY_BINDINGS = {"pivotwalk right": "W",
                "rotate counterclockwise": "A",
                "pivotwalk left": "S",
                "rotate clockwise": "D",
                "change magnetic field elevation": "T",
                "increase simulation speed": "X",
                "decrease simulation speed": "Y",
                "clear workspace": "C",
                "place red cube": "MOUSE_LEFT",
                "place blue cube": "MOUSE_RIGHT"
                }

class Simulation:
    """
    Top-level class for interacting with the Simulation
    """

    # (in seconds) bigger steps make sim faster but unprecise/unstable 0.05 seems reasonable
    STEP_TIME = 0.07

    def __init__(self, drawing=True, userControls=True):
        """
        creates a Simulation with empty configuration

        Parameters:
            width: screen width
            height: screen height
            drawing: if the simulation should draw
            userControls: if the user is able to alter the simulation state
        """
        self.drawingActive = drawing
        self.userControls = userControls

        self.stateHandler = StateHandler()
        self.renderer = Renderer(self.stateHandler)
        if self.drawingActive:
            self.renderer.pygameInit()
        self.fps = 64
        self.updatePerFrame = 1
        self.update = 0

        self.motionSteps = Queue()

    def loadConfig(self, newConfig: Configuration):
        """
        Notifies the simulation to load a new configuration on the next update.
        """
        resize = (not self.stateHandler.boardSize ==
                  newConfig.boardSize) and self.drawingActive
        if resize and self.drawingActive:
            self.renderer.pygameQuit()
        self.stateHandler.loadConfig(newConfig)
        if resize and self.drawingActive:
            self.renderer.pygameInit()
        if DEBUG:
            print("Configuration loaded.")

    def saveConfig(self) -> Configuration:
        """
        Returns the configuration the simulation currently has.
        """
        save = self.stateHandler.saveConfig()
        if DEBUG:
            print("Configuration saved.")
        return save

    def executeMotion(self, motion: Motion):
        """
        Simulates a motion returns when the motion is finished executing.

        Parameters:
            motion: motion to execute
        """
        self.__addMotionSteps(motion)
        self.__run()

    def executeMotions(self, motions: list):
        """
        Simulates a list of motions returns when all motions are finished executing.

        Parameters:
            motions: list of motions to execute
        """
        for motion in motions:
            self.__addMotionSteps(motion)
        self.__run()

    def terminate(self) -> Configuration:
        """
        Terminates the simulation. Also terminates pygame when drawing was activated once during runtime.
        This simulation wont be callable anymore after this method,
        so one last configuration of the system is returned.
        """
        config = self.saveConfig()
        self.renderer.pygameQuit()
        del self
        if DEBUG:
            print("Simulation terminated.")
        return config

    def disableDraw(self):
        """
        Disables drawing.
        """
        if not self.drawingActive:
            return
        self.renderer.pygameQuit()
        self.drawingActive = False

    def enableDraw(self):
        """
        Enables drawing.
        """
        if self.drawingActive:
            return
        self.renderer.pygameInit()
        self.drawingActive = True

    def __run(self):
        # Simulation loop
        while not self.motionSteps.empty():
            tt = time.time()
            if self.drawingActive:
                self.__userInputs()
            step = self.motionSteps.get()
            self.stateHandler.update(
                step.angChange, step.elevation, Simulation.STEP_TIME)
            self.stateHandler.timer.addToTotal(time.time() - tt)
            if self.drawingActive and self.update % self.updatePerFrame == 0: #or not self.started.is_set()
                self.renderer.render(self.fps)
            self.update += 1

    def __addMotionSteps(self, motion):
        longestChain = max(self.stateHandler.polyominoes.maxWidth, self.stateHandler.polyominoes.maxHeight)
        steps = motion.stepSequence(Simulation.STEP_TIME, longestChain)
        for i in steps:
            self.motionSteps.put(i)

    def __userInputs(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.terminate()
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == 119 and self.userControls:  # 'w' pivotwalk right
                    self.__addMotionSteps(PivotWalk(PivotWalk.RIGHT))
                elif event.key == 97 and self.userControls:  # 'a' rotate ccw
                    self.__addMotionSteps(Rotation(math.radians(-10)))
                elif event.key == 115 and self.userControls:  # 's' pivotwalk left
                    self.__addMotionSteps(PivotWalk(PivotWalk.LEFT))
                elif event.key == 100 and self.userControls:  # 'd' rotate cw
                    self.__addMotionSteps(Rotation(math.radians(10)))
                elif event.key == 116 and self.userControls:  # 't' change elevation
                    self.__addMotionSteps(Tilt((self.stateHandler.magElevation % 3) + 1))
                elif event.key == 99 and self.userControls:  # 'c' clear space
                    self.__clearSpace()
                elif event.key == 121:  # 'y' decrease speed
                    self.__slowDown()
                elif event.key == 120:  # 'x' increase speed
                    self.__speedUp()
                elif event.key == 105:  # 'i' info
                    self.__info()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if event.button == 1 and self.userControls:  # 'left click' places cube TYPE_RED
                    config = self.stateHandler.saveConfig()
                    config.addCube(Cube(Cube.TYPE_RED), mouse_pos)
                    self.stateHandler.loadConfig(config)
                elif event.button == 3 and self.userControls:  # 'right click' places cube TYPE_BLUE
                    config = self.stateHandler.saveConfig()
                    config.addCube(Cube(Cube.TYPE_BLUE), mouse_pos)
                    self.stateHandler.loadConfig(config)

    def __speedUp(self):
        if self.fps >= 64:
            self.updatePerFrame += 2
        else:
            self.fps *= 2

    def __slowDown(self):
        if self.updatePerFrame > 1:
            self.updatePerFrame -= 2
        elif self.fps > 2:
            self.fps /= 2

    def __clearSpace(self):
        self.renderer.linesToDraw.clear()
        self.renderer.pointsToDraw.clear()
        self.stateHandler.loadConfig(StateHandler.DEFAULT_CONFIG)
    
    def __info(self):
        config = self.stateHandler.saveConfig()
        self.stateHandler.timer.writeTimeStats("../results/Simulator-Time")
        # self.renderer.pointsToDraw.clear()
        # for poly in config.getPolyominoes().getAll():
        #     self.renderer.pointsToDraw.append((Renderer.BLUE, config.getPivotS(poly),4))
        #     self.renderer.pointsToDraw.append((Renderer.RED, config.getPivotN(poly),4))
        #     start = config.getCOM(poly)
        #     self.renderer.pointsToDraw.append((Renderer.BLACK, start,4))
        #     end = start + config.getPivotWalkingVec(poly, PivotWalk.DEFAULT_PIVOT_ANG, PivotWalk.RIGHT)
        #     self.renderer.linesToDraw.append((Renderer.BLACK, start, end, 3))
