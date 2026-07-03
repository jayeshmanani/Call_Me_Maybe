from typing import List
from src.schema.function_def import FunctionDef


class PromptFormatter:
    """Formats the user prompt and function definitions for the LLM."""

    @staticmethod
    def format_prompt(user_query: str, functions: List[FunctionDef]) -> str:
        prompt = (
            "Select the correct function and parameters.\n\n"
            "Available functions:\n"
        )

        for fn in functions:
            prompt += f"- {fn.name}: {fn.description}\n"
            prompt += "  Arguments:\n"
            if not fn.parameters:
                prompt += "    None\n"
            for param_name, param_data in fn.parameters.items():
                prompt += f"    - {param_name} ({param_data.type})\n"

        prompt += (
            f"\nQuery: \"{user_query}\"\n"
            "Output JSON:\n"
        )

        return prompt
