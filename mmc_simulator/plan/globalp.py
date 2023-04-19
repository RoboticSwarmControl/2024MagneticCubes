from queue import Queue

from com.state import Configuration, PolyCollection, Polyomino, Connection, Direction, Cube
from plan.plan import *
import plan.localp as local

DEBUG = False
PLAY_LOCALS = False

TIMEOUT = 1800

class TwoCutSubassemblyEdge:

    def __init__(self, start: PolyCollection, connection: Connection, end: PolyCollection) -> None:
        self.start = start
        self.connection = connection
        self.end = end

    def __str__(self) -> str:
        return f"{repr(self.start)} -{self.connection}-> {repr(self.end)}"
    
    def __repr__(self) -> str:
        return f"{repr(self.start)} -{self.connection}-> {repr(self.end)}"

class TwoCutSubassemblyGraph:

    def __init__(self, target: Polyomino) -> None:
        self.__note_edges = {}
        poly_twoCuts = {}
        polyColl = PolyCollection([target])
        self.__note_edges[polyColl] = []
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
                for twoCut, connections in twoCuts.items():
                    # create new polyCollections for each twoCut
                    newPolys = polys.copy()
                    newPolys.extend(twoCut.getAll())
                    newPolyColl = PolyCollection(newPolys)
                    for con in connections:
                        edge = TwoCutSubassemblyEdge(newPolyColl, con, polyColl)
                        if newPolyColl in self.__note_edges:
                            # if note is in tree append the edge
                            self.__note_edges[newPolyColl].append(edge)
                        else:
                            # if not put it in and add to next queue
                            self.__note_edges[newPolyColl] = [edge]
                            next.put(newPolyColl)

    def getAllCollections(self) -> set:
        return set(self.__note_edges.keys())

    def getNextCollections(self, polys: PolyCollection):
        if not polys in self.__note_edges:
            return None
        next = set()
        for edge in self.__note_edges[polys]:
            next.add(edge.end)
        return next
    
    def getTranslatedConnections(self, polys: PolyCollection, next: PolyCollection):
        translated = []
        for edge in self.__note_edges[polys]:
            if edge.end != next:
                continue
            cubeA_graph = edge.connection.cubeA
            cubeB_graph = edge.connection.cubeB
            polyA_graph = edge.start.getForCube(cubeA_graph)
            polyB_graph = edge.start.getForCube(cubeB_graph)
            edgeB = edge.connection.edgeB
            for polyA in polys.getForType(polyA_graph):
                cubeA = polyA.getCube(polyA_graph.getLocalCoordinates(cubeA_graph))
                for polyB in polys.getForType(polyB_graph):
                    if id(polyA) != id(polyB):
                        cubeB = polyB.getCube(polyB_graph.getLocalCoordinates(cubeB_graph))
                        translated.append(Connection(cubeA, cubeB, edgeB))
        return translated

    def noteCount(self):
        return len(self.__note_edges)

    def __contains__(self, key) -> bool:
        return key in self.__note_edges

    def __str__(self) -> str:
        string = ""
        for note, edges in self.__note_edges.items():
            string += str(note) + "\n"
            for edge in edges:
                string += "   " + str(edge) + "\n"
            string += "\n"
        return string


