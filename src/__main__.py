from argparse import Namespace
from pydantic import ValidationError
from typing import List

from .runtime.env import init_caching_dirs
from .runtime.arg_parser import CallMeMaybeCLI
from .runtime.json_loader import load_json_file
from .schema.function_def import FunctionDef
from .prompting.formatter import PromptFormatter


def run_app(args: Namespace) -> int:
    try:
        init_caching_dirs()

        print(f"Loading functions from: {args.functions_definition}")
        raw_functions = load_json_file(
            args.functions_definition, "functions_definition")
        if raw_functions is None:
            return 1

        try:
            functions: List[FunctionDef] = [
                FunctionDef.model_validate(fn) for fn in raw_functions
            ]
        except ValidationError as e:
            print(f"Error validating function definitions: {e}")
            return 1

        print(f"Loading prompts from:   {args.input}")
        prompts = load_json_file(args.input, "input")
        if prompts is None:
            return 1

        print(
            f"Found {len(functions)} function definitions "
            f"and {len(prompts)} prompts.\n"
        )

        print("Functions available (Validated via Pydantic):")
        for fn in functions:
            params = list(fn.parameters.keys())
            print(f"  - {fn.name}({', '.join(params)})")

        print("\n--- Example Formatted Prompt ---")
        if prompts:
            first_prompt = prompts[0].get("prompt", "")
            formatted = PromptFormatter.format_prompt(first_prompt, functions)
            print(formatted)
        print("--------------------------------\n")

        print(f"Output will be written to: {args.output}")

        return 0
    except (ValueError, TypeError) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1) from exc


def main() -> None:
    cli = CallMeMaybeCLI()
    args = cli.parse()
    run_app(args)


if __name__ == "__main__":
    main()
