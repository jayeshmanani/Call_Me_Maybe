from typing import Protocol

from src.vocab import TokenClassifier
from .json_state import JsonState, JsonStateMachine
from .mask import legal_token_ids, mask_logits


class LogitSource(Protocol):
    def get_logits_from_input_ids(self, input_ids: list[int]) -> list[float]:
        ...


def argmax(values: list[float]) -> int:
    best_index = 0
    best_value = values[0]
    for i, v in enumerate(values):
        if v > best_value:
            best_value = v
            best_index = i
    return best_index


def constrained_generate(
    model: LogitSource,
    prompt_ids: list[int],
    clf: TokenClassifier,
    max_tokens: int = 200,
    max_string_chars: int = 60,
) -> list[int]:
    state_machine = JsonStateMachine()
    current_ids = list(prompt_ids)
    chars_in_current_string = 0
    generated_ids: list[int] = []
    reached_done = False

    for _ in range(max_tokens):
        if state_machine.state == JsonState.DONE:
            reached_done = True
            break
        logits = model.get_logits_from_input_ids(current_ids)
        allowed = legal_token_ids(
            state_machine.state,
            clf,
            chars_in_current_string=chars_in_current_string,
            max_string_chars=max_string_chars,
        )
        if not allowed:
            raise RuntimeError(
                f"No legal tokens in state {state_machine.state}; "
                "this indicates a bug in legal_token_ids()."
            )
        masked = mask_logits(logits, allowed)
        next_id = argmax(masked)
        generated_ids.append(next_id)

        current_ids.append(next_id)

        surface = clf.surface_of(next_id)
        for char in surface:
            state_machine.advance(char)
            
            if state_machine.state in (JsonState.IN_KEY_STRING, JsonState.IN_STRING_VALUE):
                chars_in_current_string += 1
            else:
                chars_in_current_string = 0

    if not reached_done:
        raise RuntimeError(
            f"Hit max_tokens={max_tokens} without completing the JSON object. "
            "Check the state machine for a stuck transition."
        )
    return generated_ids
