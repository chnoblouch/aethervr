import json

from aethervr.config import Config


CONFIG_FILE_NAME = "config.json"


def load_config(config: Config):
    try:
        with open(CONFIG_FILE_NAME, "r") as file:
            data = json.load(file)
        
        config.deserialize(data)
        print("Config loaded")
    except Exception:
        print("Failed to load config")


def save_config(config: Config):
    with open(CONFIG_FILE_NAME, "w") as file:
        data = config.serialize()
        json.dump(data, file, indent=2)

    print("Config saved")