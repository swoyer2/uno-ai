from uno import Game
from uno import GameSaver
from pathlib import Path

def main():
    uno_game = Game()
    uno_game.setup_game()

    # Setup saver
    save_path = Path("saved_games/current_game.yaml")
    save_path.parent.mkdir(exist_ok=True)
    game_saver = GameSaver(uno_game, save_path)

    while not uno_game.is_game_over():
        current_player = uno_game.players[uno_game.whos_turn]
        available_cards = uno_game.get_playable_cards(current_player)
        available_card_indexes = [card_tuple[0] for card_tuple in available_cards]
        last_played_card = uno_game.played_cards[-1] if uno_game.played_cards else None

        # Strings
        options = "\n".join(f"{card_tuple[0]}. {card_tuple[1]}" for card_tuple in available_cards)
        draw_option = f"-1. Draw {uno_game.draw_debt if uno_game.draw_debt != 0 else 1}"

        print(f"Player {uno_game.whos_turn}, what do you want to do?")
        print(f"Last played card: {last_played_card}")
        print(f"Your cards: {', '.join(str(card) for card in current_player.cards)}\n")
        print(
            f"""Available options:
{options}
{draw_option}"""
        )

        try:
            player_choice = int(input())
            while player_choice not in available_card_indexes + [-1]:
                player_choice = int(input())
        except ValueError:
            print("Please enter a number.")
            continue

        if player_choice == -1:
            uno_game.play(None)  # Draw card
            game_saver.save_move(None)
        else:
            uno_game.play(current_player.cards[player_choice])
            game_saver.save_move(player_choice)

        game_saver.export()  # Save game after each move

if __name__ == "__main__":
    main()
