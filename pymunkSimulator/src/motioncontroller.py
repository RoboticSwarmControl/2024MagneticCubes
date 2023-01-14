"""
Holds the MotionControler class

@author: Aaron T Becker, Kjell Keune
"""

from queue import *
from motion import Motion

class MotionController:
    """
    Handles all the motions that have been and will be simulated.
    It also creates the step sequennces of changes
    that need to be applied to the magnetic field per update.
    """

    def __init__(self, fps):
        self.fps = fps
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
            if self.motionsOpen.empty():
                self.currentMotion = None
                return (0,0)
            self.currentMotion = self.motionsOpen.get()
            for i in self.currentMotion.stepSequence(self.fps):
                self.steps.put(i)
            print("Executing " + self.currentMotion.__str__())
        return self.steps.get()


            
                
            




