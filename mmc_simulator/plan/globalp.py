from queue import Queue

from com.state import Configuration, PolyCollection, Polyomino, Connection, Direction, Cube
from plan.plan import *
import plan.localp as local
import copy


class MonotoneCuttingPath:

    def __init__(self, poly: Polyomino, cube: Cube, edge: Direction, edgeOri: Direction) -> None:
        self.__poly = poly
        self.__path = [(cube, edge, edgeOri)]
        self.__oriAvailable = set(Direction.list())
        self.__oriAvailable.difference_update([edgeOri.inv()])

    def cutPoly(self) -> PolyCollection:
        connects = self.__poly.getConnectionMap()
        for cube, edge, ori in self.__path:
            conCube = self.__poly.getConnectedAt(cube, edge)
            if conCube != None:
                connects[cube][edge.value] = None
                connects[conCube][edge.inv().value] = None
        pc = PolyCollection()
        pc.detectPolyominoes(connects)
        return pc

    def pickConnection(self) -> Connection:
        connections = []
        for cube, edge, ori in self.__path:
            conCube = self.__poly.getConnectedAt(cube, edge)
            if conCube != None:
                connections.append(Connection(conCube, cube, edge))
        connections.sort(key=lambda con: hash(con))
        # north-south conections are preferred for planning
        for con in connections:
            if con.edgeB in (Direction.NORTH, Direction.SOUTH):
                return con
        return con

    def extendedPaths(self):
        lastCube, lastEdge, lastOri = self.__path[len(self.__path) - 1]
        # determine the 3 cubes relevant for extention
        cEdge = self.__poly.getConnectedAt(lastCube, lastEdge)
        cOri = self.__poly.getConnectedAt(lastCube, lastOri)
        if cOri != None:
            cDiag = self.__poly.getConnectedAt(cOri, lastEdge)
        elif cEdge != None:
            cDiag = self.__poly.getConnectedAt(cEdge, lastOri)
        else:
            cDiag = None
        # find valid path extentions in up to 3 directions
        ext = []
        if lastEdge.inv() in self.__oriAvailable:
            ext.append((lastCube, lastOri, lastEdge.inv()))
        if lastEdge in self.__oriAvailable:
            if cEdge != None:
                ext.append((cEdge, lastOri, lastEdge))
            elif cDiag != None:
                ext.append((cDiag, lastOri.inv(), lastEdge))
        if lastOri in self.__oriAvailable:
            if cOri != None:
                ext.append((cOri, lastEdge, lastOri))
            elif cDiag != None:
                ext.append((cDiag, lastEdge.inv(), lastOri))
        # create new paths with the valid extentions
        extPaths = []
        for n in ext:
            new = copy.deepcopy(self)
            new.extend(n[0], n[1], n[2])
            extPaths.append(new)
        return extPaths
    
    def extend(self, cube: Cube, edge: Direction, edgeOri: Direction):
        self.__path.append((cube, edge, edgeOri))
        self.__oriAvailable.difference_update([edgeOri.inv()])


def twoCutSubassemblies(poly: Polyomino) -> dict:
    twoCuts = {}
    for cube in poly.getCubes():
        for edge in Direction.list():
            if poly.getConnectedAt(cube, edge) == None:
                continue
            ori = Direction((edge.value + 1) % 4)
            for cut, cons in __monotonCutsFrom(poly, cube, edge, ori).items():
                if not cut in twoCuts:
                    twoCuts[cut] = cons
                else:
                    twoCuts[cut].update(cons)
    return twoCuts

def __monotonCutsFrom(poly: Polyomino, startCube: Cube, startEdge: Direction, startOri: Direction) -> dict:
    twoCuts = {}
    next = Queue()
    next.put(MonotoneCuttingPath(poly, startCube, startEdge, startOri))
    while not next.empty():
        path: MonotoneCuttingPath = next.get()
        extPaths = path.extendedPaths()
        if len(extPaths) == 0:
            cut = path.cutPoly()
            if cut.polyCount() == 2:
                if not cut in twoCuts:
                    twoCuts[cut] = set([path.pickConnection()])
                else:
                    twoCuts[cut].add(path.pickConnection())
        else:
            for ep in extPaths:
                next.put(ep)
    return twoCuts


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
        self.__node_edges = {}
        poly_twoCuts = {}
        polyColl = PolyCollection([target])
        self.__node_edges[polyColl] = []
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
                        if newPolyColl in self.__node_edges:
                            # if note is in tree append the edge
                            self.__node_edges[newPolyColl].append(edge)
                        else:
                            # if not put it in and add to next queue
                            self.__node_edges[newPolyColl] = [edge]
                            next.put(newPolyColl)

    def getAllCollections(self) -> set:
        return set(self.__node_edges.keys())

    def getNextCollections(self, polys: PolyCollection):
        if not polys in self.__node_edges:
            return None
        next = []
        for edge in self.__node_edges[polys]:
            next.append(edge.end)
        return next
    
    def getTranslatedConnections(self, polys: PolyCollection, next: PolyCollection):
        translated = []
        for edge in self.__node_edges[polys]:
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

    def nodeCount(self):
        return len(self.__node_edges)

    def edgeCount(self):
        count = 0
        for edges in self.__node_edges.values():
            count += len(edges)
        return count

    def __contains__(self, key) -> bool:
        return key in self.__node_edges

    def __str__(self) -> str:
        string = ""
        for note, edges in self.__node_edges.items():
            string += str(note) + "\n"
            for edge in edges:
                string += "   " + str(edge) + "\n"
            string += "\n"
        return string


