"""
Holds the Motion class and subclasses PivotWalk and Rotation.
Also holds the constant values LEFT, RIGHT, PIVOT_ANG for pivot walking
and ANG_VELOCITY for all rotations.

@author: Aaron T Becker, Kjell Keune
"""

import math
from threading import Event 
from queue import Queue

import sim.simulation as sim

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
            Returns (0,0) if all the motions have been executed
        
        Note that the return values are not absolute they need to be added to the current orientation of the magneticfield
        """
        if self.steps.empty():
            if not self.currentMotion == None:
                self.currentMotion.executed.set()
                self.motionsDone.append(self.currentMotion)
                print("Executed: " + str(self.currentMotion))
            if self.motionsOpen.empty():
                self.currentMotion = None
                return (0,0)
            self.currentMotion = self.motionsOpen.get()
            for i in self.currentMotion.stepSequence():
                self.steps.put(i)
            
        return self.steps.get()

class Motion:
    """
    Abstract super class. All motions have an executed event.
    """

    def __init__(self):
        self.executed = Event()
        self.executed.clear()
    
    def stepSequence(self):
        return [(0,0)]


class PivotWalk(Motion):
    """
    A pivot walking step either left or right.
    """
    LEFT = -1
    RIGHT = 1

    PIVOT_ANG = math.radians(12) #in radians
    PIVOT_STALLS = 0.2 #zerochanges/update when pivotwalking

    def __init__(self, direction):
        super().__init__()
        self.direction = direction

    def __str__(self):
        str = "PivotWalk("
        if self.direction == PivotWalk.LEFT:
            str += "LEFT"
        else:
            str += "RIGHT"
        return str + ")"

    def stepSequence(self):
        """
        Returns:
            The steps per updates necessary to execute this motion
        """
        steps = []
        pivotRotationSeq = Rotation(self.direction * PivotWalk.PIVOT_ANG).stepSequence()
        pivotRotationSeqInv = Rotation(-2 * self.direction * PivotWalk.PIVOT_ANG).stepSequence()
        zeros = [(0,0) * math.floor(PivotWalk.PIVOT_STALLS / sim.Simulation.STEP_TIME)]
        #Assamble step-sequence for pivot-walking-step zeros are added to let pymunk level of after rotation
        steps.append((0,-1))
        steps.extend(pivotRotationSeq)
        steps.extend(zeros)
        steps.append((0, 2))
        steps.extend(pivotRotationSeqInv)
        steps.extend(zeros)
        steps.append((0,-2))
        steps.extend(pivotRotationSeq)
        steps.extend(zeros)
        steps.append((0, 1))
        return steps

class Rotation(Motion):
    """
    A rotation around a specific angle.
    """

    ANG_VELOCITY = math.radians(22.5)  #in radians/seconds

    def __init__(self, angle):
        super().__init__()
        self.angle = angle

    def __str__(self):
        return "Rotation(" + str(math.degrees(self.angle)) + "°)"

    def stepSequence(self):
        """
        Returns:
            The steps per updates necessary to execute this motion
        """
        steps = []
        k = math.floor(abs(self.angle) / (Rotation.ANG_VELOCITY * sim.Simulation.STEP_TIME))
        angPerStep = self.angle / k
        for i in range(k):
            steps.append((angPerStep, 0))
        steps.append((self.angle - k * angPerStep, 0))
        return steps