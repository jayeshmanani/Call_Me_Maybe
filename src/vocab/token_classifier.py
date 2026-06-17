from pathlib import Path
from typing import Dict, Optional, Set

from .loader import load_vocab, token_surface


class TokenClassifier:
    _NUMBER_CHARS: frozenset[str] = frozenset("0123456789.-")
    _STRUCTURAL_CHARS: frozenset[str] = frozenset('{}[]:",')
    _WHITESPACE_CHARS: frozenset[str] = frozenset(" \t\n\r")

    def __init__(self, id_to_token: Dict[int, str]) -> None:
        self._id_to_token = id_to_token
        self._token_to_id: Dict[str, int] = {
            token: tid for tid, token in id_to_token.items()
        }
        self._build_sets()

    @classmethod
    def from_vocab_path(cls, vocab_path: str | Path) -> "TokenClassifier":
        return cls(load_vocab(vocab_path))

    def _build_sets(self) -> None:
        self.number_tokens: Set[int] = set()
        self.structural_tokens: Dict[str, int] = {}        # char -> token_id
        self.structural_tokens_id_to_char: Dict[int, str] = {}
        self.whitespace_tokens: Set[int] = set()
        self.all_string_tokens: Set[int] = set()

        for token_id, raw in self._id_to_token.items():
            surface = token_surface(raw)

            if not surface:
                continue

            if (all(c in self._NUMBER_CHARS for c in surface)
                    and any(c.isdigit() for c in surface)):
                self.number_tokens.add(token_id)

            if len(surface) == 1 and surface in self._STRUCTURAL_CHARS:
                if surface not in self.structural_tokens:
                    self.structural_tokens[surface] = token_id
                    self.structural_tokens_id_to_char[token_id] = surface

            if surface and all(c in self._WHITESPACE_CHARS for c in surface):
                self.whitespace_tokens.add(token_id)

            if all(c.isprintable() for c in surface) and '"' not in surface:
                self.all_string_tokens.add(token_id)

    def token_id_for(self, char: str) -> Optional[int]:
        return self.structural_tokens.get(char)

    def id_for_token(self, token: str) -> Optional[int]:
        return self._token_to_id.get(token)

    def surface_of(self, token_id: int) -> str:
        raw = self._id_to_token.get(token_id, "")
        return token_surface(raw)

    def summary(self) -> str:
        lines = [
            f"Vocab size       : {len(self._id_to_token)}",
            f"Number tokens    : {len(self.number_tokens)}",
            f"Structural tokens: {len(self.structural_tokens)} "
            f"→ {sorted(self.structural_tokens.keys())}",
            f"Whitespace tokens: {len(self.whitespace_tokens)}",
            f"String tokens    : {len(self.all_string_tokens)}",
        ]
        return "\n".join(lines)
