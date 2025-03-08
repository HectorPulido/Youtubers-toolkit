"""
Module to load configuration from a JSON file.
"""

import json
from pathlib import Path


def load_config(config_path: str = "config.json") -> dict:
    """
    Load configuration from a JSON file.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Could not find the configuration file: {config_path}")
    with config_file.open("r", encoding="utf-8") as f:
        config = json.load(f)
    return config


# Carga la configuración al importar el módulo
config_data = load_config()
