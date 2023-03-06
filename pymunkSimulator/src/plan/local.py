from enum import Enum
import time
from sim.simulation import Simulation
from state import Configuration, Cube
from util import Direction

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

    def __init__(self, width, height):
        self.__sim = Simulation(width, height, True, False)

    def execute(self, plan: Plan):
        self.__sim.loadConfig(plan.initial)
        self.__sim.start()
        for motion in plan.actions:
            self.__sim.executeMotion(motion)
        self.__sim.stop()



class LocalPlanner:

    def __init__(self, width, height):
        self.__sim = Simulation(width, height, False, False)

    def singleUpdate(self, config: Configuration) -> Configuration:
        self.__sim.loadConfig(config)
        self.__sim.start()
        self.__sim.stop()
        return self.__sim.saveConfig()
    
    def planCubeConnect(self, intitial: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> Plan:
        plan = Plan(intitial)
        #early failure: wrong cubes, wrong edge, created poly overlapping or cube cant be put in hole
        self.__sim.loadConfig(intitial) # could do single update instead
        #create actions for plan
        #runtime failure: polys containing cubeA/B change, created poly overlapping or cube cant be put in hole
        #                 blocked way (how to dertermin?)
        return plan
