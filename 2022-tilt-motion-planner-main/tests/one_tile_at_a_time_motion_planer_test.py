import context
from tiltmp.core.algorithms import *
import unittest

from tiltmp.core.serialization import read_instance
from tiltmp.mp.motionplanner import OneTileAtATimeMotionPlanner


class TestOneTileAtATimeMotionPlanner(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def test_motion_planner(self):
        self.test_instance = read_instance("../Testcases/test.json")
        mp = OneTileAtATimeMotionPlanner(self.test_instance)
        solution = mp.solve()
        board = deepcopy(self.test_instance.initial_state)

        for d in solution:
            board.step(d)
            board.activate_glues()
        print(solution)
        self.assertTrue(max(board.polyominoes, key=lambda p: p.size).size == 4)

        for p in board.polyominoes:
            print(p)



if __name__ == '__main__':
    unittest.main()
