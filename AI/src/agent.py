import torch
import torch.nn as nn
from pathlib import Path
import random

class UnoAgent(nn.Module):
    def __init__(self, input_size=1347, hidden_size=64, output_size=61):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, output_size)
        )
        self.first_name = None
        self.last_name = None

    def forward(self, x):
        return self.net(x)

    def decide(self, state_tensor, legal_action_indices):
        with torch.no_grad():
            logits = self(state_tensor)  # shape: [action_space_size]

            # Create mask full of False (-inf for logits)
            mask = torch.full_like(logits, float('-inf'))

            # Copy logits for legal actions
            mask[legal_action_indices] = logits[legal_action_indices]

            # Pick the highest scoring legal action
            action = torch.argmax(mask).item()

        return action


    def mutate(self, mutation_rate=0.1):
        with torch.no_grad():
            for param in self.parameters():
                param += mutation_rate * torch.randn_like(param)
    
    def create_name(self, parent_last_name: str | None) -> None:
        names_dir = Path(__file__).parent.parent / "names"
        first_names_file = names_dir / "first-names.txt"
        last_names_file = names_dir / "last-names.txt"

        # Load first name
        with open(first_names_file, "r", encoding="utf-8") as f:
            first_names = [line.strip() for line in f if line.strip()]
        self.first_name = random.choice(first_names)

        # Load last name only if parent_last_name not given
        if parent_last_name:
            self.last_name = parent_last_name
        else:
            with open(last_names_file, "r", encoding="utf-8") as f:
                last_names = [line.strip() for line in f if line.strip()]
            self.last_name = random.choice(last_names)
