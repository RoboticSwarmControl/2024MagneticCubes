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

    def __init__(self, initial: Configuration=None, goal: Configuration=None, actions=None, state=PlanState.UNDEFINED):
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

    def __init__(self, initial: Configuration=None, goal: Configuration=None, actions=None, state=PlanState.UNDEFINED, connection=None):
        super().__init__(initial, goal, actions, state)
        self.connection = connection

    def __str__(self) -> str:
        return f"{self.state} for {self.connection}"

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
        sim = Simulation(True, False)
        sim.loadConfig(self.initial)
        if self.connection != None:
            sim.renderer.markedCubes.add(self.connection[0])
            sim.renderer.markedCubes.add(self.connection[1])
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
        polyB = save.getPolyominoes().getForCube(self.connection[1])
        return bool(polyB.getConnection(self.connection[1], self.connection[2]) != self.connection[0]) ^ bool(self.state == PlanState.SUCCESS)


class GlobalPlan(Plan):

    def __init__(self, initial: Configuration=None, goal: Configuration=None, actions=None, state=PlanState.UNDEFINED, target: Polyomino=None):
        super().__init__(initial, goal, actions, state)
        self.target = target

    def __str__(self) -> str:
        return f"{self.state} for assembling:\n{self.target}"

    def execute(self):
        """
        Visually executes the actions of all local plans in this global plan 
        """
        sim = Simulation(True, False)
        for plan in self.actions:
            sim.loadConfig(plan.initial)
            if plan.connection != None:
                sim.renderer.markedCubes.add(plan.connection[0])
                sim.renderer.markedCubes.add(plan.connection[1])
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


class TwoCutSubassemblyEdge:

    def __init__(self, start: PolyCollection, connection: tuple, goal: PolyCollection) -> None:
        self.start = start
        self.connection = connection
        self.goal = goal

    def __str__(self) -> str:
        return f"{repr(self.start)} -{self.connection}-> {repr(self.goal)}"

class TwoCutSubassemblyGraph:

    def __init__(self, target: Polyomino) -> None:
        self.note_edges = {}
        poly_twoCuts = {}
        polyColl = PolyCollection([target])
        self.note_edges[polyColl] = {}
        next = Queue()
        next.put(polyColl)
        while not next.empty():
            polyColl: PolyCollection = next.get()
            # make twoCuts for all poly types
            for poly in polyColl.getTypes():
                # dont make twoCut for trivial
                if poly.isTrivial():
                    continue
                # calculate possible twoCuts or take from dict if calculated before
                if poly in poly_twoCuts:
                    twoCuts = poly_twoCuts[poly]
                else:
                    twoCuts = twoCutSubassemblies(poly)
                    poly_twoCuts[poly] = twoCuts
                # list all polys and remove one of the current type 
                polys = polyColl.getAll()
                polys.remove(poly)
                for twoCut, connection in twoCuts.items():
                    # create new polyCollections for each twoCut
                    newPolys = polys.copy()
                    newPolys.extend(twoCut.getAll())
                    newPolyColl = PolyCollection(newPolys)
                    edge = TwoCutSubassemblyEdge(newPolyColl, connection, polyColl)
                    if newPolyColl in self.note_edges:
                        # if note is in tree append the edge
                        self.note_edges[newPolyColl][polyColl] = edge
                    else:
                       # if not put it in and add to next queue
                       self.note_edges[newPolyColl] = {polyColl: edge}
                       next.put(newPolyColl)

    def getAdjacentNotes(self, polys: PolyCollection):
        if not polys in self:
            return None
        return set(self.note_edges[polys].keys())
    
    def getTranslatedConnections(self, polys: PolyCollection, goal: PolyCollection):
        translated = []
        edge: TwoCutSubassemblyEdge = self.note_edges[polys][goal]
        cubeA_graph = edge.connection[0]
        cubeB_graph = edge.connection[1]
        polyA_graph = edge.start.getForCube(cubeA_graph)
        polyB_graph = edge.start.getForCube(cubeB_graph)
        for polyA in polys.getForType(polyA_graph):
            cubeA = polyA.getCube(polyA_graph.getLocalCoordinates(cubeA_graph))
            for polyB in polys.getForType(polyB_graph):
                cubeB = polyB.getCube(polyB_graph.getLocalCoordinates(cubeB_graph))
                translated.append((cubeA, cubeB, edge.connection[2]))
        return translated

    def __contains__(self, key) -> bool:
        return key in self.note_edges

    def __str__(self) -> str:
        string = ""
        for note, edges in self.note_edges.items():
            string += str(note) + "\n"
            for edge in edges.values():
                string += "   " + str(edge) + "\n"
        return string


def twoCutSubassemblies(poly: Polyomino) -> dict:
    twoCuts = {}
    for cube in poly.getCubes():
        for edge in Direction.list():
            if poly.getConnection(cube, edge) != None:
                twoCuts.update(__monotonCutFrom(poly, cube, edge))
    return twoCuts


def __monotonCutFrom(poly: Polyomino, startCube: Cube, startEdge: Direction) -> dict:
    twoCuts = {}
    available = set(Direction.list())
    nextPath = Queue()
    nextPath.put([(startEdge, startCube, available.difference([startEdge.inv()]))])
    while not nextPath.empty():
        path = nextPath.get()
        lastCon = path[len(path) - 1]
        edge = lastCon[0]
        cube = lastCon[1]
        available = lastCon[2]
        dirToTake = __directionsToTake(poly, edge, cube, available)
        if len(dirToTake) <= 1:
            cut = __cutAtPath(poly, path)
            if cut.polyCount() == 2:
                twoCuts[cut] = __pickConnection(poly, path)
                continue
        for edgeToTake, cubeToTake in dirToTake.items():
            newPath = path.copy()
            newPath.append((edgeToTake, cubeToTake, available.difference([edgeToTake.inv()])))
            nextPath.put(newPath)
    return twoCuts

def __cutAtPath(poly: Polyomino, path: list) -> PolyCollection:
    connects = poly.connectionMap()
    for edge, cube, _ in path:
        conCube = poly.getConnection(cube, edge)
        connects[cube][edge.value] = None
        connects[conCube][edge.inv().value] = None
    pc = PolyCollection()
    pc.detectPolyominoes(connects)
    return pc

def __pickConnection(poly: Polyomino, path: list) -> tuple:
    for edge, cube, _ in path:
        if edge in (Direction.NORTH, Direction.SOUTH):
            return (poly.getConnection(cube, edge), cube, edge)
    return (poly.getConnection(cube, edge), cube, edge)

def __directionsToTake(poly: Polyomino, edge: Direction, cube: Cube, availableDir:set=set(Direction.list())):
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