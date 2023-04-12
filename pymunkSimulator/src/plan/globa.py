
from sim.state import *
from plan.plan import *
import plan.local as local

DEBUG = True

def planTargetAssembly(initial: Configuration, target: Polyomino) -> Plan:
    # single update if no poly info available
    if initial.getPolyominoes().isEmpty():
        initial = singleUpdate(initial)
    # check if target is already in initial
    if target in initial.getPolyominoes():
        return Plan(initial=initial, goal=initial, state=PlanState.SUCCESS)
    globalFail = (PlanState.FAILURE_SAME_TYPE, PlanState.FAILURE_HOLE, PlanState.FAILURE_INVAL_POLY, PlanState.FAILURE_MAX_ITR, PlanState.FAILURE_STUCK)
    tcsaGraph = TwoCutSubassemblyGraph(target)
    planStack = []
    config_options = {}
    config = initial
    while True:
        if DEBUG: print(f"------{config}------")
        # Plan finished when we assembled the target
        if target in config.getPolyominoes():
            if DEBUG: print("Target successfully assembled!")
            return __localPlansToGlobal(planStack)
        # get possible conection options for this config
        if config in config_options:
            options = config_options[config]
        else:
            options = __determineConnectOptions(config, tcsaGraph)
            config_options[config] = options
        if len(options) == 0:
            # if no options are left fall back to last initial-config in planStack
            if DEBUG: print("No connections left. Fall back to last config.")
            if len(planStack) == 0:
                # failure if nothing is left to fall back to
                if DEBUG: print("Nothing to fall back to. Failure!")
                return Plan(initial=initial, state=PlanState.FAILURE)
            plan = planStack.pop()
            config = plan.initial
        else:
            # else try out options
            while len(options) > 0:
                if DEBUG: print(f"{len(options)} connections possible. Starting local planner.")
                con = options.pop(0)
                plan = local.planCubeConnect(config, con[0], con[1], con[2])
                if DEBUG: plan.execute()
                # if plan is valid for global planning and polyCollection is in tcsaGraph, we move to the goal config
                if not plan.state in globalFail and plan.goal != None and plan.goal.getPolyominoes() in tcsaGraph:
                    config = plan.goal
                    planStack.append(plan)
                    if DEBUG:print(f"Valid local plan. Continue with goal!\n")
                    break
                if DEBUG:print(f"Invalid local plan. Try next connection.\n")
        
def __determineConnectOptions(config: Configuration, tcsaGraph: TwoCutSubassemblyGraph) -> list:
    conections = []
    polys = config.getPolyominoes()
    adjNotes = tcsaGraph.getAdjacentNotes(polys)
    if adjNotes == None:
        return conections
    for adj in adjNotes:
        conections.extend(tcsaGraph.getTranslatedConnections(polys, adj))
    return conections

def __localPlansToGlobal(planStack: list) -> Plan:
    plan: Plan = planStack[0]
    for i in range(1, len(planStack)):
        plan = plan.concat(planStack[i])
    plan.connection = None
    plan.state = PlanState.SUCCESS
    return plan