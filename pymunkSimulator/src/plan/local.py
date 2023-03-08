from enum import Enum
import time

from sim.motion import Rotation, PivotWalk
from sim.simulation import Simulation
from sim.state import *

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
        self.__sim = Simulation(drawing=True, userInputs=False)

    def execute(self, plan: Plan):
        self.__sim.loadConfig(plan.initial)
        self.__sim.start()
        for motion in plan.actions:
            self.__sim.executeMotion(motion)
        self.__sim.stop()

DEBUG = True

class LocalPlanner:

    def __init__(self):
        self.__sim = Simulation(drawing=True, userInputs=True)
        self.__config = None

    def singleUpdate(self, config: Configuration) -> Configuration:
        self.__loadConfig__(config)
        self.__sim.start()
        time.sleep(0.005)
        self.__sim.stop()
        save = self.__sim.saveConfig()
        self.__config = save
        if DEBUG: print("Single update.")
        return save
    
    def planCubeConnect(self, intitial: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> Plan:
        #single update if no poly info available
        if intitial.polyominoes == None:
            intitial = self.singleUpdate(intitial)
        #early failure: wrong cubes, wrong edge, created poly overlapping or cube cant be put in hole
        plans = []
        for direction in (PivotWalk.LEFT, PivotWalk.RIGHT):
            self.__loadConfig__(intitial)
            plan = Plan(intitial)
            while not self.__isConnected__(cubeA, cubeB, edgeB):
                plan.actions.extend(self.__alignEdges__(cubeA, cubeB, edgeB))
                plan.actions.extend(self.__walk__(5, direction))
            plan.goal = self.__config
            plans.append(plan)
        #runtime failure: polys containing cubeA/B change, created poly overlapping or cube cant be put in hole
        #                 blocked way (how to dertermin?)
        return plans
    
    def __alignEdges__(self, cubeA: Cube, cubeB: Cube, edgeB: Direction):
        magAng = self.__config.magAngle
        vecBA = self.__config.getPosition(cubeA) - self.__config.getPosition(cubeB)
        vecEdgeB = edgeB.vec(magAng)
        if edgeB in (Direction.WEST, Direction.EAST):
            # For side connection just rotate edgeB to vecBA
            vecDes = vecBA
            vecSrc = vecEdgeB
            print(f"src={vecSrc}\ndes={vecDes}")
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
        self.__sim.stop()
        self.__config = self.__sim.saveConfig()
        if DEBUG: print("Edges Aligned.")
        return [rotation]
    
    def __walk__(self, amount, direction, pivotAng=PivotWalk.DEFAULT_PIVOT_ANG):
        motions = []
        pWalk = PivotWalk(direction, pivotAng)
        self.__sim.start()
        for _ in range(amount):
            self.__sim.executeMotion(pWalk)
            motions.append(pWalk)
        self.__sim.stop()
        self.__config = self.__sim.saveConfig()
        if DEBUG: print("Walking done.")
        return motions

    def __isConnected__(self, cubeA: Cube, cubeB: Cube, edgeB: Direction):
        polyB = self.__config.polyominoes.getPoly(cubeB)
        return polyB.getConnection(cubeB, edgeB) == cubeA

    def __loadConfig__(self, config: Configuration):
        if config == self.__config:
            return
        self.__sim.loadConfig(config)
        self.__config = config


