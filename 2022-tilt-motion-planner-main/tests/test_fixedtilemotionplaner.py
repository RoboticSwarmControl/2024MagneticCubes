import context
from tiltmp.mp.fixedtilemotionplanner import *
import unittest

from tiltmp.core.serialization import read_instance


class TestSingleTileMotionPlanner(unittest.TestCase):
    def test_must_can_move(self):
        test_instance = read_instance("instances/must_can_move.json")
        obg = OriginalBoardGenerator(test_instance.initial_state)
        stack_frame = StackFrame(set(obg.board.get_tiles()), obg.board.get_state(), obg.board.fixed_tiles)
        must, can = obg.must_can_move(stack_frame, Direction.W)
        self.assertTrue(sorted([(tile.y, tile.x) for tile in must]) == sorted([(24, 12), (24, 13), (15, 11)]))
        self.assertTrue(sorted([(tile.y, tile.x) for tile in can])
                        == sorted([(13, 20), (9, 10), (11, 9), (10, 11)]))

    def test_iterate_original_boards(self):
        test_instance = read_instance("instances/must_can_move_only_up_move_legal.json")
        obg = OriginalBoardGenerator(test_instance.initial_state)
        board = obg.board
        hashes = set()
        i = 0
        for _ in obg.iterate_original_board_positions():
            h = hash(board)
            self.assertTrue(h not in hashes)
            hashes.add(h)
            i += 1
        self.assertTrue(i == 24)


