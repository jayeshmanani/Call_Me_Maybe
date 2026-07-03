from pathlib import Path
from typing import Dict, Set

from .loader import load_vocab, token_surface


class TokenClassifier:
    def __init__(self, id_to_token: Dict[int, str]) -> None:
        self._id_to_token = id_to_token
        self._build_sets()

    @classmethod
    def from_vocab_path(cls, vocab_path: str | Path) -> "TokenClassifier":
        return cls(load_vocab(vocab_path))

    def _build_sets(self) -> None:
        self.all_string_tokens: Set[int] = set()
        self.tokens_containing_quote: Set[int] = set()
        self.number_char_tokens: Set[int] = set()

        for token_id, raw in self._id_to_token.items():
            surface = token_surface(raw)

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
        return token_surface(raw)

    def summary(self) -> str:
        lines = [
            f"Vocab size         : {len(self._id_to_token)}",
            f"String tokens      : {len(self.all_string_tokens)}",
            f"Quote tokens       : {len(self.tokens_containing_quote)}",
            f"Number char tokens : {len(self.number_char_tokens)}",
        ]
        return "\n".join(lines)
