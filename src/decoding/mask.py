import math
from typing import Set, Iterable

from src.vocab import TokenClassifier
from .json_state import JsonState, JsonStateMachine


def allowed_next_chars_for_prefix(
    prefix: str, allowed_strings: Iterable[str]
) -> Set[str]:
    next_chars: Set[str] = set()
    for s in allowed_strings:
        if s.startswith(prefix):
            if len(s) > len(prefix):
                next_chars.add(s[len(prefix)])
            elif len(s) == len(prefix):
                next_chars.add('"')
    return next_chars


def legal_token_ids(
    state_machine: JsonStateMachine,
    clf: TokenClassifier,
    chars_in_current_string: int = 0,
    max_string_chars: int = 500,
) -> Set[int]:
    state = state_machine.state
    allowed: Set[int] = set()

    is_constrained_string = False
    allowed_next_chars: Set[str] = set()

    if state == JsonState.IN_KEY_STRING:
        if len(state_machine.path) == 1 and state_machine.path[0] == "":
            is_constrained_string = True
            allowed_next_chars = allowed_next_chars_for_prefix(
                state_machine.current_key_accum, ("name", "parameters")
            )
        elif (
            state_machine.inside_parameters_object
            and state_machine.path[-1] == "parameters"
        ):
            is_constrained_string = True
            allowed_next_chars = allowed_next_chars_for_prefix(
                state_machine.current_key_accum,
                state_machine.allowed_parameter_keys,
            )
    elif state == JsonState.IN_STRING_VALUE:
        if (
            state_machine.current_key == "name"
            and len(state_machine.path) == 1
        ):
            is_constrained_string = True
            allowed_next_chars = allowed_next_chars_for_prefix(
                state_machine.current_value_accum,
                (func.name for func in state_machine.functions),
            )

    in_string = state in (JsonState.IN_KEY_STRING, JsonState.IN_STRING_VALUE)

    if (
        in_string
        and not is_constrained_string
        and chars_in_current_string < max_string_chars
    ):
        allowed.update(clf.all_string_tokens)

    candidates: list[int] = []
    if in_string:
        if is_constrained_string:
            for char in allowed_next_chars:
                candidates.extend(clf.tokens_by_first_non_ws.get(char, []))
        candidates.extend(clf.tokens_containing_quote)
    else:
        valid_first_chars_non_ws = set()
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
            param_type = state_machine.active_parameter_type
            if param_type == "number":
                valid_first_chars_non_ws.update("0123456789.-")
            elif param_type == "string":
                valid_first_chars_non_ws.add('"')
            else:
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

        candidates.extend(clf.whitespace_tokens)
        for char in valid_first_chars_non_ws:
            candidates.extend(clf.tokens_by_first_non_ws.get(char, []))

    candidates = list(set(candidates))

    in_str_states = (JsonState.IN_KEY_STRING, JsonState.IN_STRING_VALUE)
    for token_id in candidates:
        surface = clf.surface_of(token_id)
        if not surface:
            continue

        temp_sm = state_machine.clone()
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
