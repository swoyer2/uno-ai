from enums.color import Color
from enums.card_type import CardType

class Card:
    def __init__(self, color: Color, card_type: CardType) -> None:
        self.color = color
        self.card_type = card_type
    
    def __str__(self) -> str:
        if self.card_type == CardType.WILD or self.card_type == CardType.WILD_DRAW_FOUR:
            return f"{str(self.card_type)}"
        return f"{str(self.color)} {str(self.card_type)}"
    
    # Used for wildcards
    def set_color(self, color: Color) -> None:
        self.color = color

    def playable(self, previous_card: "Card", draw_debt: bool) -> bool:
        """ 
        Returns if card is playable given the previous card and if there is a "draw_debt" meaning a +2 or +4
        has been played previously and nobody has drawn the cards yet (due to stacking or being the next player)
        """
        if draw_debt:
            # stacking draw 2s
            if previous_card.card_type == CardType.DRAW_TWO and self.card_type != CardType.DRAW_TWO:
                return False
            
            # stacking draw 4s
            if previous_card.card_type == CardType.WILD_DRAW_FOUR and self.card_type != CardType.WILD_DRAW_FOUR:
                return False

        if self.color == previous_card.color:
            return True
        if self.card_type == previous_card.card_type:
            return True
        if self.card_type == CardType.WILD or self.card_type == CardType.WILD_DRAW_FOUR:
            return True
        return False