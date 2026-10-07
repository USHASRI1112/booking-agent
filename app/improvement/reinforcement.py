"""
reinforcement.py - loads and saves the learned rules (data/reinforcements.json).

This file is the agent's "memory" of lessons learned. main.py and the eval both read it.
"""
import json
from pathlib import Path

RULES_FILE = Path(__file__).resolve().parents[2] / "data" / "reinforcements.json"


def load_rules():
    if not RULES_FILE.exists():
        return []
    return json.loads(RULES_FILE.read_text())


def save_rules(rules):
    RULES_FILE.write_text(json.dumps(rules, indent=2))
