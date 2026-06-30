from pathlib import Path
from typing import Dict, Set

from .loader import load_vocab, token_surface


class TokenClassifier:
    _WHITESPACE_CHARS: frozenset[str] = frozenset(" \t\n\r")

    def __init__(self, id_to_token: Dict[int, str]) -> None:
        self._id_to_token = id_to_token
        self._build_sets()

    @classmethod
    def from_vocab_path(cls, vocab_path: str | Path) -> "TokenClassifier":
        return cls(load_vocab(vocab_path))

    def _build_sets(self) -> None:
        self.whitespace_tokens: Set[int] = set()
        self.all_string_tokens: Set[int] = set()
        self.tokens_containing_quote: list[int] = []
        self.tokens_by_first_non_ws: Dict[str, list[int]] = {}

        for token_id, raw in self._id_to_token.items():
            surface = token_surface(raw)

            if not surface:
                continue

            if surface and all(c in self._WHITESPACE_CHARS for c in surface):
                self.whitespace_tokens.add(token_id)

            if all(c.isprintable() for c in surface) and '"' not in surface:
                self.all_string_tokens.add(token_id)

            if '"' in surface:
                self.tokens_containing_quote.append(token_id)

            stripped = surface.lstrip(" \t\n\r")
            if stripped:
                first = stripped[0]
                if first not in self.tokens_by_first_non_ws:
                    self.tokens_by_first_non_ws[first] = []
                self.tokens_by_first_non_ws[first].append(token_id)

    def surface_of(self, token_id: int) -> str:
        raw = self._id_to_token.get(token_id, "")
        return token_surface(raw)

    def summary(self) -> str:
        lines = [
            f"Vocab size       : {len(self._id_to_token)}",
            f"Whitespace tokens: {len(self.whitespace_tokens)}",
            f"String tokens    : {len(self.all_string_tokens)}",
        ]
        return "\n".join(lines)
