import configparser
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "fastzip"
CONFIG_FILE = CONFIG_DIR / "config.ini"


def load_config() -> configparser.ConfigParser:
    """Загружает конфиг, если его нет — создает базовую структуру."""
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE, encoding="utf-8")

    if not config.has_section("paths"):
        config.add_section("paths")
        default_saves = str(Path.home() / ".local/share/atlauncher/instances/job12110/saves")
        default_zips = str(Path.home() / "Documents/work/worldzips")
        config.set("paths", "source_dir", default_saves)
        config.set("paths", "dest_dir", default_zips)
        save_config(config)

    return config


def save_config(config: configparser.ConfigParser):
    """Сохраняет изменения в файл конфигурации."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as configfile:
        config.write(configfile)