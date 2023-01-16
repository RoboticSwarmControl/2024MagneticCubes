"""
Holds the Simulation class

@author: Aaron T Becker, Kjell Keune
"""

import pygame
import pymunk
import pymunk.pygame_util
import math
from threading import Thread, Event, Lock
from configuration import Configuration
from motioncontroller import MotionController
from motion import *
from cube import RAD, MRAD, Cube

RED = (255, 0, 0,100)
GREEN = (0, 255, 0,100)
BLACK = (0, 0, 0,100)
LIGHTBROWN = (196, 164, 132,100)
#LIGHTGREEN = (205, 255, 205,100)
#LIGHTRED   = (255, 205, 205,100)
#YELLOW = (255,255,0,100)
#https://sashamaps.net/docs/resources/20-colors/
SASHACOLORS = ((230, 25, 75,100), (60, 180, 75,100), (255, 225, 25,100), (0, 130, 200,100), (245, 130, 48,100), (145, 30, 180,100), (70, 240, 240,100), (240, 50, 230,100), (210, 245, 60,100), (250, 190, 212,100), (0, 128, 128,100), 
            (220, 190, 255,100), (170, 110, 40,100), (255, 250, 200,100), (128, 0, 0,100), (170, 255, 195,100), (128, 128, 0,100), (255, 215, 180,100), (0, 0, 128,100), (128, 128, 128,100), (255, 255, 255,100), (0, 0, 0,100))

