from uno import Game, GameSaver, Player, Color
from agent import UnoAgent
from input_encoding import build_state_tensor, CARD_TO_INDEX, INDEX_TO_CARD
from db_utils import init_db, save_game_result, save_agent_score, save_agent_snapshot
import uuid  # For generating unique agent IDs

import time
from pathlib import Path
from typing import List
import random
from tqdm import tqdm

DRAW_ACTION = "DRAW"  # Your global draw action
DRAW_INDEX = CARD_TO_INDEX[DRAW_ACTION]  # Index of the draw action in action space

def get_seat_position(player: Player, game: Game) -> int:
    return game.players.index(player)

def map_hand_card_to_action_indices(card_str: str) -> list[int]:
    """
    Map a card string to one or more global action indices.
    Wild cards map to all colored variants.
    """
    indices = []
    if card_str == "WILD":
        for color in ["RED", "YELLOW", "BLUE", "GREEN"]:
            key = f"{color}_WILD"
            if key in CARD_TO_INDEX:
                indices.append(CARD_TO_INDEX[key])
    elif card_str == "WILD_DRAW_FOUR":
        for color in ["RED", "YELLOW", "BLUE", "GREEN"]:
            key = f"{color}_WILD_DRAW_FOUR"
            if key in CARD_TO_INDEX:
                indices.append(CARD_TO_INDEX[key])
    else:
        if card_str in CARD_TO_INDEX:
            indices.append(CARD_TO_INDEX[card_str])
    return indices

def get_legal_action_indices(player: Player, game: Game) -> list[int]:
    """
    Return a sorted list of legal global action indices for the player,
    including the draw action index.
    """
    available_cards = game.get_playable_cards(player)
    legal_action_indices = set()

    for _, card in available_cards:
        card_str = str(card).upper()
        indices = map_hand_card_to_action_indices(card_str)
        legal_action_indices.update(indices)

    if not legal_action_indices or len(player.cards) < 15: # Only let agents draw cards if they have no card to play or less than 15 cards in hand
        legal_action_indices.add(DRAW_INDEX)
    
    return sorted(legal_action_indices)

def map_action_index_to_hand_card(action_idx: int, player: Player) -> int | None:
    """
    Given a global action index, find the first matching card index in player's hand,
    or None if it's the draw action.
    """
    if action_idx == DRAW_INDEX:
        return None

    for hand_idx, card in enumerate(player.cards):
        card_str = str(card).upper()
        possible_indices = map_hand_card_to_action_indices(card_str)
        if action_idx in possible_indices:
            return hand_idx
    raise KeyError

def get_player_action(player: Player, game: Game, agent: UnoAgent) -> tuple[int | None, Color | None]:
    your_hand = [str(card) for card in player.cards]
    last_card = str(game.played_cards[-1]) if game.played_cards else "None"

    player_seat = get_seat_position(player, game)
    other_hand_sizes = [
        len(game.players[(player_seat + i) % 4].cards)
        for i in range(1, 4)
    ]

    your_history = [str(card) for card in game.history[player_seat]]
    opponent_ids = [(player_seat + i) % 4 for i in range(1, 4)]
    others_history = [
        [str(card) for card in game.history[pid]] for pid in opponent_ids
    ]

    legal_action_indices = get_legal_action_indices(player, game)

    state_tensor = build_state_tensor(
        your_hand=your_hand,
        last_card=last_card,
        other_hand_sizes=other_hand_sizes,
        your_history=your_history,
        others_history=others_history,
        clockwise_turn=game.clockwise_turn
    )

    chosen_action_idx = agent.decide(state_tensor, legal_action_indices)

    chosen_card_str = INDEX_TO_CARD[chosen_action_idx]
    chosen_color = None
    if "WILD" in chosen_card_str:
        color_str = chosen_card_str.split('_')[0]  # e.g. "RED_WILD" -> "RED"
        chosen_color = Color[color_str]  # get enum by key

    hand_card_index = map_action_index_to_hand_card(chosen_action_idx, player)

    # Return hand index or -1 for draw, plus color choice (None if no color)
    return (hand_card_index if hand_card_index is not None else -1, chosen_color)

NUM_AGENTS = 100
AGENTS_PER_GAME = 4
GAMES_PER_ROUND = 1000
ROUNDS = 500
TOP_K = 25
SAVE_DIR = Path("saved_games")

