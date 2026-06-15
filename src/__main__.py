from argparse import Namespace
from .runtime.env import init_caching_dirs
from .runtime.arg_parser import CallMeMaybeCLI
from .runtime.json_loader import load_json_file


def run_app(args: Namespace) -> int:
    try:
        init_caching_dirs()
        print(f"Loading functions from: {args.functions_definition}")
        functions = load_json_file(
            args.functions_definition, "functions_definition")
        if functions is None:
            return 1

        print(f"Loading prompts from:   {args.input}")
        prompts = load_json_file(args.input, "input")
        if prompts is None:
            return 1

        print(
            f"Found {len(functions)} function definitions\
                  and {len(prompts)} prompts.")
        print()

        print("Functions available:")
        for fn in functions:
            params = list(fn.get("parameters", {}).keys())
            print(f"  - {fn['name']}({', '.join(params)})")

        print()
        print("Prompts to process:")
        for i, p in enumerate(prompts, 1):
            print(f"  {i:>2}. {p['prompt']}")

        print()
        print(f"Output will be written to: {args.output}")

        return 0
    except (
        ValueError,
    ) as exc:
        print(f"Error: {exc}")
        raise SystemExit(1) from exc


def main() -> None:
    cli = CallMeMaybeCLI()
    args = cli.parse()
    run_app(args)


if __name__ == "__main__":
    main()
