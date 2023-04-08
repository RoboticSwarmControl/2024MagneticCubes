from enum import Enum
import time

from sim.motion import Idle
from sim.simulation import Simulation
from sim.state import *

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
    FAILURE_HOLE = 9

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
        executeMotions(sim, self.actions)
        time.sleep(1)
        sim.terminate()

    def validate(self) -> bool:
        """
        Validates the plan by executing its actions and checking if the goal matches
        """
        if len(self.actions) == 0:
            save = singleUpdate(self.initial)
        else:
            sim = Simulation(False, False)
            sim.loadConfig(self.initial)
            executeMotions(sim, self.actions)
            save = sim.saveConfig()
        polyB = save.getPolyominoes().getForCube(self.info[1])
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



class TwoCutSubassemblyGraph():

    def __init__(self, target: Polyomino) -> None:
        poly_assemblies = {}
        poly_assemblies[target] = twoCutSubassemblies(target)


def twoCutSubassemblies(poly: Polyomino) -> set:
    twoCuts = set()
    for cube in poly.getCubes():
        for edge in Direction.list():
            if poly.getConnection(cube, edge) != None:
                twoCuts.update(__monotonCutFrom(poly, cube, edge))
    return twoCuts


def __monotonCutFrom(poly: Polyomino, startCube: Cube, startEdge: Direction) -> list:
    twoCuts = []
    available = set(Direction.list())
    nextPath = Queue()
    nextPath.put([(startEdge, startCube, available.difference([startEdge.inv()]))])
    while not nextPath.empty():
        path = nextPath.get()
        lastCon = path[len(path) - 1]
        available = lastCon[2]
        conToTake = __connectionsToTake(poly, lastCon[0], lastCon[1], available)
        if len(conToTake) <= 1:
            cut = __cutByPath(poly, path)
            if cut.polyCount() == 2:
                twoCuts.append(cut)
                continue
        for edge, cube in conToTake.items():
            newPath = path.copy()
            newPath.append((edge, cube, available.difference([edge.inv()])))
            nextPath.put(newPath)
    return twoCuts

def __cutByPath(poly: Polyomino, path: list) -> PolyCollection:
    connects = poly.connectionMap()
    for edge, cube, _ in path:
        conCube = poly.getConnection(cube, edge)
        connects[cube][edge.value] = None
        connects[conCube][edge.inv().value] = None
    pc = PolyCollection()
    pc.detectPolyominoes(connects)
    return pc

def __connectionsToTake(poly: Polyomino, edge: Direction, cube: Cube, availableDir:set=set(Direction.list())):
    dir_cube = {}
    for dir in availableDir:
        if edge.value <= 1 and dir.value <= 1:
            conEdge = Direction((dir.value + 1) % 2)
        elif edge.value <= 1 and dir.value > 1:
            conEdge = dir.inv()
        elif edge.value > 1 and dir.value <= 1:
            conEdge = dir.inv()
        elif edge.value > 1 and dir.value > 1:
            conEdge = Direction(((dir.value - 1) % 2) + 2)
        try:
            conCube = poly.getConnection(cube, conEdge)
            if poly.getConnection(conCube, dir) != None:
                dir_cube[dir] = conCube
        except KeyError:
            pass
    return dir_cube