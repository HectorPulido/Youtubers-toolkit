import json
from pathlib import Path


def load_config(config_path: str = "config.json") -> dict:
    """
    Carga la configuración desde un archivo JSON.

    Args:
        config_path (str): Ruta del archivo JSON de configuración.

    Returns:
        dict: Configuración cargada.
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo de configuración: {config_path}"
        )
    with config_file.open("r", encoding="utf-8") as f:
        config = json.load(f)
    return config


# Carga la configuración al importar el módulo
config_data = load_config()
