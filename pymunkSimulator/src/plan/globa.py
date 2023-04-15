
from sim.state import *
from plan.plan import *
import plan.local as local

DEBUG = True
PLAY_LOCALS = False

def planTargetAssembly(initial: Configuration, target: Polyomino) -> GlobalPlan:
    # single update if no poly info available
    if initial.getPolyominoes().isEmpty():
        initial = singleUpdate(initial)
    # check if target is already in initial
    if target in initial.getPolyominoes():
        return GlobalPlan(initial=initial, goal=initial, state=PlanState.SUCCESS, target=target)
    tcsaGraph = TwoCutSubassemblyGraph(target)
    # check if initial is in tsca tree
    if not initial.getPolyominoes() in tcsaGraph:
        return GlobalPlan(initial=initial, state=PlanState.FAILURE, target=target)
    # init varialbes
    globalFails = set((PlanState.FAILURE_ALLOWED_POLYS, PlanState.FAILURE_MAX_ITR, PlanState.FAILURE_STUCK,
                      PlanState.FAILURE_CAVE, PlanState.FAILURE_INVAL_POLY, PlanState.FAILURE_SAME_TYPE))
    planStack = []
    config_options = {}
    config = initial
    nlocalPlans = 0
    while True:
        if DEBUG: 
            print(f"----------------{repr(config)}----------------\n")
            print(f"{len(planStack)} local plans in stack.\n{config.getPolyominoes()}")
        # Plan finished when we assembled the target
        if target in config.getPolyominoes():
            if DEBUG: print(f"Target successfully assembled with {len(planStack)} local plans!\n{len(config_options)} configs, {nlocalPlans} local plans in total.\n")
            return GlobalPlan(planStack[0].initial, planStack[len(planStack)-1].goal, planStack, PlanState.SUCCESS, target)
        # get possible conection options for this config
        if config in config_options:
            options = config_options[config]
        else:
            options = __determineConnectOptions(config, tcsaGraph)
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
                return GlobalPlan(initial=initial, state=PlanState.FAILURE, target=target)
            lastPlan = planStack.pop()
            config = lastPlan.initial
            if DEBUG: print(f"No connections left. Fall back to {repr(config)}.\n")
        
def __determineConnectOptions(config: Configuration, tcsaGraph: TwoCutSubassemblyGraph) -> list:
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