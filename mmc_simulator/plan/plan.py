from enum import Enum
import time

from com.motion import Idle
from sim.simulation import Simulation
from com.state import Configuration, Connection, Polyomino

class PlanState(Enum):

    UNDEFINED = 0
    SUCCESS = 1
    FAILURE = 2
    FAILURE_SAME_TYPE = 3
    FAILURE_CONNECT = 4
    FAILURE_SLIDE_IN = 5
    FAILURE_INVAL_POLY = 6
    FAILURE_MAX_ITR = 7
    FAILURE_STUCK = 8
    FAILURE_CAVE = 9
    FAILURE_ALLOWED_POLYS = 10

    def  __str__(self) -> str:
        return self.name


class OptionSorting(Enum):

    MIN_DIST = 0
    GROW_LARGEST = 1
    GROW_SMALLEST = 2

    @staticmethod
    def list() -> list:
        return [OptionSorting(i) for i in range(3)]


class Plan:

    def __init__(self, initial: Configuration, actions=None, goal: Configuration=None,  state=PlanState.UNDEFINED):
        self.initial = initial
        self.goal = goal
        if actions == None:
            self.actions = []
        else:
            self.actions = actions
        self.state = state

    def cost(self):
        cost = 0
        for action in self.actions:
            cost += action.cost()
        return cost


class LocalPlan(Plan):

    def __init__(self, connection: Connection, initial: Configuration, actions:list=None, goal: Configuration=None, state=PlanState.UNDEFINED):
        super().__init__(initial, actions, goal, state)
        self.connection = connection

    def __str__(self) -> str:
        return f"{self.state} for {repr(self.initial)} -{self.connection}-> {repr(self.goal)}"

    def compare(self, other):
        """
        Returns the better plan, meaning the one with lowest costs if it is valid
        """
        # return successfull plan with lowest costs
        if self.state == PlanState.SUCCESS:
            if not other.state == PlanState.SUCCESS:
                return self
            if self.cost() <= other.cost():
                return self
            return other
        if other.state == PlanState.SUCCESS:
            return other
        # if both are not successfull connect and slide failure are preferable
        if self.state in (PlanState.FAILURE_CONNECT, PlanState.FAILURE_SLIDE_IN):
            if not other.state in (PlanState.FAILURE_CONNECT, PlanState.FAILURE_SLIDE_IN):
                return self
            if self.cost() <= other.cost():
                return self
            return other
        if other.state in (PlanState.FAILURE_CONNECT, PlanState.FAILURE_SLIDE_IN):
            return other
        # as a last resort take the one with lowest costs
        if self.cost() <= other.cost():
            return self
        return other
    
    def execute(self):
        """
        Visually executes the motions of a plan starting from its initial config 
        """
        if len(self.actions) == 0:
            return 0
        sim = Simulation(True, False)
        sim.loadConfig(self.initial)
        if self.connection != None:
            sim.renderer.markedCubes.add(self.connection.cubeA)
            sim.renderer.markedCubes.add(self.connection.cubeB)
        executeMotions(sim, self.actions)
        upd = sim.update
        time.sleep(1)
        sim.terminate()
        return upd

    def validate(self) -> bool:
        """
        Validates the plan by executing its actions and checks if the connection at the goal matches
        """
        if len(self.actions) == 0:
            save = singleUpdate(self.initial)
        else:
            sim = Simulation(False, False)
            sim.loadConfig(self.initial)
            executeMotions(sim, self.actions)
            save = sim.saveConfig()
        polyB = save.getPolyominoes().getForCube(self.connection.cubeB)
        return bool(polyB.getConnectedAt(self.connection.cubeB, self.connection.edgeB) != self.connection.cubeA) ^ bool(self.state == PlanState.SUCCESS)


class GlobalPlan(Plan):

    def __init__(self, target: Polyomino, initial: Configuration, actions:list=None, goal: Configuration=None, state=PlanState.UNDEFINED, nconfig=1, nlocal=0, ntcsa=0):
        super().__init__(initial, actions, goal, state)
        self.target = target
        self.nconfig = nconfig
        self.nlocal = nlocal
        self.ntcsa = ntcsa

    def __str__(self) -> str:
        return f"{self.state} for {repr(self.initial)} --> {repr(self.goal)} assembling:\n{self.target}"

    def execute(self):
        """
        Visually executes the actions of all local plans in this global plan 
        """
        sim = Simulation(True, False)
        for plan in self.actions:
            sim.loadConfig(plan.initial)
            if plan.connection != None:
                sim.renderer.markedCubes.add(plan.connection.cubeA)
                sim.renderer.markedCubes.add(plan.connection.cubeB)
            executeMotions(sim, plan.actions)
            if plan.connection != None:
                sim.renderer.markedCubes.clear()
        upd = sim.update
        time.sleep(1)
        sim.terminate()
        return upd

    def validate(self) -> bool:
        """
        Validates the plan by validating all local plans and checking if the target polyomino is present in the end
        """
        return True
        

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
    sim.executeMotion(Idle(1))
    return sim.terminate()

def executeMotions(sim: Simulation, motions: list):
    """
    Starts sim, executes motions and stops sim.
    This happens in a way which tries to prevent any zero updates.
    Neitherless while stating and stopping one zero update each can occure.
    """
    if len(motions) == 0:
        return
    last = motions[len(motions) - 1]
    for i in range(len(motions)):
        sim.executeMotion_nowait(motions[i])
    sim.start()
    last.executed.wait()
    sim.stop()