import json
import sys
from pathlib import Path

from aethervr.config import Config


def load_config(config: Config):
    try:
        with open(get_config_path(), "r") as file:
            data = json.load(file)
        
        config.deserialize(data)
        print("Config loaded")
    except Exception:
        print("Failed to load config")


def save_config(config: Config):
    with open(get_config_path(), "w") as file:
        data = config.serialize()
        json.dump(data, file, indent=2)

    print("Config saved")


def get_config_path():
    return Path(sys.argv[0]).parent / "config.json"
