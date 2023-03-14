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

    MAX_ITR = 64
    CRITICAL_DISTANCE = 4 * Cube.RAD
    SLOWWALK_DISTANCE = CRITICAL_DISTANCE * 2
    ANG_NONCRT = PivotWalk.DEFAULT_PIVOT_ANG
    ANG_CRT = ANG_NONCRT / 1.5
    STEPS_NONCRT = 3
    STEPS_CRT = 1
    ANG_ALIGNED = math.radians(4)


    def executePlan(self, plan: Plan):
        sim = Simulation(True, False)
        sim.loadConfig(plan.initial)
        if plan.info != None:
            sim.markCube(plan.info[0])
            sim.markCube(plan.info[1])
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
        if initial.polyominoes == None:
            initial = self.singleUpdate(initial)
        # when already connected return successfull plan
        if self.__isConnected__(initial, cubeA, cubeB, edgeB):
            return Plan(initial, initial, [], PlanState.SUCCESS, (cubeA,cubeB,edgeB))
        # cant connect cubes sideways if they are same type
        if edgeB in (Direction.EAST, Direction.WEST) and cubeA.type == cubeB.type:
            return Plan(initial, None, None, PlanState.FAILURE_SAME_TYPE, (cubeA,cubeB,edgeB))
        # pre check if connecting the polys is even possible
        if not self.__polyConnectPossible__(initial, cubeA, cubeB, edgeB):
            return Plan(initial, None, None, PlanState.FAILURE_POLY_CON, (cubeA,cubeB,edgeB))
        # Make plans for moving left, right and choose better one
        left =  self.__alignWalkRealign__(initial, cubeA, cubeB, edgeB, PivotWalk.LEFT)
        if DEBUG: print(f"Left plan done. {left.state} in {round(left.cost(),2)}rad")
        right =  self.__alignWalkRealign__(initial, cubeA, cubeB, edgeB, PivotWalk.RIGHT)
        if DEBUG: print(f"Right plan done. {right.state} in {round(right.cost(),2)}rad")
        return left.compare(right)
            

    def __alignWalkRealign__(self, initial: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction, direction, terminated: Event=None):
        if terminated == None:
            terminated = Event()
        sim = Simulation(DEBUG, False)
        sim.loadConfig(initial)
        sim.markCube(cubeA)
        sim.markCube(cubeB)
        config = initial
        state = PlanState.UNDEFINED
        actions = []
        itr = 0
        while not terminated.is_set():
            # aligne the cubes multiple times until they are nearly aligned
            rotation_pre = Rotation(0)
            while True:
                rotation = self.__alignCubesByEdge__(config, cubeA, cubeB, edgeB)
                if abs(rotation.angle) < LocalPlanner.ANG_ALIGNED:
                    if DEBUG: print(f"Aligned.")
                    break
                if abs(abs(rotation.angle) - abs(rotation_pre.angle)) < LocalPlanner.ANG_ALIGNED:
                    if DEBUG: print(f"Cutting rotation in half.")
                    rotation.angle /= 2
                if not self.__polyConnectPossible__(config, cubeA, cubeB, edgeB):
                    break 
                self.__executeMotions__(sim, [rotation])
                actions.extend([rotation, Idle(1)])
                if DEBUG: print(f"{itr}: {rotation}")
                config = sim.saveConfig()
                rotation_pre = rotation
            # check if cubes are in critical distance for magnets to attract
            distance = config.getPosition(cubeA).get_distance(config.getPosition(cubeB))
            if distance < LocalPlanner.CRITICAL_DISTANCE:
                # if so let magnets do the rest
                wait = Idle(10)
                self.__executeMotions__(sim, [wait])
                actions.append(wait)
                if DEBUG: print(f"{itr}: {wait}")
            else:
                # if not walk into direction
                pWalks = self.__walkDirectionDynamic__(config, cubeA, cubeB, direction)
                self.__executeMotions__(sim, pWalks)
                pWalks.append(Idle(1))
                actions.extend(pWalks)
                if DEBUG: print(f"{itr}: {len(pWalks)-1} x {pWalks[0]}")
            config = sim.saveConfig()
            # check if cubes are connected at edgeB
            if self.__isConnected__(config, cubeA, cubeB, edgeB):
                state = PlanState.SUCCESS
                break
            # check if you can connect the polys of A and B
            if not self.__polyConnectPossible__(config, cubeA, cubeB, edgeB):
                state = PlanState.FAILURE_POLY_CON
                break
            # if we cant conect after a lot of iterations report failure
            if itr >= LocalPlanner.MAX_ITR:
                state = PlanState.FAILURE_MAX_ITR
                break
            itr += 1
        sim.terminate()
        return Plan(initial, config, actions, state, (cubeA,cubeB,edgeB))

    def __alignCubesByEdge__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction):
        magAng = config.magAngle
        posA = config.getPosition(cubeA)
        posB = config.getPosition(cubeB)
        vecBA = posA - posB
        vecEdgeB = edgeB.vec(magAng)
        distance = posA.get_distance(posB)
        if edgeB in (Direction.WEST, Direction.EAST) or distance < LocalPlanner.CRITICAL_DISTANCE:
            # For side connection, or if cubes are near enought, just rotate edgeB to vecBA
            vecDes = vecBA
            vecSrc = vecEdgeB
            if DEBUG: print("Straight align")
        else:
            # For Top bottom connection move vecDes one cube length perpendicular to vecAB
            vecPer = (2.5 * Cube.RAD) * vecBA.perpendicular_normal()
            dotPerEdgeB = round(vecPer.dot(vecEdgeB), 3)
            if dotPerEdgeB <= 0:
                vecDes = vecBA + vecPer
            else:
                vecDes = vecBA - vecPer
            # Take either west or east as vecSrc. Always the angle <= 90
            vecE = Direction.EAST.vec(magAng)
            vecW = Direction.WEST.vec(magAng)
            if bool(vecDes.dot(vecE) >= 0) ^ bool(dotPerEdgeB == 0):
                vecSrc = vecE
            else:
                vecSrc = vecW
            if DEBUG: print("N-S align")
        # Calculate the rotation and execute it
        rotAng = vecSrc.get_angle_between(vecDes)
        return Rotation(rotAng)

    def __walkDirectionDynamic__(self, config: Configuration, cubeA: Cube, cubeB: Cube, direction) -> list:
        posA = config.getPosition(cubeA)
        posB = config.getPosition(cubeB)
        distance = posA.get_distance(posB)
        if distance < LocalPlanner.SLOWWALK_DISTANCE:
            pivotAng = LocalPlanner.ANG_CRT
            steps = LocalPlanner.STEPS_CRT
        else:
            pivotAng = LocalPlanner.ANG_NONCRT
            steps = LocalPlanner.STEPS_NONCRT
        return [PivotWalk(direction, pivotAng)] * steps

    def __isConnected__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
        polyB = config.polyominoes.getPoly(cubeB)
        return polyB.getConnection(cubeB, edgeB) == cubeA

    def __polyConnectPossible__(self, config: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
        # cubes are inside the same polyomino
        polyA = config.polyominoes.getPoly(cubeA)
        polyB = config.polyominoes.getPoly(cubeB)
        if polyA.id == polyB.id:
            return False
        # poly resulting from connection would overlap
        targetPoly = Polyomino.connectPoly(polyA, cubeA, polyB, cubeB, edgeB)
        if targetPoly == None:
            return False
        return True

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