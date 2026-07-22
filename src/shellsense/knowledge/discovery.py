from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from shellsense.utils.logging import get_logger

logger = get_logger(__name__)

CommandDict = dict[str, Any]

_MAN_CACHE: dict[str, str] = {}
_MAN_CACHE_TTL: int = 86400
_MAN_CACHE_LAST: float = 0.0

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "files": [
        "ls",
        "cp",
        "mv",
        "rm",
        "mkdir",
        "touch",
        "find",
        "locate",
        "chmod",
        "chown",
        "ln",
        "stat",
        "du",
        "df",
        "tree",
        "rename",
        "umask",
        "file",
        "basename",
        "dirname",
        "readlink",
        "realpath",
        "mktemp",
    ],
    "text": [
        "cat",
        "less",
        "more",
        "head",
        "tail",
        "grep",
        "sed",
        "awk",
        "sort",
        "uniq",
        "cut",
        "tr",
        "wc",
        "diff",
        "patch",
        "vim",
        "nano",
        "echo",
        "printf",
        "tee",
        "nl",
        "fold",
        "fmt",
        "pr",
        "paste",
        "join",
        "comm",
        "cmp",
        "expand",
        "unexpand",
        "rev",
    ],
    "processes": [
        "ps",
        "top",
        "htop",
        "kill",
        "pkill",
        "nice",
        "renice",
        "nohup",
        "bg",
        "fg",
        "jobs",
        "strace",
        "ltrace",
        "pidof",
        "pgrep",
        "pstack",
        "timeout",
        "watch",
        "crontab",
        "at",
        "batch",
    ],
    "permissions": [
        "chmod",
        "chown",
        "chgrp",
        "umask",
        "setfacl",
        "getfacl",
        "sudo",
        "su",
        "visudo",
        "passwd",
    ],
    "users": [
        "who",
        "whoami",
        "id",
        "useradd",
        "usermod",
        "userdel",
        "groupadd",
        "groupmod",
        "groupdel",
        "passwd",
        "finger",
        "last",
        "logname",
        "sudo",
        "su",
    ],
    "disk": [
        "df",
        "du",
        "fdisk",
        "parted",
        "mkfs",
        "mount",
        "umount",
        "blkid",
        "lsblk",
        "fsck",
        "e2fsck",
        "resize2fs",
        "tune2fs",
        "dd",
        "badblocks",
        "smartctl",
        "iostat",
    ],
    "archives": [
        "tar",
        "gzip",
        "gunzip",
        "bzip2",
        "bunzip2",
        "xz",
        "unxz",
        "zip",
        "unzip",
        "7z",
        "rar",
        "unrar",
        "zcat",
        "zless",
        "zgrep",
        "zstd",
    ],
    "networking": [
        "ping",
        "curl",
        "wget",
        "ssh",
        "scp",
        "sftp",
        "netstat",
        "ss",
        "ip",
        "ifconfig",
        "nslookup",
        "dig",
        "host",
        "traceroute",
        "nmap",
        "tcpdump",
        "iptables",
        "ufw",
        "firewall-cmd",
        "nmcli",
        "nmtui",
        "iwconfig",
        "iwlist",
        "ethtool",
        "mtr",
        "whois",
        "nc",
        "telnet",
        "ftp",
    ],
    "packages": [
        "apt",
        "apt-get",
        "apt-cache",
        "dpkg",
        "snap",
        "flatpak",
        "yum",
        "dnf",
        "rpm",
        "pacman",
        "zypper",
        "brew",
        "pip",
        "pip3",
        "npm",
        "cargo",
        "gem",
    ],
    "system": [
        "uname",
        "hostname",
        "dmesg",
        "systemctl",
        "journalctl",
        "uptime",
        "free",
        "lscpu",
        "lsusb",
        "lspci",
        "lsmod",
        "modprobe",
        "insmod",
        "rmmod",
        "depmod",
        "sysctl",
        "timedatectl",
        "locale",
        "localectl",
        "hostnamectl",
        "loginctl",
        "shutdown",
        "reboot",
        "halt",
        "poweroff",
        "init",
        "service",
    ],
    "git": [
        "git",
        "git-add",
        "git-commit",
        "git-push",
        "git-pull",
        "git-clone",
        "git-branch",
        "git-checkout",
        "git-merge",
        "git-rebase",
        "git-log",
        "git-diff",
        "git-status",
        "git-stash",
        "git-tag",
        "git-fetch",
        "git-remote",
        "git-config",
    ],
    "docker": [
        "docker",
        "docker-compose",
        "docker-run",
        "docker-build",
        "docker-ps",
        "docker-images",
        "docker-exec",
        "docker-logs",
        "docker-volume",
        "docker-network",
        "podman",
        "containerd",
    ],
    "security": [
        "openssl",
        "gpg",
        "gpg2",
        "ssh-keygen",
        "ssh-keyscan",
        "ssh-agent",
        "ssh-add",
        "certbot",
        "letsencrypt",
        "keytool",
        "cfssl",
    ],
    "python": [
        "python",
        "python3",
        "pip",
        "pip3",
        "pytest",
        "python3-config",
        "venv",
        "virtualenv",
    ],
    "performance": [
        "perf",
        "strace",
        "ltrace",
        "valgrind",
        "gdb",
        "time",
        "bench",
        "hyperfine",
        "flamegraph",
        "bpftrace",
        "sysdig",
    ],
    "development": [
        "make",
        "cmake",
        "gcc",
        "g++",
        "clang",
        "rustc",
        "go",
        "javac",
        "node",
        "npm",
        "yarn",
        "npx",
        "tsc",
        "gdb",
        "ldd",
        "objdump",
        "readelf",
        "nm",
        "strip",
        "ar",
    ],
}