def planTargetAssembly(initial: Configuration, target: Polyomino, sorting: OptionSorting=OptionSorting.MIN_DIST) -> GlobalPlan:
    # single update if no poly info available
    if initial.getPolyominoes().isEmpty():
        initial = singleUpdate(initial)
    # check if target is already in initial
    tcsaGraph = TwoCutSubassemblyGraph(target)
    if target in initial.getPolyominoes():
        return GlobalPlan(target, initial, goal=initial, state=PlanState.SUCCESS, ntcsa=tcsaGraph.noteCount())
    # check if initial is in tsca tree
    if not initial.getPolyominoes() in tcsaGraph:
        return GlobalPlan(target, initial, state=PlanState.FAILURE, ntcsa=tcsaGraph.noteCount())
    # init varialbes
    globalFails = set((PlanState.FAILURE_ALLOWED_POLYS, PlanState.FAILURE_MAX_ITR, PlanState.FAILURE_STUCK,
                        PlanState.FAILURE_CAVE, PlanState.FAILURE_INVAL_POLY, PlanState.FAILURE_SAME_TYPE))
    planStack = []
    config_options = {}
    config = initial
    nlocalPlans = 0
    t0 = time.time()
    while True:
        if DEBUG: 
            print(f"----------------{repr(config)}----------------\n")
            print(f"{len(planStack)} local plans in stack.\n{config.getPolyominoes()}")
        # failure when planning takes to long
        if (time.time() - t0) >= TIMEOUT:
            if DEBUG: print(f"Timeout -> Failure!\n{len(config_options)} configs, {nlocalPlans} local plans in total.\n")
            return GlobalPlan(target, initial, state=PlanState.FAILURE, nconfig=len(config_options),
                              nlocal=nlocalPlans, ntcsa=tcsaGraph.noteCount())
        # Plan finished when we assembled the target
        if target in config.getPolyominoes():
            if DEBUG: print(f"Target successfully assembled with {len(planStack)} local plans!\n{len(config_options)} configs, {nlocalPlans} local plans in total.\n")
            return GlobalPlan(target, initial, planStack, config, PlanState.SUCCESS, len(config_options),
                              nlocalPlans, tcsaGraph.noteCount())
        # get possible conection options for this config
        if config in config_options:
            options = config_options[config]
        else:
            options = __determineOptions(config, tcsaGraph, sorting)
            config_options[config] = options
        # else try out options until a valid one is found
        valid = False
        while len(options) > 0:
            optPossible = len(options)
            con = options.pop(0)
            if DEBUG: print(f"{optPossible} connections possible. Starting local planner for {con}.")
            plan = local.planCubeConnect(config, con.cubeA, con.cubeB, con.edgeB, tcsaGraph.getAllCollections())
            nlocalPlans += 1
            if PLAY_LOCALS: plan.execute()
            if not plan.state in globalFails and plan.goal != None:
                valid = True
                config = plan.goal
                planStack.append(plan)
                if DEBUG:print(f"Valid local plan: {plan}.\nContinue with {repr(config)}!\n")
                break
            if DEBUG:print(f"Invalid local plan: {plan}.\nTry next connection.\n")
        if not valid:
            # if all options failed, fall back to last initial-config in planStack
            if len(planStack) == 0:
                # failure if nothing is left to fall back to
                if DEBUG: print(f"Nothing to fall back to -> Failure!\n{len(config_options)} configs, {nlocalPlans} local plans in total.\n")
                return GlobalPlan(target, initial, state=PlanState.FAILURE, nconfig=len(config_options),
                                  nlocal=nlocalPlans, ntcsa=tcsaGraph.noteCount())
            lastPlan = planStack.pop()
            config = lastPlan.initial
            if DEBUG: print(f"No connections left. Fall back to {repr(config)}.\n")


def __determineOptions(config: Configuration, tcsaGraph: TwoCutSubassemblyGraph, sorting: OptionSorting) -> list:
    if sorting == OptionSorting.MIN_DIST:
        return __optionsMinDist(config, tcsaGraph)

def __optionsMinDist(config: Configuration, tcsaGraph: TwoCutSubassemblyGraph) -> list:
    connections = []
    polys = config.getPolyominoes()
    adjNotes = tcsaGraph.getNextCollections(polys)
    if adjNotes == None:
        return connections
    for adj in adjNotes:
        con = tcsaGraph.getTranslatedConnections(polys, adj)
        connections.extend(con)
    connections.sort(key=lambda con: config.getPosition(con.cubeA).get_distance(config.getPosition(con.cubeB)))
    return connections


def twoCutSubassemblies(poly: Polyomino) -> dict:
    twoCuts = {}
    for cube in poly.getCubes():
        for edge in Direction.list():
            if poly.getConnectedAt(cube, edge) != None:
                for cut, con in __monotonCutsFrom(poly, cube, edge).items():
                    if cut in twoCuts:
                        twoCuts[cut].add(con)
                    else:
                        twoCuts[cut] = set([con])
    return twoCuts

def __monotonCutsFrom(poly: Polyomino, startCube: Cube, startEdge: Direction) -> dict:
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
    connects = poly.getConnectionMap()
    for edge, cube, _ in path:
        conCube = poly.getConnectedAt(cube, edge)
        connects[cube][edge.value] = None
        connects[conCube][edge.inv().value] = None
    pc = PolyCollection()
    pc.detectPolyominoes(connects)
    return pc

def __pickConnection(poly: Polyomino, path: list) -> Connection:
    connections = []
    for edge, cube, _ in path:
        connections.append(Connection(poly.getConnectedAt(cube, edge), cube, edge))
    connections.sort(key=lambda con: hash(con))
    # north-south conections are preferred for planning
    for con in connections:
        if con.edgeB in (Direction.NORTH, Direction.SOUTH):
            return con
    return con

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
            conCube = poly.getConnectedAt(cube, conEdge)
            if poly.getConnectedAt(conCube, dir) != None:
                dir_cube[dir] = conCube
        except KeyError:
            pass
    return dir_cube