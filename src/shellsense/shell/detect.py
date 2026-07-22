from __future__ import annotations

import os
import platform
from pathlib import Path

SHELL_NAMES: dict[str, str] = {
    "bash": "bash",
    "zsh": "zsh",
    "fish": "fish",
}

SUPPORTED_OS: dict[str, str] = {
    "ubuntu": "Ubuntu",
    "debian": "Debian",
    "kali": "Kali Linux",
    "linuxmint": "Linux Mint",
    "fedora": "Fedora",
    "rhel": "RHEL",
    "rocky": "Rocky Linux",
    "almalinux": "AlmaLinux",
    "arch": "Arch Linux",
    "manjaro": "Manjaro",
    "opensuse": "openSUSE",
}

SHELL_CONFIG_FILES: dict[str, list[str]] = {
    "bash": [".bashrc", ".bash_profile", ".profile"],
    "zsh": [".zshrc", ".zprofile", ".zshenv"],
    "fish": ["config.fish"],
}


def detect_current_shell() -> str:
    shell = os.environ.get("SHELL", "")
    if not shell:
        return "bash"
    for name, key in SHELL_NAMES.items():
        if key in shell:
            return name
    return "bash"


def detect_os() -> str:
    try:
        import distro
    except ImportError:
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        return line.strip().split("=", 1)[1].strip().strip('"').lower()
            with open("/etc/lsb-release") as f:
                for line in f:
                    if line.startswith("DISTRIB_ID="):
                        return line.strip().split("=", 1)[1].strip().lower()
        except FileNotFoundError:
            pass
        return platform.system().lower()
    return distro.id().lower() if hasattr(distro, "id") else "linux"


def is_os_supported() -> bool:
    os_id = detect_os()
    return os_id in SUPPORTED_OS


def get_config_files(shell: str) -> list[Path]:
    home = Path.home()
    files: list[str] = SHELL_CONFIG_FILES.get(shell, [])
    result: list[Path] = []
    for f in files:
        path = home / f
        if path.exists():
            result.append(path)
    if not result:
        for f in files:
            path = home / f
            result.append(path)
            break
    return result


def get_shell_config_path(shell: str) -> Path:
    files = get_config_files(shell)
    if files:
        return files[0]
    home = Path.home()
    defaults: dict[str, str] = {
        "bash": ".bashrc",
        "zsh": ".zshrc",
        "fish": "config.fish",
    }
    return home / defaults.get(shell, ".bashrc")


def get_shell_version(shell: str) -> str:
    import subprocess

    try:
        result = subprocess.run(
            [shell, "--version"], capture_output=True, text=True, timeout=5
        )
        return result.stdout.split("\n")[0] if result.stdout else "unknown"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def get_backup_path(filepath: Path) -> Path:
    return filepath.with_suffix(filepath.suffix + ".shellsense.bak")
