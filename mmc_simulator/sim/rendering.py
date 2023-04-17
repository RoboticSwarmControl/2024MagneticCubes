import pygame
import pymunk.pygame_util
from sim.handling import StateHandler
from com.state import Cube, Direction

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
                connects = poly.getConnected(cube)
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