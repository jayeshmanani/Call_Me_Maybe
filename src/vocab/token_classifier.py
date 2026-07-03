import json
from pathlib import Path
from typing import Dict, Set


def _load_vocab(vocab_path: str | Path) -> Dict[int, str]:
    """Load vocabulary JSON mapping from file."""
    with open(vocab_path, "r", encoding="utf-8") as f:
        token_to_id: Dict[str, int] = json.load(f)
    return {
        token_id: token_str
        for token_str, token_id in token_to_id.items()
    }


def _token_surface(token_str: str) -> str:
    """Clean the special unicode characters for spaces and newlines."""
    return token_str.replace("\u0120", " ").replace("\u010a", "\n")


class TokenClassifier:
    """Classifies vocabulary tokens to restrict decoding options."""

    def __init__(self, id_to_token: Dict[int, str]) -> None:
        self._id_to_token = id_to_token
        self._build_sets()

    @classmethod
    def from_vocab_path(cls, vocab_path: str | Path) -> "TokenClassifier":
        return cls(_load_vocab(vocab_path))

    def _build_sets(self) -> None:
        self.all_string_tokens: Set[int] = set()
        self.tokens_containing_quote: Set[int] = set()
        self.number_char_tokens: Set[int] = set()

        for token_id, raw in self._id_to_token.items():
            surface = _token_surface(raw)

            if not surface:
                continue

            if all(c.isprintable() for c in surface) and '"' not in surface:
                self.all_string_tokens.add(token_id)

            if '"' in surface:
                self.tokens_containing_quote.add(token_id)

            if all(c in "0123456789.-" for c in surface):
                self.number_char_tokens.add(token_id)

    def surface_of(self, token_id: int) -> str:
        raw = self._id_to_token.get(token_id, "")
        return _token_surface(raw)
