import math
from typing import Set

from src.vocab import TokenClassifier
from .json_state import JsonState


def legal_token_ids(
    state: JsonState,
    clf: TokenClassifier,
    chars_in_current_string: int = 0,
    max_string_chars: int = 500,
) -> Set[int]:
    if state == JsonState.START:
        tid = clf.token_id_for("{")
        return {tid} if tid is not None else set()
    return set()


def mask_logits(logits: list[float], allowed_ids: Set[int]) -> list[float]:
    return [
        value if token_id in allowed_ids else -math.inf
        for token_id, value in enumerate(logits)
    ]
