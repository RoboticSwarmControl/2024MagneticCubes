from multiprocessing.pool import Pool
from sim.rendering import Renderer
import math
from pymunk.vec2d import Vec2d

from com.motion import Idle, Rotation, PivotWalk
from sim.simulation import Simulation
from com.state import Configuration, Cube, Direction
from plan.plan import *


DEBUG = False

CRITICAL_DISTANCE = Cube.MAG_DISTANCE_MIN
SLOWWALK_DISTANCE = CRITICAL_DISTANCE * 1.5

IDLE_AMOUNT = 10
IDLE_STUCK_AMOUNT = 60

STUCK_TIMES_MAX = 3
STUCK_OFFSET = Cube.RAD / 6

NS_ALIGN_OFFSET = 3 * Cube.RAD
ALIGNED_THRESHOLD = math.radians(4)

PWALK_ANG_BIG = PivotWalk.DEFAULT_PIVOT_ANG
PWALK_ANG_SMALL = PWALK_ANG_BIG / 1.5
PWALK_PORTION = 1/2


def planCubeConnect(initial: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, allowedPolyColls: set=None) -> LocalPlan:
    # single update if no poly info available
    if initial.getPolyominoes().isEmpty():
        initial = singleUpdate(initial)
    connection = (cubeA,cubeB,edgeB)
    # cant connect cubes sideways if they are same type
    if edgeB in (Direction.EAST, Direction.WEST) and cubeA.type == cubeB.type:
        return LocalPlan(initial=initial, state=PlanState.FAILURE_SAME_TYPE, connection=connection)
    # check if the current poly set is allowed
    if not __polysAllowed(initial, allowedPolyColls):
        return LocalPlan(initial=initial, state=PlanState.FAILURE_ALLOWED_POLYS, connection=connection)
    # check if config contains invalid polys
    if __polysInvalid(initial, cubeA, cubeB, edgeB):
        return LocalPlan(initial=initial, state=PlanState.FAILURE_INVAL_POLY, connection=connection)
    # when already connected return successfull plan
    if __isConnected(initial, cubeA, cubeB, edgeB):
        return LocalPlan(initial=initial, goal=initial, state=PlanState.SUCCESS, connection=connection)
    # pre check if connecting the polys is even possible and valid
    if not __connectPossible(initial, cubeA, cubeB, edgeB):
        return LocalPlan(initial=initial, state=PlanState.FAILURE_CONNECT, connection=connection)
    # pre-check if connection edges are inside a hole
    if __edgeInCave(initial, cubeA, edgeB.inv()) or __edgeInCave(initial, cubeB, edgeB):
        return LocalPlan(initial=initial, state=PlanState.FAILURE_CAVE, connection=connection)
    # pre check if polys can slide together from either east or west
    slideDirections = __slideInDirections(initial, cubeA, cubeB, edgeB)
    if len(slideDirections) == 0:
        return LocalPlan(initial=initial, state=PlanState.FAILURE_SLIDE_IN, connection=connection)
    # determine which plans to execute. left and right either with or without initial flip
    plansToExec = []
    faceing = __faceingDirection(initial, cubeA, cubeB)
    facingInv = faceing.inv()
    if faceing in slideDirections:
        plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.LEFT, faceing, allowedPolyColls))
        plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT, faceing, allowedPolyColls))
    if facingInv  in slideDirections:
        plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.LEFT, facingInv, allowedPolyColls))
        plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT, facingInv, allowedPolyColls))
    if DEBUG:
        return __planSequential(plansToExec)
    else:
        return __planParallel(plansToExec)
    
def __planParallel(data) -> LocalPlan:
    if DEBUG: print(f"Starting {len(data)} processes for simulation...")
    optPlan = None
    with Pool(len(data)) as pool:
        it = pool.imap_unordered(__alignWalkRealign, data)
        for i in range(len(data)):
            plan = next(it)
            if DEBUG: print(f"{i+1} finished: {plan}")
            if plan.state == PlanState.SUCCESS:
                pool.terminate()
                return plan
            if optPlan == None:
                optPlan = plan
            else:
                optPlan = optPlan.compare(plan)
        pool.terminate()
        return optPlan

