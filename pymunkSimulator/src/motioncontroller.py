from queue import *
from motion import Motion

class MotionController:

    def __init__(self, fps):
        self.fps = fps
        self.motionsOpen = Queue()
        self.currentMotion = None
        self.motionsDone = []
        self.steps = Queue()
        

    def add(self, motion):
        self.motionsOpen.put(motion)

    def nextStep(self):
        if self.steps.empty():
            if not self.currentMotion == None:
                self.currentMotion.executed = True
                self.motionsDone.append(self.currentMotion)
                print("...Done")
            if self.motionsOpen.empty():
                self.currentMotion = None
                return (0,0)
            self.currentMotion = self.motionsOpen.get()
            for i in self.currentMotion.stepSequence(self.fps):
                self.steps.put(i)
            print("Executing " + self.currentMotion.__str__() + "...")
        return self.steps.get()


            
                
            




