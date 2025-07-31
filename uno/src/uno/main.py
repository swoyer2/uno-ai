from .game import Game

def main():
    uno_game = Game()
    uno_game.setup_game()
    while not uno_game.is_game_over():
        current_player = uno_game.players[uno_game.whos_turn]
        avaiable_cards = uno_game.get_playable_cards(current_player)
        avaiable_card_indexes = [card_tuple[0] for card_tuple in avaiable_cards]
        last_played_card = uno_game.played_cards[-1] if len(uno_game.played_cards) else None
        # Strings
        options = "\n".join(f"{card_tuple[0]}. {card_tuple[1]}" for card_tuple in avaiable_cards)
        draw_option = f"-1. Draw {uno_game.draw_debt if uno_game.draw_debt != 0 else 1}"

        print(f"Player {uno_game.whos_turn}, what do you want to do?")
        print(f"Last played card: {last_played_card}")
        print(f"Your cards: {", ".join(str(card) for card in current_player.cards)}\n")
        print(
            f"""Available options:
{options}
{draw_option}"""
        )
        
        player_choice = int(input())
        while player_choice not in avaiable_card_indexes + [-1]:
            player_choice = int(input())
        
        if player_choice == -1:
            uno_game.play(None) # Draw card
        else:
            uno_game.play(current_player.cards[player_choice])

if __name__ == "__main__":
    main()