import json
from pathlib import Path
from typing import Dict, Set


class TokenClassifier:
    """Classifies vocabulary tokens into categories for decoding."""

    def __init__(self, id_to_token: Dict[int, str]) -> None:
        self._id_to_token = id_to_token
        self.all_string_tokens: Set[int] = set()
        self.tokens_containing_quote: Set[int] = set()
        self.number_char_tokens: Set[int] = set()
        self._build_sets()

    @classmethod
    def from_vocab_path(cls, vocab_path: str | Path) -> "TokenClassifier":
        with open(vocab_path, "r", encoding="utf-8") as f:
            token_to_id: Dict[str, int] = json.load(f)
        id_to_token = {v: k for k, v in token_to_id.items()}
        return cls(id_to_token)

    def _build_sets(self) -> None:
        for token_id, raw in self._id_to_token.items():
            surface = self.surface_of(token_id)
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
        return raw.replace("\u0120", " ").replace("\u010a", "\n")
