import context
from tiltmp.core.algorithms import *
import unittest

from tiltmp.mp.rrtmotionplanner import bottleneck_edge_length, Configuration


class MatchingTest(unittest.TestCase):

    def test_motion_planner(self):
        board = Board(100, 100)
        t1 = Tile(position=(10, 10), glues=Glues("A", "A", "A", "A"))
        t2 = Tile(position=(50, 50), glues=Glues("A", "A", "A", "A"))
        t3 = Tile(position=(5, 5), glues=Glues("B", "B", "B", "B"))
        board.add(Polyomino(tiles=[t1]))
        board.add(Polyomino(tiles=[t2]))
        board.add(Polyomino(tiles=[t3]))
        c1 = Configuration.from_board(board)
        board._move_polyominoes(board.polyominoes, 5, 4)
        c2 = Configuration.from_board(board)
        self.assertTrue(bottleneck_edge_length(c1, c2) == 9.0)
        board._move_polyominoes(board.polyominoes, 1, 0)
        c3 = Configuration.from_board(board)
        self.assertTrue(bottleneck_edge_length(c1, c3) == 10.0)


