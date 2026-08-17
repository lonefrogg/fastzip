import configparser
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "fastzip"
CONFIG_FILE = CONFIG_DIR / "config.ini"


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE, encoding="utf-8")

    default_saves = str(Path.home() / ".local/share/atlauncher/instances/job12110/saves")
    default_zips = str(Path.home() / "Documents/work/worldzips")
    config_updated = False

    sections = {
        "paths" : {
            "source_dir" : default_saves,
            "dest_dir" : default_zips
        },
        "google" : {
            "google_sync" : "false",
            "auto_sync" : "false",
            "auto_share" : "false",
            "credentials_path" : str(CONFIG_DIR / "credentials.json"),
            "token_path" : str(CONFIG_DIR / "token.json")
        }
    }

    for section_name, section_dict in sections.items():
        if not config.has_section(section_name):
            config.add_section(section_name)
            config_updated = True
        for option_name, option_value in section_dict.items():
            if not config.has_option(section_name, option_name):
                config.set(section_name, option_name, option_value)
                config_updated = True

    if config_updated:
        save_config(config)

    return config


def save_config(config: configparser.ConfigParser):
    # Сохранение изменений в конфигурации
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as configfile:
        config.write(configfile)
