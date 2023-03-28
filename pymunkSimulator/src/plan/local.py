from multiprocessing.pool import Pool
import time
from sim.handling import Renderer

from sim.motion import Idle, Rotation, PivotWalk
from sim.simulation import Simulation
from sim.state import *
from plan.plan import *


DEBUG = False

MAX_ITR = 32

CRITICAL_DISTANCE = Cube.MAG_DISTANCE_MIN
SLOWWALK_DISTANCE = CRITICAL_DISTANCE * 1.5
IDLE_TRIES = 1
IDLE_AMOUNT = 20

STUCK_TIMES_MAX = IDLE_TRIES + 1
STUCK_OFFSET = Cube.RAD / 6
IDLE_STUCK_AMOUNT = 60

NS_ALIGN_OFFSET = 2.75 * Cube.RAD
ALIGNED_THRESHOLD = math.radians(4)

PWALK_ANG_BIG = PivotWalk.DEFAULT_PIVOT_ANG
PWALK_ANG_SMALL = PWALK_ANG_BIG / 1.5
PWALK_PORTION = 1/2



def planCubeConnect(initial: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> Plan:
    # single update if no poly info available
    if initial.getPolyominoes().isEmpty():
        initial = singleUpdate(initial)
    # when already connected return successfull plan
    info = (cubeA,cubeB,edgeB)
    if __isConnected(initial, cubeA, cubeB, edgeB):
        return Plan(initial=initial, goal=initial, state=PlanState.SUCCESS, info=info)
    # cant connect cubes sideways if they are same type
    if edgeB in (Direction.EAST, Direction.WEST) and cubeA.type == cubeB.type:
        return Plan(initial=initial, state=PlanState.FAILURE_SAME_TYPE, info=info)
    # pre check if connecting the polys is even possible and valid
    if not __connectPossible(initial, cubeA, cubeB, edgeB):
        return Plan(initial=initial, state=PlanState.FAILURE_CONNECT, info=info)
    # pre check if polys can slide together from either east or west
    slideDirections = __slideInDirections(initial, cubeA, cubeB, edgeB)
    if len(slideDirections) == 0:
        return Plan(initial=initial, state=PlanState.FAILURE_SLIDE_IN, info=info)
    # determine which plans to execute. left and right either with or without initial flip
    plansToExec = []
    faceing = __faceingDirection(initial, cubeA, cubeB)
    facingInv = faceing.inv()
    if faceing in slideDirections:
        plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.LEFT, faceing))
        plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT, faceing))
    if facingInv  in slideDirections:
        plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.LEFT, facingInv))
        plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT, facingInv))
    if DEBUG:
        return __planSequential(plansToExec)
    else:
        return __planParallel(plansToExec)
    
def __planParallel(data) -> Plan:
    print(f"Starting {len(data)} processes for simulation...")
    with Pool(len(data)) as pool:
        it = pool.imap_unordered(__alignWalkRealign, data)
        for i in range(len(data)):
            plan = next(it)
            print(f"{i+1} finished: {plan}")
            if plan.state == PlanState.SUCCESS:
                pool.terminate()
                return plan
        pool.terminate()
        return plan

def __planSequential(data) -> Plan:
    optPlan = None
    for i, item in enumerate(data):
        plan = __alignWalkRealign(item)
        print(f"{i+1} finished: {plan}")
        if optPlan == None:
            optPlan = plan
        else:
            optPlan = optPlan.compare(plan)
    return optPlan
        
