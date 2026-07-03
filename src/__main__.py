import argparse
import json
import sys
from pathlib import Path
from pydantic import ValidationError

from llm_sdk import Small_LLM_Model
from src.vocab import TokenClassifier
from src.decoding import constrained_generate
from src.schema import FunctionDef, PromptTest
from src.runtime import init_caching_dirs, load_json_file, normalize_arguments
from src.prompting import format_prompt


def run_app(args: argparse.Namespace) -> int:
    """Main loop executing function calling pipeline."""
    try:
        init_caching_dirs()

        print(f"Loading functions from: {args.functions_definition}")
        raw_functions = load_json_file(
            args.functions_definition, "functions_definition"
        )
        if raw_functions is None:
            return 1

        try:
            functions_validated = [
                FunctionDef.model_validate(fn) for fn in raw_functions
            ]
        except ValidationError as e:
            print(
                f"ERROR: Function definition validation failed:\n{e}",
                file=sys.stderr,
            )
            return 1

        functions = [fn.model_dump() for fn in functions_validated]

        print(f"Loading prompts from:   {args.input}")
        raw_prompts = load_json_file(args.input, "input")
        if raw_prompts is None:
            return 1

        try:
            prompts_validated = [
                PromptTest.model_validate(p) for p in raw_prompts
            ]
        except ValidationError as e:
            print(
                f"ERROR: Input prompts validation failed:\n{e}",
                file=sys.stderr,
            )
            return 1

        prompts = [p.model_dump() for p in prompts_validated]

        print(
            f"Found {len(functions)} function definitions "
            f"and {len(prompts)} prompts.\n"
        )

        print("Initializing model...")
        model = Small_LLM_Model(model_name=str(args.model_name))
        vocab_path = model.get_path_to_vocab_file()
        clf = TokenClassifier.from_vocab_path(vocab_path)

        results = []
        for item in prompts:
            query = item.get("prompt", "")
            if not query:
                continue

            try:
                formatted_prompt = format_prompt(query, functions)
                prompt_tensor = model.encode(formatted_prompt)
                prompt_ids = prompt_tensor[0].tolist()

                print(f"\nProcessing prompt: {query!r}")
                generated_ids = constrained_generate(
                    model=model,
                    prompt_ids=prompt_ids,
                    clf=clf,
                    functions=functions,
                )

                generated_text = model.decode(generated_ids)
                parsed = json.loads(generated_text)
                name = parsed.get("name", "")
                params = parsed.get("parameters", {})

                fn_def = next(
                    (fn for fn in functions if fn.get("name") == name), None
                )
                if fn_def:
                    params = normalize_arguments(params, fn_def, query)

                results.append({
                    "prompt": query,
                    "name": name,
                    "parameters": params,
                })
            except Exception as e:
                print(f"Error processing prompt {query!r}: {e}")
                results.append({
                    "prompt": query,
                    "name": "",
                    "parameters": {},
                })

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"\nWrote {len(results)} results to: {args.output}")
        return 0
    except (ValueError, TypeError) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1) from exc


def main() -> None:
    """Parse CLI arguments and run application."""
    parser = argparse.ArgumentParser(
        prog="call_me_maybe",
        description="Natural language prompts to structured function calls",
    )
    parser.add_argument(
        "--functions_definition",
        type=Path,
        default="data/input/functions_definition.json",
        help="Path to function definitions JSON",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default="data/input/function_calling_tests.json",
        help="Path to input tests JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default="data/output/function_calling_results.json",
        help="Path to output JSON",
    )
    parser.add_argument(
        "--model_name",
        type=Path,
        default="Qwen/Qwen3-0.6B",
        help="Model name to use",
    )
    args = parser.parse_args()
    run_app(args)


if __name__ == "__main__":
    main()
