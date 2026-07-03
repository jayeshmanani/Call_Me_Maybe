from typing import Any, Dict, List


def format_prompt(user_query: str, functions: List[Dict[str, Any]]) -> str:
    """Format user query alongside candidate function signatures."""
    lines = [
        "Select the correct function and parameters.",
        "Extract parameter values exactly as described in the query.\n",
        "Available functions:",
    ]
    for fn in functions:
        name = fn.get("name", "")
        desc = fn.get("description", "")
        lines.append(f"- {name}: {desc}")
        params = fn.get("parameters", {})
        if not params:
            lines.append("  Arguments:\n    None")
        else:
            lines.append("  Arguments:")
            for p_name, p_data in params.items():
                p_type = p_data.get("type", "") if isinstance(p_data, dict) \
                    else ""
                lines.append(f"    - {p_name} ({p_type})")

    lines.append(f'\nQuery: "{user_query}"')
    lines.append("Output JSON:")
    return "\n".join(lines)