CATEGORY_FALLBACK = "system"


def _guess_category(name: str) -> str:
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if name in keywords:
            return cat
    parts = Path(name).name.lower()
    if any(c in parts for c in ["git", "hub"]):
        return "git"
    if any(c in parts for c in ["docker", "podman", "container"]):
        return "docker"
    if any(c in parts for c in ["ssh", "scp", "sftp"]):
        return "networking"
    if any(c in parts for c in ["apt", "dpkg", "rpm", "yum", "dnf", "pacman", "pip"]):
        return "packages"
    if any(c in parts for c in ["python"]):
        return "python"
    if any(c in parts for c in ["chmod", "chown", "chgrp", "umask", "acl"]):
        return "permissions"
    if any(c in parts for c in ["user", "group", "passwd", "who"]):
        return "users"
    return CATEGORY_FALLBACK


def scan_system_commands() -> list[str]:
    seen: set[str] = set()
    commands: list[str] = []

    paths = os.environ.get("PATH", "/usr/bin:/bin").split(":")
    for p in paths:
        try:
            d = Path(p)
            if not d.is_dir():
                continue
            for entry in d.iterdir():
                if not entry.is_file() and not entry.is_symlink():
                    continue
                if not os.access(str(entry), os.X_OK, follow_symlinks=True):
                    continue
                name = entry.name
                if name.startswith("."):
                    continue
                if name not in seen:
                    seen.add(name)
                    commands.append(name)
        except PermissionError:
            continue
        except OSError:
            continue

    commands.sort()
    logger.info("Scanned %d system commands from PATH", len(commands))
    return commands


def get_command_path(name: str) -> str | None:
    return shutil.which(name)