def play_game(agents: List[UnoAgent], game_id: int, round_num: int, save_game: bool = False) -> int | None:
    uno_game = Game()
    uno_game.deck.shuffle()

    game_saver = None
    if save_game:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        save_path = SAVE_DIR / f"round_{round_num}_game_{game_id}_{timestamp}.yaml"
        game_saver = GameSaver(uno_game, save_path)
        game_saver.export()
        
    uno_game.deal_cards()
    uno_game.played_cards.append(uno_game.deck.cards.pop())

    game_length = 0

    while not uno_game.is_game_over():
        current_player = uno_game.players[uno_game.whos_turn]
        agent = agents[uno_game.whos_turn]

        card_idx, color_choice = get_player_action(current_player, uno_game, agent)

        if card_idx == -1:
            uno_game.play(None)
            if game_saver:
                game_saver.save_move(None)
        else:
            played_card = current_player.cards[card_idx]
            uno_game.play(played_card, color_input=color_choice)
            if game_saver:
                game_saver.save_move(card_idx)

        game_length += 1
    
    if game_saver:
        game_saver.export()
    
    return uno_game.get_winner()

def evolve_agents():
    init_db()  # Ensure tables exist

    agents = [UnoAgent(agent_id=str(uuid.uuid4()), parent_id=None) for _ in range(NUM_AGENTS)]
    for agent in agents:
        agent.create_name(parent_last_name=None)
    scores = [0] * NUM_AGENTS
    games_per_agent = (GAMES_PER_ROUND * AGENTS_PER_GAME) // NUM_AGENTS
    assert GAMES_PER_ROUND % (NUM_AGENTS // AGENTS_PER_GAME) == 0, "GAMES_PER_ROUND must be divisible by (NUM_AGENTS / AGENTS_PER_GAME)"

    games_per_round = NUM_AGENTS // AGENTS_PER_GAME
    rounds_needed = GAMES_PER_ROUND // games_per_round

    for round_num in range(ROUNDS):
        print(f"\n=== Round {round_num + 1} ===")
        full_schedule: list[list[int]] = []

        for _ in range(rounds_needed):
            indices = list(range(NUM_AGENTS))
            random.shuffle(indices)
            for i in range(0, NUM_AGENTS, AGENTS_PER_GAME):
                game = indices[i:i + AGENTS_PER_GAME]
                full_schedule.append(game)

        assert len(full_schedule) == GAMES_PER_ROUND

        for game_id, agent_indices in enumerate(tqdm(full_schedule, desc=f"Round {round_num + 1}", unit="game")):
            game_agents = [agents[i] for i in agent_indices]
            for agent in game_agents:
                agent.games_played += 1
            save_game = game_id < 1
            winner_idx = play_game(game_agents, game_id, round_num, save_game)
            
            if winner_idx != None:
                global_winner_idx = agent_indices[winner_idx]
                winner_agent = agents[global_winner_idx]
                scores[global_winner_idx] += 1
                winner_agent.wins += 1

                # Save to DB
                save_game_result(round_num, game_id, winner_agent.agent_id)
            else:
                save_game_result(round_num, game_id, "None")

        # Log scores and snapshots
        for agent, score in zip(agents, scores):
            save_agent_score(agent.agent_id, round_num, score)
            save_agent_snapshot(agent.agent_id, round_num, agent.serialize_weights(), agent.metadata())

        # Selection
        agent_score_pairs = list(zip(agents, scores))
        agent_score_pairs.sort(key=lambda x: x[1], reverse=True)

        survivors = [a for a, _ in agent_score_pairs[:TOP_K]]

        score_counts = {}
        for score in scores:
            score_counts[score] = score_counts.get(score, 0) + 1
        print(f"\n[Round {round_num + 1} | Game {game_id + 1}] Score distribution:")
        for score in sorted(score_counts.keys(), reverse=True):
            print(f"  Score {score}: {score_counts[score]} agents")

        # Reproduce with mutation
        new_agents = survivors[:]
        while len(new_agents) < NUM_AGENTS:
            parent = random.choice(survivors)
            child = UnoAgent(agent_id=str(uuid.uuid4()), parent_id=parent.agent_id)
            child.load_state_dict(parent.state_dict())
            child.mutate(mutation_rate=0.1)
            child.create_name(parent_last_name=parent.last_name)
            new_agents.append(child)

        agents = new_agents
        scores = [0] * NUM_AGENTS

    return agents

if __name__ == "__main__":
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    final_agents = evolve_agents()