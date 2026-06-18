from typing import Dict, Optional
from pydantic import BaseModel, Field, field_validator


class ParameterDef(BaseModel):
    type: str
    description: Optional[str] = None

    @field_validator("type")
    @classmethod
    def standardize_type(cls, v: str) -> str:
        v = v.lower()
        if v == "number":
            return "float"
        return v


class ReturnDef(BaseModel):
    type: str

    @field_validator("type")
    @classmethod
    def standardize_type(cls, v: str) -> str:
        v = v.lower()
        if v == "number":
            return "float"
        return v


class FunctionDef(BaseModel):
    name: str
    description: str
    parameters: Dict[str, ParameterDef] = Field(default_factory=dict)
    returns: Optional[ReturnDef] = None
