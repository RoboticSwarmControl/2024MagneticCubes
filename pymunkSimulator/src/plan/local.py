from multiprocessing.pool import Pool
import time

from sim.motion import Idle, Rotation, PivotWalk
from sim.simulation import Simulation
from sim.state import *
from plan.plan import *


DEBUG = False

MAX_ITR = 24

CRITICAL_DISTANCE = 4 * Cube.RAD
SLOWWALK_DISTANCE = CRITICAL_DISTANCE * 2
IDLE_TRIES = 1
IDLE_AMOUNT = 10

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
    while True:
        if DEBUG: print(f"Itr: {itr}")
        # aligne the cubes
        rotation = __alignCubes(config, cubeA, cubeB, edgeB, slide)
        executeMotions(sim, [rotation])
        plan.actions.append(Idle(1))
        plan.actions.append(rotation)
        plan.actions.append(Idle(1))
        config = sim.saveConfig()
        if DEBUG: print(rotation)
        # update the planstate. Check failure and success conditions
        plan.state = __updatePlanState(config, cubeA, cubeB, edgeB, slide, itr)
        if plan.state != PlanState.UNDEFINED:
            break
        # check if cubes are in critical distance for magnets to attract
        distance = config.getPosition(cubeA).get_distance(config.getPosition(cubeB))
        if distance < CRITICAL_DISTANCE and idleTry < IDLE_TRIES:
            # if so let magnets do the rest
            wait = Idle(IDLE_AMOUNT)
            executeMotions(sim, [wait])
            plan.actions.append(wait)
            idleTry += 1
            if DEBUG: print(wait)
        else:
            # if not walk into direction
            pWalks = __walkDynamic(config, cubeA, cubeB, direction)
            executeMotions(sim, pWalks)
            plan.actions.append(Idle(1))
            plan.actions.extend(pWalks)
            plan.actions.append(Idle(1))
            idleTry = 0
            if DEBUG: print(f"{len(pWalks)} x {pWalks[0]}")
        config = sim.saveConfig()
        # update the planstate. Check failure and success conditions
        plan.state = __updatePlanState(config, cubeA, cubeB, edgeB, slide, itr)
        if plan.state != PlanState.UNDEFINED:
            break
        itr += 1
    sim.terminate()
    plan.goal = config
    #print(f"itrations: {itr}")
    #sim.stateHandler.timer.printTimeStats()
    return plan

def __alignCubes(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, slide:Direction):
    posA = config.getPosition(cubeA)
    posB = config.getPosition(cubeB)
    comA = config.getCOM(config.getPolyominoes().getPoly(cubeA))
    comB = config.getCOM(config.getPolyominoes().getPoly(cubeB))
    if edgeB in (Direction.WEST, Direction.EAST):
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
        chasingPoly = config.getPolyominoes().getPoly(cubeA)
    else:
        chasingPoly = config.getPolyominoes().getPoly(cubeB)
    # estimate the pivot steps neccessary for the chasing poly to reach the other. Only take half.
    pivotSteps = math.ceil((distance / config.getPivotWalkingDistance(chasingPoly, pivotAng)) * PWALK_PORTION)
    return [PivotWalk(direction, pivotAng)] * pivotSteps

def __updatePlanState(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, slide:Direction, itr) -> PlanState:
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
    # if we cant conect after a lot of iterations report failure
    if itr >= MAX_ITR:
        return PlanState.FAILURE_MAX_ITR
    return PlanState.UNDEFINED

def __isConnected(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
    polyB = config.getPolyominoes().getPoly(cubeB)
    return polyB.getConnection(cubeB, edgeB) == cubeA

def __connectPossible(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
    polyA = config.getPolyominoes().getPoly(cubeA)
    polyB = config.getPolyominoes().getPoly(cubeB)
    # poly resulting from connection would overlap, or cubes are inside the same polyomino
    targetPoly = polyA.connectPoly(cubeA, polyB, cubeB, edgeB)
    if targetPoly == None or not targetPoly.isValid():
        return False
    return True

def __slideInDirections(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> set:
    # check if poly can be connected by walking in form the east and west
    slide = set()
    polyA = config.getPolyominoes().getPoly(cubeA)
    polyB = config.getPolyominoes().getPoly(cubeB)
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