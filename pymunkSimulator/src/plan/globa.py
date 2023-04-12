
from sim.state import *
from plan.plan import *
import plan.local as local

def planTargetAssembly(initial: Configuration, target: Polyomino):
    # single update if no poly info available
    if initial.getPolyominoes().isEmpty():
        initial = singleUpdate(initial)
    globalFail = (PlanState.FAILURE_SAME_TYPE, PlanState.FAILURE_HOLE, PlanState.FAILURE_INVAL_POLY, PlanState.FAILURE_MAX_ITR, PlanState.FAILURE_STUCK)
    tcsaGraph = TwoCutSubassemblyGraph(target)
    planStack = []
    config_options = {}
    config = initial
    while True:
        # get possible conection options for this config
        if config in config_options:
            options = config_options[config]
        else:
            options = __determineConnectOptions(config, tcsaGraph)
            config_options[config] = options
        # if no options are left fall back to last initial-config in planStack
        if len(options) == 0:
            # failure if nothing is left to fall back to
            if len(planStack) == 0:
                #TODO
                break
            plan = planStack.pop()
            config = plan.initial
            continue
        # try first option with local planner
        con = options.pop(0)
        plan = local.planCubeConnect(config, con[0], con[1], con[2])
        # if plan is valid for global planning and polyCollection is in tcsaGraph, plan is appended to planStack
        if not plan.state in globalFail and plan.goal != None and plan.goal.getPolyominoes() in tcsaGraph:
            config = plan.goal
            planStack.append(plan)
        # Plan finished if we assembled the target
        if target in plan.goal.getPolyominoes():
            #TODO
            break
    #TODO add up plans in planStack if success or report failure
    return
        

def __determineConnectOptions(config: Configuration, tcsaGraph: TwoCutSubassemblyGraph) -> list:
    conections = []
    polys = config.getPolyominoes()
    adjNotes = tcsaGraph.getAdjacentNotes(polys)
    if adjNotes == None:
        return conections
    for adj in adjNotes:
        conections.extend(tcsaGraph.getTranslatedConnections(polys, adj))
    return conections
