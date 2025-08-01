from enum import Enum

# enum of CardType
class CardType(Enum):
    ZERO = "Zero"
    ONE = "One"
    TWO = "Two"
    THREE = "Three"
    FOUR = "Four"
    FIVE = "Five"
    SIX = "Six"
    SEVEN = "Seven"
    EIGHT = "Eight"
    NINE = "Nine"
    SKIP = "Skip"
    REVERSE = "Reverse"
    DRAW_TWO = "Draw_two"
    WILD = "Wild"
    WILD_DRAW_FOUR = "Wild_draw_four"

    def __str__(self) -> str:
        return self.value
