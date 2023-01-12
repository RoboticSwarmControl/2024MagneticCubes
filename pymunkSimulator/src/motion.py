import math 

LEFT = -1
RIGHT = 1

ANG_VEL = math.pi / 8 #in radians/second
PIVOT_ANG = math.pi / 16 #in radians

class Motion:

    def __init__(self):
        self.executed = False
    
    def stepSequence(self, fps):
        return [(0,0)]


class PivotWalk(Motion):

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

    def __init__(self, angle):
        super().__init__()
        self.angle = angle

    def __str__(self):
        return "Rotation(" + str(math.degrees(self.angle)) + "°)"

    def stepSequence(self, fps):
        steps = []
        k = math.floor((abs(self.angle) / ANG_VEL) * fps)
        angPerStep = self.angle / k
        for i in range(k):
            steps.append((angPerStep, 0))
        steps.append((self.angle - k * angPerStep, 0))
        return steps