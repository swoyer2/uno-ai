import torch
import numpy as np
import yaml
from pathlib import Path

# Load config and card/action mappings
CONFIG_PATH = Path(__file__).resolve().parent / "../config/config.yaml"
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

ACTION_SPACE = config["ACTIONS"]
CARD_TO_INDEX = {card: i for i, card in enumerate(ACTION_SPACE)}
print(len(CARD_TO_INDEX))
INDEX_TO_CARD = {i: card for i, card in enumerate(ACTION_SPACE)}
NUM_CARD_TYPES = len(CARD_TO_INDEX)

def card_to_one_hot(card: str | None) -> np.ndarray:
    one_hot = np.zeros(NUM_CARD_TYPES, dtype=np.float32)
    if card in CARD_TO_INDEX:
        one_hot[CARD_TO_INDEX[card]] = 1.0
    return one_hot

def build_legal_mask(legal_cards: list[str | None]) -> torch.BoolTensor:
    mask = torch.zeros(NUM_CARD_TYPES + 1, dtype=torch.bool)  # +1 for DRAW
    
    for card in legal_cards:
        if card is None:
            mask[-1] = True  # last index = draw
        elif card == "WILD":
            for color in {"RED", "YELLOW", "BLUE", "GREEN"}:
                key = f"{color}_WILD"
                if key in CARD_TO_INDEX:
                    mask[CARD_TO_INDEX[key]] = True
        elif card == "WILD_DRAW_FOUR":
            for color in {"RED", "YELLOW", "BLUE", "GREEN"}:
                key = f"{color}_WILD_DRAW_FOUR"
                if key in CARD_TO_INDEX:
                    mask[CARD_TO_INDEX[key]] = True
        elif card in CARD_TO_INDEX:
            mask[CARD_TO_INDEX[card]] = True

    return mask

def build_state_tensor(
    your_hand: list[str],
    last_card: str,
    other_hand_sizes: list[int],
    your_history: list[str],
    others_history: list[list[str]],
    clockwise_turn: bool,
    max_history_len: int = 5,
) -> torch.Tensor:
    vec = []

    # Hand sizes (self and others), normalized
    vec.append(min(len(your_hand), 20) / 20.0)
    vec += [min(s, 20) / 20.0 for s in other_hand_sizes]

    # Your hand: count of each card type
    hand_counts = np.zeros(NUM_CARD_TYPES, dtype=np.float32)

    for card in your_hand:
        if card == "WILD":
            for color in {"RED", "YELLOW", "BLUE", "GREEN"}:
                key = color + "_WILD"
                if key in CARD_TO_INDEX:
                    hand_counts[CARD_TO_INDEX[key]] += 1.0
        elif card == "WILD_DRAW_FOUR":
            for color in {"RED", "YELLOW", "BLUE", "GREEN"}:
                key = color + "_WILD_DRAW_FOUR"
                if key in CARD_TO_INDEX:
                    hand_counts[CARD_TO_INDEX[key]] += 1.0
        elif card in CARD_TO_INDEX:
            hand_counts[CARD_TO_INDEX[card]] += 1.0

    vec += hand_counts.tolist()

    # Last played card (one-hot)
    vec += card_to_one_hot(last_card).tolist()

    # Your play history (padded)
    padded_history = (your_history + [None] * max_history_len)[:max_history_len]
    for card in padded_history:
        vec += card_to_one_hot(card).tolist()

    # Each opponent’s play history (also padded)
    for history in others_history:
        padded = (history + [None] * max_history_len)[:max_history_len]
        for card in padded:
            vec += card_to_one_hot(card).tolist()
    
    vec.append(float(clockwise_turn)) # The current direction of play

    return torch.tensor(vec, dtype=torch.float32)
