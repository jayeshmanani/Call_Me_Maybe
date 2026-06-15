import os
from pathlib import Path


class CachingConfig:
    def __init__(self, root: Path):
        self.root = root
        self.hf_root = root / ".hf"

    @property
    def env(self):
        return {
            "UV_CACHE_DIR": self.root / ".uv-cache",
            "TMPDIR": self.root / ".tmp",
            "HF_HOME": self.hf_root,
            "TRANSFORMERS_CACHE": self.hf_root / "transformers",
            "HUGGINGFACE_HUB_CACHE": self.hf_root / "hub",
        }

    @property
    def dirs(self):
        return set(self.env.values())


def init_caching_dirs() -> None:
    """Init Caching Dirs in Goinfre"""
    cfg = CachingConfig(Path("/goinfre/jmanani"))

    for k, v in cfg.env.items():
        os.environ.setdefault(k, str(v))

    for d in cfg.dirs:
        d.mkdir(parents=True, exist_ok=True)
