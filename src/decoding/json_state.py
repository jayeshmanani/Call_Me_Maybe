from enum import Enum, auto


class JsonState(Enum):
    START = auto()
    EXPECT_KEY_OPEN = auto()
    IN_KEY_STRING = auto()
    EXPECT_COLON = auto()
    EXPECT_VALUE_OPEN = auto()
    IN_STRING_VALUE = auto()
    IN_NUMBER_VALUE = auto()
    AFTER_VALUE = auto()
    DONE = auto()


class JsonStateMachine:
    def __init__(self) -> None:
        self.state: JsonState = JsonState.START

    def advance(self, char: str) -> None:
        handler = self._TRANSITIONS.get(self.state)
        if handler is None:
            raise ValueError(f"No transition handler for state {self.state}")
        self.state = handler(self, char)

    def _from_start(self, char: str) -> JsonState:
        if char == "{":
            return JsonState.EXPECT_KEY_OPEN
        raise ValueError(f"START: expected '{{', got {char!r}")

    def _from_done(self, char: str) -> JsonState:
        raise ValueError("DONE: no more characters expected")

    _TRANSITIONS: dict = {}


JsonStateMachine._TRANSITIONS = {
    JsonState.START: JsonStateMachine._from_start,
    JsonState.DONE: JsonStateMachine._from_done,
}
