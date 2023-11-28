from .config_models import Config

CONFIG_PATH = "/Users/stanislavserbakov/Desktop/itmo/hpcbot2/setup/config.json"

with open(CONFIG_PATH, "r") as config_file:
    config = Config.model_validate_json(config_file.read())
