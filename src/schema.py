from typing import Any, Dict
from pydantic import BaseModel, Field, field_validator


class ParameterDef(BaseModel):
    """Definition of a function parameter schema."""
    type: str
    description: str | None = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {
            "string", "str", "number", "float",
            "integer", "int", "boolean", "bool"
        }
        val = v.strip().lower()
        if val not in valid_types:
            raise ValueError(
                f"Invalid parameter type: {v}. Expected one of {valid_types}"
            )
        return val


class FunctionDef(BaseModel):
    """Definition of an executable tool function."""
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    parameters: Dict[str, ParameterDef] = Field(default_factory=dict)
    returns: Dict[str, Any] | None = None

    @field_validator("name", "description")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace.")
        return v.strip()


class PromptTest(BaseModel):
    """Input prompt test case."""
    prompt: str = Field(min_length=1)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Prompt cannot be empty or whitespace.")
        return v.strip()


class FunctionCallResult(BaseModel):
    """Structured output result for a processed prompt."""
    prompt: str
    name: str
    parameters: Dict[str, Any]
