"""Configuration loading utilities."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]  # src/utils/ -> project root


@lru_cache()
def load_yaml(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


@lru_cache()
def get_project_config() -> dict:
    return load_yaml("config/project_config.yaml")


@lru_cache()
def get_simulation_assumptions() -> dict:
    return load_yaml("config/simulation_assumptions.yaml")


def get(path: str | Path, *keys, default=None):
    cfg = load_yaml(path)
    cur: object = cfg
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")
