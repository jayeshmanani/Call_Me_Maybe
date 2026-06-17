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
