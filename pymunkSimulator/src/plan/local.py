from enum import Enum
import time

from sim.motion import Idle, Rotation, PivotWalk
from sim.simulation import Simulation
from sim.state import *
from plan.plan import *


DEBUG = False

class LocalPlanner:

    MAX_ITR = 100
    CRITICAL_DISTANCE = 4 * Cube.RAD
    SLOWWALK_DISTANCE = CRITICAL_DISTANCE * 1.5
    ANG_NONCRT = PivotWalk.DEFAULT_PIVOT_ANG
    ANG_CRT = ANG_NONCRT / 1.5
    STEPS_NONCRT = 3
    STEPS_CRT = 2

    def __init__(self, drawing=False):
        self.__sim = Simulation(drawing, userControls=False)
        self.__config = None

    def executePlan(self, plan: Plan):
        self.__sim.enableDraw()
        self.__loadConfig__(plan.initial)
        self.__executeMotions__(plan.actions)
        time.sleep(1)
        self.__sim.disableDraw()

    def loadAndUpdate(self, config: Configuration) -> Configuration:
        """
        Loads the config and lets it do a single update
        Can be useful for retrieving polyomino information.
        returns:
            the config after updating
        """
        self.__loadConfig__(config)
        return self.__executeMotions__([Idle(1)])

    def planCubeConnect(self, initial: Configuration, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> Plan:
        # single update if no poly info available else just load
        if initial.polyominoes == None:
            self.loadAndUpdate(initial)
        else:
            self.__loadConfig__(initial)
        # when already connected return successfull plan
        if self.__isConnected__(cubeA, cubeB, edgeB):
            return Plan(initial, self.__config, [], PlanState.SUCCESS)
        # cant connect cubes sideways if they are same type
        if edgeB in (Direction.EAST, Direction.WEST) and cubeA.type == cubeB.type:
            return Plan(initial, None, None, PlanState.FAILURE)
        # first align of the cubes
        alignRot = self.__alignEdges__(cubeA, cubeB, edgeB)
        configAligned = self.__saveConfig__()
        # creating plan for walking right and one for walking left
        plans = {}
        for direction in (PivotWalk.LEFT, PivotWalk.RIGHT):
            state = PlanState.UNDEFINED
            actions = list(alignRot)
            itr = 0
            while True:
                # check if cubes are in critical distance for magnets to attract
                distance = self.__config.getPosition(cubeA).get_distance(self.__config.getPosition(cubeB))
                if distance < LocalPlanner.CRITICAL_DISTANCE:
                    # if so let magnets do the rest
                    wait = [Idle(10)]
                    self.__executeMotions__(wait)
                    actions.extend(wait)
                    actions.append(Idle(1))
                else:
                    # if not walk into direction
                    actions.extend(self.__walk__(cubeA, cubeB, direction))
                # re aligne the cubes
                actions.extend(self.__alignEdges__(cubeA, cubeB, edgeB))
                # check if cubes are connected at edgeB
                if self.__isConnected__(cubeA, cubeB, edgeB):
                    state = PlanState.SUCCESS
                    break
                # check if you can connect the polys of A and B
                if not self.__polyConnectPossible__(cubeA, cubeB, edgeB):
                    state = PlanState.FAILURE
                    if DEBUG: print(f"Dir{direction}: polyConnect failure")
                    break
                # if we cant conect after a lot of iterations report failure
                if itr >= LocalPlanner.MAX_ITR:
                    state = PlanState.FAILURE
                    if DEBUG: print(f"Dir{direction}: maxIteration failure")
                    break
                itr += 1
            plans[direction] = Plan(initial, self.__config, actions, state)
            self.__loadConfig__(configAligned)
        # evaluate wich plan to return
        return plans[PivotWalk.LEFT].compare(plans[PivotWalk.RIGHT])
    
    def __alignEdges__(self, cubeA: Cube, cubeB: Cube, edgeB: Direction):
        magAng = self.__config.magAngle
        posA = self.__config.getPosition(cubeA)
        posB = self.__config.getPosition(cubeB)
        vecBA = posA - posB
        vecEdgeB = edgeB.vec(magAng)
        distance = posA.get_distance(posB)
        if edgeB in (Direction.WEST, Direction.EAST) or distance < LocalPlanner.CRITICAL_DISTANCE:
            # For side connection, or if cubes are near enought, just rotate edgeB to vecBA
            vecDes = vecBA
            vecSrc = vecEdgeB
        else:
            # For Top bottom connection move vecDes one cube length perpendicular to vecAB
            vecPer = (2.5 * Cube.RAD) * vecBA.perpendicular_normal()
            dotPerEdgeB = round(vecPer.dot(vecEdgeB),3)
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
        # Calculate the rotation and execute it
        rotAng = vecSrc.get_angle_between(vecDes)
        rotation = [Rotation(rotAng)]
        self.__executeMotions__(rotation)
        rotation.append(Idle(1))
        if DEBUG: print(f"Edges Aligned by turning {round(math.degrees(rotAng), 3)}°")
        return rotation
    
    def __walk__(self, cubeA: Cube, cubeB: Cube, direction):
        posA = self.__config.getPosition(cubeA)
        posB = self.__config.getPosition(cubeB)
        distance = posA.get_distance(posB)
        if distance < LocalPlanner.SLOWWALK_DISTANCE:
            pivotAng = LocalPlanner.ANG_CRT
            steps = LocalPlanner.STEPS_CRT
        else:
            pivotAng = LocalPlanner.ANG_NONCRT
            steps = LocalPlanner.STEPS_NONCRT
        pWalks = [PivotWalk(direction, pivotAng)] * steps
        self.__executeMotions__(pWalks)
        pWalks.append(Idle(1))
        if DEBUG: print(f"Walking {steps} steps with pivAng {round(math.degrees(pivotAng), 3)}")
        return pWalks

    def __isConnected__(self, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
        polyB = self.__config.polyominoes.getPoly(cubeB)
        return polyB.getConnection(cubeB, edgeB) == cubeA

    def __polyConnectPossible__(self, cubeA: Cube, cubeB: Cube, edgeB: Direction) -> bool:
        # cubes are inside the same polyomino
        polyA = self.__config.polyominoes.getPoly(cubeA)
        polyB = self.__config.polyominoes.getPoly(cubeB)
        if polyA.id == polyB.id:
            return False
        # poly resulting from connection would overlap
        targetPoly = Polyomino.connectPoly(polyA, cubeA, polyB, cubeB, edgeB)
        if targetPoly == None:
            return False
        return True

    def __executeMotions__(self, motions)-> Configuration:
        self.__sim.start()
        for motion in motions:
            self.__sim.executeMotion(motion)
        self.__sim.stop()
        return self.__saveConfig__()

    def __loadConfig__(self, config: Configuration):
        self.__sim.loadConfig(config)
        self.__config = config

    def __saveConfig__(self) -> Configuration:
        save = self.__sim.saveConfig()
        self.__config = save
        return save


