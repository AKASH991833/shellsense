from __future__ import annotations

import sys

from shellsense import __version__


def check_python_version(min_version: str = "3.12") -> tuple[bool, str]:
    current = f"{sys.version_info.major}.{sys.version_info.minor}"
    if _compare_versions(current, min_version) < 0:
        return False, f"Python >= {min_version} required, found {current}"
    return True, ""


def check_shellsense_version(
    min_version: str, max_version: str = ""
) -> tuple[bool, str]:
    current = __version__

    if min_version and _compare_versions(current, min_version) < 0:
        return (
            False,
            f"ShellSense >= {min_version} required, current is {current}",
        )

    if max_version and _compare_versions(current, max_version) > 0:
        return (
            False,
            f"ShellSense <= {max_version} required, current is {current}",
        )

    return True, ""


def check_platform(target: str = "linux") -> tuple[bool, str]:
    import platform

    system = platform.system().lower()
    if system != target:
        return False, f"Platform '{target}' required, current is '{system}'"
    return True, ""


def _compare_versions(v1: str, v2: str) -> int:
    parts1 = [int(p) for p in v1.split(".") if p.isdigit()]
    parts2 = [int(p) for p in v2.split(".") if p.isdigit()]
    for a, b in zip(parts1, parts2):
        if a < b:
            return -1
        if a > b:
            return 1
    if len(parts1) < len(parts2):
        return -1
    if len(parts1) > len(parts2):
        return 1
    return 0
