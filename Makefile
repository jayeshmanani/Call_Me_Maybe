SRC_FILES = src/

USERNAME := $(shell whoami)
GOINFRE               = /goinfre/$(USERNAME)
VENV                  = $(GOINFRE)/.venv
UV_CACHE_DIR          = $(GOINFRE)/.uv-cache
TMPDIR                = $(GOINFRE)/.tmp
HF_HOME               = $(GOINFRE)/.hf
TRANSFORMERS_CACHE    = $(HF_HOME)/transformers
HUGGINGFACE_HUB_CACHE = $(HF_HOME)/hub

export UV_PROJECT_ENVIRONMENT := $(VENV)

UV = UV_CACHE_DIR=$(UV_CACHE_DIR) TMPDIR=$(TMPDIR) HF_HOME=$(HF_HOME) TRANSFORMERS_CACHE=$(TRANSFORMERS_CACHE) HUGGINGFACE_HUB_CACHE=$(HUGGINGFACE_HUB_CACHE)

uname:
	@echo "Username: $(USERNAME)"
	@echo "Goinfre Path: $(GOINFRE)"
	@echo "Virtual Environment: $(VENV)"
	@echo "UV Cache Directory: $(UV_CACHE_DIR)"
	@echo "Temporary Directory: $(TMPDIR)"
	@echo "Hugging Face Home: $(HF_HOME)"
	@echo "Transformers Cache: $(TRANSFORMERS_CACHE)"
	@echo "Hugging Face Hub Cache: $(HUGGINGFACE_HUB_CACHE)"

init-cache:
	@mkdir -p $(VENV) $(UV_CACHE_DIR) $(TMPDIR) $(HF_HOME) \
		$(TRANSFORMERS_CACHE) $(HUGGINGFACE_HUB_CACHE)
	@echo "✔ All directories ready under $(GOINFRE)"

install: init-cache
	$(UV) uv venv --python 3.11 $(VENV)
	$(UV) uv sync --active

run: init-cache
	$(UV) uv run python -m src $(args)

debug: init-cache
	$(UV) uv run python -m pdb -m src $(args)

lint:
	$(UV) uv run flake8 $(SRC_FILES)
	$(UV) uv run mypy $(SRC_FILES) \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	$(UV) uv run flake8 $(SRC_FILES)
	$(UV) uv run mypy $(SRC_FILES) --strict

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	rm -rf data/output

fclean: clean
	rm -rf $(VENV)

env:
	@echo "# Default uv goinfre environment" > .env.goinfre
	@echo "export UV_CACHE_DIR=$(UV_CACHE_DIR)" >> .env.goinfre
	@echo "export TMPDIR=$(TMPDIR)" >> .env.goinfre
	@echo "export HF_HOME=$(HF_HOME)" >> .env.goinfre
	@echo "export TRANSFORMERS_CACHE=$(TRANSFORMERS_CACHE)" >> .env.goinfre
	@echo "export HUGGINGFACE_HUB_CACHE=$(HUGGINGFACE_HUB_CACHE)" >> .env.goinfre
	@echo "export UV_PROJECT_ENVIRONMENT=$(VENV)" >> .env.goinfre
	@echo "env file written, Now Run Command → source .env.goinfre"

.PHONY: install run debug lint lint-strict clean fclean init-cache env