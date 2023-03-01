"""
Holds the Motion class and subclasses PivotWalk and Rotation.
Also holds the constant values LEFT, RIGHT, PIVOT_ANG for pivot walking
and ANG_VELOCITY for all rotations.

@author: Aaron T Becker, Kjell Keune
"""

import math
from threading import Event 
from queue import Queue

from util import DEBUG
from sim.statehandler import StateHandler

class Step:

    def __init__(self, angChange=0, elevChange=0):
        self.angChange = angChange
        self.elevChange = elevChange

class Motion:
    """
    Abstract super class. All motions have an executed event and a stepSequence.
    """

    def __init__(self):
        self.executed = Event()

    def stepSquence(self):
        return [Step()]


class PivotWalk(Motion):
    """
    A pivot walking step either left or right with a pivot-angle.
    """
    LEFT = -1
    RIGHT = 1

    DEFAULT_PIVOT_ANG = math.radians(20) #in radians

    def __init__(self, direction, pivotAng=DEFAULT_PIVOT_ANG):
        super().__init__()
        self.direction = direction
        self.pivotAng = pivotAng
        
    def __str__(self):
        str = "PivotWalk("
        if self.direction == PivotWalk.LEFT:
            str += "LEFT"
        else:
            str += "RIGHT"
        return str + ")"     

    def stepSequence(self):
        steps = []
        pivotRotationSeq = Rotation(self.direction * self.pivotAng).stepSequence()
        pivotRotationSeqInv = Rotation(-2 * self.direction * self.pivotAng).stepSequence()
        #Assamble step-sequence for pivot-walking-step zeros are added to let pymunk level of after rotation
        steps.append(Step(0, 1))
        steps.extend(pivotRotationSeq)
        steps.append(Step(0, -2))
        steps.extend(pivotRotationSeqInv)
        steps.append(Step(0, 2))
        steps.extend(pivotRotationSeq)
        steps.append(Step(0, -1))
        return steps

class Rotation(Motion):
    """
    A rotation around a specific angle.
    """

    ANG_VELOCITY = math.radians(22.5)  #in radians/seconds
    ROTATION_STALLS = 0.25 #zerochanges/update when rotating

    def __init__(self, angle):
        super().__init__()
        self.angle = angle

    def __str__(self):
        return "Rotation(" + str(math.degrees(self.angle)) + "°)"

    def stepSequence(self):
        steps = []
        k = math.floor(abs(self.angle) / (Rotation.ANG_VELOCITY * StateHandler.STEP_TIME))
        angPerStep = self.angle / k
        for i in range(k):
            steps.append(Step(angPerStep, 0))
        steps.append(Step(self.angle - k * angPerStep, 0))
        zeros = [Step() for _ in range(StateHandler.max_poly_length * math.floor(Rotation.ROTATION_STALLS / StateHandler.STEP_TIME))]
        steps.extend(zeros)
        return steps

class MotionController:
    """
    Handles all the motions that have been and will be simulated.
    It also creates the step sequennces of changes
    that need to be applied to the magnetic field per update.
    """

    def __init__(self):
        self.motionsOpen = Queue()
        self.currentMotion = None
        self.motionsDone = []
        self.steps = Queue()
        
    def add(self, motion: Motion):
        """
        Adds motion to be executed.

        Parameters:
            motion
        """
        self.motionsOpen.put(motion)

    def nextStep(self) -> Step:
        """
        Returns:
            The next step to execute the current motion as a tupel (angle update, elevation update)
            Returns (0,0) if all motions have been executed
        
        Note that the return values are not absolute they need to be added to the current orientation of the magneticfield
        """
        if self.steps.empty():
            if not self.currentMotion == None:
                self.currentMotion.executed.set()
                self.motionsDone.append(self.currentMotion)
                if DEBUG: print("Executed: " + str(self.currentMotion))
            if self.motionsOpen.empty():
                self.currentMotion = None
                return Step()
            self.currentMotion = self.motionsOpen.get()
            for i in self.currentMotion.stepSequence():
                self.steps.put(i)
            
        return self.steps.get()