from player import Player
from deck import Deck

class Game:
    def __init__(self, player_count: int = 6) -> None:
        self.deck: Deck = Deck()
        self.players: list[Player] = [Player() for i in range(player_count)]