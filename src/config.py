import json
import os
from typing import TypedDict

from src.dirs import ligametools_user_dirs


class Config(TypedDict):
    games: list[str]


default_config: Config = {"games": ["queens", "zip", "tango", "mini-sudoku"]}
CONFIG_PATH = os.path.join(ligametools_user_dirs.user_config_dir, "config.json")


def load_config() -> Config:
    config = default_config.copy()
    if os.path.isfile(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                loaded = json.load(f)
            config.update(loaded)
        except Exception:
            raise
    return config


def _save_config(config: Config):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except Exception:
        raise
