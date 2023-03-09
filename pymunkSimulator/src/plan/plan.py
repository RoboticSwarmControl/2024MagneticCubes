from enum import Enum

from sim.state import Configuration

class PlanState(Enum):

    UNDEFINED = 0
    SUCCESS = 1
    FAILURE = 2

    def  __str__(self) -> str:
        return self.name


class Plan:

    def __init__(self, initial: Configuration, goal: Configuration, actions, state: PlanState):
        self.initial = initial
        self.goal = goal
        if actions == None:
            self.actions = []
        else:
            self.actions = actions
        self.state = state

    def cost(self):
        cost = 0
        for action in self.actions:
            cost += action.cost()
        return cost

    def compare(self, other):
        """
        Returns the better plan, meaning the one with lowest costs if it is valid
        """
        # if both plans are valid return the one with lowest costs
        if self.state == PlanState.SUCCESS and other.state == PlanState.SUCCESS:
            if self.cost() < other.cost():
                return self
            else:
                return other
        # if only one in valid return that one. If both are invalid it doesnt matter so return planB
        if self.state == PlanState.SUCCESS:
            return self
        else:
            return other

    def concat(self, other):
        if self.goal != other.initial:
            return None
        if self.state != PlanState.SUCCESS or other.state != PlanState.SUCCESS:
            return None
        ccPlan = Plan(self.initial, other.goal)
        ccPlan.actions = list(self.actions) + list(other.actions)
        ccPlan.state = PlanState.SUCCESS
        return ccPlan