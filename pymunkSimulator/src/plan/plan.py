from enum import Enum
import time
from sim.motion import Idle
from sim.simulation import Simulation

from sim.state import Configuration

class PlanState(Enum):

    UNDEFINED = 0
    SUCCESS = 1
    FAILURE = 2
    FAILURE_SAME_TYPE = 3
    FAILURE_CONNECT = 4
    FAILURE_SLIDE_IN = 5
    FAILURE_INVAL_POLY = 6
    FAILURE_MAX_ITR = 7

    def  __str__(self) -> str:
        return self.name


class Plan:

    def __init__(self, initial: Configuration=None, goal: Configuration=None, actions=None, state=PlanState.UNDEFINED, info=None):
        self.initial = initial
        self.goal = goal
        if actions == None:
            self.actions = []
        else:
            self.actions = actions
        self.state = state
        self.info = info

    def __str__(self) -> str:
        return f"{self.state}, {self.info}"

    def cost(self):
        cost = 0
        for action in self.actions:
            cost += action.cost()
        return cost

    def compare(self, other):
        """
        Returns the better plan, meaning the one with lowest costs if it is valid
        """
        # if both plans are valid return the one with lowest costs
        if self.state == PlanState.SUCCESS and other.state == PlanState.SUCCESS:
            if self.cost() < other.cost():
                return self
            else:
                return other
        # if only one in valid return that one. If both are invalid it doesnt matter so return planB
        if self.state == PlanState.SUCCESS:
            return self
        else:
            return other

    def concat(self, other):
        if self.goal != other.initial:
            return None
        if self.state != PlanState.SUCCESS or other.state != PlanState.SUCCESS:
            return None
        ccPlan = Plan(self.initial, other.goal)
        ccPlan.actions = list(self.actions) + list(other.actions)
        ccPlan.state = PlanState.SUCCESS
        return ccPlan
    
    def execute(self):
        """
        Visually executes the motions of a plan starting from its initial config 
        """
        sim = Simulation(True, False)
        sim.loadConfig(self.initial)
        if self.info != None:
            sim.renderer.markedCubes.add(self.info[0])
            sim.renderer.markedCubes.add(self.info[1])
        sim.start()
        for motion in self.actions:
            sim.executeMotion(motion)
        sim.stop()
        time.sleep(1)
        sim.terminate()

    def validate(self) -> bool:
        """
        Validates the plan by executing its actions and checking if the goal matches
        """
        sim = Simulation(False, False)
        sim.loadConfig(self.initial)
        sim.start()
        for motion in self.actions:
            sim.executeMotion(motion)
        sim.stop()
        save = sim.saveConfig()
        polyB = save.getPolyominoes().getPoly(self.info[1])
        return bool(polyB.getConnection(self.info[1], self.info[2]) != self.info[0]) ^ bool(self.state == PlanState.SUCCESS)



def singleUpdate(config: Configuration) -> Configuration:
    """
    Loads the config and lets it do a single update
    Can be useful for retrieving polyomino information.
    returns:
        the config after updating
    """
    sim = Simulation(False, False)
    sim.loadConfig(config)
    sim.start()
    sim.executeMotion(Idle(2))
    return sim.terminate()