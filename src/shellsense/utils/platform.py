import platform
import subprocess
from dataclasses import dataclass


@dataclass
class SystemInfo:
    system: str
    release: str
    version: str
    architecture: str
    hostname: str
    python_version: str
    distro: str | None = None
    kernel: str | None = None
    shell: str | None = None
    terminal: str | None = None


def get_system_info() -> SystemInfo:
    uname = platform.uname()
    return SystemInfo(
        system=uname.system,
        release=uname.release,
        version=uname.version,
        architecture=uname.machine,
        hostname=uname.node,
        python_version=platform.python_version(),
        distro=_get_distro(),
        kernel=uname.release,
        shell=_get_env_var("SHELL"),
        terminal=_get_env_var("TERM"),
    )


def _get_distro() -> str | None:
    try:
        result = subprocess.run(
            ["lsb_release", "-ds"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip().strip('"')
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    for release_file in ["/etc/os-release", "/usr/lib/os-release"]:
        try:
            with open(release_file) as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        return line.split("=", 1)[1].strip().strip('"')
        except FileNotFoundError:
            continue
    return None


def _get_env_var(name: str) -> str | None:
    import os

    return os.environ.get(name)


def is_linux() -> bool:
    return platform.system() == "Linux"


def is_supported_distro() -> bool:
    if not is_linux():
        return False
    info = get_system_info()
    supported = [
        "ubuntu",
        "debian",
        "kali",
        "fedora",
        "red hat",
        "rocky",
        "alma",
        "arch",
        "opensuse",
    ]
    if info.distro:
        distro_lower = info.distro.lower()
        return any(name in distro_lower for name in supported)
    return True
