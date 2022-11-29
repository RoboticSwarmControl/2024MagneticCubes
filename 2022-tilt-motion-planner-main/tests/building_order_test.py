import os.path

import context
from tiltmp.core.algorithms import *
import unittest


COMPLEX = {
    (0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (1, 3), (2, 1)
}
LINE = {(0, 0), (1, 0), (2, 0)}
DISCONNECTED = {(0, 0), (0, 2)}
TILE = {(0, 0)}


class TestBuildOrder(unittest.TestCase):

    def test_is_connected(self):
        self.assertTrue(is_connected(TILE))
        self.assertTrue(is_connected(COMPLEX))
        self.assertFalse(is_connected(DISCONNECTED))

    def test_is_convex(self):
        self.assertTrue(is_convex(TILE, (0, 0)))
        self.assertTrue(is_convex(COMPLEX, (0, 0)))
        self.assertFalse(is_convex(LINE, (1, 0)))

    def test_building_order(self):
        for shape in set(), TILE, LINE, COMPLEX:
            bo = building_order(shape)
            s = set()
            for t in bo:
                s.add(t)
                self.assertTrue(is_convex(s, t))
                self.assertTrue(is_connected(s))
            self.assertTrue(s == shape)


if __name__ == '__main__':
    unittest.main()
