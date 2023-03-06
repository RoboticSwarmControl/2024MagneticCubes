"""
Holds the Simulation class

@author: Aaron T Becker, Kjell Keune
"""
import pygame
import math
from threading import Thread, Event

from util import DEBUG
from state import Configuration, Cube
from motion import *
from sim.handling import *

class Simulation:
    """
    Top-level class for interacting with the Simulation
    """

    def __init__(self, drawing=True, userInputs=True):
        """
        creates a Simulation with empty configuration

        Parameters:
            width: screen width
            height: screen height
            drawing: if the simulation should draw
            userInputs: if user inputs are enabled
        """
        self.drawingActive = drawing
        self.userInputsActive = userInputs

        self.stopped = Event()
        self.started = Event()

        self.stateHandler = StateHandler()
        self.renderer = Renderer(self.stateHandler)

        self.motionsToExecute = Queue()
        self.currentMotion = None
        self.motionSteps = Queue()

    def loadConfig(self, newConfig: Configuration):
        """
        Notifies the simulation to load a new configuration on the next update.
        """
        self.stateHandler.loadConfig(newConfig)
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
        if self.renderer.initialized:
            self.renderer.pygameQuit()
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

    def __run__(self):
        # initialisation
        if self.drawingActive and not self.renderer.initialized:
            self.renderer.pygameInit()
        self.started.set()
        # Simulation loop
        while self.started.isSet():
            if self.renderer.initialized:
                self.__userInputs__()
            step = self.__nextStep__()
            self.stateHandler.update(step.angChange, step.elevChange)
            if self.drawingActive:
                self.renderer.draw()
        self.stopped.set()

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
            longestChain = max(self.stateHandler.polyominoes.maxPolyWidth, self.stateHandler.polyominoes.maxPolyHeight)
            steps = self.currentMotion.stepSequence(StateHandler.STEP_TIME, longestChain)
            for i in steps:
                self.motionSteps.put(i) 
        return self.motionSteps.get()

    def __userInputs__(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                thread = Thread(target=self.terminate, daemon=False)
                thread.start()
                break
            if self.userInputsActive:   
                if event.type == pygame.KEYDOWN:
                    if event.key == 119:  # 'w' pivotwalk right
                        self.executeMotion_nowait(PivotWalk(PivotWalk.RIGHT))
                    elif event.key == 97:  # 'a' rotate ccw
                        self.executeMotion_nowait(Rotation(math.radians(-10)))
                    elif event.key == 115:  # 's' pivotwalk left
                        self.executeMotion_nowait(PivotWalk(PivotWalk.LEFT))
                    elif event.key == 100:  # 'd' rotate cw
                        self.executeMotion_nowait(Rotation(math.radians(10)))
                    elif event.key == 105:  # 'i' info
                        config = self.stateHandler.saveConfig()
                        print(config.polyominoes)
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
            
