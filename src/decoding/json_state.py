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
    EXPECT_ELEMENT_OPEN = auto()
    AFTER_ELEMENT = auto()
    DONE = auto()


class ContainerType(Enum):
    OBJECT = auto()
    ARRAY = auto()


class JsonStateMachine:
    def __init__(self) -> None:
        self.state: JsonState = JsonState.START
        self.stack: list[tuple[ContainerType, JsonState]] = []

    def advance(self, char: str) -> None:
        handler = self._TRANSITIONS.get(self.state)
        if handler is None:
            raise ValueError(f"No transition handler for state {self.state}")
        self.state = handler(self, char)

    def _from_start(self, char: str) -> JsonState:
        if char == "{":
            self.stack.append((ContainerType.OBJECT, JsonState.DONE))
            return JsonState.EXPECT_KEY_OPEN
        if char == "[":
            self.stack.append((ContainerType.ARRAY, JsonState.DONE))
            return JsonState.EXPECT_ELEMENT_OPEN
        if char in " \t\n\r":
            return JsonState.START
        raise ValueError(f"START: expected '{{' or '[', got {char!r}")

    def _from_expect_key_open(self, char: str) -> JsonState:
        if char == '"':
            return JsonState.IN_KEY_STRING
        if char == "}":
            if not self.stack or self.stack[-1][0] != ContainerType.OBJECT:
                raise ValueError(
                    "EXPECT_KEY_OPEN: unexpected '}' (not in object)"
                )
            _, return_state = self.stack.pop()
            return return_state
        if char in " \t\n\r":
            return JsonState.EXPECT_KEY_OPEN
        raise ValueError(
            f"EXPECT_KEY_OPEN: expected '\"' or '}}', got {char!r}"
        )

    def _from_in_key_string(self, char: str) -> JsonState:
        if char == '"':
            return JsonState.EXPECT_COLON
        return JsonState.IN_KEY_STRING

    def _from_expect_colon(self, char: str) -> JsonState:
        if char == ":":
            return JsonState.EXPECT_VALUE_OPEN
        if char in " \t\n\r":
            return JsonState.EXPECT_COLON
        raise ValueError(f"EXPECT_COLON: expected ':', got {char!r}")

    def _from_expect_value_open(self, char: str) -> JsonState:
        if char == '"':
            return JsonState.IN_STRING_VALUE
        if char.isdigit() or char in "-.":
            return JsonState.IN_NUMBER_VALUE
        if char == "{":
            self.stack.append((ContainerType.OBJECT, JsonState.AFTER_VALUE))
            return JsonState.EXPECT_KEY_OPEN
        if char == "[":
            self.stack.append((ContainerType.ARRAY, JsonState.AFTER_VALUE))
            return JsonState.EXPECT_ELEMENT_OPEN
        if char in " \t\n\r":
            return JsonState.EXPECT_VALUE_OPEN
        raise ValueError(
            "EXPECT_VALUE_OPEN: expected '\"', number, '{', or '[', "
            f"got {char!r}"
        )

    def _from_in_string_value(self, char: str) -> JsonState:
        if char == '"':
            if self.stack and self.stack[-1][0] == ContainerType.ARRAY:
                return JsonState.AFTER_ELEMENT
            return JsonState.AFTER_VALUE
        return JsonState.IN_STRING_VALUE

    def _from_in_number_value(self, char: str) -> JsonState:
        if char.isdigit() or char in "-.":
            return JsonState.IN_NUMBER_VALUE
        if char in " \t\n\r":
            if self.stack and self.stack[-1][0] == ContainerType.ARRAY:
                return JsonState.AFTER_ELEMENT
            return JsonState.AFTER_VALUE
        if char == ",":
            if not self.stack:
                raise ValueError(
                    "IN_NUMBER_VALUE: unexpected ',' (no container)"
                )
            if self.stack[-1][0] == ContainerType.OBJECT:
                return JsonState.EXPECT_KEY_OPEN
            else:
                return JsonState.EXPECT_ELEMENT_OPEN
        if char == "}":
            if not self.stack or self.stack[-1][0] != ContainerType.OBJECT:
                raise ValueError("IN_NUMBER_VALUE: unexpected '}'")
            _, return_state = self.stack.pop()
            return return_state
        if char == "]":
            if not self.stack or self.stack[-1][0] != ContainerType.ARRAY:
                raise ValueError("IN_NUMBER_VALUE: unexpected ']'")
            _, return_state = self.stack.pop()
            return return_state
        raise ValueError(f"IN_NUMBER_VALUE: unexpected char {char!r}")

    def _from_after_value(self, char: str) -> JsonState:
        if char == ",":
            return JsonState.EXPECT_KEY_OPEN
        if char == "}":
            if not self.stack or self.stack[-1][0] != ContainerType.OBJECT:
                raise ValueError("AFTER_VALUE: unexpected '}'")
            _, return_state = self.stack.pop()
            return return_state
        if char in " \t\n\r":
            return JsonState.AFTER_VALUE
        raise ValueError(f"AFTER_VALUE: expected ',' or '}}', got {char!r}")

    def _from_expect_element_open(self, char: str) -> JsonState:
        if char == '"':
            return JsonState.IN_STRING_VALUE
        if char.isdigit() or char in "-.":
            return JsonState.IN_NUMBER_VALUE
        if char == "{":
            self.stack.append((ContainerType.OBJECT, JsonState.AFTER_ELEMENT))
            return JsonState.EXPECT_KEY_OPEN
        if char == "[":
            self.stack.append((ContainerType.ARRAY, JsonState.AFTER_ELEMENT))
            return JsonState.EXPECT_ELEMENT_OPEN
        if char == "]":
            if not self.stack or self.stack[-1][0] != ContainerType.ARRAY:
                raise ValueError("EXPECT_ELEMENT_OPEN: unexpected ']'")
            _, return_state = self.stack.pop()
            return return_state
        if char in " \t\n\r":
            return JsonState.EXPECT_ELEMENT_OPEN
        raise ValueError(
            "EXPECT_ELEMENT_OPEN: expected '\"', number, '{', '[', or ']', "
            f"got {char!r}"
        )

    def _from_after_element(self, char: str) -> JsonState:
        if char == ",":
            return JsonState.EXPECT_ELEMENT_OPEN
        if char == "]":
            if not self.stack or self.stack[-1][0] != ContainerType.ARRAY:
                raise ValueError("AFTER_ELEMENT: unexpected ']'")
            _, return_state = self.stack.pop()
            return return_state
        if char in " \t\n\r":
            return JsonState.AFTER_ELEMENT
        raise ValueError(f"AFTER_ELEMENT: expected ',' or ']', got {char!r}")

    def _from_done(self, char: str) -> JsonState:
        if char in " \t\n\r":
            return JsonState.DONE
        raise ValueError("DONE: no more characters expected")

    _TRANSITIONS: dict = {}


JsonStateMachine._TRANSITIONS = {
    JsonState.START: JsonStateMachine._from_start,
    JsonState.EXPECT_KEY_OPEN: JsonStateMachine._from_expect_key_open,
    JsonState.IN_KEY_STRING: JsonStateMachine._from_in_key_string,
    JsonState.EXPECT_COLON: JsonStateMachine._from_expect_colon,
    JsonState.EXPECT_VALUE_OPEN: JsonStateMachine._from_expect_value_open,
    JsonState.IN_STRING_VALUE: JsonStateMachine._from_in_string_value,
    JsonState.IN_NUMBER_VALUE: JsonStateMachine._from_in_number_value,
    JsonState.AFTER_VALUE: JsonStateMachine._from_after_value,
    JsonState.EXPECT_ELEMENT_OPEN: JsonStateMachine._from_expect_element_open,
    JsonState.AFTER_ELEMENT: JsonStateMachine._from_after_element,
    JsonState.DONE: JsonStateMachine._from_done,
}