def __planSequential(data) -> LocalPlan:
    optPlan = None
    for i, item in enumerate(data):
        plan = __alignWalkRealign(item)
        if DEBUG: print(f"{i+1} finished: {plan}")
        if optPlan == None:
            optPlan = plan
        else:
            optPlan = optPlan.compare(plan)
    return optPlan
        
def __alignWalkRealign(data: tuple) -> LocalPlan:
    # unpack data
    config: Configuration = data[0]
    cubeA: Cube = data[1]
    cubeB: Cube  = data[2]
    edgeB: Direction = data[3]
    direction = data[4]
    slide: Direction = data[5]
    allowed: set = data[6]
    # init plan and simulation
    plan = LocalPlan(initial=config, connection=(cubeA,cubeB,edgeB))
    sim = Simulation(DEBUG, False)
    sim.loadConfig(config)
    sim.renderer.markedCubes.add(cubeA)
    sim.renderer.markedCubes.add(cubeB)
    # init varables
    MAX_MOVING_DIST = 2 * (config.boardSize[0] + config.boardSize[1])
    if DEBUG: print(f"Max walking distance: {MAX_MOVING_DIST}")
    distMoved = 0
    stuckTimes = 0
    itr = 0
    wait = True
    while True:
        # aligne the cubes.
        rotation = __alignCubes(config, cubeA, cubeB, edgeB, slide)
        executeMotions(sim, [rotation])
        if DEBUG: print(rotation)
        plan.actions.append(rotation)
        config = sim.saveConfig()
        # update the planstate. Check failure and success conditions
        plan.state = __updatePlanState(config, cubeA, cubeB, edgeB, slide, allowed)
        if plan.state != PlanState.UNDEFINED:
            break
        # determine next actions based on distance
        distAB = config.getPosition(cubeA).get_distance(config.getPosition(cubeB))
        if distAB < CRITICAL_DISTANCE and wait:
            # if in critical distance wait short time
            idle = Idle(IDLE_AMOUNT)
            executeMotions(sim, [idle])
            if DEBUG: print(idle)
            plan.actions.append(idle)
            config = sim.saveConfig()
            wait = False
        else:
            # if not walk into direction
            pA0 = config.getPosition(cubeA)
            pB0 = config.getPosition(cubeB)
            pWalks = __walkDynamic(config, cubeA, cubeB, direction)
            executeMotions(sim, pWalks)
            if DEBUG: print(f"{len(pWalks)} x {pWalks[0]}")
            plan.actions.extend(pWalks)
            config = sim.saveConfig()
            # determine how distance changes after pivot walking
            distChangeA = config.getPosition(cubeA).get_distance(pA0)
            distChangeB = config.getPosition(cubeB).get_distance(pB0)
            distMoved += distChangeA + distChangeB
            sim.renderer.linesToDraw.append((Renderer.RED, pA0, config.getPosition(cubeA), 3))
            sim.renderer.linesToDraw.append((Renderer.BLUE, pB0, config.getPosition(cubeB), 3))
            # if both A and B did not move increase stuck
            if distChangeA < STUCK_OFFSET and distChangeB < STUCK_OFFSET:
                stuckTimes += 1
            else:
                stuckTimes = 0
            wait = True
        # if stuck condition is reached
        if stuckTimes >= STUCK_TIMES_MAX:
            # force a straight align
            rotation = __alignCubes(config, cubeA, cubeB, edgeB, slide, True)
            executeMotions(sim, [rotation])
            if DEBUG: print(rotation)
            plan.actions.append(rotation)
            config = sim.saveConfig()
            # wait as long as their positions change
            distAB = config.getPosition(cubeA).get_distance(config.getPosition(cubeB))
            while True:
                idle = Idle(IDLE_STUCK_AMOUNT)
                executeMotions(sim, [idle])
                if DEBUG: print(f"{idle} because stuck.")
                plan.actions.append(idle)
                config = sim.saveConfig()
                newDistAB = config.getPosition(cubeA).get_distance(config.getPosition(cubeB))
                if distAB - newDistAB < STUCK_OFFSET / 2:
                    break
                distAB = newDistAB
        # update the planstate. Check failure and success conditions
        plan.state = __updatePlanState(config, cubeA, cubeB, edgeB, slide, allowed)
        if plan.state != PlanState.UNDEFINED:
            break
        # if the polys got stuck and the straight align didnt fix state failure
        if stuckTimes >= STUCK_TIMES_MAX:
            plan.state = PlanState.FAILURE_STUCK
            break
        # if we cant connect after moving max walking distance state failure
        if distMoved >= MAX_MOVING_DIST:
            plan.state = PlanState.FAILURE_MAX_ITR
            break
        if DEBUG: print(f"Itr: {itr}, {stuckTimes} times stuck, {distMoved} dist moved.")
        itr += 1
    # terminate sim and return plan with last state sim was in as goal
    plan.goal = sim.terminate()
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

