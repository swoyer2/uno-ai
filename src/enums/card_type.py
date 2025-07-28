from enum import Enum

# enum of CardType
class CardType(Enum):
    # Standard numbers
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9

    # Special cards
    SKIP = 10
    REVERSE = 11
    DRAW_TWO = 12
    WILD = 13
    WILD_DRAW_FOUR = 14

    def __str__(self) -> str:
        return self.name.capitalize()
