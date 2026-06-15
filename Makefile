SRC_FILES = src/

install:
	uv sync --python 3.11

run:
	uv run python3 -m src $(args)

debug:
	uv run python3 -m pdb src $(args)

lint:
	uv run flake8 $(SRC_FILES)
	uv run mypy $(SRC_FILES) --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run flake8 $(SRC_FILES)
	uv run mypy $(SRC_FILES) --strict

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	rm -rf data/output/*.json

fclean: clean
	rm -rf .venv

.PHONY: install run debug lint lint-strict clean fclean