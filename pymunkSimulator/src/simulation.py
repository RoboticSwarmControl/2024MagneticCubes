"""
Holds the Simulation class

@author: Aaron T Becker, Kjell Keune
"""

import pygame
import pymunk
import pymunk.pygame_util
import math
import threading
from configuration import Configuration
from motioncontroller import MotionController
from motion import *
from cube import RAD, MRAD

class Simulation:
    """
    Top-level class for interacting with the Simulation
    """
    
    def __init__(self, width, height, fps):
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

        self.space = None
        self.window = None
        self.drawOptions = None

        self.running = False
        self.config = Configuration(0, 0, [])
        self.controller = MotionController(fps)
        
        
    def start(self):
        """
        Starts the simulation on a new thread. The new thread initializes pygame.
        """
        if (self.running):
            print("Simulation already running.")
            return
        self.running = True
        thread = threading.Thread(target=self.__run__, daemon=True)
        thread.start()

    def stop(self):
        """
        Stops Simulation. pygame will also terminate
        """
        self.running = False

    def loadConfig(self, newConfig: Configuration) -> Configuration:
        """
        Loads a new configuration and returns the old one. The simulation needs to be stopped befor calling this method. 
        """
        if self.running:
            print("Simulation needs to be stopped befor loading new configuration.")
            return
        oldConfig = self.config
        self.config = newConfig
        return oldConfig
  

    def pivotWalk(self, direction) -> bool:
        motion = PivotWalk(direction)
        self.controller.add(motion)
        #TODO wait on motion.executed
        return False #return if config changed

    def rotate(self, angle) -> bool:
        motion = Rotation(angle)
        self.controller.add(motion)
        #TODO wait on motion.executed
        return False #return if config changed

    def pivotWalk_nowait(self, direction):
        self.controller.add(PivotWalk(direction))

    def rotate_nowait(self, angle):
        self.controller.add(Rotation(angle))

    def __run__(self):
        #initialisation
        pygame.init()
        clock = pygame.time.Clock()
        self.space = pymunk.Space()
        self.space.gravity = (0,0)  # gravity doesn't exist
        self.space.damping = 0.2  #simulate top-down gravity with damping
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("magnetic cube simulator")
        self.drawOptions = pymunk.pygame_util.DrawOptions(self.window)
        self.__createBoundaries__()
        for cube in self.config.cubes:
            self.__createCube__(cube)
        #Simulation loop
        while self.running:
            self.__update__()
            self.space.step(1 / self.fps)
            self.__draw__()
            clock.tick(self.fps)
        pygame.quit()


    def __update__(self):
        change = self.controller.nextStep()
        self.config.update(self.config.magAngle + change[0], self.config.magElevation + change[1])

    def __draw__(self):
        RED = (255, 0, 0,100)
        GREEN = (0, 255, 0,100)
        BLACK = (0, 0, 0,100)
        LIGHTBROWN = (196, 164, 132,100)
        #YELLOW = (255,255,0,100)
        #https://sashamaps.net/docs/resources/20-colors/
        sashaColors = ((230, 25, 75,100), (60, 180, 75,100), (255, 225, 25,100), (0, 130, 200,100), (245, 130, 48,100), (145, 30, 180,100), (70, 240, 240,100), (240, 50, 230,100), (210, 245, 60,100), (250, 190, 212,100), (0, 128, 128,100), 
                    (220, 190, 255,100), (170, 110, 40,100), (255, 250, 200,100), (128, 0, 0,100), (170, 255, 195,100), (128, 128, 0,100), (255, 215, 180,100), (0, 0, 128,100), (128, 128, 128,100), (255, 255, 255,100), (0, 0, 0,100))
        self.window.fill("white" )

        self.space.debug_draw(self.drawOptions)
        
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
                pygame.draw.line(self.window, sashaColors[self.config.poly[i]], self.config.cubes[i].shape.body.local_to_world((0,0)), self.config.cubes[j].shape.body.local_to_world((0,0)),3)
                #pygame.draw.line(window, "yellow", cubes[i].body.local_to_world((0,0)), cubes[j].body.local_to_world((0,0)),3)
                #pygame.draw.circle(window, YELLOW,  cubes[i].body.local_to_world, 6)
        
        # draw the compass  
        pygame.draw.circle(self.window, LIGHTBROWN,  (10,10), 11)
        pygame.draw.line(self.window, "red",   (10,10), (10+10*math.cos(self.config.magAngle), 10+10*math.sin(self.config.magAngle)) ,3) 
        pygame.draw.line(self.window, "green", (10,10), (10-10*math.cos(self.config.magAngle), 10-10*math.sin(self.config.magAngle)) ,3) 
        
        pygame.display.update() #draw to the screen
        return

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
        LIGHTBROWN = (196, 164, 132,100)
                #LIGHTGREEN = (205, 255, 205,100)
        #LIGHTRED   = (255, 205, 205,100)
        body = pymunk.Body()
        body.position = cube.position
        shape = pymunk.Poly(body, [(-RAD,-RAD),(-RAD,RAD),(RAD,RAD),(RAD,-RAD)],radius = 1)
        #shape = pymunk.Poly.create_box(body,(2*rad,2*rad), radius = 1)
        shape.mass = 10
        shape.elasticity = 0.4
        shape.friction = 0.4
        shape.color = LIGHTBROWN

        shape.magnetPos = [(MRAD,0),(0,MRAD),(-MRAD,0),(0,-MRAD)]
        if cube.cubeType == 0:
            shape.magnetOri = [(1,0),(0,1),(1,0),(0,-1)]
        else:
            shape.magnetOri = [(1,0),(0,-1),(1,0),(0,1)]
        body.angle = self.config.magAngle
        self.space.add(body,shape)
        cube.shape = shape