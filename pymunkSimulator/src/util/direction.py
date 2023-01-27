from enum import Enum

class Direction(Enum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def __str__(self) -> str:
        return self.name

    def inv(self):
        return Direction((self.value + 2) % 4)