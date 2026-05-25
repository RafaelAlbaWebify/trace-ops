import json
from pathlib import Path
from typing import Any, Dict, Iterable

from .config import SAMPLES_DIR


def list_sample_files(samples_dir: Path = SAMPLES_DIR) -> Iterable[Path]:
    return sorted(samples_dir.glob("*.json"))


def load_sample_file(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as sample_file:
        return json.load(sample_file)


def load_all_samples(samples_dir: Path = SAMPLES_DIR) -> Dict[str, Dict[str, Any]]:
    return {path.stem: load_sample_file(path) for path in list_sample_files(samples_dir)}
