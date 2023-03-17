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
    SLOWWALK_DISTANCE = CRITICAL_DISTANCE * 2
    ANG_BIG = PivotWalk.DEFAULT_PIVOT_ANG
    ANG_SMALL = ANG_BIG / 1.5
    ANG_ALIGNED = math.radians(4)
    ALIGN_TRIES = 2
    IDLE_TRIES = 1


    def __init__(self) -> None:
        self.plans = {}

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
        sim.executeMotion(Idle(1))
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
        slide = self.__slideInPossible__(initial, cubeA, cubeB, edgeB)
        if not slide[0] and not slide[1]:
            return Plan(initial=initial, state=PlanState.FAILURE_POLY_CON, info=info)
        # determine if flip neccesary
        flip = False
        if edgeB in (Direction.NORTH,Direction.SOUTH) and slide[0] ^ slide[1]:
            vecAB = initial.getPosition(cubeB) - initial.getPosition(cubeA)
            faceingEast = vecAB.dot(Direction.EAST.vec(initial.magAngle)) > 0
            if slide != (faceingEast, not faceingEast):
                flip = True
        self.plans[PivotWalk.LEFT] = Plan(initial=initial, info=info)
        self.plans[PivotWalk.RIGHT] = Plan(initial=initial, info=info)
        # Make plans for moving left, right and choose better one
        self.__alignWalkRealign__(initial, cubeA, cubeB, edgeB, PivotWalk.LEFT, flip)
        if DEBUG: print(f"Left plan done. {self.plans[PivotWalk.LEFT].state} in {round(self.plans[PivotWalk.LEFT].cost(),2)}rad")
        self.__alignWalkRealign__(initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT, flip)
        if DEBUG: print(f"Right plan done. {self.plans[PivotWalk.RIGHT].state} in {round(self.plans[PivotWalk.RIGHT].cost(),2)}rad")
        return self.plans[PivotWalk.LEFT].compare(self.plans[PivotWalk.RIGHT])
        # with Pool(2) as pool:
        #     it = pool.imap_unordered(self.__alignWalkRealign__,[(initial, cubeA, cubeB, edgeB, PivotWalk.LEFT, flip),(initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT, flip)])
        #     first = self.plans[next(it)]
        #     if first.state == PlanState.SUCCESS:
        #         pool.terminate()
        #         return first
        #     second = self.plans[next(it)]
        #     pool.terminate()
        #     if first.state == PlanState.SUCCESS:
        #         return second
        #     return first
            
    def __alignWalkRealign__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, direction, flip: bool):
    # def __alignWalkRealign__(self, data: tuple):
    #     config = data[0]
    #     cubeA = data[1]
    #     cubeB  = data[2]
    #     edgeB = data[3]
    #     direction = data[4]
    #     flip = data[5]
        sim = Simulation(DEBUG, False)
        sim.loadConfig(config)
        sim.renderer.markedCubes.add(cubeA)
        sim.renderer.markedCubes.add(cubeB)
        # Make an initial alignement rotation also handels an initial flip
        initAlign = self.__alignCubesByEdge__(config, cubeA, cubeB, edgeB, flip)
        self.__executeMotions__(sim, [initAlign])
        self.plans[direction].actions.append(initAlign)
        self.plans[direction].actions.append(Idle(1))
        if DEBUG: print(f"Initial Align: {initAlign}, flip={flip}")
        config = sim.saveConfig()
        itr = 0
        idleTry = 0
        while True:
            # aligne the cubes as long as poly connection is still possible
            alignTry = 0
            while self.__polyConnectPossible__(config, cubeA, cubeB, edgeB):
                # check if alignement is neccessary
                rotation = self.__alignCubesByEdge__(config, cubeA, cubeB, edgeB)
                if abs(rotation.angle) < LocalPlanner.ANG_ALIGNED:
                    if DEBUG: print(f"Aligned.")
                    break
                # after normal align failed ALIGN_TRIES times we cut the angle in half to avoid oscilation
                if alignTry > LocalPlanner.ALIGN_TRIES:
                    if DEBUG: print(f"Cutting rotation in half.")
                    rotation.angle /= 2
                # execute the rotation
                self.__executeMotions__(sim, [rotation])
                self.plans[direction].actions.append(rotation)
                self.plans[direction].actions.append(Idle(1))
                config = sim.saveConfig()
                alignTry += 1
                if DEBUG: print(f"{itr}: {rotation}")
            # check if cubes are in critical distance for magnets to attract
            distance = config.getPosition(cubeA).get_distance(config.getPosition(cubeB))
            if distance < LocalPlanner.CRITICAL_DISTANCE and idleTry < LocalPlanner.IDLE_TRIES:
                # if so let magnets do the rest
                wait = Idle(10)
                self.__executeMotions__(sim, [wait])
                self.plans[direction].actions.append(wait)
                idleTry += 1
                if DEBUG: print(f"{itr}: {wait}")
            else:
                # if not walk into direction
                pWalks = self.__walkDirectionDynamic__(config, cubeA, cubeB, direction)
                self.__executeMotions__(sim, pWalks)
                self.plans[direction].actions.extend(pWalks)
                self.plans[direction].actions.append(Idle(1))
                idleTry = 0
                if DEBUG: print(f"{itr}: {len(pWalks)-1} x {pWalks[0]}")
            config = sim.saveConfig()
            # check if cubes are connected at edgeB
            if self.__isConnected__(config, cubeA, cubeB, edgeB):
                self.plans[direction].state = PlanState.SUCCESS
                break
            # check if you can connect the polys of A and B
            if not self.__polyConnectPossible__(config, cubeA, cubeB, edgeB):
                self.plans[direction].state = PlanState.FAILURE_POLY_CON
                break
            # if we cant conect after a lot of iterations report failure
            if itr >= LocalPlanner.MAX_ITR:
                self.plans[direction].state = PlanState.FAILURE_MAX_ITR
                break
            itr += 1
        sim.terminate()
        self.plans[direction].actions.append(Idle(3))
        self.plans[direction].goal = config
        print(itr)
        return direction

    def __alignCubesByEdge__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, flip: bool=False):
        magAng = config.magAngle
        posA = config.getPosition(cubeA)
        posB = config.getPosition(cubeB)
        vecBA = posA - posB
        vecEdgeB = edgeB.vec(magAng)
        distance = vecBA.length
        if edgeB in (Direction.WEST, Direction.EAST) or distance < LocalPlanner.CRITICAL_DISTANCE:
            # For side connection, or if cubes are near enought, just rotate edgeB to vecBA
            vecDes = vecBA
            vecSrc = vecEdgeB
            if DEBUG: print("Straight align")
        else:
            # For Top bottom connection move vecDes one cube length perpendicular to vecAB
            vecPer = (2.5 * Cube.RAD) * vecBA.perpendicular_normal()
            dotPerEdgeB = round(vecPer.dot(vecEdgeB), 3)
            if bool(dotPerEdgeB <= 0) ^ flip:
                vecDes = vecBA + vecPer
            else:
                vecDes = vecBA - vecPer
            # Take either west or east as vecSrc. Always the angle <= 90
            vecE = Direction.EAST.vec(magAng)
            vecW = Direction.WEST.vec(magAng)
            if (bool(vecDes.dot(vecE) >= 0) ^ bool(dotPerEdgeB == 0)) ^ flip:
                vecSrc = vecE
            else:
                vecSrc = vecW
            if DEBUG: print("N-S align")
        # Calculate the rotation
        rotAng = vecSrc.get_angle_between(vecDes)
        return Rotation(rotAng)

    def __walkDirectionDynamic__(self, config: Configuration, cubeA: Cube, cubeB: Cube, direction) -> list:
        posA = config.getPosition(cubeA)
        posB = config.getPosition(cubeB)
        vecBA = posA - posB
        distance = vecBA.length
        # take eith big or small pivot angle depending on distance
        if distance < LocalPlanner.SLOWWALK_DISTANCE:
            pivotAng = LocalPlanner.ANG_SMALL
        else:
            pivotAng = LocalPlanner.ANG_BIG
        # determin which poly is chasing which
        if direction == PivotWalk.LEFT:
            vecDir = Direction.WEST.vec(config.magAngle)
        else:
            vecDir = Direction.EAST.vec(config.magAngle)
        if vecBA.dot(vecDir) > 0:
            chasingPoly = config.getPolyominoes().getPoly(cubeB)
        else:
            chasingPoly = config.getPolyominoes().getPoly(cubeA)
        # estimate the pivot steps neccessary for the chasing poly to reach the other. Only take half.
        pivotSteps = math.ceil((distance / config.getPivotWalkingDistance(chasingPoly, pivotAng)) / 2)
        return [PivotWalk(direction, pivotAng)] * pivotSteps

    def __isConnected__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
        polyB = config.getPolyominoes().getPoly(cubeB)
        return polyB.getConnection(cubeB, edgeB) == cubeA

    def __polyConnectPossible__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
        polyA = config.getPolyominoes().getPoly(cubeA)
        polyB = config.getPolyominoes().getPoly(cubeB)
        # poly resulting from connection would overlap, orcubes are inside the same polyomino
        targetPoly = polyA.connectPoly(cubeA, polyB, cubeB, edgeB)
        if targetPoly == None:
            return False
        return True

    def __slideInPossible__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction):
        # check if poly can be connected by walking in form the east and west
        polyA = config.getPolyominoes().getPoly(cubeA)
        polyB = config.getPolyominoes().getPoly(cubeB)
        eastSlide = polyA.connectPolyPossible(cubeA, polyB, cubeB, edgeB, Direction.EAST)
        westSlide = polyA.connectPolyPossible(cubeA, polyB, cubeB, edgeB, Direction.WEST)
        return eastSlide, westSlide

    def __executeMotions__(self, sim: Simulation, motions):
        sim.start()
        for motion in motions:
            sim.executeMotion(motion)
        sim.stop()


        #----multi threading solution. 50% slower than just single thread.
        # with ThreadPoolExecutor(2) as executor:
        #    terminated = Event()
        #    left = executor.submit(self.__alignWalkRealign__, initial, cubeA, cubeB, edgeB, PivotWalk.LEFT, terminated)
        #    right = executor.submit(self.__alignWalkRealign__, initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT, terminated)
        #    done, notDone = wait([left, right], return_when=FIRST_COMPLETED)
        #    firstPlan = done.pop().result()
        #    if firstPlan.state == PlanState.SUCCESS:
        #        terminated.set()
        #        executor.shutdown(wait=False)
        #        return firstPlan
        #    done, _ = wait(notDone, return_when=ALL_COMPLETED)
        #    executor.shutdown(wait=False)
        #    secondPlan = done.pop().result()
        #    if secondPlan.state == PlanState.SUCCESS:
        #        return secondPlan
        #    return firstPlan
        #----Use multi processing. I cant return a plan because "It iS nO ThReAd.LoCk ObJeCt"... wichser
        # with Pool(2) as pool:
        #     it = pool.imap_unordered(self.__alignWalkRealign__,[(initial, cubeA, cubeB, edgeB, PivotWalk.LEFT),(initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT)])
        #     first = next(it)
        #     if first.state == PlanState.SUCCESS:
        #         pool.terminate()
        #         return first
        #     second = next(it)
        #     pool.terminate()
        #     if first.state == PlanState.SUCCESS:
        #         return second
        #     return first