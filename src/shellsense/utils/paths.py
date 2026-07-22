from pathlib import Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent


def get_shellsense_dir() -> Path:
    return Path.home() / ".shellsense"


def get_config_path() -> Path:
    return get_shellsense_dir() / "config.json"


def get_log_path() -> Path:
    return get_shellsense_dir() / "shellsense.log"


def get_db_path() -> Path:
    return get_shellsense_dir() / "shellsense.db"


def get_cache_dir() -> Path:
    return get_shellsense_dir() / "cache"


def get_plugins_dir() -> Path:
    return get_shellsense_dir() / "plugins"


def get_examples_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "plugins" / "examples"


def get_conversations_dir() -> Path:
    return get_shellsense_dir() / "conversations"


def get_backup_dir() -> Path:
    return get_shellsense_dir() / "backups"


def ensure_shellsense_dir() -> Path:
    path = get_shellsense_dir()
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    config_path = get_config_path()
    if config_path.exists():
        config_path.chmod(0o600)
    return path
