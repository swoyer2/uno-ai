from card import Card

class Player:
    def __init__(self) -> None:
        self.cards: list[Card] = []
    
    def recieve_cards(self, cards: list[Card]) -> None:
        self.cards += cards

    def remove_card(self, card: Card) -> None:
        self.cards.remove(card)