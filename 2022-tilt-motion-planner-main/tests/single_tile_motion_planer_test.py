import context
from tiltmp.core.algorithms import *
import unittest

from tiltmp.core.serialization import read_instance
from tiltmp.mp.motionplanner import SingleTileMotionPlanner


class TestSingleTileMotionPlanner(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_instance = read_instance("instances/single_tile_mp.json")
        self.poly = None
        for poly in self.test_instance.initial_state.polyominoes:
            if poly.size > 1:
                self.poly = poly
        assert self.poly.size == 3
        self.tile = None
        for tile in self.test_instance.initial_state.get_tiles():
            if tile.parent is not self.poly:
                self.tile = tile

    def test_add_to_right(self):
        mp = SingleTileMotionPlanner(self.test_instance, self.tile, self.poly, (2, 1))
        solution = mp.solve()
        board = deepcopy(self.test_instance.initial_state)

        for d in solution:
            board.step(d)
            board.activate_glues()

        self.assertTrue(len(board.polyominoes) == 4)
        self.assertTrue(max(board.polyominoes, key=lambda p: p.size).size == 4)

        # for p in board.polyominoes:
        #     print(p)

    def test_add_to_left(self):
        mp = SingleTileMotionPlanner(self.test_instance, self.tile, self.poly, (-1, 0))
        solution = mp.solve()
        board = deepcopy(self.test_instance.initial_state)

        for d in solution:
            board.step(d)
            board.activate_glues()

        self.assertTrue(len(board.polyominoes) == 4)
        self.assertTrue(max(board.polyominoes, key=lambda p: p.size).size == 4)

        # for p in board.polyominoes:
        #     print(p)


if __name__ == '__main__':
    unittest.main()
