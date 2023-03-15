"""
Holds the Simulation class

@author: Aaron T Becker, Kjell Keune
"""
import sys
import pygame
import math
from threading import Thread, Event

from sim.state import Configuration, Cube
from sim.motion import *
from sim.handling import *

DEBUG = False


class Simulation:
    """
    Top-level class for interacting with the Simulation
    """

    # (in seconds) bigger steps make sim faster but unprecise/unstable 0.04 seems reasonable
    STEP_TIME = 0.05

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

        self.stopped = Event()
        self.started = Event()

        self.stateHandler = StateHandler()
        self.renderer = Renderer(self.stateHandler)
        self.fps = 64
        self.updatePerFrame = 1

        self.motionsToExecute = Queue()
        self.currentMotion = None
        self.motionSteps = Queue()

    def loadConfig(self, newConfig: Configuration):
        """
        Notifies the simulation to load a new configuration on the next update.
        """
        wasRunning = self.started.is_set()
        resize = (not self.stateHandler.boardSize ==
                  newConfig.boardSize) and self.drawingActive
        if resize:
            if wasRunning:
                self.stop()
            self.renderer.pygameQuit()
        self.stateHandler.loadConfig(newConfig)
        if wasRunning and resize:
            self.start()
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
        Notifies the simulation to execute a motion returns when the motion is finished executing.

        Parameters:
            motion: motion to execute
        """
        motion.executed.clear()
        self.motionsToExecute.put(motion)
        motion.executed.wait()

    def executeMotion_nowait(self, motion: Motion):
        """
        Notifies the simulation to execute a motion returns immediately.

        Parameters:
            motion: motion to execute
        """
        motion.executed.clear()
        self.motionsToExecute.put(motion)

    def start(self):
        """
        Starts the simulation on a new thread. The new thread initializes pygame if drawing is activ. Returns when initialization is done.
        """
        if (self.started.isSet()):
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
        if (self.started.is_set()):
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
        if (self.stopped.is_set()):
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
        self.renderer.pygameQuit()
        del self
        if DEBUG:
            print("Simulation terminated.")
        return config

    def disableDraw(self):
        """
        Disables drawing. Restartes to quit pygame.
        """
        if not self.drawingActive:
            return
        wasRunning = self.started.is_set()
        if wasRunning:
            self.stop()
        self.renderer.pygameQuit()
        self.drawingActive = False
        if wasRunning:
            self.start()

    def enableDraw(self):
        """
        Enables drawing. Restarts to initialize pygame.
        """
        if self.drawingActive:
            return
        wasRunning = self.started.is_set()
        if wasRunning:
            self.stop()
        self.drawingActive = True
        if wasRunning:
            self.start()

    def __run__(self):
        # initialisation
        if self.drawingActive:
            self.renderer.pygameInit()
        update = 0
        self.started.set()
        # Simulation loop
        while self.started.isSet():
            if self.drawingActive:
                self.__userInputs__()
            step = self.__nextStep__()
            self.stateHandler.update(
                step.angChange, step.elevChange, Simulation.STEP_TIME)
            if self.drawingActive and (update % self.updatePerFrame == 0 or not self.started.is_set()):
                self.renderer.render(self.fps)
            update += 1
        self.stopped.set()
        sys.exit()

    def __nextStep__(self) -> Step:
        """
        Returns:
            The next step to execute the current motion.
            Returns Step with zero updates if all motions have been executed.
        """
        if self.motionSteps.empty():
            if not self.currentMotion == None:
                self.currentMotion.executed.set()
                if DEBUG:
                    print(f"{self.currentMotion} executed.")
            if self.motionsToExecute.empty():
                self.currentMotion = None
                return Step()
            self.currentMotion = self.motionsToExecute.get()
            longestChain = max(self.stateHandler.polyominoes.maxPolyWidth,
                               self.stateHandler.polyominoes.maxPolyHeight)
            steps = self.currentMotion.stepSequence(
                Simulation.STEP_TIME, longestChain)
            for i in steps:
                self.motionSteps.put(i)
        return self.motionSteps.get()

    def __speedUp__(self):
        if self.fps >= 64:
            self.updatePerFrame += 2
        else:
            self.fps *= 2

    def __slowDown__(self):
        if self.updatePerFrame > 1:
            self.updatePerFrame -= 2
        elif self.fps > 2:
            self.fps /= 2

    def __userInputs__(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                thread = Thread(target=self.terminate, daemon=False)
                thread.start()
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == 119 and self.userControls:  # 'w' pivotwalk right
                    self.executeMotion_nowait(PivotWalk(PivotWalk.RIGHT))
                elif event.key == 97 and self.userControls:  # 'a' rotate ccw
                    self.executeMotion_nowait(Rotation(math.radians(-10)))
                elif event.key == 115 and self.userControls:  # 's' pivotwalk left
                    self.executeMotion_nowait(PivotWalk(PivotWalk.LEFT))
                elif event.key == 100 and self.userControls:  # 'd' rotate cw
                    self.executeMotion_nowait(Rotation(math.radians(10)))
                elif event.key == 121:  # 'y' decrease speed
                    self.__slowDown__()
                elif event.key == 120:  # 'x' increase speed
                    self.__speedUp__()
                elif event.key == 99 and self.userControls:  # 'c' clear space
                    self.renderer.linesToDraw.clear()
                    self.renderer.pointsToDraw.clear()
                    self.stateHandler.loadConfig(StateHandler.DEFAULT_CONFIG)
                elif event.key == 105:  # 'i' info
                    config = self.stateHandler.saveConfig()
                    self.renderer.pointsToDraw.clear()
                    for poly in config.getPolyominoes().getAll():
                        start = config.getCOM(poly)
                        self.renderer.pointsToDraw.append((Renderer.BLACK, start,4))
                        end = start + config.getPivotWalkingVec(poly, PivotWalk.DEFAULT_PIVOT_ANG, PivotWalk.RIGHT)
                        self.renderer.linesToDraw.append((Renderer.BLACK, start, end, 3))
                    pass
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
