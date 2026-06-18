from typing import List
from src.schema.function_def import FunctionDef


class PromptFormatter:
    """Formats the user prompt and function definitions for the LLM."""

    @staticmethod
    def format_prompt(user_query: str, functions: List[FunctionDef]) -> str:
        prompt = (
            "You are a helpful AI assistant that translates natural language "
            "into structured function calls. You must reply ONLY with a valid "
            "JSON object containing 'name' (the function name) and "
            "'parameters' (the function arguments).\n\n"
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
            f"\nUser query: \"{user_query}\"\n"
            "Output JSON:\n"
        )

        return prompt
