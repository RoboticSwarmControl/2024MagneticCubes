import context
from typing import Iterator
from tiltmp.core.algorithms import *
import unittest

COMPLEX = {
    (0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)
}
#  □ □
#  □ □ □
#    □
#    □

SHAPE1 = {
    (0, 0), (0, 1), (0, 2), (1, 0)
}
DOMINO = {(0, 0), (0, 1)}
LINE = {(0, 0), (1, 0), (2, 0)}
TILE = {(0, 0)}


class TestPackingFunctions(unittest.TestCase):

    def test_fits(self):
        self.assertTrue(fits(TILE, TILE))
        self.assertTrue(fits(COMPLEX, SHAPE1))
        self.assertFalse(fits(SHAPE1, COMPLEX))

    def test_get_packings(self):
        p = get_packings(DOMINO, TILE)
        self.assertIsInstance(p, Iterator)
        packings = list(p)
        self.assertTrue(len(packings) == len(DOMINO))
        self.assertTrue(set(packings) == DOMINO)
        packings = list(get_packings(DOMINO, DOMINO))
        self.assertTrue(packings == [(0, 0)])
        packings = list(get_packings(COMPLEX, SHAPE1))
        self.assertTrue(packings == [(1, 1)])
        self.assertFalse(list(get_packings(SHAPE1, COMPLEX)))
        packings = list(get_packings(COMPLEX, TILE))
        self.assertTrue(len(packings) == len(COMPLEX))

    def test_is_packable(self):
        self.assertTrue(is_packable(COMPLEX, [DOMINO, SHAPE1, TILE]))
        self.assertFalse(is_packable(COMPLEX, [DOMINO, TILE, TILE, SHAPE1]))
        self.assertFalse(is_packable(LINE, [DOMINO]))
        self.assertFalse(is_packable(LINE, [DOMINO, TILE]))

    def test_bigger_example(self):
        outer = set()
        for x in range(8):
            for y in range(8):
                outer.add((x, y))
        self.assertTrue(is_packable(outer, [SHAPE1] * 4))
        self.assertFalse(is_packable(outer, [COMPLEX] * 6))


if __name__ == '__main__':
    unittest.main()
