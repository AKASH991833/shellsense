from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

from shellsense.database.manager import DatabaseManager
from shellsense.shell.detect import (
    detect_current_shell,
    get_shell_version,
    is_os_supported,
)
from shellsense.shell.installer import is_integrated
from shellsense.utils.config import ConfigManager
from shellsense.utils.logging import get_logger
from shellsense.utils.paths import get_db_path, get_shellsense_dir

logger = get_logger(__name__)

CheckResult = dict[str, Any]


def run_all_checks() -> list[CheckResult]:
    return [
        check_python_version(),
        check_shell_detection(),
        check_os_support(),
        check_configuration(),
        check_database(),
        check_shell_integration(),
        check_completion_scripts(),
        check_permissions(),
        check_dependencies(),
        check_cache_directory(),
    ]


def check_python_version() -> CheckResult:
    import sys

    version = sys.version_info
    ok = version.major >= 3 and version.minor >= 12
    return {
        "name": "Python Version",
        "status": "passed" if ok else "failed",
        "detail": f"{sys.version}",
        "fix": "Python 3.12+ required" if not ok else None,
    }


def check_shell_detection() -> CheckResult:
    try:
        shell = detect_current_shell()
        version = get_shell_version(shell)
        return {
            "name": "Shell Detection",
            "status": "passed",
            "detail": f"Shell: {shell} ({version})",
            "fix": None,
        }
    except Exception as e:
        return {
            "name": "Shell Detection",
            "status": "failed",
            "detail": str(e),
            "fix": "Ensure a supported shell is installed",
        }


def check_os_support() -> CheckResult:
    supported = is_os_supported()
    return {
        "name": "OS Support",
        "status": "passed" if supported else "warning",
        "detail": f"OS: {'' if supported else 'not '}in supported list",
        "fix": None if supported else "ShellSense works best on supported distros",
    }


def check_configuration() -> CheckResult:
    try:
        config = ConfigManager()
        path = config.path
        return {
            "name": "Configuration",
            "status": "passed",
            "detail": f"Config: {path}",
            "fix": None,
        }
    except Exception as e:
        return {
            "name": "Configuration",
            "status": "failed",
            "detail": str(e),
            "fix": "Run 'shellsense config reset' to reset configuration",
        }


def check_database() -> CheckResult:
    try:
        db_path = get_db_path()
        db = DatabaseManager(db_path)
        db.initialize()
        seeded = db.is_seeded()
        db.close()
        return {
            "name": "Database",
            "status": "passed" if seeded else "warning",
            "detail": f"DB: {db_path} (seeded: {seeded})",
            "fix": None if seeded else "Run 'shellsense search' to seed the database",
        }
    except Exception as e:
        return {
            "name": "Database",
            "status": "failed",
            "detail": str(e),
            "fix": "Check permissions on ~/.shellsense/",
        }


def check_shell_integration() -> CheckResult:
    try:
        shell = detect_current_shell()
        integrated = is_integrated(shell)
        return {
            "name": "Shell Integration",
            "status": "passed" if integrated else "warning",
            "detail": f"Shell: {shell} (integrated: {integrated})",
            "fix": None if integrated else "Run 'shellsense install' to integrate",
        }
    except Exception as e:
        return {
            "name": "Shell Integration",
            "status": "failed",
            "detail": str(e),
            "fix": "Run 'shellsense install' to install shell integration",
        }


def check_completion_scripts() -> CheckResult:
    completion_dir = Path.home() / ".shellsense"
    found = (
        list(completion_dir.glob("shellsense-completion.*"))
        if completion_dir.exists()
        else []
    )
    return {
        "name": "Completion Scripts",
        "status": "passed" if found else "warning",
        "detail": f"{len(found)} script(s) found" if found else "No completion scripts",
        "fix": (
            None if found else "Run 'shellsense install' to generate completion scripts"
        ),
    }


def check_permissions() -> CheckResult:
    shellsense_dir = get_shellsense_dir()
    if not shellsense_dir.exists():
        return {
            "name": "Permissions",
            "status": "warning",
            "detail": "ShellSense directory does not exist",
            "fix": "Run a command to create it automatically",
        }
    readable = os.access(shellsense_dir, os.R_OK)
    writable = os.access(shellsense_dir, os.W_OK)
    ok = readable and writable
    return {
        "name": "Permissions",
        "status": "passed" if ok else "failed",
        "detail": f"~/.shellsense/ readable={readable} writable={writable}",
        "fix": "Check directory permissions" if not ok else None,
    }


def check_dependencies() -> CheckResult:
    missing: list[str] = []
    for dep in ["python3", "shellsense"]:
        if not shutil.which(dep):
            missing.append(dep)
    return {
        "name": "Dependencies",
        "status": "passed" if not missing else "failed",
        "detail": f"Missing: {', '.join(missing)}" if missing else "All found",
        "fix": "Install missing dependencies" if missing else None,
    }


def check_cache_directory() -> CheckResult:
    cache_dir = get_shellsense_dir() / "cache"
    if not cache_dir.exists():
        return {
            "name": "Cache Directory",
            "status": "warning",
            "detail": "Cache directory does not exist",
            "fix": None,
        }
    return {
        "name": "Cache Directory",
        "status": "passed",
        "detail": str(cache_dir),
        "fix": None,
    }
