import configparser
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "fastzip"
CONFIG_FILE = CONFIG_DIR / "config.ini"


def load_config() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    if CONFIG_FILE.exists():
        config.read(CONFIG_FILE, encoding="utf-8")

    config_changed = False

    if not config.has_section("paths"):
        config.add_section("paths")
        default_saves = str(Path.home() / ".local/share/atlauncher/instances/job12110/saves")
        default_zips = str(Path.home() / "Documents/work/worldzips")
        config.set("paths", "source_dir", default_saves)
        config.set("paths", "dest_dir", default_zips)
        config_changed = True

    if not config.has_section("google"):
        config.add_section("google")
        config.set("google", "credentials_path", str(CONFIG_DIR / "credentials.json"))
        config.set("google", "token_path", str(CONFIG_DIR / "token.json"))
        config_changed = True


    if not config.has_option("google", "google_sync"):
        config.set("google", "google_sync", "false")
        config_changed = True

    if not config.has_option("google", "auto_sync"):
        config.set("google", "auto_sync", "false")
        config_changed = True

    if not config.has_option("google", "auto_share"):
        config.set("google", "auto_share", "false")
        config_changed = True


    if config_changed:
        save_config(config)

    return config


def save_config(config: configparser.ConfigParser):
    # Сохранение изменений в конфигурации
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as configfile:
        config.write(configfile)
