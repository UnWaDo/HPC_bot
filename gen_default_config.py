from HPC_bot.utils.config import Config


config = Config()
with open('config_example.json', 'w+', encoding='utf-8') as f:
    f.write(config.model_dump_json(indent=2))
