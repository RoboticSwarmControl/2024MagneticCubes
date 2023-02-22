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
        

    def add(self, motion):
        """
        Adds motion to be executed.

        Parameters:
            motion
        """
        self.motionsOpen.put(motion)

    def nextStep(self):
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
                return (0,0)
            self.currentMotion = self.motionsOpen.get()
            for i in self.currentMotion.stepSequence:
                self.steps.put(i)
            
        return self.steps.get()

class Motion:
    """
    Abstract super class. All motions have an executed event and a stepSequence.
    """

    def __init__(self):
        self.executed = Event()
        self.stepSequence = [(0,0)]


class PivotWalk(Motion):
    """
    A pivot walking step either left or right with a pivot-angle.
    """
    LEFT = -1
    RIGHT = 1

    DEFAULT_PIVOT_ANG = math.radians(12) #in radians
    PIVOT_STALLS = 0.2 #zerochanges/update when pivotwalking

    def __init__(self, direction, pivotAng=DEFAULT_PIVOT_ANG):
        super().__init__()
        self.direction = direction
        self.pivotAng = pivotAng
        if pivotAng == PivotWalk.DEFAULT_PIVOT_ANG:
            if direction == PivotWalk.LEFT:
                self.stepSequence = DEFAULT_PIVOT_STEPSEQ_LEFT
            else:
                self.stepSequence =  DEFAULT_PIVOT_STEPSEQ_RIGHT
        else:
            self.stepSequence = PivotWalk.__stepSequence__(self.direction, self.pivotAng)

    def __str__(self):
        str = "PivotWalk("
        if self.direction == PivotWalk.LEFT:
            str += "LEFT"
        else:
            str += "RIGHT"
        return str + ")"     

    @staticmethod
    def __stepSequence__(direction, pivotAng):
        steps = []
        pivotRotationSeq = Rotation(direction * pivotAng).stepSequence
        pivotRotationSeqInv = Rotation(-2 * direction * pivotAng).stepSequence
        zeros = [(0,0) * math.floor(PivotWalk.PIVOT_STALLS / StateHandler.STEP_TIME)]
        #Assamble step-sequence for pivot-walking-step zeros are added to let pymunk level of after rotation
        steps.append((0, 1))
        steps.extend(pivotRotationSeq)
        steps.extend(zeros)
        steps.append((0, -2))
        steps.extend(pivotRotationSeqInv)
        steps.extend(zeros)
        steps.append((0, 2))
        steps.extend(pivotRotationSeq)
        steps.extend(zeros)
        steps.append((0, -1))
        return steps

class Rotation(Motion):
    """
    A rotation around a specific angle.
    """

    ANG_VELOCITY = math.radians(22.5)  #in radians/seconds

    def __init__(self, angle):
        super().__init__()
        self.angle = angle
        self.stepSequence = Rotation.__stepSequence__(angle)

    def __str__(self):
        return "Rotation(" + str(math.degrees(self.angle)) + "°)"

    @staticmethod
    def __stepSequence__(angle):
        steps = []
        k = math.floor(abs(angle) / (Rotation.ANG_VELOCITY * StateHandler.STEP_TIME))
        angPerStep = angle / k
        for i in range(k):
            steps.append((angPerStep, 0))
        steps.append((angle - k * angPerStep, 0))
        return steps
    
DEFAULT_PIVOT_STEPSEQ_LEFT = PivotWalk.__stepSequence__(PivotWalk.LEFT, PivotWalk.DEFAULT_PIVOT_ANG)
DEFAULT_PIVOT_STEPSEQ_RIGHT = PivotWalk.__stepSequence__(PivotWalk.RIGHT, PivotWalk.DEFAULT_PIVOT_ANG)