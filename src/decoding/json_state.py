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
        self.object_depth: int = 0
        self.current_string: str = ""
        self.is_escaping: bool = False

    def process_string(self, text: str) -> None:
        for char in text:
            self.process_char(char)

    def process_char(self, char: str) -> None:
        if self.state == JsonState.START:
            if char == '{':
                self.state = JsonState.EXPECT_KEY_OPEN
                self.object_depth += 1
        elif self.state == JsonState.EXPECT_COLON:
            if char == ':':
                self.state = JsonState.EXPECT_VALUE_OPEN