def __alignWalkRealign(data: tuple) -> Plan:
    config = data[0]
    cubeA = data[1]
    cubeB  = data[2]
    edgeB = data[3]
    direction = data[4]
    slide = data[5]
    plan = Plan(initial=config, info=(cubeA,cubeB,edgeB))
    sim = Simulation(DEBUG, False)
    sim.loadConfig(config)
    sim.renderer.markedCubes.add(cubeA)
    sim.renderer.markedCubes.add(cubeB)
    itr = 0
    idleTry = 0
    stuckTimes = 0
    # not a mistake this insures that initial stuck check is false
    posA = config.getPosition(cubeB)
    posB = config.getPosition(cubeA)
    while True:
        # check if the polys got stuck.
        #sim.renderer.pointsToDraw.clear()
        if __arePolysStuck(config.getPosition(cubeA), posA, config.getPosition(cubeB), posB):
            stuckTimes += 1
        else:
            stuckTimes = 0
        if DEBUG: print(f"Itr: {itr}, {stuckTimes} times stuck.")
        posA = config.getPosition(cubeA)
        posB = config.getPosition(cubeB)
        #sim.renderer.pointsToDraw.append((Renderer.BLUE, posA, 3))
        #sim.renderer.pointsToDraw.append((Renderer.RED, posB, 3))
        # aligne the cubes. If they are stuck force straight align
        rotation = __alignCubes(config, cubeA, cubeB, edgeB, slide, stuckTimes >= STUCK_TIMES_MAX)
        executeMotions(sim, [rotation])
        plan.actions.append(Idle(1))
        plan.actions.append(rotation)
        plan.actions.append(Idle(1))
        config = sim.saveConfig()
        if DEBUG: print(rotation)
        # update the planstate. Check failure and success conditions
        plan.state = __updatePlanState(config, cubeA, cubeB, edgeB, slide)
        if plan.state != PlanState.UNDEFINED:
            break
        # determine next actions based on distance anf stucktimes
        distance = config.getPosition(cubeA).get_distance(config.getPosition(cubeB))
        if stuckTimes >= STUCK_TIMES_MAX:
            # if stuck wait as long as their positions change
            while True:
                idle = Idle(IDLE_STUCK_AMOUNT)
                executeMotions(sim, [idle])
                if DEBUG: print(f"{idle} because stuck.")
                plan.actions.append(Idle(1))
                plan.actions.append(idle)
                plan.actions.append(Idle(1))
                config = sim.saveConfig()
                newDist = config.getPosition(cubeA).get_distance(config.getPosition(cubeB))
                if distance - newDist < STUCK_OFFSET / 2:
                    break
                distance = newDist
        else:
            if distance < CRITICAL_DISTANCE and idleTry < IDLE_TRIES:
                # if in critical distance wait short time
                motions = [Idle(IDLE_AMOUNT)]
                idleTry += 1
            else:
                # if not walk into direction
                motions = __walkDynamic(config, cubeA, cubeB, direction)
                idleTry = 0 
            executeMotions(sim, motions)
            if DEBUG: print(f"{len(motions)} x {motions[0]}")
            plan.actions.append(Idle(1))
            plan.actions.extend(motions)
            plan.actions.append(Idle(1))
            config = sim.saveConfig()
        # update the planstate. Check failure and success conditions
        plan.state = __updatePlanState(config, cubeA, cubeB, edgeB, slide)
        if plan.state != PlanState.UNDEFINED:
            break
        # if the polys got stuck and the straight align didnt fix report failure
        if stuckTimes >= STUCK_TIMES_MAX:
            plan.state = PlanState.FAILURE_STUCK
            break
        # if we cant conect after a lot of iterations report failure
        if itr >= MAX_ITR:
            plan.state = PlanState.FAILURE_MAX_ITR
            break
        itr += 1
    sim.terminate()
    plan.goal = config
    #print(f"itrations: {itr}")
    #sim.stateHandler.timer.printTimeStats()
    return plan

def __alignCubes(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, slide:Direction, forceStraight: bool=False):
    posA = config.getPosition(cubeA)
    posB = config.getPosition(cubeB)
    comA = config.getCOM(config.getPolyominoes().getForCube(cubeA))
    comB = config.getCOM(config.getPolyominoes().getForCube(cubeB))
    if (edgeB in (Direction.WEST, Direction.EAST)) or forceStraight:
        # For side connection, or if cubes are near enought, do straight align
        alignEdge = edgeB
        if DEBUG: print("Straight align")
    else:
        # For Top bottom connection do n-s align
        alignEdge = slide.inv()
        posB += NS_ALIGN_OFFSET  * edgeB.vec(config.magAngle)
        if DEBUG: print("N-S align")
    return __calcAlignRotation(comA, posA, comB, posB, alignEdge, config.magAngle)

