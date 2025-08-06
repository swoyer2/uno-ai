import sqlite3
import json
from pathlib import Path
import torch
import time

DB_PATH = Path("uno_agents.db")

def safe_execute(statement, params, retries=5, delay=0.1):
    for attempt in range(retries):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                c = conn.cursor()
                c.execute(statement, params)
            return
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                time.sleep(delay * (2 ** attempt))  # exponential backoff
            else:
                raise

def init_db():
    """Initialize the SQLite database with necessary tables."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")

        c = conn.cursor()

        c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            round_num INTEGER,
            game_id INTEGER,
            winner_agent_id TEXT
        );
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS agent_scores (
            agent_id TEXT,
            round_num INTEGER,
            score INTEGER,
            PRIMARY KEY(agent_id, round_num)
        );
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS agent_snapshots (
            agent_id TEXT,
            round_num INTEGER,
            weights_json TEXT,
            metadata_json TEXT,
            PRIMARY KEY(agent_id, round_num)
        );
        """)

def serialize_state_dict(state_dict: dict) -> dict:
    """Convert PyTorch state dict to JSON-serializable format."""
    return {k: v.tolist() if isinstance(v, torch.Tensor) else v for k, v in state_dict.items()}

def save_game_result(round_num: int, game_id: int, winner_agent_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        safe_execute("""
            INSERT INTO games (round_num, game_id, winner_agent_id)
            VALUES (?, ?, ?)
        """, (round_num, game_id, winner_agent_id))

def save_agent_score(agent_id: str, round_num: int, score: int):
    with sqlite3.connect(DB_PATH) as conn:
        safe_execute("""
            INSERT OR REPLACE INTO agent_scores (agent_id, round_num, score)
            VALUES (?, ?, ?)
        """, (agent_id, round_num, score))

def save_agent_snapshot(agent_id: str, round_num: int, weights_dict: dict, metadata_dict: dict):
    serializable_weights = serialize_state_dict(weights_dict)
    with sqlite3.connect(DB_PATH) as conn:
        safe_execute("""
            INSERT OR REPLACE INTO agent_snapshots (
                agent_id, round_num, weights_json, metadata_json
            ) VALUES (?, ?, ?, ?)
        """, (
            agent_id,
            round_num,
            #json.dumps(serializable_weights), # Turned this off for now because it was a lot of storage
            json.dumps({}),
            json.dumps(metadata_dict)
        ))

def get_top_agents(round_num: int, top_k: int):
    for attempt in range(5):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                c = conn.cursor()
                c.execute("""
                    SELECT agent_id, score FROM agent_scores
                    WHERE round_num = ?
                    ORDER BY score DESC
                    LIMIT ?
                """, (round_num, top_k))
                return c.fetchall()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < 4:
                time.sleep(0.1 * (2 ** attempt))
            else:
                raise