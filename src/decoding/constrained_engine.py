import math
from typing import Any, Dict, List, Protocol

from src.vocab import TokenClassifier


class LogitSource(Protocol):
    def get_logits_from_input_ids(self, input_ids: List[int]) -> List[float]:
        ...

    def encode(self, text: str) -> Any:
        ...


def force_feed(
    model: LogitSource,
    current_ids: List[int],
    generated_ids: List[int],
    literal_text: str,
) -> None:
    encoded = model.encode(literal_text)
    first_item = encoded[0]
    token_ids = (
        first_item.tolist() if hasattr(first_item, "tolist")
        else list(first_item)
    )
    current_ids.extend(token_ids)
    generated_ids.extend(token_ids)
    print(literal_text, end="", flush=True)


def get_masked_vals(
    allowed: set[int],
    logits: List[float],
) -> List[float]:
    return [
        v if i in allowed else -math.inf
        for i, v in enumerate(logits)
    ]


def generate_name(
    model: LogitSource,
    current_ids: List[int],
    generated_ids: List[int],
    clf: TokenClassifier,
    functions: List[Dict[str, Any]],
) -> str:
    candidate_names = [fn.get("name", "") for fn in functions]
    name_prefix = ""

    dummy_logits = model.get_logits_from_input_ids(current_ids)
    name_candidate_tokens = [
        t_id for t_id in range(len(dummy_logits))
        if clf.surface_of(t_id) and '"' not in clf.surface_of(t_id)
        and any(clf.surface_of(t_id) in name for name in candidate_names)
    ]

    for _ in range(50):
        if name_prefix in candidate_names:
            break
        logits = model.get_logits_from_input_ids(current_ids)
        allowed = {
            t_id for t_id in name_candidate_tokens
            if any(
                name.startswith(name_prefix + clf.surface_of(t_id))
                for name in candidate_names
            )
        }
        if not allowed:
            raise RuntimeError(f"No allowed tokens for prefix {name_prefix!r}")
        masked = get_masked_vals(allowed, logits)
        next_id = max(range(len(masked)), key=masked.__getitem__)
        current_ids.append(next_id)
        generated_ids.append(next_id)

        surface = clf.surface_of(next_id)
        print(surface, end="", flush=True)
        name_prefix += surface

    return name_prefix


def generate_value(
    model: LogitSource,
    current_ids: List[int],
    generated_ids: List[int],
    clf: TokenClassifier,
    param_type: str,
    max_string_chars: int = 100,
) -> None:
    """Generate value for given parameter type."""
    if param_type in ("boolean", "bool"):
        t_tok = model.encode("true")[0]
        f_tok = model.encode("false")[0]
        t_id = t_tok.tolist()[0] if hasattr(t_tok, "tolist") else t_tok[0]
        f_id = f_tok.tolist()[0] if hasattr(f_tok, "tolist") else f_tok[0]
        logits = model.get_logits_from_input_ids(current_ids)
        chosen_id = t_id if logits[t_id] > logits[f_id] else f_id
        current_ids.append(chosen_id)
        generated_ids.append(chosen_id)
        print("true" if chosen_id == t_id else "false", end="", flush=True)

    elif param_type in ("integer", "float", "number", "int"):
        digit_seen = False
        for _ in range(20):
            logits = model.get_logits_from_input_ids(current_ids)
            allowed = (
                clf.number_char_tokens
                if not digit_seen
                else set(range(len(logits)))
            )
            masked = get_masked_vals(allowed, logits)
            next_id = max(range(len(masked)), key=masked.__getitem__)
            if next_id not in clf.number_char_tokens:
                break
            current_ids.append(next_id)
            generated_ids.append(next_id)
            surface = clf.surface_of(next_id)
            print(surface, end="", flush=True)
            if any(c.isdigit() for c in surface):
                digit_seen = True

    else:
        string_tokens = set(clf.all_string_tokens)
        encoded_quote = model.encode('"')[0]
        quote_token = (
            encoded_quote.tolist()[0]
            if hasattr(encoded_quote, "tolist")
            else encoded_quote[0]
        )
        chars_gen = 0
        first_step_allowed = string_tokens
        max_step_allowed = {quote_token} | clf.tokens_containing_quote
        normal_step_allowed = string_tokens | max_step_allowed
        for _ in range(max_string_chars):
            logits = model.get_logits_from_input_ids(current_ids)
            if chars_gen == 0:
                step_allowed = first_step_allowed
            elif chars_gen >= max_string_chars:
                step_allowed = max_step_allowed
            else:
                step_allowed = normal_step_allowed

            masked = get_masked_vals(step_allowed, logits)
            next_id = max(range(len(masked)), key=masked.__getitem__)
            surface = clf.surface_of(next_id)

            if chars_gen == 0:
                surface = surface.lstrip()

            is_quote = (
                next_id == quote_token
                or next_id in clf.tokens_containing_quote
            )
            if is_quote:
                quote_idx = surface.find('"')
                if quote_idx > 0 and surface[quote_idx - 1] == '\\':
                    current_ids.append(next_id)
                    generated_ids.append(next_id)
                    print(surface, end="", flush=True)
                    chars_gen += len(surface)
                elif chars_gen > 0:
                    force_feed(
                        model, current_ids, generated_ids,
                        surface[:quote_idx + 1]
                    )
                    break
                else:
                    current_ids.append(next_id)
                    generated_ids.append(next_id)
                    print(surface, end="", flush=True)
                    chars_gen += len(surface)
            else:
                current_ids.append(next_id)
                generated_ids.append(next_id)
                print(surface, end="", flush=True)
                chars_gen += len(surface)


def constrained_generate(
    model: LogitSource,
    prompt_ids: List[int],
    clf: TokenClassifier,
    functions: List[Dict[str, Any]],
    max_string_chars: int = 100,
) -> List[int]:
    """Execute constrained generation loop for JSON function call."""
    if not functions:
        raise ValueError("Candidate functions definition must be provided.")

    current_ids = list(prompt_ids)
    generated_ids: List[int] = []

    force_feed(model, current_ids, generated_ids, '{\n  "name": "')
    name = generate_name(model, current_ids, generated_ids, clf, functions)
    force_feed(model, current_ids, generated_ids, '",\n  "parameters": {')

    chosen_fn = next((fn for fn in functions if fn.get("name") == name), None)
    if not chosen_fn:
        raise RuntimeError(f"Function {name!r} not found.")

    params_list = list(chosen_fn.get("parameters", {}).items())
    for i, (p_name, p_def) in enumerate(params_list):
        force_feed(model, current_ids, generated_ids, f'\n    "{p_name}": ')
        if isinstance(p_def, dict):
            p_type = p_def.get("type", "")
        else:
            p_type = getattr(p_def, "type", "")
        if p_type in ("string", "str"):
            force_feed(model, current_ids, generated_ids, '"')

        generate_value(
            model, current_ids, generated_ids, clf, p_type,
            max_string_chars=max_string_chars
        )

        if i < len(params_list) - 1:
            force_feed(model, current_ids, generated_ids, ",")

    force_feed(model, current_ids, generated_ids, "\n  }\n}")
    print()

    return generated_ids
