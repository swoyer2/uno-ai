from enum import Enum

# enum of colors, use as Color.BLUE etc.
class Color(Enum):
    RED = "Red"
    YELLOW = "Yellow"
    GREEN = "Green"
    BLUE = "Blue"
    WILD = "Wild"

    def __str__(self) -> str:
        return self.value