from .player import Player
from .deck import Deck
from .card import Card

from .enums.card_type import CardType
from .enums.color import Color

class Game:
    def __init__(self, player_count: int = 6) -> None:
        self.deck: Deck = Deck()
        self.players: list[Player] = [Player() for i in range(player_count)]
        self.played_cards: list[Card] = []
        self.whos_turn: int = 0
        self.clockwise_turn: bool = True # Normally goes clockwise for turns, unless reverse card then it flips
        self.draw_debt: int = 0 # The number of cards to draw for 


    def __repr__(self) -> str:
        return "\n ".join(f"Player {i}: [{hand}]" for i, hand in enumerate(self.players))
    
    def __smart_draw(self, amount_to_draw: int = 1) -> list[Card]:
        """
        Draws card/s up until deck runs out, then shuffles played_cards and sets that as deck, then
        continues to draw cards until amount_to_draw = len(cards_to_draw)
        """
        cards_to_draw: list[Card] = []
        while len(cards_to_draw) != amount_to_draw:
            if self.deck.cards:
                cards_to_draw.append(*self.deck.draw())
            else: # Remake deck
                self.deck.cards = self.played_cards
                self.played_cards = []
                self.deck.shuffle()

        return cards_to_draw
    
    def setup_game(self) -> None:
        # Starting game
        self.deck.shuffle()
        self.deal_cards()

    def play(self, played_card: Card | None) -> None:
        """
        Handles the current player's action of playing a card or drawing from the deck.

        If `played_card` is None, the player draws cards (1 by default unless draw debt exists).
        If a valid card is played, it's added to the pile and card effects (Skip, Reverse, Draw) are handled.

        Args:
            played_card (Card | None): The card being played, or None if the player is drawing.
        """
        current_player: Player = self.players[self.whos_turn]

        if not played_card: # This means the player chose to/had to draw
            if not self.draw_debt: # If 0 cards are needed to be drawn (nobody played a draw 2 or draw 4), then set the draw amount to 1
                self.draw_debt = 1

            cards_to_draw: list[Card] = self.__smart_draw(self.draw_debt)
            current_player.recieve_cards(cards_to_draw)
            self.draw_debt = 0

        else:
            self.played_cards.append(played_card)
            current_player.remove_card(played_card)

            if played_card.card_type == CardType.SKIP:
                self.__skip()
            
            elif played_card.card_type == CardType.REVERSE:
                self.__reverse()

            elif played_card.card_type == CardType.WILD:
                played_card.color = self.__get_color_input()
            
            elif played_card.card_type == CardType.WILD_DRAW_FOUR:
                played_card.color = self.__get_color_input()
                self.draw_debt += 4
            
            elif played_card.card_type == CardType.DRAW_TWO:
                self.draw_debt += 2

        self.__set_whos_turn()
    
    def get_playable_cards(self, player: Player) -> list[tuple[int, Card]]:
        """ Returns a list of indexes and card types for available cards """
        if not self.played_cards:
            # If no card has been played yet, all cards are playable
            return list(enumerate(player.cards))
        
        last_played_card = self.played_cards[-1]
        playable_cards: list[tuple[int, Card]] = [
            (i, card) for i, card in enumerate(player.cards)
            if card.playable(last_played_card, True if self.draw_debt else False)
        ]
        return playable_cards

    def __get_color_input(self) -> Color:
        print("Choose color, Blue: 1, Yellow: 2, Red: 3, Green: 4")
        user_input = input()
        while user_input not in {'1', '2', '3', '4'}:
           user_input = input()
        
        color_map = {1: Color.BLUE, 2: Color.YELLOW, 3: Color.RED, 4: Color.GREEN}

        return color_map[int(user_input)]

    def __set_whos_turn(self) -> None:
        if self.clockwise_turn:
            self.whos_turn += 1
        else:
            self.whos_turn -= 1
        
        self.whos_turn %= len(self.players)

    def __skip(self) -> None:
        self.__set_whos_turn()

    def __reverse(self) -> None:
        self.clockwise_turn = not self.clockwise_turn
    
    def is_game_over(self) -> bool:
        for player in self.players:
            if len(player.cards) == 0:
                return True
        return False

    def deal_cards(self) -> None:
        NUM_CARDS_TO_DEAL = 7
        current_player_to_deal: int = 0
        for i in range(NUM_CARDS_TO_DEAL * len(self.players)):
            self.players[current_player_to_deal].recieve_cards(self.deck.draw())
            current_player_to_deal = (current_player_to_deal + 1) % len(self.players)
    
    def get_cards(self, player: Player) -> list[Card]:
        """ Get cards in hand for a specified player"""
        return player.cards