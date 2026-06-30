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
    allowed: Set[int] = set()
    
    if state not in (JsonState.IN_KEY_STRING, JsonState.IN_STRING_VALUE):
        allowed.update(clf.whitespace_tokens)
        
    if state == JsonState.START:
        tid = clf.token_id_for("{")
        if tid is not None: allowed.add(tid)
    elif state == JsonState.EXPECT_KEY_OPEN:
        for char in ['"', '}']:
            tid = clf.token_id_for(char)
            if tid is not None: allowed.add(tid)
    elif state == JsonState.IN_KEY_STRING:
        if chars_in_current_string < max_string_chars:
            allowed.update(clf.all_string_tokens)
        tid = clf.token_id_for('"')
        if tid is not None: allowed.add(tid)
    elif state == JsonState.EXPECT_COLON:
        tid = clf.token_id_for(':')
        if tid is not None: allowed.add(tid)
    elif state == JsonState.EXPECT_VALUE_OPEN:
        tid = clf.token_id_for('"')
        if tid is not None: allowed.add(tid)
        allowed.update(clf.number_tokens)
    elif state == JsonState.IN_STRING_VALUE:
        if chars_in_current_string < max_string_chars:
            allowed.update(clf.all_string_tokens)
        tid = clf.token_id_for('"')
        if tid is not None: allowed.add(tid)
    elif state == JsonState.IN_NUMBER_VALUE:
        allowed.update(clf.number_tokens)
        for char in [',', '}']:
            tid = clf.token_id_for(char)
            if tid is not None: allowed.add(tid)
    elif state == JsonState.AFTER_VALUE:
        for char in [',', '}']:
            tid = clf.token_id_for(char)
            if tid is not None: allowed.add(tid)
    elif state == JsonState.DONE:
        pass
    return allowed


def mask_logits(logits: list[float], allowed_ids: Set[int]) -> list[float]:
    return [
        value if token_id in allowed_ids else -math.inf
        for token_id, value in enumerate(logits)
    ]
