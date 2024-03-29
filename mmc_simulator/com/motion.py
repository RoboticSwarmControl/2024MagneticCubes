"""
Holds the Motion class and subclasses PivotWalk and Rotation.
Also holds the constant values LEFT, RIGHT, PIVOT_ANG for pivot walking
and ANG_VELOCITY for all rotations.

@author: Aaron T Becker, Kjell Keune
"""
import math
from threading import Event


class Step:

    def __init__(self, angChange=0, elevation=0):
        self.angChange = angChange
        self.elevation = elevation

class Motion:
    """
    Abstract super class. All motions have an executed event and a stepSequence.
    """

    def __init__(self) -> None:
        pass

    def stepSequence(self, stepTime, longestChain):
        return [Step()]
    
    def cost(self):
        return 0
    
    def __getstate__(self):
        state = self.__dict__.copy()
        return state
    
    def __setstate__(self, state):
        self.__dict__.update(state)

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
        if self.direction == PivotWalk.LEFT:
            dire = "LEFT"
        else:
            dire = "RIGHT"
        return f"PivotWalk({dire},{round(math.degrees(self.pivotAng), 2)}°)"    

    def stepSequence(self, stepTime, longestChain):
        steps = []
        pivotRotationSeq = Rotation(self.direction * self.pivotAng).stepSequence(stepTime, longestChain)
        pivotRotationSeqInv = Rotation(-2 * self.direction * self.pivotAng).stepSequence(stepTime, longestChain)
        #Assemble step-sequence for pivot-walking-step zeros are added to let pymunk level of after rotation
        steps.append(Step(0, Tilt.SOUTH_DOWN))
        steps.extend(pivotRotationSeq)
        steps.append(Step(0, Tilt.NORTH_DOWN))
        steps.extend(pivotRotationSeqInv)
        steps.append(Step(0, Tilt.SOUTH_DOWN))
        steps.extend(pivotRotationSeq)
        steps.append(Step(0, Tilt.HORIZONTAL))
        return steps
    
    def cost(self):
        return 4 * abs(self.pivotAng)

class Rotation(Motion):
    """
    A rotation around a specific angle.
    """

    ANG_VELOCITY = math.radians(22.5)  #in radians/seconds
    ROTATION_STALLS = 5 #zero upodates to append to motion

    def __init__(self, angle):
        super().__init__()
        self.angle = angle

    def __str__(self):
        return f"Rotation({round(math.degrees(self.angle),2)}°)"

    def stepSequence(self, stepTime, longestChain):
        if self.angle == 0:
            return [Step()]
        steps = []
        updates = math.ceil(abs(self.angle) / (Rotation.ANG_VELOCITY * stepTime))
        angPerUpdate = self.angle / updates
        for i in range(updates):
            steps.append(Step(angPerUpdate, 0))
        steps.append(Step(self.angle - updates * angPerUpdate, 0))
        zeros = [Step() for _ in range(longestChain * Rotation.ROTATION_STALLS)]
        steps.extend(zeros)
        return steps
    
    def cost(self):
        return abs(self.angle)

class Tilt(Motion):

    HORIZONTAL = 1
    NORTH_DOWN = 2
    SOUTH_DOWN = 3

    def __init__(self, tilt):
        super().__init__()
        self.tilt = tilt

    def __str__(self):
        if self.tilt == Tilt.HORIZONTAL:
            str = "HORIZONTAL"
        elif self.tilt == Tilt.NORTH_DOWN:
            str = "NORTH_DOWN"
        elif self.tilt == Tilt.SOUTH_DOWN:
            str = "SOUTH_DOWN"
        return f"Tilt({str})"

    def stepSequence(self, stepTime, longestChain):
        return [Step(0, self.tilt)]
    
    def cost(self):
        return 0


class Idle(Motion):
    """
    Idle motion meaning a certain amount of zero updates
    """

    def __init__(self, updates):
        super().__init__()
        self.updates = updates

    def __str__(self):
        return f"Idle({self.updates}upd)"

    def stepSequence(self, stepTime, longestChain):
        return [Step()] * self.updates
    
    def cost(self):
        return 0