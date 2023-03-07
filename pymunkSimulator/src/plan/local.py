from enum import Enum
import time
from motion import Rotation
from sim.simulation import Simulation
from state import Configuration, Cube
from util import *

class PlanState(Enum):

    UNDEFINED = 0
    SUCCESS = 1
    INVALID = 2

class Plan:

    def __init__(self, initial: Configuration=None, goal: Configuration=None):
        self.initial = initial
        self.goal = goal
        self.actions = []
        self.state = PlanState.UNDEFINED

    @staticmethod
    def concat(planA, planB):
        if planA.goal != planB.initial:
            return None
        if planA.state != PlanState.SUCCESS or planB.state != PlanState.SUCCESS:
            return None
        ccPlan = Plan(planA.initial, planB.goal)
        ccPlan.actions = list(planA.actions) + list(planB.actions)
        ccPlan.state = PlanState.SUCCESS
        return ccPlan



class PlanExecutor:

    def __init__(self):
        self.__sim = None

    def execute(self, plan: Plan):
        self.__sim = Simulation(plan.initial.boardSize, True, False)
        self.__sim.loadConfig(plan.initial)
        self.__sim.start()
        for motion in plan.actions:
            self.__sim.executeMotion(motion)
        self.__sim.stop()



class LocalPlanner:

    def __init__(self):
        self.__sim = Simulation(drawing=True, userInputs=False)
        self.__sim.setDrawingSpeed(64)
        self.__loadedConfig = None

    def singleUpdate(self, config: Configuration) -> Configuration:
        self.__sim.loadConfig(config)
        self.__sim.start()
        self.__sim.stop()
        return self.__sim.saveConfig()
    
    def planCubeConnect(self, intitial: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> Plan:
        plan = Plan(intitial)
        #early failure: wrong cubes, wrong edge, created poly overlapping or cube cant be put in hole
        #create actions for plan
        self.__loadConfig__(intitial)
        self.__alignEdges__(cubeA, cubeB, edgeB)
        #runtime failure: polys containing cubeA/B change, created poly overlapping or cube cant be put in hole
        #                 blocked way (how to dertermin?)
        return plan
    
    def __alignEdges__(self, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> Rotation:
        posA = self.__loadedConfig.getPosition(cubeA)
        posB = self.__loadedConfig.getPosition(cubeB)
        magAng = self.__loadedConfig.magAngle
        vecBA = Vec2d(posA[0], posA[1]) - Vec2d(posB[0], posB[1])
        vecEdgeB = edgeB.vec(magAng)
        if edgeB in (Direction.WEST, Direction.EAST):
            # For side connection just rotate edgeB to vecBA
            vecDes = vecBA
            vecSrc = vecEdgeB
        else:
            # For Top bottom connection move vecDes one cube length perpendicular to vecAB
            vecPer = (2 * Cube.RAD) * vecBA.perpendicular_normal()
            dotPerEdgeB = round(vecPer.dot(vecEdgeB),3)
            if dotPerEdgeB <= 0:
                vecDes = vecBA + vecPer
            else:
                vecDes = vecBA - vecPer
            # Take either west or east as vecSrc. Always the angle <= 90
            vecE = Direction.EAST.vec(magAng)
            vecW = Direction.WEST.vec(magAng)
            if bool(vecDes.dot(vecE) >= 0) ^ bool(dotPerEdgeB == 0):
                vecSrc = vecE
            else:
                vecSrc = vecW
        # Calculate the rotation and execute it
        rotation = Rotation(vecSrc.get_angle_between(vecDes))
        self.__sim.start()
        self.__sim.executeMotion(rotation)
        #self.__sim.stop()
        self.__loadedConfig = self.__sim.saveConfig()
        return rotation
    
    def __loadConfig__(self, config: Configuration):
        self.__sim.loadConfig(config)
        self.__loadedConfig = config


