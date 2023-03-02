"""
Holds the Motion class and subclasses PivotWalk and Rotation.
Also holds the constant values LEFT, RIGHT, PIVOT_ANG for pivot walking
and ANG_VELOCITY for all rotations.

@author: Aaron T Becker, Kjell Keune
"""

import math
from threading import Event

from util import DEBUG

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

    def stepSquence(self, stepTime, longestChain):
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

    def stepSequence(self, stepTime, longestChain):
        steps = []
        pivotRotationSeq = Rotation(self.direction * self.pivotAng).stepSequence(stepTime, longestChain)
        pivotRotationSeqInv = Rotation(-2 * self.direction * self.pivotAng).stepSequence(stepTime, longestChain)
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

    def stepSequence(self, stepTime, longestChain):
        steps = []
        k = math.floor(abs(self.angle) / (Rotation.ANG_VELOCITY * stepTime))
        angPerStep = self.angle / k
        for i in range(k):
            steps.append(Step(angPerStep, 0))
        steps.append(Step(self.angle - k * angPerStep, 0))
        zeros = [Step() for _ in range(longestChain * math.floor(Rotation.ROTATION_STALLS / stepTime))]
        steps.extend(zeros)
        return steps