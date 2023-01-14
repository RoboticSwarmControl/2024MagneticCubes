"""
Holds the Motion class and subclasses PivotWalk and Rotation.
Also holds the constant values LEFT, RIGHT, PIVOT_ANG for pivot walking
and ANG_VELOCITY for all rotations.

@author: Aaron T Becker, Kjell Keune
"""

import math
from threading import Event 

LEFT = -1
RIGHT = 1

ANG_VELOCITY = math.pi / 8 #in radians/second
PIVOT_ANG = math.pi / 16 #in radians

class Motion:
    """
    Abstract super class. All motions have an executed event.
    """
    def __init__(self):
        self.executed = Event()
        self.executed.clear()
    
    def stepSequence(self, fps):
        return [(0,0)]


class PivotWalk(Motion):
    """
    A pivot walking step either left or right.
    """
    
    def __init__(self, direction):
        super().__init__()
        self.direction = direction

    def __str__(self):
        str = "PivotWalk("
        if self.direction == LEFT:
            str += "LEFT"
        else:
            str += "RIGHT"
        return str + ")"

    def stepSequence(self, fps):
        """
        Returns:
            The steps per updates necessary to execute this motion
        """
        steps = []
        pivotRotationSeq = Rotation(self.direction * PIVOT_ANG).stepSequence(fps)
        pivotRotationSeqInv = Rotation(-2 * self.direction * PIVOT_ANG).stepSequence(fps)
        steps.append((0,-1))
        steps.extend(pivotRotationSeq)
        steps.append((0, 2))
        steps.extend(pivotRotationSeqInv)
        steps.append((0,-2))
        steps.extend(pivotRotationSeq)
        steps.append((0, 1))
        return steps

class Rotation(Motion):
    """
    A rotation around a specific angle.
    """

    def __init__(self, angle):
        super().__init__()
        self.angle = angle

    def __str__(self):
        return "Rotation(" + str(math.degrees(self.angle)) + "°)"

    def stepSequence(self, fps):
        """
        Returns:
            The steps per updates necessary to execute this motion
        """
        steps = []
        #TODO maybe make ANG_VOLOCITY in rad/update so fps acctualy effects simspeed
        k = math.floor((abs(self.angle) / ANG_VELOCITY) * fps)
        angPerStep = self.angle / k
        for i in range(k):
            steps.append((angPerStep, 0))
        steps.append((self.angle - k * angPerStep, 0))
        return steps