def __walkDynamic(config: Configuration, cubeA: Cube, cubeB: Cube, direction):
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
    pWalks = []
    for _ in range(pivotSteps):
        pWalks.append(PivotWalk(direction, pivotAng))
    return pWalks

def __updatePlanState(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, slide:Direction, allowed: set) -> PlanState:
    # check if the current poly set is allowed
    if not __polysAllowed(config, allowed):
        return PlanState.FAILURE_ALLOWED_POLYS
    # check if config contains invalid polys
    if __polysInvalid(config, cubeA, cubeB, edgeB):
        return PlanState.FAILURE_INVAL_POLY
    # check if cubes are connected at edgeB
    if __isConnected(config, cubeA, cubeB, edgeB):
        return PlanState.SUCCESS
    # check if you can connect the polys of A and B
    if not __connectPossible(config, cubeA, cubeB, edgeB):
        return PlanState.FAILURE_CONNECT
    # check if connection edges are inside a hole
    if __edgeInCave(config, cubeA, edgeB.inv()) or __edgeInCave(config, cubeB, edgeB):
        return PlanState.FAILURE_CAVE
    # check if we cant slide in anymore
    if not slide in __slideInDirections(config, cubeA, cubeB, edgeB):
        return PlanState.FAILURE_SLIDE_IN
    return PlanState.UNDEFINED

def __isConnected(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
    polyB = config.getPolyominoes().getForCube(cubeB)
    return polyB.getConnectedAt(cubeB, edgeB) == cubeA

def __connectPossible(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
    polyA = config.getPolyominoes().getForCube(cubeA)
    polyB = config.getPolyominoes().getForCube(cubeB)
    # poly resulting from connection would overlap, or cubes are inside the same polyomino
    targetPoly = polyA.connectPoly(cubeA, polyB, cubeB, edgeB)
    if targetPoly == None or not targetPoly.isValid():
        return False
    return True

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

def __edgeInCave(config: Configuration, cube: Cube, edge: Direction) -> bool:
    poly = config.getPolyominoes().getForCube(cube)
    coords = poly.getLocalCoordinates(cube)
    if edge == Direction.NORTH:
        coordsToCheck = ((coords[0] + 1, coords[1] + 1),(coords[0] - 1, coords[1] + 1))
    elif edge == Direction.EAST:
        coordsToCheck = ((coords[0] + 1, coords[1] + 1),(coords[0] + 1, coords[1] - 1))
    elif edge == Direction.SOUTH:
        coordsToCheck = ((coords[0] + 1, coords[1] - 1),(coords[0] - 1, coords[1] - 1))
    else:
        coordsToCheck = ((coords[0] - 1, coords[1] + 1),(coords[0] - 1, coords[1] - 1))
    if poly.getCube(coordsToCheck[0]) != None and poly.getCube(coordsToCheck[1]) != None:
        return True
    return False

def __polysAllowed(config: Configuration, allowed: set) -> bool:
    return allowed == None or config.getPolyominoes() in allowed

def __polysInvalid(config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
    if config.getPolyominoes().containsInvalid():
        return True
    polyA = config.getPolyominoes().getForCube(cubeA)
    polyB = config.getPolyominoes().getForCube(cubeB)
    targetPoly = polyA.connectPoly(cubeA, polyB, cubeB, edgeB)
    if targetPoly != None and not targetPoly.isValid():
        return True
    return False

def __faceingDirection(config: Configuration, cubeA: Cube, cubeB: Cube) -> Direction:
    """
    returns 'direction',so that cubeB is in 'direction' of cubeA.
    Direction is either EAST or WEST
    """
    vecAB = config.getPosition(cubeB) - config.getPosition(cubeA)
    if vecAB.dot(Direction.EAST.vec(config.magAngle)) > 0:
        return Direction.EAST
    else:
        return Direction.WEST