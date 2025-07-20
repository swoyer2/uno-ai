from enums.color import Color
from enums.card_type import CardType

class Card:
    def __init__(self, color: Color, card_type: CardType) -> None:
        self.color = color
        self.card_type = card_type
    
    # Used for wildcards
    def set_color(self, color: Color) -> None:
        self.color = color

    def playable(self, previous_card: "Card") -> bool:
        if self.color == previous_card.color:
            return True
        if self.card_type == previous_card.card_type:
            return True
        if self.card_type == CardType.WILD or self.card_type == CardType.WILD_DRAW_FOUR:
            return True
        return False