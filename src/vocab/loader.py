import json
from pathlib import Path


def load_vocab(vocab_path: str | Path) -> dict[int, str]:
    with open(vocab_path, "r", encoding="utf-8") as f:
        token_to_id: dict[str, int] = json.load(f)

    return {token_id: token_str for token_str, token_id in token_to_id.items()}


def token_surface(token_str: str) -> str:
    return token_str.replace("\u0120", " ").replace("\u010a", "\n")
