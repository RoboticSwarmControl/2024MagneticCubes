import pygame
import pymunk
import pymunk.pygame_util
import math
import threading

class Simulation:

    def __init__(self):
        pygame.init()

        self.running = False
        self.fps = 60
        self.width = 800 
        self.height = 800
        self.magAngle = 0  #orientation of magnetic field (in radians)
        self.magElevation = 0 
        self.fmag = 1000
        
        self.MRAD = 15  #distance of magnet from center of cube
        self.rad = 20 #half length of side of cube

        self.space = pymunk.Space()
        self.space.gravity = (0,0)  # gravity doesn't exist
        self.space.damping = 0.2  #simulate top-down gravity with damping
        
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("magnetic cube simulator")

        self.__create_boundaries__()
        
    def start(self):
        if (self.running):
            print("Simulation already running.")
            return
        self.running = True
        thread = threading.Thread(target=self.__simloop__, daemon=True)
        thread.start()

    def stop(self):
        self.running = False

    def __simloop__(self):
        while self.running:
            self.space.step(1 / self.fps)
            pygame.time.Clock().tick(self.fps)


    def __create_boundaries__(self):
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