DEBUG = False
PLAY_LOCALS = False
TIMEOUT = 600

def planTargetAssembly(initial: Configuration, target: Polyomino, sorting: OptionSorting=OptionSorting.MIN_DIST) -> GlobalPlan:
    # single update if no poly info available
    if initial.getPolyominoes().isEmpty():
        initial = singleUpdate(initial)
    # check if target is already in initial
    tcsaGraph = TwoCutSubassemblyGraph(target)
    if target in initial.getPolyominoes():
        return GlobalPlan(target, initial, goal=initial, state=PlanState.SUCCESS, ntcsa=tcsaGraph.nodeCount())
    # check if initial is in tsca tree
    if not initial.getPolyominoes() in tcsaGraph:
        return GlobalPlan(target, initial, state=PlanState.FAILURE, ntcsa=tcsaGraph.nodeCount())
    # init varialbes
    globalFails = set((PlanState.FAILURE_ALLOWED_POLYS, PlanState.FAILURE_MAX_ITR, PlanState.FAILURE_STUCK,
                        PlanState.FAILURE_CAVE, PlanState.FAILURE_INVAL_POLY, PlanState.FAILURE_SAME_TYPE))
    planStack = []
    config_options = {}
    config = initial
    nlocalPlans = 0
    t0 = time.monotonic()
    while True:
        if DEBUG: 
            print(f"----------------{repr(config)}----------------\n")
            print(f"{len(planStack)} local plans in stack.\n{config.getPolyominoes()}")
        # failure when planning takes to long
        if (time.monotonic() - t0) >= TIMEOUT:
            if DEBUG: print(f"Timeout -> Failure!\n{len(config_options)} configs, {nlocalPlans} local plans in total.\n")
            return GlobalPlan(target, initial, state=PlanState.FAILURE, nconfig=len(config_options),
                              nlocal=nlocalPlans, ntcsa=tcsaGraph.nodeCount())
        # Plan finished when we assembled the target
        if target in config.getPolyominoes():
            if DEBUG: print(f"Target successfully assembled with {len(planStack)} local plans!\n{len(config_options)} configs, {nlocalPlans} local plans in total.\n")
            return GlobalPlan(target, initial, planStack, config, PlanState.SUCCESS, len(config_options),
                              nlocalPlans, tcsaGraph.nodeCount())
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
                                  nlocal=nlocalPlans, ntcsa=tcsaGraph.nodeCount())
            lastPlan = planStack.pop()
            config = lastPlan.initial
            if DEBUG: print(f"No connections left. Fall back to {repr(config)}.\n")


def __determineOptions(config: Configuration, tcsaGraph: TwoCutSubassemblyGraph, sorting: OptionSorting) -> list:
    connections = []
    polys = config.getPolyominoes()
    adjNotes = tcsaGraph.getNextCollections(polys)
    # return no options if polys not in graph or if it has no options
    if adjNotes == None or len(adjNotes) == 0:
        return connections
    # Sort for minimal distance with no respect to the notes
    if sorting == OptionSorting.MIN_DIST:
        for adj in adjNotes:
            conAdj = tcsaGraph.getTranslatedConnections(polys, adj)
            connections.extend(conAdj)
        connections.sort(key=lambda con: config.getPosition(con.cubeA).get_distance(config.getPosition(con.cubeB)))
        return connections
    # Add connections to classes of the maxSize
    maxSize_connects = {}
    for adj in adjNotes:
        conAdj = tcsaGraph.getTranslatedConnections(polys, adj)
        if adj.maxSize in maxSize_connects:
            maxSize_connects[adj.maxSize].extend(conAdj)
        else:
            maxSize_connects[adj.maxSize] = conAdj
    # Sort the classes either ascending or descending
    sizes = list(maxSize_connects.keys())
    if sorting == OptionSorting.GROW_LARGEST:
        sizes.sort(reverse=True)
    elif sorting == OptionSorting.GROW_SMALLEST:
        sizes.sort(reverse=False)
    # extend connects of the classes sorted by minimal distance
    for maxSize in sizes:
        connects: list = maxSize_connects[maxSize]
        connects.sort(key=lambda con: config.getPosition(con.cubeA).get_distance(config.getPosition(con.cubeB)))
        connections.extend(connects)
    return connections