def __calcAlignRotation(comA: Vec2d, posA: Vec2d, comB: Vec2d, posB: Vec2d, edgeB: Direction, magAngle):
    step = math.radians(2)
    minAngDiff = 2 * math.pi
    minRotAng = 2 * math.pi
    ang = magAngle
    while ang < (magAngle + 2 * math.pi):
        rotAng = ang - magAngle
        if abs(rotAng) > math.pi:
            rotAng = -1 * (2 * math.pi - rotAng)
        rA = (posA - comA).rotated(rotAng)
        rB = (posB - comB).rotated(rotAng)
        vecBA = (comA + rA) - (comB + rB)
        vecEdgeB = edgeB.vec(ang)
        angDiff = abs(vecEdgeB.get_angle_between(vecBA))
        if angDiff < ALIGNED_THRESHOLD:
            return Rotation(rotAng)
        if angDiff < minAngDiff:
            minAngDiff = angDiff
            minRotAng = rotAng
        ang += step
        #print(f"angleBetween: {round(math.degrees(angDiff),2)}, rotation: {round(math.degrees(rotAng),2)}")
    return Rotation(minRotAng)

def __walkDynamic(config: Configuration, cubeA: Cube, cubeB: Cube, direction) -> list:
    posA = config.getPosition(cubeA)
    posB = config.getPosition(cubeB)
    vecBA = posA - posB
    distance = vecBA.length
    # take eith big or small pivot angle depending on distance
    if distance < SLOWWALK_DISTANCE:
        pivotAng = PWALK_ANG_SMALL
    else:
        pivotAng = PWALK_ANG_BIG
    # determin which poly is chasing which
    if bool(__faceingDirection(config, cubeA, cubeB) == Direction.EAST) ^ bool(direction == PivotWalk.LEFT):
        chasingPoly = config.getPolyominoes().getForCube(cubeA)
    else:
        chasingPoly = config.getPolyominoes().getForCube(cubeB)
    # estimate the pivot steps neccessary for the chasing poly to reach the other. Only take half.
    pivotSteps = math.ceil((distance / config.getPivotWalkingDistance(chasingPoly, pivotAng)) * PWALK_PORTION)
    return [PivotWalk(direction, pivotAng)] * pivotSteps

def __updatePlanState(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, slide:Direction) -> PlanState:
    # check if config contains inValid polys
    if config.getPolyominoes().containsInvalid():
        return PlanState.FAILURE_INVAL_POLY
    # check if cubes are connected at edgeB
    if __isConnected(config, cubeA, cubeB, edgeB):
        return PlanState.SUCCESS
    # check if you can connect the polys of A and B
    if not __connectPossible(config, cubeA, cubeB, edgeB):
        return PlanState.FAILURE_CONNECT
    # check if we cant slide in anymore
    if not slide in __slideInDirections(config, cubeA, cubeB, edgeB):
        return PlanState.FAILURE_SLIDE_IN
    return PlanState.UNDEFINED

def __isConnected(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
    polyB = config.getPolyominoes().getForCube(cubeB)
    return polyB.getConnection(cubeB, edgeB) == cubeA

def __connectPossible(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
    polyA = config.getPolyominoes().getForCube(cubeA)
    polyB = config.getPolyominoes().getForCube(cubeB)
    # poly resulting from connection would overlap, or cubes are inside the same polyomino
    targetPoly = polyA.connectPoly(cubeA, polyB, cubeB, edgeB)
    if targetPoly == None or not targetPoly.isValid():
        return False
    return True

def __arePolysStuck(newPosA: Vec2d, oldPosA: Vec2d, newPosB: Vec2d, oldPosB: Vec2d) -> bool:
    distChangeA = newPosA.get_distance(oldPosA)
    distChangeB = newPosB.get_distance(oldPosB)
    return distChangeA < STUCK_OFFSET and distChangeB < STUCK_OFFSET

def __slideInDirections(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> set:
    # check if poly can be connected by walking in form the east and west
    slide = set()
    polyA = config.getPolyominoes().getForCube(cubeA)
    polyB = config.getPolyominoes().getForCube(cubeB)
    if polyA.connectPolyPossible(cubeA, polyB, cubeB, edgeB, Direction.EAST):
        slide.add(Direction.EAST)
    if polyA.connectPolyPossible(cubeA, polyB, cubeB, edgeB, Direction.WEST):
        slide.add(Direction.WEST)
    return slide

def __faceingDirection(config: Configuration, cubeA: Cube, cubeB: Cube) -> Direction:
    """
    returns 'direction',that cubeB is in 'direction' of cubeA.
    Direction is either EAST or WEST
    """
    vecAB = config.getPosition(cubeB) - config.getPosition(cubeA)
    if vecAB.dot(Direction.EAST.vec(config.magAngle)) > 0:
        return Direction.EAST
    else:
        return Direction.WEST