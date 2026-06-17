import json
from pathlib import Path
import sys
from typing import List, Dict


def load_json_file(
    path: Path, label: str
) -> List[Dict[str, Dict[str, object]]] | None:
    """Load a JSON file"""
    if not path.exists():
        print(f"ERROR: {label} file not found: {path}", file=sys.stderr)
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            print(
                f"ERROR: {label} file must contain\
                      a JSON array, got: {type(data).__name__}",
                file=sys.stderr)
            return None
        return data
    except json.JSONDecodeError as e:
        print(f"ERROR: {label} file contains invalid JSON: {e}",
              file=sys.stderr)
        return None
