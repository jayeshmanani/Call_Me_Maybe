*This project has been created as part of the 42 curriculum by jmanani.*

# Call Me Maybe - Constrained LLM Decoding for Function Calling

## Description
**Call Me Maybe** is a lightweight, high-reliability function calling tool that translates natural language prompts (e.g., *"What is the sum of 2 and 3?"*) into structured JSON function calls (e.g., `{"name": "fn_add_numbers", "parameters": {"a": 2, "b": 3}}`).

Instead of relying on large model sizes or unconstrained prompt engineering, which frequently results in malformed syntax or hallucinated function names, this project implements a **custom constrained decoding engine** built from scratch. By intervening in the autoregressive token selection process via logit masking and deterministic template force-feeding, the engine guarantees 100% syntactically valid and schema-compliant JSON outputs using a small 0.6B parameter model (`Qwen/Qwen3-0.6B`).

---

## Instructions

### Prerequisites
* Python 3.11 or later
* `uv` package manager

### Environment Setup & Installation
Run the following commands to configure storage directories under `/goinfre`, set up the virtual environment, and install dependencies:

```bash
# Initialize storage directories
make init-cache

# Generate environment configuration file
make env

# Load environment variables into terminal session
source .env.goinfre

# Install project dependencies
make install
```

### Execution
Run the main program using the default input/output paths:

```bash
# Using Makefile
make run

# Or directly using uv
uv run python -m src
```

---

## Example Usage

### Running with Custom Arguments
You can specify custom paths for function definitions, input test prompts, output JSON destinations, or model checkpoints:

```bash
uv run python -m src \
  --functions_definition data/input/functions_definition.json \
  --input data/input/function_calling_tests.json \
  --output data/output/function_calling_results.json \
  --model_name "Qwen/Qwen3-0.6B"
```

### Development Commands
```bash
# Run code quality linter (flake8 & mypy)
make lint

# Run strict type checking
make lint-strict

# Run in debug mode with pdb
make debug

# Clean temporary build artifacts and caches
make clean
```

---

## Algorithm Explanation

The constrained decoding engine operates autoregressively on the model's logits:

```
Formatted Prompt -> Tokenization -> LLM Forward Pass -> Logit Masking (-math.inf) -> Argmax Token Selection
```

### 1. Template Force-Feeding
Deterministic structural JSON syntax (such as `{\n  "name": "`, `",\n  "parameters": {`, and parameter keys `"\n    "key": `) is encoded and appended directly to the context window without invoking model forward passes. This guarantees valid JSON syntax while reducing inference latency.

### 2. Candidate Function Name Masking
When generating the function name:
1. Candidate names are extracted from the schema definitions.
2. At each token step, logits for tokens that would not form a valid prefix of any candidate name are set to `-math.inf`.
3. Greedy choice (`max`) selects the highest-probability valid token until a complete candidate name is produced.

### 3. Type-Constrained Value Decoding
Values are generated according to their target schema type:
* **Booleans (`boolean`/`bool`)**: Direct binary comparison between `"true"` and `"false"` token logits.
* **Numbers (`integer`/`float`)**: The first token is strictly constrained to numeric characters (`0-9`, `.`, `-`). Subsequent steps allow any token; as soon as a non-numeric token (e.g., `,` or `\n`) is selected, generation breaks without appending the non-numeric token.
* **Strings (`string`/`str`)**: First token forbids double quotes to prevent empty strings (`""`). Subsequent steps allow string body tokens and quote tokens. Escaped quotes (`\"`) are preserved, while unescaped quotes (`"`) mark the string boundary and trigger termination.

---

## Design Decisions

* **Structural Subtyping (`typing.Protocol`)**: Defined `LogitSource` protocol to decouple the decoding engine from specific model implementations, enabling modularity and unit testability.
* **Pre-computed Token Sets**: Static set unions (`first_step_allowed`, `max_step_allowed`, `normal_step_allowed`) are pre-computed prior to the string generation loop to avoid repeated set creation overhead.
* **Pydantic Validation**: All data schemas (`ParameterDef`, `FunctionDef`, `PromptTest`, `FunctionCallResult`) use Pydantic `BaseModel` for validation.
* **No High-Level Frameworks**: Implemented pure Python logit manipulation without importing heavy constrained decoding frameworks like Outlines or DSPy.

---

## Performance Analysis

* **Accuracy**: **100%** across test prompts (correct function identification and parameter value extraction).
* **JSON Reliability**: **100%** parseable and schema-compliant JSON output (zero syntax errors, zero trailing commas).
* **Execution Speed**: Processes all 11 test cases in **~1.5 to 3 minutes total** on standard hardware (significantly below the 5-minute requirement).

---

## Challenges Faced & Solutions

1. **Premature Empty Strings (`""`)**:
   * *Challenge*: The model occasionally selected a closing quote on the first step of string generation.
   * *Solution*: Enforced `step_allowed = string_tokens` (excluding quotes) when `chars_gen == 0`.

2. **Byte-Pair Encoding Control Symbols**:
   * *Challenge*: Tokenizers use special control symbols (e.g., `Ġ` for spaces, `Ċ` for newlines).
   * *Solution*: Implemented `TokenClassifier.surface_of()` to convert BPE symbols to standard characters before evaluating string properties.

3. **Escaped vs. Unescaped Quotes**:
   * *Challenge*: Distinguishing between quotes inside string content (`\"`) and structural closing quotes (`"`).
   * *Solution*: Inspected the character immediately preceding the quote index (`surface[quote_idx - 1] == '\\'`) to determine whether to continue string generation or terminate.

---

## Testing Strategy

* **Static Analysis**: Enforced zero linter warnings using `flake8` and `mypy --strict`.
* **Input Validation**: Verified graceful error handling for missing files, invalid JSON input, and schema mismatches.
* **Output Verification**: Checked output JSON structure against required schema fields (`prompt`, `name`, `parameters`).

---

## Resources & AI Usage

### References
* [Youtube - Constrained Generation for Better LLM Prompting Results](https://www.youtube.com/watch?v=ugxPshXr7Ro)
* [Youtube - Taking Control of LLM Outputs: An Introductory Journey into Logits](https://www.youtube.com/watch?v=EiMPQsI2__Y)
* [Youtube - Structured Output from LLMs: Grammars, Regex, and State Machines](https://www.youtube.com/watch?v=xpvFinvqRCA)
* [Youtube - LLMs as constrained generators - Fabien Potencier - Upsun](https://www.youtube.com/watch?v=ujdg2PwIhVc)
* [Pydantic Documentation](https://docs.pydantic.dev/)
* [Hugging Face Transformers Tokenizer Documentation](https://huggingface.co/docs/transformers/main_classes/tokenizer)


### AI Usage Description
Artificial Intelligence tools (Github Copilot and ChatGPT) were used during development for:
* Learning about Constrained Decoding and logit masking.
* Learning how LLMs function at a low level.
* Discussing design flows and potential solutions.
* Discussing opitimizations and efficiency improvements.
* Code quality verification (ensuring PEP 257 docstring adherence and `mypy --strict` compliance).
* Writing and structuring project documentation and explanations.
* Writing this README.md.