class Simulation:
    """
    Top-level class for interacting with the Simulation
    """
    
    def __init__(self, width=800, height=800, fps=60, drawing=True, userInputs=True):
        """
        creates a Simulation with empty configuration

        Parameters:
            width: screen width
            height: screen height
            fps: frames/updates pre second (simulation speed)
        """
        self.width = width 
        self.height = height
        self.fps = fps
        self.drawingActive = drawing
        self.userInputsActive = userInputs

        self.space = None
        self.window = None

        self.running = False
        self.stopped = Event()
        self.updateLock = Lock()
        self.config = Configuration(0, 0, [])
        self.config.loaded = True
        self.controller = MotionController(fps)
        
        
    def start(self):
        """
        Starts the simulation on a new thread. The new thread initializes pygame.
        """
        if (self.running):
            print("Simulation already running.")
            return
        self.running = True
        self.stopped.clear()
        thread = Thread(target=self.__run__, daemon=False)
        thread.start()

    def stop(self):
        """
        Stops Simulation. pygame will also terminate
        """
        self.running = False
        self.stopped.wait(1)

    def loadConfig(self, newConfig: Configuration) -> Configuration:
        """
        Loads a new configuration and returns the old one. The simulation needs to be stopped befor calling this method
        and newConfig should not be loaded by any simulation. 
        """
        if newConfig.loaded:
            print("Configuration is already loaded by a simulation")
            return
        if self.running:
            print("Simulation needs to be stopped befor loading new configuration.")
            return
        oldConfig = self.config
        oldConfig.loaded = False
        self.config = newConfig
        self.config.loaded = True
        return oldConfig
  
    def saveConfig(self):
        """
        Returns a duplicate of the current state the configuration is in.
        """
        self.updateLock.acquire()
        save = self.config.duplicate()
        self.updateLock.release()
        return save

    def pivotWalk(self, direction) -> bool:
        """
        Notifies the simulation to do one pivot walking cycle and returns when the motion finished executing.

        Parameters:
            direction: direction of pivot walk. Either motion.LEFT (-1) or motion.RIGHT (1)

        Returns: 
            if a configuration change accured. Not implemented yet.
        """
        motion = PivotWalk(direction)
        self.controller.add(motion)
        motion.executed.wait()
        return False #return if config changed

    
    def rotate(self, angle) -> bool:
        """
        Notifies the simulation to do a rotation and returns when the motion finished executing.

        Parameters:
            angle: rotation angle in radians. Negativ values for rotation counterclockwise.

        Returns: 
            if a configuration change accured. Not implemented yet.
        """
        motion = Rotation(angle)
        self.controller.add(motion)
        motion.executed.wait()
        return False #return if config changed

    def pivotWalk_nowait(self, direction):
        """
        Notifies the simulation to do one pivot walking cycle and returns immediately.

        Parameters:
            direction: direction of pivot walk. Either motion.LEFT (-1) or motion.RIGHT (1)
        """
        self.controller.add(PivotWalk(direction))

    def rotate_nowait(self, angle):
        """
        Notifies the simulation to do a rotation and returns immediately.

        Parameters:
            angle: rotation angle in radians. Negativ values for rotation counterclockwise.
        """
        self.controller.add(Rotation(angle))
    
    def addCube(self, cube):
        """
        Adds a cube to the current configuration

        Parameters:
            cube: cube to be added
        """
        self.__createCube__(cube)
        self.config.cubes.append(cube)

    def __run__(self):
        #initialisation
        pygame.init()
        self.space = pymunk.Space()
        self.space.gravity = (0,0)  # gravity doesn't exist
        self.space.damping = 0.2  #simulate top-down gravity with damping
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("magnetic cube simulator")
        drawOptions = pymunk.pygame_util.DrawOptions(self.window)
        clock = pygame.time.Clock()
        
        self.__createBoundaries__()
        for cube in self.config.cubes:
            self.__createCube__(cube)
        #Simulation loop
        while self.running:
            if self.userInputsActive:
                self.__userInputs__()
            self.__update__()
            self.space.step(1 / self.fps)
            if self.drawingActive:
                self.__draw__(drawOptions)
                clock.tick(self.fps)   
        pygame.quit()
        self.stopped.set()


    def __update__(self):
        change = self.controller.nextStep()
        self.updateLock.acquire()
        self.config._update_(self.config.magAngle + change[0], self.config.magElevation + change[1])
        self.updateLock.release()

    def __draw__(self, drawOptions):
        self.window.fill("white")
        self.space.debug_draw(drawOptions)
        # draw the magnets and CenterOfGravity-- for all cubes
        for cube in self.config.cubes: #COM
            pygame.draw.circle(self.window, BLACK,  cube.shape.body.local_to_world(cube.shape.body.center_of_gravity), 7)
        
        for cube in self.config.cubes:
            #magnets
            for i, magP in enumerate(cube.shape.magnetPos):
                if 0 < magP[0]*cube.shape.magnetOri[i][0]+magP[1]*cube.shape.magnetOri[i][1]:
                    magcolor = GREEN
                else:
                    magcolor = RED
                pygame.draw.circle(self.window, magcolor,  cube.shape.body.local_to_world(magP) , 5)
                
        #draw the connections
        for i,connects in enumerate(self.config.magConnect):
            for j in connects:
                pygame.draw.line(self.window, SASHACOLORS[self.config.poly[i]], self.config.cubes[i].shape.body.local_to_world((0,0)), self.config.cubes[j].shape.body.local_to_world((0,0)),3)
                #pygame.draw.line(window, "yellow", cubes[i].body.local_to_world((0,0)), cubes[j].body.local_to_world((0,0)),3)
                #pygame.draw.circle(window, YELLOW,  cubes[i].body.local_to_world, 6)
        
        # draw the compass  
        pygame.draw.circle(self.window, LIGHTBROWN,  (10,10), 11)
        pygame.draw.line(self.window, "red",   (10,10), (10+10*math.cos(self.config.magAngle), 10+10*math.sin(self.config.magAngle)) ,3) 
        pygame.draw.line(self.window, "green", (10,10), (10-10*math.cos(self.config.magAngle), 10-10*math.sin(self.config.magAngle)) ,3) 

        pygame.display.update() #draw to the screen
        return

    def __userInputs__(self):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == 119:  #'w' pivotwalk right
                    self.pivotWalk_nowait(RIGHT)
                elif event.key == 97: #'a' rotate ccw
                    self.rotate_nowait(-math.radians(5))
                elif event.key == 115: #'s' pivotwalk left
                    self.pivotWalk_nowait(LEFT)
                elif event.key == 100: #'d' rotate cw
                    self.rotate_nowait(math.radians(5))
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: #'left click' places cube type=0
                    self.addCube(Cube(pygame.mouse.get_pos(), 0))
                elif event.button == 3: #'right click' places cube type=1
                    self.addCube(Cube(pygame.mouse.get_pos(), 1))
            elif event.type == pygame.QUIT:
                self.running = False
                break


    def __createBoundaries__(self):
        rects = [
            [(self.width / 2, self.height - 10),(self.width, 20)],
            [(self.width / 2, 10),(self.width, 20)],
            [(10,  self.height / 2),(20, self.height)],
            [(self.width - 10,  self.height / 2),(20, self.height)]
        ]
        for pos, size in rects:
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = pos
            shape = pymunk.Poly.create_box(body, size)
            shape.elasticity = 0.4
            shape.friction = 0.5
            self.space.add(body,shape)

    def __createCube__(self, cube):          
        body = pymunk.Body()
        body.position = cube.position
        shape = pymunk.Poly(body, [(-RAD,-RAD),(-RAD,RAD),(RAD,RAD),(RAD,-RAD)],radius = 1)
        #shape = pymunk.Poly.create_box(body,(2*rad,2*rad), radius = 1)
        shape.mass = 10
        shape.elasticity = 0.4
        shape.friction = 0.4
        shape.color = LIGHTBROWN

        shape.magnetPos = [(MRAD,0),(0,MRAD),(-MRAD,0),(0,-MRAD)]
        if cube.type == 0:
            shape.magnetOri = [(1,0),(0,1),(1,0),(0,-1)]
        else:
            shape.magnetOri = [(1,0),(0,-1),(1,0),(0,1)]
        body.angle = self.config.magAngle
        self.space.add(body,shape)
        cube.shape = shape