def _get_cached_man(name: str) -> str:
    now = time.time()
    global _MAN_CACHE_LAST
    if now - _MAN_CACHE_LAST > _MAN_CACHE_TTL:
        _MAN_CACHE.clear()
    _MAN_CACHE_LAST = now
    if name in _MAN_CACHE:
        return _MAN_CACHE[name]
    try:
        result = subprocess.run(
            ["man", name],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            text = result.stdout.strip()
            text = _strip_man_formatting(text)
            _MAN_CACHE[name] = text
            return text
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    _MAN_CACHE[name] = ""
    return ""


def get_description_via_whatis(name: str) -> str:
    try:
        result = subprocess.run(
            ["whatis", name],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )
        if result.returncode == 0 and result.stdout.strip():
            line = result.stdout.strip().split("\n")[0]
            parts = line.split(" - ", 1)
            if len(parts) == 2:
                return parts[1].strip()
            return line
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ""


def get_description_via_man(name: str) -> str:
    text = _get_cached_man(name)
    if not text:
        return ""
    match = re.search(
        r"NAME\s+\S+\s+\-\-\s+(.+?)(?:\n\n|\n\s*\n)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        desc = match.group(1).strip()
        desc = re.sub(r"\s+", " ", desc)
        return desc[:500]
    return ""


def _strip_man_formatting(text: str) -> str:
    text = re.sub(r".\b", "", text)
    text = re.sub(r"_\b", "", text)
    text = text.replace("\x08", "")
    return text


def get_description_via_help(name: str) -> str:
    try:
        result = subprocess.run(
            [name, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=3,
        )
        if result.returncode == 0 and result.stdout.strip():
            first_line = result.stdout.strip().split("\n")[0]
            return first_line[:200]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return ""


def get_description(name: str) -> str:
    desc = get_description_via_whatis(name)
    if desc:
        return desc
    desc = get_description_via_man(name)
    if desc:
        return desc
    desc = get_description_via_help(name)
    if desc:
        return desc
    return ""


def get_syntax_via_man(name: str) -> str:
    text = _get_cached_man(name)
    if not text:
        return ""
    match = re.search(
        r"SYNOPSIS\s+(.+?)(?:\n\n|\n\s*\n)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        syn = match.group(1).strip()
        syn = re.sub(r"\s+", " ", syn)
        return syn[:300]
    return ""


def get_options_via_man(name: str) -> list[dict[str, str]]:
    text = _get_cached_man(name)
    if not text:
        return []
    options: list[dict[str, str]] = []
    in_options = False
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^(OPTIONS|OPTION)", line, re.IGNORECASE):
            in_options = True
            i += 1
            continue
        if in_options and re.match(
            r"^(ENVIRONMENT|FILES|EXAMPLES|SEE ALSO|BUGS|HISTORY|AUTHOR)",
            line,
            re.IGNORECASE,
        ):
            break
        if in_options:
            flag_match = re.match(r"^\s*(-[a-zA-Z0-9]|--[a-zA-Z0-9_-]+)", line)
            if flag_match:
                flag = flag_match.group(1).strip()
                desc_parts: list[str] = []
                i += 1
                while (
                    i < len(lines)
                    and lines[i].strip()
                    and not re.match(r"^\s*-[a-zA-Z0-9]|^\s*--[a-zA-Z0-9_-]", lines[i])
                ):
                    desc_parts.append(lines[i].strip())
                    i += 1
                desc = " ".join(desc_parts).strip()[:200] if desc_parts else ""
                if flag and desc:
                    options.append({"flag": flag, "description": desc})
                continue
        i += 1
    return options[:15]


def discover_command(name: str) -> CommandDict | None:
    cmd_path = get_command_path(name)
    if not cmd_path:
        logger.debug("Command '%s' not found in PATH, skipping", name)
        return None
    description = get_description(name)
    if not description:
        logger.debug("No description found for '%s', skipping", name)
        return None
    category = _guess_category(name)
    syntax = get_syntax_via_man(name)
    options = get_options_via_man(name)
    return {
        "name": name,
        "aliases": [],
        "short_description": description[:200],
        "long_description": description,
        "syntax": syntax or f"{name} [options]",
        "category": category,
        "difficulty": "intermediate",
        "risk_level": "SAFE",
        "availability": "linux",
        "official_docs": "",
        "keywords": f"{name} {category}",
        "notes": "",
        "warnings": "",
        "examples": [],
        "options": options,
        "common_errors": [],
        "related_commands": [],
        "tags": [category, "auto-discovered"],
    }


def discover_all(
    progress_callback: Any = None,
    max_commands: int = 500,
    workers: int = 10,
) -> list[CommandDict]:
    all_commands = scan_system_commands()
    logger.info(
        "Starting discovery of %d commands with %d workers",
        len(all_commands),
        workers,
    )
    discovered: list[CommandDict] = []
    skipped = 0
    limit = min(max_commands, len(all_commands))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_name = {
            executor.submit(discover_command, name): name
            for i, name in enumerate(all_commands[:limit])
        }
        completed = 0
        for future in as_completed(future_to_name):
            completed += 1
            name = future_to_name[future]
            if progress_callback:
                progress_callback(completed, limit, name)
            try:
                cmd = future.result()
                if cmd:
                    discovered.append(cmd)
                else:
                    skipped += 1
            except Exception as e:
                logger.debug("Failed to discover '%s': %s", name, e)
                skipped += 1
    logger.info(
        "Discovery complete: %d discovered, %d skipped",
        len(discovered),
        skipped,
    )
    return discovered
