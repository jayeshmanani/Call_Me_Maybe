from argparse import ArgumentParser, Namespace
import argparse
from pathlib import Path


class CallMeMaybeCLI:
    ARG_DEFS = [
        ("--functions_definition",
         "data/input/functions_definition.json",
         "Path to function definitions JSON"),

        ("--input",
         "data/input/function_calling_tests.json",
         "Path to input tests JSON"),

        ("--output",
         "data/output/function_calling_results.json",
         "Path to output JSON"),

        ("--model_name",
         "Qwen/Qwen3-0.6B",
         "Model name to use"),
    ]

    def __init__(self) -> None:
        self.parser = self._build_parser()

    def _build_parser(self) -> ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="call_me_maybe",
            description="prompts to function calls",
        )

        for name, default, help_text in self.ARG_DEFS:
            parser.add_argument(
                name,
                type=Path,
                default=default,
                help=help_text,
            )

        return parser

    def parse(self) -> Namespace:
        return self.parser.parse_args()
