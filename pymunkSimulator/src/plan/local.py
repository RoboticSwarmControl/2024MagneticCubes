import multiprocessing
from multiprocessing.pool import Pool
from threading import Event
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED, ALL_COMPLETED

from sim.motion import Idle, Rotation, PivotWalk
from sim.simulation import Simulation
from sim.state import *
from plan.plan import *


DEBUG = False

class LocalPlanner:

    MAX_ITR = 24
    CRITICAL_DISTANCE = 4 * Cube.RAD
    NS_ALIGN_OFFSET = 2.75 * Cube.RAD
    ALIGNED_THRESHOLD = math.radians(4)
    ALIGN_TRIES = 2

    SLOWWALK_DISTANCE = CRITICAL_DISTANCE * 2
    PWALK_ANG_BIG = PivotWalk.DEFAULT_PIVOT_ANG
    PWALK_ANG_SMALL = PWALK_ANG_BIG / 1.5
    PWALK_PORTION = 1/2
    IDLE_TRIES = 1

    def executePlan(self, plan: Plan):
        sim = Simulation(True, False)
        sim.loadConfig(plan.initial)
        if plan.info != None:
            sim.renderer.markedCubes.add(plan.info[0])
            sim.renderer.markedCubes.add(plan.info[1])
        sim.start()
        for motion in plan.actions:
            sim.executeMotion(motion)
        sim.stop()
        time.sleep(1)
        sim.terminate()

    def singleUpdate(self, config: Configuration) -> Configuration:
        """
        Loads the config and lets it do a single update
        Can be useful for retrieving polyomino information.
        returns:
            the config after updating
        """
        sim = Simulation(False, False)
        sim.loadConfig(config)
        sim.start()
        sim.executeMotion(Idle(2))
        return sim.terminate()

    def planCubeConnect(self, initial: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> Plan:
        # single update if no poly info available
        if initial.getPolyominoes().isEmpty():
            initial = self.singleUpdate(initial)
        # when already connected return successfull plan
        info = (cubeA,cubeB,edgeB)
        if self.__isConnected__(initial, cubeA, cubeB, edgeB):
            return Plan(initial=initial, goal=initial, state=PlanState.SUCCESS, info=info)
        # cant connect cubes sideways if they are same type
        if edgeB in (Direction.EAST, Direction.WEST) and cubeA.type == cubeB.type:
            return Plan(initial=initial, state=PlanState.FAILURE_SAME_TYPE, info=info)
        # pre check if connecting the polys is even possible
        if not self.__polyConnectPossible__(initial, cubeA, cubeB, edgeB):
            return Plan(initial=initial, state=PlanState.FAILURE_POLY_CON, info=info)
        # pre check if polys can slide together from either east or west
        slideDirections = self.__slideInDirections__(initial, cubeA, cubeB, edgeB)
        if len(slideDirections) == 0:
            return Plan(initial=initial, state=PlanState.FAILURE_SLIDE_IN, info=info)
        # determine which plans to execute. left and right either with or without initial flip
        plansToExec = []
        faceing = self.__faceingDirection__(initial, cubeA, cubeB)
        facingInv = faceing.inv()
        if faceing in slideDirections:
            plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.LEFT, faceing))
            plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT, faceing))
        if facingInv  in slideDirections:
            plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.LEFT, facingInv))
            plansToExec.append((initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT, facingInv))
        if DEBUG:
            return self.__planSequential__(plansToExec)
        else:
            return self.__planParallel__(plansToExec)
        

    def __planParallel__(self, data) -> Plan:
        print(f"Starting {len(data)} processes for simulation...")
        with Pool(len(data)) as pool:
            it = pool.imap_unordered(self.__alignWalkRealign__, data)
            for i in range(len(data)):
                plan = next(it)
                print(f"{i+1} finished: {plan}")
                if plan.state == PlanState.SUCCESS:
                    pool.terminate()
                    return plan
            pool.terminate()
            return plan

    def __planSequential__(self, data) -> Plan:
        optPlan = None
        for i, item in enumerate(data):
            plan = self.__alignWalkRealign__(item)
            print(f"{i+1} finished: {plan}")
            if optPlan == None:
                optPlan = plan
            else:
                optPlan = optPlan.compare(plan)
        return optPlan
            

    #def __alignWalkRealign__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, direction, flip: bool) -> Plan:
    def __alignWalkRealign__(self, data: tuple) -> Plan:
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
            rotation = self.__alignCubes__(config, cubeA, cubeB, edgeB, slide)
            # execute the rotation
            self.__executeMotions__(sim, [rotation])
            plan.actions.append(rotation)
            plan.actions.append(Idle(2))
            config = sim.saveConfig()
            if DEBUG: print(rotation)
            # check if cubes are in critical distance for magnets to attract
            distance = config.getPosition(cubeA).get_distance(config.getPosition(cubeB))
            if distance < LocalPlanner.CRITICAL_DISTANCE and idleTry < LocalPlanner.IDLE_TRIES:
                # if so let magnets do the rest
                wait = Idle(10)
                self.__executeMotions__(sim, [wait])
                plan.actions.append(wait)
                idleTry += 1
                if DEBUG: print(wait)
            else:
                # if not walk into direction
                pWalks = self.__walkDirectionDynamic__(config, cubeA, cubeB, direction)
                self.__executeMotions__(sim, pWalks)
                plan.actions.extend(pWalks)
                plan.actions.append(Idle(2))
                idleTry = 0
                if DEBUG: print(f"{len(pWalks)} x {pWalks[0]}")
            config = sim.saveConfig()
            # check if cubes are connected at edgeB
            if self.__isConnected__(config, cubeA, cubeB, edgeB):
                plan.state = PlanState.SUCCESS
                break
            # check if you can connect the polys of A and B
            if not self.__polyConnectPossible__(config, cubeA, cubeB, edgeB):
                plan.state = PlanState.FAILURE_POLY_CON
                break
            # if we cant conect after a lot of iterations report failure
            if itr >= LocalPlanner.MAX_ITR:
                plan.state = PlanState.FAILURE_MAX_ITR
                break
            itr += 1
        #print(f"itrations: {itr}")
        sim.stateHandler.timer.printTimeStats()
        sim.terminate()
        plan.actions.append(Idle(2))
        plan.goal = config
        return plan

    def __alignCubes__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, slide:Direction):
        posA = config.getPosition(cubeA)
        posB = config.getPosition(cubeB)
        comA = config.getCOM(config.getPolyominoes().getPoly(cubeA))
        comB = config.getCOM(config.getPolyominoes().getPoly(cubeB))
        #distance = posA.get_distance(posB)
        if edgeB in (Direction.WEST, Direction.EAST):
            # For side connection, or if cubes are near enought, do straight align
            alignEdge = edgeB
            if DEBUG: print("Straight align")
        else:
            # For Top bottom connection do n-s align
            alignEdge = slide.inv()
            posB += LocalPlanner.NS_ALIGN_OFFSET  * edgeB.vec(config.magAngle)
            if DEBUG: print("N-S align")
        return self.__calcAlignRotation__(comA, posA, comB, posB, alignEdge, config.magAngle)

    def __calcAlignRotation__(self, comA: Vec2d, posA: Vec2d, comB: Vec2d, posB: Vec2d, edgeB: Direction, magAngle):
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
            if angDiff < LocalPlanner.ALIGNED_THRESHOLD:
                return Rotation(rotAng)
            if angDiff < minAngDiff:
                minAngDiff = angDiff
                minRotAng = rotAng
            ang += step
            #print(f"angleBetween: {round(math.degrees(angDiff),2)}, rotation: {round(math.degrees(rotAng),2)}")
        return Rotation(minRotAng)

    def __walkDirectionDynamic__(self, config: Configuration, cubeA: Cube, cubeB: Cube, direction) -> list:
        posA = config.getPosition(cubeA)
        posB = config.getPosition(cubeB)
        vecBA = posA - posB
        distance = vecBA.length
        # take eith big or small pivot angle depending on distance
        if distance < LocalPlanner.SLOWWALK_DISTANCE:
            pivotAng = LocalPlanner.PWALK_ANG_SMALL
        else:
            pivotAng = LocalPlanner.PWALK_ANG_BIG
        # determin which poly is chasing which
        if bool(self.__faceingDirection__(config, cubeA, cubeB) == Direction.EAST) ^ bool(direction == PivotWalk.LEFT):
            chasingPoly = config.getPolyominoes().getPoly(cubeA)
        else:
            chasingPoly = config.getPolyominoes().getPoly(cubeB)
        # estimate the pivot steps neccessary for the chasing poly to reach the other. Only take half.
        pivotSteps = math.ceil((distance / config.getPivotWalkingDistance(chasingPoly, pivotAng)) * LocalPlanner.PWALK_PORTION)
        return [PivotWalk(direction, pivotAng)] * pivotSteps

    def __isConnected__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
        polyB = config.getPolyominoes().getPoly(cubeB)
        return polyB.getConnection(cubeB, edgeB) == cubeA

    def __polyConnectPossible__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
        polyA = config.getPolyominoes().getPoly(cubeA)
        polyB = config.getPolyominoes().getPoly(cubeB)
        # poly resulting from connection would overlap, or cubes are inside the same polyomino
        targetPoly = polyA.connectPoly(cubeA, polyB, cubeB, edgeB)
        if targetPoly == None:
            return False
        return True

    def __slideInDirections__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> set:
        # check if poly can be connected by walking in form the east and west
        slide = set()
        polyA = config.getPolyominoes().getPoly(cubeA)
        polyB = config.getPolyominoes().getPoly(cubeB)
        if polyA.connectPolyPossible(cubeA, polyB, cubeB, edgeB, Direction.EAST):
            slide.add(Direction.EAST)
        if polyA.connectPolyPossible(cubeA, polyB, cubeB, edgeB, Direction.WEST):
            slide.add(Direction.WEST)
        return slide
    
    def __faceingDirection__(self, config: Configuration, cubeA: Cube, cubeB: Cube) -> Direction:
        """
        returns 'direction',that cubeB is in 'direction' of cubeA.
        Direction is either EAST or WEST
        """
        vecAB = config.getPosition(cubeB) - config.getPosition(cubeA)
        if vecAB.dot(Direction.EAST.vec(config.magAngle)) > 0:
            return Direction.EAST
        else:
            return Direction.WEST

    def __executeMotions__(self, sim: Simulation, motions):
        sim.start()
        for motion in motions:
            sim.executeMotion(motion)
        sim.stop()