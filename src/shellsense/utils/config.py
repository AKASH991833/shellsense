import base64
import hashlib
import json
import os
from typing import Any

from shellsense.utils.logging import get_logger
from shellsense.utils.paths import ensure_shellsense_dir, get_config_path

logger = get_logger(__name__)

_KEY_FILE = str(get_config_path().parent / ".keys")


def _get_machine_key() -> bytes:
    parts: list[str] = []
    for path in ["/etc/machine-id", "/var/lib/dbus/machine-id"]:
        try:
            with open(path) as f:
                parts.append(f.read().strip())
        except OSError:
            pass
    try:
        parts.append(os.uname().nodename)
    except AttributeError:
        parts.append("shellsense-default")
    raw = ".".join(parts)
    return hashlib.pbkdf2_hmac("sha256", raw.encode(), b"shellsense-key-v1", 100000, 32)


def _xor_encrypt(data: bytes, key: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))


def encrypt_api_key(api_key: str) -> str:
    key = _get_machine_key()
    encrypted = _xor_encrypt(api_key.encode(), key)
    encoded = base64.b64encode(encrypted).decode()
    keys = _load_key_file()
    keys["ai.api_key"] = encoded
    _save_key_file(keys)
    return encoded


def decrypt_api_key(encoded: str | None = None) -> str:
    if encoded is None:
        keys = _load_key_file()
        encoded = keys.get("ai.api_key", "")
    if not encoded:
        return ""
    try:
        key = _get_machine_key()
        encrypted = base64.b64decode(encoded.encode())
        decrypted = _xor_encrypt(encrypted, key)
        return decrypted.decode()
    except Exception:
        return ""


def _load_key_file() -> dict[str, str]:
    try:
        if os.path.isfile(_KEY_FILE):
            with open(_KEY_FILE) as f:
                data: dict[str, str] = json.load(f)
                return data
    except Exception:
        pass
    return {}


def _save_key_file(keys: dict[str, str]) -> None:
    ensure_shellsense_dir()
    with open(_KEY_FILE, "w") as f:
        json.dump(keys, f, indent=2)
    os.chmod(_KEY_FILE, 0o600)


DEFAULT_CONFIG: dict[str, Any] = {
    "general": {
        "theme": "default",
        "language": "en",
        "verbose": False,
    },
    "logging": {
        "level": "INFO",
        "file": str(get_config_path().parent / "shellsense.log"),
        "max_bytes": 10485760,
        "backup_count": 5,
    },
    "database": {
        "path": str(get_config_path().parent / "shellsense.db"),
        "timeout": 5.0,
    },
    "ai": {
        "enabled": False,
        "provider": "openai",
        "model": "gpt-4o-mini",
        "api_key": "",
        "temperature": 0.3,
        "max_tokens": 1024,
    },
    "suggestions": {
        "enabled": True,
        "max_suggestions": 5,
        "min_confidence": 0.6,
    },
    "correction": {
        "enabled": True,
        "fuzzy_threshold": 0.8,
    },
    "learning": {
        "enabled": False,
        "history_size": 1000,
    },
    "suggestion_engine": {
        "limit": 10,
        "fuzzy_threshold": 60,
        "cache_size": 500,
        "cache_ttl": 300,
    },
    "ranking": {
        "exact_match": 100.0,
        "prefix_match": 80.0,
        "alias_match": 70.0,
        "contains_match": 40.0,
        "fuzzy_match_multiplier": 0.5,
        "category_match": 20.0,
        "popularity_multiplier": 10.0,
        "history_multiplier": 15.0,
        "command_length_penalty": 0.1,
        "edit_distance_bonus": 50.0,
    },
    "shell": {
        "autocomplete_enabled": True,
        "suggestion_delay_ms": 50,
        "suggestion_count": 10,
        "dangerous_command_warnings": True,
        "history_learning": True,
        "prompt_integration": False,
        "theme": "default",
    },
    "shortcuts": {
        "accept_suggestion": "right",
        "cycle_next": "ctrl+n",
        "cycle_previous": "ctrl+p",
        "dismiss": "esc",
        "interactive_help": "ctrl+h",
    },
    "privacy": {
        "share_current_directory": True,
        "share_shell": True,
        "share_operating_system": True,
        "share_distribution": True,
        "share_kernel_version": True,
        "share_user": False,
        "share_hostname": False,
        "share_system_time": False,
        "share_git_repository": False,
        "share_git_branch": False,
        "share_git_status": False,
        "share_history": False,
        "share_environment_variables": False,
        "share_virtual_env": False,
        "share_container_info": False,
        "share_package_managers": False,
        "share_processes": False,
        "share_filesystems": False,
        "share_last_error": True,
        "share_last_command": True,
    },
    "intelligence": {
        "enabled": True,
        "max_history_context": 5,
        "max_log_lines": 100,
    },
    "plugins": {
        "enabled": True,
        "auto_discover": True,
        "auto_load": False,
        "auto_enable": False,
        "sandbox_enabled": False,
        "dir": str(get_config_path().parent / "plugins"),
    },
    "marketplace": {
        "enabled": True,
        "auto_sync": False,
        "verify_signatures": True,
        "offline_mode": False,
    },
    "enterprise": {
        "enabled": False,
        "approved_plugins": [],
        "blocked_plugins": [],
        "mandatory_plugins": [],
    },
}


class ConfigManager:
    def __init__(self, config_path: str | os.PathLike[str] | None = None) -> None:
        self._config_path = (
            os.fspath(config_path) if config_path else str(get_config_path())
        )
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self._config_path) as f:
                self._data = json.load(f)
            merged = False
            for key, value in DEFAULT_CONFIG.items():
                if key not in self._data:
                    self._data[key] = value
                    merged = True
                elif isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        if sub_key not in self._data[key]:
                            self._data[key][sub_key] = sub_val
                            merged = True
            if merged:
                self._save()
            logger.info("Configuration loaded from %s", self._config_path)
        except FileNotFoundError:
            logger.info(
                "No config file found at %s, creating default configuration",
                self._config_path,
            )
            self._data = DEFAULT_CONFIG.copy()
            self._save()
        except json.JSONDecodeError as e:
            logger.warning(
                "Invalid config file at %s: %s. Using defaults.", self._config_path, e
            )
            self._data = DEFAULT_CONFIG.copy()

    def _save(self) -> None:
        ensure_shellsense_dir()
        with open(self._config_path, "w") as f:
            json.dump(self._data, f, indent=2)
        logger.info("Configuration saved to %s", self._config_path)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split(".")
        value = self._data
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        keys = key.split(".")
        target = self._data
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]
        target[keys[-1]] = value
        self._save()

    def all(self) -> dict[str, Any]:
        return self._data.copy()

    def reset(self) -> None:
        self._data = DEFAULT_CONFIG.copy()
        self._save()

    @property
    def path(self) -> str:
        return self._config_path
