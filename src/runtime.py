import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
import getpass


def init_caching_dirs() -> None:
    """Initialize model & uv cache directories under /goinfre."""
    username = os.environ.get("USER") or getpass.getuser()
    goinfre_path = Path(f"/goinfre/{username}")
    root = goinfre_path if Path("/goinfre").exists() else Path.home() / ".cache"
    hf_root = root / ".hf"
    env_mapping = {
        "UV_CACHE_DIR": root / ".uv-cache",
        "TMPDIR": root / ".tmp",
        "HF_HOME": hf_root,
        "TRANSFORMERS_CACHE": hf_root / "transformers",
        "HUGGINGFACE_HUB_CACHE": hf_root / "hub",
    }
    for k, v in env_mapping.items():
        os.environ.setdefault(k, str(v))
    for directory in env_mapping.values():
        directory.mkdir(parents=True, exist_ok=True)


def load_json_file(path: Path, label: str) -> List[Dict[str, Any]] | None:
    """Load JSON array from file with validation and detailed feedback."""
    if not path.exists():
        print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print(
                f"ERROR: {label} file must contain a JSON array, "
                f"got {type(data).__name__}",
                file=sys.stderr,
            )
            return None
        return data
    except json.JSONDecodeError as e:
        print(
            f"ERROR: {label} file contains invalid JSON: {e}",
            file=sys.stderr,
        )
        return None


def normalize_arguments(
    parameters: Dict[str, Any],
    function_def: Dict[str, Any],
    query: str = "",
) -> Dict[str, Any]:
    """Coerce parameters in-place based on schema target types."""
    spec = function_def.get("parameters", {})
    fn_name = function_def.get("name", "")

    if fn_name == "fn_format_template" and "Format template:" in query:
        extracted = query.split("Format template:", 1)[1].strip()
        if extracted:
            parameters["template"] = extracted

    for k, v in list(parameters.items()):
        p_type = spec.get(k, {}).get("type", "")
        if p_type in ("string", "str") and isinstance(v, str):
            parameters[k] = v.strip()
        elif p_type in ("float", "number"):
            try:
                parameters[k] = float(v)
            except (ValueError, TypeError):
                pass
        elif p_type in ("int", "integer"):
            try:
                parameters[k] = int(v)
            except (ValueError, TypeError):
                pass
    return parameters
