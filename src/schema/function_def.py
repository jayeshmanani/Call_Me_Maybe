from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator

_TYPE_ALIASES: dict[str, str] = {
    "number": "float",
    "float": "float",
    "int": "integer",
    "integer": "integer",
    "str": "string",
    "string": "string",
    "bool": "boolean",
    "boolean": "boolean",
}


_CANONICAL_TYPES = sorted(set(_TYPE_ALIASES.values()))


def normalize_type(value: str) -> str:
    key = value.strip().lower()
    try:
        return _TYPE_ALIASES[key]
    except KeyError:
        raise ValueError(
            f"Unsupported type {value!r}; expected one of {_CANONICAL_TYPES}"
        ) from None


class ParameterDef(BaseModel):
    type: str
    description: Optional[str] = None

    @field_validator("type")
    @classmethod
    def standardize_type(cls, v: str) -> str:
        return normalize_type(v)


class ReturnDef(BaseModel):
    type: str

    @field_validator("type")
    @classmethod
    def standardize_type(cls, v: str) -> str:
        return normalize_type(v)


class FunctionDef(BaseModel):
    name: str
    description: str
    parameters: Dict[str, ParameterDef] = Field(default_factory=dict)
    returns: Optional[ReturnDef] = None
