import json
from argparse import Namespace
from pydantic import ValidationError
from typing import List

from llm_sdk import Small_LLM_Model
from .runtime.env import init_caching_dirs
from .runtime.arg_parser import CallMeMaybeCLI
from .runtime.json_loader import load_json_file
from .schema.function_def import FunctionDef
from .prompting.formatter import PromptFormatter
from .vocab import TokenClassifier
from .decoding.constrained_engine import constrained_generate


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

        print(f"Initializing model: {args.model_name}...")
        model = Small_LLM_Model(model_name=str(args.model_name))

        vocab_path = model.get_path_to_vocab_file()
        print(f"Loading TokenClassifier from vocab path: {vocab_path}")
        clf = TokenClassifier.from_vocab_path(vocab_path)

        results = []
        for item in prompts[:1]:
            query = item.get("prompt", "")
            if not query:
                continue

            formatted_prompt = PromptFormatter.format_prompt(query, functions)
            prompt_tensor = model.encode(formatted_prompt)
            prompt_ids = prompt_tensor[0].tolist()

            print(f"Generating function call for query: {query!r}")
            generated_ids = constrained_generate(
                model=model,
                prompt_ids=prompt_ids,
                clf=clf
            )

            generated_text = model.decode(generated_ids)
            # print(f"Generated text: {generated_text}")

            try:
                parsed_json = json.loads(generated_text)
                name = parsed_json.get("name", "")
                parameters = parsed_json.get("parameters", {})

                fn_def = next(
                    (fn for fn in functions if fn.name == name), None
                )
                if fn_def:
                    for param_name, param_val in list(parameters.items()):
                        param_def = fn_def.parameters.get(param_name)
                        if param_def and param_def.type in ("float", "number"):
                            try:
                                parameters[param_name] = float(param_val)
                            except (ValueError, TypeError):
                                pass

                results.append({
                    "prompt": query,
                    "name": name,
                    "parameters": parameters
                })
            except Exception as e:
                print(f"Error parsing generated JSON: {e}")
                results.append({
                    "prompt": query,
                    "name": "",
                    "parameters": {}
                })

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        print(f"\nSuccessfully wrote {len(results)} results to: {args.output}")
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
