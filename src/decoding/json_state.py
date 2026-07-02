from enum import Enum, auto
from src.schema.function_def import FunctionDef


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
    def __init__(self, functions: list[FunctionDef] | None = None) -> None:
        self.state: JsonState = JsonState.START
        self.stack: list[tuple[ContainerType, JsonState]] = []
        self.functions: list[FunctionDef] = functions or []

        self.current_key: str = ""
        self.current_key_accum: str = ""
        self.current_function_name: str | None = None
        self.current_value_accum: str = ""
        self.parsed_params: set[str] = set()
        self.path: list[str] = []

    @property
    def inside_parameters_object(self) -> bool:
        return "parameters" in self.path

    @property
    def current_param_name(self) -> str | None:
        if "parameters" not in self.path:
            return None
        idx = self.path.index("parameters")
        if len(self.path) > idx + 1:
            return self.path[idx + 1]
        return self.current_key

    @property
    def allowed_parameter_keys(self) -> set[str]:
        if not self.functions:
            return set()
        if self.current_function_name:
            for func in self.functions:
                if func.name == self.current_function_name:
                    return set(func.parameters.keys()) - self.parsed_params
            return set()
        union_keys: set[str] = set()
        for func in self.functions:
            union_keys.update(func.parameters.keys())
        return union_keys - self.parsed_params

    @property
    def active_parameter_type(self) -> str | None:
        if not self.current_param_name or not self.current_function_name:
            return None
        for func in self.functions:
            if func.name == self.current_function_name:
                if self.current_param_name in func.parameters:
                    return func.parameters[self.current_param_name].type
        return None

    def clone(self) -> "JsonStateMachine":
        new_sm = JsonStateMachine(self.functions)
        new_sm.state = self.state
        new_sm.stack = list(self.stack)
        new_sm.current_key = self.current_key
        new_sm.current_key_accum = self.current_key_accum
        new_sm.current_function_name = self.current_function_name
        new_sm.current_value_accum = self.current_value_accum
        new_sm.parsed_params = set(self.parsed_params)
        new_sm.path = list(self.path)
        return new_sm

    def advance(self, char: str) -> None:
        handler = self._TRANSITIONS.get(self.state)
        if handler is None:
            raise ValueError(f"No transition handler for state {self.state}")

        prev_stack_len = len(self.stack)
        next_state = handler(self, char)
        new_stack_len = len(self.stack)

        if len(self.path) == 1 and self.path[0] == "":
            if next_state == JsonState.IN_KEY_STRING:
                accum = (
                    self.current_key_accum + char
                    if char != '"'
                    else self.current_key_accum
                )
                if not (
                    "name".startswith(accum)
                    or "parameters".startswith(accum)
                ):
                    raise ValueError(
                        f"Invalid first-level key prefix: {accum}"
                    )
            elif (
                self.state == JsonState.IN_KEY_STRING
                and next_state == JsonState.EXPECT_COLON
            ):
                key = self.current_key_accum
                if key not in ("name", "parameters"):
                    raise ValueError(f"Invalid first-level key: {key}")

        if self.current_key == "name" and len(self.path) == 1:
            if next_state == JsonState.IN_STRING_VALUE:
                accum = (
                    self.current_value_accum + char
                    if char != '"'
                    else self.current_value_accum
                )
                if self.functions:
                    match_found = any(
                        func.name.startswith(accum) for func in self.functions
                    )
                    if not match_found:
                        raise ValueError(
                            f"Invalid function name prefix: {accum}"
                        )
            elif (
                self.state == JsonState.IN_STRING_VALUE
                and next_state not in (
                    JsonState.IN_STRING_VALUE,
                    JsonState.IN_NUMBER_VALUE,
                )
            ):
                val = self.current_value_accum
                if self.functions:
                    match_found = any(
                        func.name == val for func in self.functions
                    )
                    if not match_found:
                        raise ValueError(f"Invalid function name: {val}")

        if self.inside_parameters_object and self.path[-1] == "parameters":
            allowed_keys = self.allowed_parameter_keys
            if allowed_keys:
                if next_state == JsonState.IN_KEY_STRING:
                    accum = (
                        self.current_key_accum + char
                        if char != '"'
                        else self.current_key_accum
                    )
                    match_found = any(
                        k.startswith(accum) for k in allowed_keys
                    )
                    if not match_found:
                        raise ValueError(f"Invalid param key prefix: {accum}")
                elif (
                    self.state == JsonState.IN_KEY_STRING
                    and next_state == JsonState.EXPECT_COLON
                ):
                    key = self.current_key_accum
                    if key not in allowed_keys:
                        raise ValueError(f"Invalid param key: {key}")

        if self.inside_parameters_object and self.current_param_name:
            param_type = self.active_parameter_type
            if param_type == "number":
                if next_state == JsonState.IN_STRING_VALUE:
                    raise ValueError("Expected number, got string")
            elif param_type == "string":
                if next_state == JsonState.IN_NUMBER_VALUE:
                    raise ValueError("Expected string, got number")
                if next_state in (
                    JsonState.EXPECT_KEY_OPEN,
                    JsonState.EXPECT_ELEMENT_OPEN,
                ):
                    raise ValueError("Expected string, got container")

        if new_stack_len > prev_stack_len:
            self.path.append(self.current_key)
        elif new_stack_len < prev_stack_len:
            if self.path:
                self.path.pop()

        if next_state == JsonState.IN_KEY_STRING:
            if char != '"':
                self.current_key_accum += char

        elif (
            self.state == JsonState.IN_KEY_STRING
            and next_state == JsonState.EXPECT_COLON
        ):
            self.current_key = self.current_key_accum
            self.current_key_accum = ""
            if self.path and self.path[-1] == "parameters":
                self.parsed_params.add(self.current_key)

        is_val_state = (JsonState.IN_STRING_VALUE, JsonState.IN_NUMBER_VALUE)
        if next_state in is_val_state:
            if char != '"':
                self.current_value_accum += char

        if self.state in is_val_state and next_state not in is_val_state:
            finished_value = self.current_value_accum
            self.current_value_accum = ""
            if self.current_key == "name" and len(self.path) == 1:
                self.current_function_name = finished_value

        self.state = next_state

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
