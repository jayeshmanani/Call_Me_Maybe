import math
from typing import Set

from src.vocab import TokenClassifier
from .json_state import JsonState, JsonStateMachine


def legal_token_ids(
    state_machine: JsonStateMachine,
    clf: TokenClassifier,
    chars_in_current_string: int = 0,
    max_string_chars: int = 500,
) -> Set[int]:
    state = state_machine.state
    allowed: Set[int] = set()

    in_string = state in (JsonState.IN_KEY_STRING, JsonState.IN_STRING_VALUE)
    if in_string and chars_in_current_string < max_string_chars:
        allowed.update(clf.all_string_tokens)

    valid_first_chars_non_ws = set()
    if not in_string:
        if state == JsonState.START:
            valid_first_chars_non_ws.add("{")
            valid_first_chars_non_ws.add("[")
        elif state == JsonState.EXPECT_KEY_OPEN:
            valid_first_chars_non_ws.add('"')
            valid_first_chars_non_ws.add("}")
        elif state == JsonState.EXPECT_COLON:
            valid_first_chars_non_ws.add(":")
        elif state in (
            JsonState.EXPECT_VALUE_OPEN,
            JsonState.EXPECT_ELEMENT_OPEN,
        ):
            valid_first_chars_non_ws.add('"')
            valid_first_chars_non_ws.update("0123456789.-")
            valid_first_chars_non_ws.add("{")
            valid_first_chars_non_ws.add("[")
            if state == JsonState.EXPECT_ELEMENT_OPEN:
                valid_first_chars_non_ws.add("]")
        elif state == JsonState.AFTER_VALUE:
            valid_first_chars_non_ws.add(",")
            valid_first_chars_non_ws.add("}")
        elif state == JsonState.AFTER_ELEMENT:
            valid_first_chars_non_ws.add(",")
            valid_first_chars_non_ws.add("]")
        elif state == JsonState.IN_NUMBER_VALUE:
            valid_first_chars_non_ws.update("0123456789.-")
            valid_first_chars_non_ws.add(",")
            valid_first_chars_non_ws.add("}")
            valid_first_chars_non_ws.add("]")
        elif state == JsonState.DONE:
            pass

    if in_string:
        candidates = clf.tokens_containing_quote
    else:
        candidates = list(clf.whitespace_tokens)
        for char in valid_first_chars_non_ws:
            candidates.extend(clf.tokens_by_first_non_ws.get(char, []))

    temp_sm = JsonStateMachine()
    in_str_states = (JsonState.IN_KEY_STRING, JsonState.IN_STRING_VALUE)
    for token_id in candidates:
        surface = clf.surface_of(token_id)
        if not surface:
            continue

        temp_sm.state = state
        temp_sm.stack = list(state_machine.stack)
        current_chars = chars_in_current_string
        valid = True

        for char in surface:
            if temp_sm.state in in_str_states:
                if current_chars >= max_string_chars:
                    if char != '"':
                        valid = False
                        break
            try:
                temp_sm.advance(char)
            except ValueError:
                valid = False
                break

            if temp_sm.state in in_str_states:
                current_chars += 1
            else:
                current_chars = 0

        if valid:
            allowed.add(token_id)

    return allowed


def mask_logits(logits: list[float], allowed_ids: Set[int]) -> list[float]:
    return [
        value if token_id in allowed_ids else -math.inf
        for token_id, value in enumerate(logits)
    ]
