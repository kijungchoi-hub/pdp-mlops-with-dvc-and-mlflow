from pathlib import Path
import os

import yaml


def ensure_dirs(*dirs: str) -> None:
    for directory in dirs:
        Path(directory).mkdir(parents=True, exist_ok=True)


def load_params(path: str = "params.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_env(name: str, default: str) -> str:
    return os.getenv(name, default)
