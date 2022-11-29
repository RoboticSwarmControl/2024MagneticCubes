import context
from typing import Iterator
from tiltmp.core.algorithms import *
import unittest

from tiltmp.core.build_order import get_blueprint_with_glue_types, building_order_with_glues

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

GLUE_RULES = GlueRules()
GLUE_RULES.add_rule(("A", "B"))
GLUE_RULES.add_rule(("B", "C"))
GLUE_RULES.add_rule(("C", "C"))
yellow = Glues("A", "A", "A", "A")
red = Glues("B", "B", "B", "B")
green = Glues("B", "B", "C", "C")


class TestBluePrintFunctions(unittest.TestCase):

    def test_get_blueprint_with_glue_types_simple(self):

        tiles = []
        self.assertTrue(get_blueprint_with_glue_types(COMPLEX, tiles, GLUE_RULES) is None)

        tiles = [Tile(glues=yellow) for _ in range(10)]
        self.assertTrue(get_blueprint_with_glue_types(COMPLEX, tiles, ReflexiveGlueRules()) is not None)
        self.assertTrue(get_blueprint_with_glue_types(TILE, tiles, ReflexiveGlueRules()) is not None)
        self.assertTrue(get_blueprint_with_glue_types(COMPLEX, tiles, GLUE_RULES) is None)

    def test_get_blueprint_with_glue_types_complex(self):
        tiles = [Tile(glues=yellow) for _ in range(3)] + [Tile(glues=red) for _ in range(3)] \
                + [Tile(glues=green)]
        self.assertTrue(get_blueprint_with_glue_types(COMPLEX, tiles, GLUE_RULES) is not None)

        tiles = [Tile(glues=yellow) for _ in range(5)] + [Tile(glues=red) for _ in range(1)] \
                + [Tile(glues=green)]

        self.assertTrue(get_blueprint_with_glue_types(COMPLEX, tiles, GLUE_RULES) is None)

    def test_is_connected_with_glues(self):
        glues = {
            (0, 0): yellow,
            (0, 1): green,
            (1, 0): red,
            (1, 1): yellow,
            (1, 2): red,
            (1, 3): yellow,
            (2, 1): red
        }
        self.assertTrue(is_connected_by_glues(glues, GLUE_RULES))
        glues[(1, 0)] = yellow
        self.assertFalse(is_connected_by_glues(glues, GLUE_RULES))
        glues[(1, 0)] = red
        glues.pop((1, 2))
        self.assertFalse(is_connected_by_glues(glues, GLUE_RULES))

    def test_building_order_with_glues(self):
        glues = {
            (0, 0): yellow,
            (0, 1): green,
            (1, 0): red,
            (1, 1): yellow,
            (1, 2): red,
            (1, 3): yellow,
            (2, 1): red
        }
        self.assertTrue(len(building_order_with_glues(glues, GLUE_RULES)) == len(glues))



if __name__ == '__main__':
    unittest.main()
