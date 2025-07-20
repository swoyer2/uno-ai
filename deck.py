import yaml
from pathlib import Path
import random

from card import Card
from enums.color import Color
from enums.card_type import CardType

class Deck:
    def __init__(self) -> None:
        self.cards: list[Card] = []
        
        self.__init_deck()
    
    def __init_deck(self) -> None:
        config_path = Path("config/config.yaml")

        with config_path.open("r") as f:
            config = yaml.safe_load(f)
        
        for color in config["CARDS"]:
            for card_type in config["CARDS"][color]:
                card_to_add = Card(Color[color], CardType[card_type])
                amount_to_add = config["CARDS"][color][card_type]
                self.add_cards(card_to_add, amount_to_add)
    
    def add_cards(self, card: Card, amount_to_add: int) -> None:
        for i in range(amount_to_add):
            self.cards.append(card)

    def shuffle(self) -> None:
        random.shuffle(self.cards)
    
    def draw(self, amount=1) -> list[Card]:
        cards_to_return = []
        for i in range(amount):
            cards_to_return.append(self.cards.pop(0))
        return cards_to_return
