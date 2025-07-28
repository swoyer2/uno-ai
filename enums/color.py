from enum import Enum

# enum of colors, use as Color.BLUE etc.
class Color(Enum):
    BLUE = 1
    YELLOW = 2
    RED = 3
    GREEN = 4
    WILD = 5

    def __str__(self) -> str:
        return self.name.capitalize()