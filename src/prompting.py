from typing import Any, Dict, List


def format_prompt(user_query: str, functions: List[Dict[str, Any]]) -> str:
    """Format the user prompt with semantic function signatures."""
    prompt = (
        "Select the correct function and parameters. "
        "Extract parameter values exactly as described in the query.\n\n"
        "Available functions:\n"
    )
    for fn in functions:
        prompt += f"- {fn.get('name', '')}: {fn.get('description', '')}\n"
        prompt += "  Arguments:\n"
        params = fn.get("parameters", {})
        if not params:
            prompt += "    None\n"
        for param_name, param_data in params.items():
            prompt += f"    - {param_name} ({param_data.get('type', '')})\n"

    prompt += f"\nQuery: \"{user_query}\"\n"
    prompt += "Output JSON:\n"
    return prompt
