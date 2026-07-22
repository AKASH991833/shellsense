from __future__ import annotations

from typing import Any

CommandDict = dict[str, Any]

SYSTEM_INFO: dict[str, Any] = {
    "version": 1,
    "title": "ShellSense AI command knowledge base",
    "description": "Offline command knowledge base for Linux terminal assistance",
}


def _cmd(
    name: str,
    category: str,
    short_description: str,
    long_description: str,
    syntax: str,
    difficulty: str = "beginner",
    risk_level: str = "SAFE",
    availability: str = "linux",
    aliases: list[str] | None = None,
    official_docs: str = "",
    keywords: str = "",
    notes: str = "",
    warnings: str = "",
    examples: list[dict[str, str]] | None = None,
    options: list[dict[str, str]] | None = None,
    common_errors: list[dict[str, str]] | None = None,
    related_commands: list[dict[str, str]] | None = None,
    tags: list[str] | None = None,
) -> CommandDict:
    return {
        "name": name,
        "aliases": aliases or [],
        "short_description": short_description,
        "long_description": long_description,
        "syntax": syntax,
        "category": category,
        "difficulty": difficulty,
        "risk_level": risk_level,
        "availability": availability,
        "official_docs": official_docs,
        "keywords": keywords,
        "notes": notes,
        "warnings": warnings,
        "examples": examples or [],
        "options": options or [],
        "common_errors": common_errors or [],
        "related_commands": related_commands or [],
        "tags": tags or [],
    }


_COMMANDS_DATA: list[dict[str, Any]] = [
    # ── Files ──────────────────────────────────────────────────────────
    _cmd(
        "ls",
        "files",
        "List directory contents",
        "Lists information about files and directories. Supports many options for output format, sorting, and filtering.",
        "ls [OPTION]... [FILE]...",
        keywords="list, directory, files, ls, dir",
        notes="One of the most frequently used Linux commands.",
        official_docs="https://man7.org/linux/man-pages/man1/ls.1.html",
        examples=[
            dict(
                title="Basic listing",
                command="ls",
                output="Documents  Downloads  Music",
                description="List files in current directory.",
            ),
            dict(
                title="Detailed listing",
                command="ls -l",
                output="-rw-r--r-- 1 user user 1024 Mar 15 file.txt",
                description="Long format with permissions and size.",
            ),
            dict(
                title="Show hidden",
                command="ls -a",
                output=".  ..  .bashrc  file.txt",
                description="Include hidden files.",
            ),
        ],
        options=[
            dict(flag="-l", description="Long format"),
            dict(flag="-a", description="Show hidden files"),
            dict(flag="-h", description="Human-readable sizes"),
            dict(flag="-R", description="Recursive"),
        ],
        common_errors=[
            dict(
                error_pattern="No such file or directory",
                explanation="Path does not exist.",
                solution="Check the path spelling.",
            )
        ],
        related_commands=[
            dict(name="find", relationship="file search"),
            dict(name="tree", relationship="directory tree"),
        ],
        tags=["files", "listing"],
    ),
    _cmd(
        "cd",
        "files",
        "Change directory",
        "Changes the current working directory. With no argument, changes to the home directory.",
        "cd [DIRECTORY]",
        keywords="change, directory, navigate, cd",
        notes="cd is a shell built-in, not a standalone binary.",
        examples=[
            dict(
                title="Go home",
                command="cd",
                output="",
                description="Change to home directory.",
            ),
            dict(
                title="Go to directory",
                command="cd /var/log",
                output="",
                description="Change to /var/log.",
            ),
            dict(
                title="Parent directory",
                command="cd ..",
                output="",
                description="Move up one level.",
            ),
        ],
        common_errors=[
            dict(
                error_pattern="No such file or directory",
                explanation="Directory does not exist.",
                solution="Check the path.",
            )
        ],
        related_commands=[
            dict(name="pwd", relationship="print working directory"),
            dict(name="pushd", relationship="directory stack"),
        ],
        tags=["files", "navigation"],
    ),
    _cmd(
        "pwd",
        "files",
        "Print working directory",
        "Outputs the full path of the current working directory.",
        "pwd",
        keywords="print, working, directory, current, path",
        notes="Use $PWD in scripts.",
        examples=[
            dict(
                title="Current path",
                command="pwd",
                output="/home/user/projects",
                description="Display current directory.",
            )
        ],
        related_commands=[
            dict(name="cd", relationship="change directory"),
            dict(name="dirname", relationship="strip path"),
        ],
        tags=["files", "navigation"],
    ),
    _cmd(
        "mkdir",
        "files",
        "Create directories",
        "Creates one or more directories. Supports parent directory creation and permission setting.",
        "mkdir [OPTION]... DIRECTORY...",
        keywords="make, directory, create, folder",
        examples=[
            dict(
                title="Single directory",
                command="mkdir new_folder",
                output="",
                description="Create a directory.",
            ),
            dict(
                title="Nested directories",
                command="mkdir -p parent/child/grandchild",
                output="",
                description="Create parent directories as needed.",
            ),
            dict(
                title="With permissions",
                command="mkdir -m 700 secret",
                output="",
                description="Create with rwx------.",
            ),
        ],
        options=[
            dict(flag="-p", description="Create parent directories"),
            dict(flag="-m", description="Set permissions"),
        ],
        common_errors=[
            dict(
                error_pattern="File exists",
                explanation="Name already exists.",
                solution="Use a different name.",
            )
        ],
        related_commands=[
            dict(name="rmdir", relationship="remove empty directories"),
            dict(name="rm", relationship="remove files"),
        ],
        tags=["files", "directories"],
    ),
    _cmd(
        "rm",
        "files",
        "Remove files or directories",
        "Removes files and directories. Use with extreme caution.",
        "rm [OPTION]... [FILE]...",
        risk_level="DANGEROUS",
        keywords="remove, delete, rm",
        warnings="rm -rf / destroys your system. Double-check paths.",
        examples=[
            dict(
                title="Remove file",
                command="rm file.txt",
                output="",
                description="Remove file.",
            ),
            dict(
                title="Interactive",
                command="rm -i file.txt",
                output="rm: remove file?",
                description="Prompt before removal.",
            ),
            dict(
                title="Recursive",
                command="rm -rf dir/",
                output="",
                description="Remove directory and contents.",
            ),
        ],
        options=[
            dict(flag="-f", description="Force"),
            dict(flag="-i", description="Interactive"),
            dict(flag="-r", description="Recursive"),
        ],
        common_errors=[
            dict(
                error_pattern="Cannot remove",
                explanation="Permission denied.",
                solution="Check permissions or use sudo.",
            )
        ],
        related_commands=[
            dict(name="rmdir", relationship="remove empty dirs"),
            dict(name="shred", relationship="secure delete"),
        ],
        tags=["files", "delete", "dangerous"],
    ),
    _cmd(
        "cp",
        "files",
        "Copy files and directories",
        "Copies files and directories from source to destination.",
        "cp [OPTION]... SOURCE... DEST",
        risk_level="CAUTION",
        keywords="copy, duplicate, cp",
        examples=[
            dict(
                title="Copy file",
                command="cp file.txt backup.txt",
                output="",
                description="Copy file.",
            ),
            dict(
                title="Copy directory",
                command="cp -r src/ dest/",
                output="",
                description="Copy entire directory.",
            ),
            dict(
                title="Archive mode",
                command="cp -a project/ backup/",
                output="",
                description="Preserve all attributes.",
            ),
        ],
        options=[
            dict(flag="-r", description="Recursive"),
            dict(flag="-a", description="Archive mode"),
            dict(flag="-i", description="Interactive"),
            dict(flag="-u", description="Update if newer"),
        ],
        common_errors=[
            dict(
                error_pattern="Cannot stat",
                explanation="Source not found.",
                solution="Verify source path.",
            )
        ],
        related_commands=[
            dict(name="mv", relationship="move files"),
            dict(name="rsync", relationship="advanced copy"),
        ],
        tags=["files", "copy"],
    ),
    _cmd(
        "mv",
        "files",
        "Move or rename files",
        "Moves or renames files and directories.",
        "mv [OPTION]... SOURCE... DEST",
        risk_level="CAUTION",
        keywords="move, rename, mv",
        examples=[
            dict(
                title="Rename",
                command="mv old.txt new.txt",
                output="",
                description="Rename file.",
            ),
            dict(
                title="Move to directory",
                command="mv file.txt /target/dir/",
                output="",
                description="Move file.",
            ),
        ],
        options=[
            dict(flag="-i", description="Interactive"),
            dict(flag="-f", description="Force"),
            dict(flag="-u", description="Update if newer"),
        ],
        related_commands=[
            dict(name="cp", relationship="copy files"),
            dict(name="rename", relationship="batch rename"),
        ],
        tags=["files", "move", "rename"],
    ),
    _cmd(
        "touch",
        "files",
        "Create empty file or update timestamp",
        "Updates file timestamps. Creates an empty file if it does not exist.",
        "touch [OPTION]... FILE...",
        keywords="create, file, timestamp, touch",
        examples=[
            dict(
                title="Create file",
                command="touch main.py",
                output="",
                description="Create empty file.",
            ),
            dict(
                title="Update timestamp",
                command="touch existing.txt",
                output="",
                description="Update to current time.",
            ),
        ],
        options=[
            dict(flag="-a", description="Change access time"),
            dict(flag="-m", description="Change modification time"),
        ],
        related_commands=[
            dict(name="mkdir", relationship="create directories"),
            dict(name="stat", relationship="view timestamps"),
        ],
        tags=["files", "create"],
    ),
    _cmd(
        "find",
        "files",
        "Search for files in directory hierarchy",
        "Recursively searches the directory tree for files matching criteria like name, type, size, and date.",
        "find [PATH...] [EXPRESSION]",
        difficulty="intermediate",
        keywords="search, find, file, recursive",
        notes="Combine with -exec to act on found files.",
        examples=[
            dict(
                title="By name",
                command="find /home -name '*.txt'",
                output="/home/user/file.txt",
                description="Find .txt files.",
            ),
            dict(
                title="By type",
                command="find . -type d",
                output="./subdir",
                description="Find directories.",
            ),
            dict(
                title="By size",
                command="find / -size +100M",
                output="/var/log/syslog",
                description="Files larger than 100MB.",
            ),
        ],
        options=[
            dict(flag="-name", description="Match name"),
            dict(flag="-type", description="Filter by type"),
            dict(flag="-size", description="Filter by size"),
            dict(flag="-exec", description="Execute command"),
        ],
        related_commands=[
            dict(name="locate", relationship="fast file search"),
            dict(name="grep", relationship="search contents"),
        ],
        tags=["files", "search"],
    ),
    _cmd(
        "tree",
        "files",
        "Display directory tree structure",
        "Recursively lists directories and files in a tree-like format.",
        "tree [OPTION]... [DIRECTORY]",
        keywords="directory, tree, structure",
        examples=[
            dict(
                title="Show tree",
                command="tree",
                output=".\\n├── docs\\n└── src",
                description="Display directory tree.",
            ),
            dict(
                title="Directories only",
                command="tree -d",
                output=".\\n├── docs\\n└── src",
                description="Show only directories.",
            ),
        ],
        options=[
            dict(flag="-d", description="Directories only"),
            dict(flag="-L", description="Limit depth"),
        ],
        related_commands=[
            dict(name="ls", relationship="list contents"),
            dict(name="find", relationship="search files"),
        ],
        tags=["files", "visualization"],
    ),
    # ── Text Processing ────────────────────────────────────────────────
    _cmd(
        "grep",
        "text",
        "Search text using patterns",
        "Searches input files for lines matching a regular expression pattern.",
        "grep [OPTION]... PATTERN [FILE]...",
        difficulty="intermediate",
        keywords="search, pattern, regex, grep",
        notes="Use -r for recursive, -i for case-insensitive.",
        official_docs="https://man7.org/linux/man-pages/man1/grep.1.html",
        examples=[
            dict(
                title="Simple search",
                command="grep 'error' log.txt",
                output="[ERROR] failed",
                description="Find lines containing 'error'.",
            ),
            dict(
                title="Case-insensitive",
                command="grep -i 'warning' log.txt",
                output="[WARNING] low disk",
                description="Case-insensitive search.",
            ),
            dict(
                title="Recursive",
                command="grep -r 'TODO' .",
                output="./src/main.py:12: TODO",
                description="Search recursively.",
            ),
            dict(
                title="Count matches",
                command="grep -c 'error' log.txt",
                output="42",
                description="Count matches.",
            ),
        ],
        options=[
            dict(flag="-i", description="Case-insensitive"),
            dict(flag="-r", description="Recursive"),
            dict(flag="-v", description="Invert match"),
            dict(flag="-c", description="Count"),
            dict(flag="-n", description="Line numbers"),
        ],
        common_errors=[
            dict(
                error_pattern="No such file",
                explanation="File not found.",
                solution="Check file path.",
            )
        ],
        related_commands=[
            dict(name="sed", relationship="stream editor"),
            dict(name="awk", relationship="text processing"),
            dict(name="ripgrep", relationship="faster alternative"),
        ],
        tags=["text", "search", "regex"],
    ),
    _cmd(
        "sed",
        "text",
        "Stream editor for text transformation",
        "A stream editor for filtering and transforming text using sed scripts.",
        "sed [OPTION]... [SCRIPT] [FILE]...",
        difficulty="advanced",
        risk_level="CAUTION",
        keywords="stream, editor, substitute, sed",
        warnings="Always test without -i first.",
        official_docs="https://man7.org/linux/man-pages/man1/sed.1.html",
        examples=[
            dict(
                title="Substitute",
                command="sed 's/old/new/' file.txt",
                output="new text",
                description="Replace first occurrence per line.",
            ),
            dict(
                title="Global replace",
                command="sed 's/old/new/g' file.txt",
                output="new new text",
                description="Replace all occurrences.",
            ),
            dict(
                title="In-place edit",
                command="sed -i.bak 's/foo/bar/g' config.txt",
                output="",
                description="Edit with backup.",
            ),
        ],
        options=[
            dict(flag="-i", description="In-place edit"),
            dict(flag="-n", description="Suppress printing"),
            dict(flag="-E", description="Extended regex"),
        ],
        related_commands=[
            dict(name="awk", relationship="text processing"),
            dict(name="grep", relationship="pattern search"),
        ],
        tags=["text", "editor", "advanced"],
    ),
    _cmd(
        "awk",
        "text",
        "Pattern scanning and text processing language",
        "A powerful programming language for text processing and report generation.",
        "awk [OPTION]... [PROGRAM] [FILE]...",
        difficulty="advanced",
        keywords="awk, text, columns, scripting",
        official_docs="https://man7.org/linux/man-pages/man1/awk.1.html",
        examples=[
            dict(
                title="Print column",
                command="awk '{print $1}' file.txt",
                output="col1",
                description="Print first column.",
            ),
            dict(
                title="Filter rows",
                command="awk '$3 > 100 {print $1}' data.txt",
                output="item",
                description="Print where col3 > 100.",
            ),
            dict(
                title="Field separator",
                command="awk -F: '{print $1}' /etc/passwd",
                output="root",
                description="Use colon separator.",
            ),
        ],
        options=[
            dict(flag="-F", description="Field separator"),
            dict(flag="-v", description="Assign variable"),
        ],
        related_commands=[
            dict(name="sed", relationship="stream editor"),
            dict(name="cut", relationship="column extraction"),
        ],
        tags=["text", "scripting", "advanced"],
    ),
    _cmd(
        "cut",
        "text",
        "Remove sections from each line of files",
        "Extracts sections from each line using field delimiters or character positions.",
        "cut OPTION... [FILE]...",
        keywords="cut, column, field, extract",
        examples=[
            dict(
                title="First field",
                command="cut -d: -f1 /etc/passwd",
                output="root",
                description="Extract first field by colon.",
            ),
            dict(
                title="Character range",
                command="cut -c1-10 file.txt",
                output="first 10 c",
                description="First 10 characters.",
            ),
        ],
        options=[
            dict(flag="-d", description="Delimiter"),
            dict(flag="-f", description="Fields"),
            dict(flag="-c", description="Characters"),
        ],
        related_commands=[
            dict(name="awk", relationship="field extraction"),
            dict(name="paste", relationship="merge columns"),
        ],
        tags=["text", "columns"],
    ),
    # ── Permissions ────────────────────────────────────────────────────
    _cmd(
        "chmod",
        "permissions",
        "Change file mode bits",
        "Changes file permissions (read, write, execute) for owner, group, and others.",
        "chmod [OPTION]... MODE FILE...",
        difficulty="intermediate",
        risk_level="CAUTION",
        keywords="permissions, chmod, mode, access",
        warnings="chmod 777 grants access to everyone.",
        official_docs="https://man7.org/linux/man-pages/man1/chmod.1.html",
        examples=[
            dict(
                title="Add execute",
                command="chmod +x script.sh",
                output="",
                description="Make executable.",
            ),
            dict(
                title="Octal mode",
                command="chmod 755 script.sh",
                output="",
                description="Set rwxr-xr-x.",
            ),
            dict(
                title="Symbolic",
                command="chmod u=rw,go=r file.txt",
                output="",
                description="Owner rw, others r.",
            ),
        ],
        options=[
            dict(flag="-R", description="Recursive"),
            dict(flag="-v", description="Verbose"),
        ],
        common_errors=[
            dict(
                error_pattern="Operation not permitted",
                explanation="Not file owner.",
                solution="Use sudo.",
            )
        ],
        related_commands=[
            dict(name="chown", relationship="change owner"),
            dict(name="umask", relationship="default permissions"),
        ],
        tags=["permissions", "security"],
    ),
    _cmd(
        "chown",
        "permissions",
        "Change file owner and group",
        "Changes the owner and/or group of files. Only root can change ownership.",
        "chown [OPTION]... [OWNER][:[GROUP]] FILE...",
        difficulty="intermediate",
        risk_level="CAUTION",
        keywords="owner, chown, group, change",
        official_docs="https://man7.org/linux/man-pages/man1/chown.1.html",
        examples=[
            dict(
                title="Change owner",
                command="sudo chown alice file.txt",
                output="",
                description="Set alice as owner.",
            ),
            dict(
                title="Owner and group",
                command="sudo chown alice:dev file.txt",
                output="",
                description="Change both owner and group.",
            ),
        ],
        options=[dict(flag="-R", description="Recursive")],
        related_commands=[
            dict(name="chmod", relationship="change permissions"),
            dict(name="chgrp", relationship="change group"),
        ],
        tags=["permissions", "owner"],
    ),
    _cmd(
        "umask",
        "permissions",
        "Set default file creation permissions",
        "Sets the default permission mask for newly created files and directories.",
        "umask [MASK]",
        difficulty="intermediate",
        keywords="umask, permissions, mask, default",
        examples=[
            dict(
                title="View umask",
                command="umask",
                output="0022",
                description="Show current umask.",
            ),
            dict(
                title="Set restrictive",
                command="umask 077",
                output="",
                description="New files: rwx------.",
            ),
        ],
        related_commands=[dict(name="chmod", relationship="change permissions")],
        tags=["permissions", "mask"],
    ),
    # ── Users ───────────────────────────────────────────────────────────
    _cmd(
        "useradd",
        "users",
        "Create a new user",
        "Creates a new user account on the system.",
        "useradd [OPTION]... USERNAME",
        difficulty="intermediate",
        risk_level="CAUTION",
        keywords="user, create, add, useradd",
        official_docs="https://man7.org/linux/man-pages/man8/useradd.8.html",
        examples=[
            dict(
                title="Create user",
                command="sudo useradd -m -s /bin/bash newuser",
                output="",
                description="Create with home dir and bash.",
            )
        ],
        options=[
            dict(flag="-m", description="Create home dir"),
            dict(flag="-s", description="Login shell"),
            dict(flag="-G", description="Supplementary groups"),
        ],
        common_errors=[
            dict(
                error_pattern="already exists",
                explanation="User already exists.",
                solution="Choose different name.",
            )
        ],
        related_commands=[
            dict(name="usermod", relationship="modify users"),
            dict(name="userdel", relationship="delete users"),
        ],
        tags=["users", "administration"],
    ),
    _cmd(
        "usermod",
        "users",
        "Modify a user account",
        "Modifies user account settings including groups, shell, and home directory.",
        "usermod [OPTION]... USERNAME",
        difficulty="intermediate",
        risk_level="CAUTION",
        keywords="user, modify, usermod",
        examples=[
            dict(
                title="Add to group",
                command="sudo usermod -aG sudo alice",
                output="",
                description="Add alice to sudo group.",
            ),
            dict(
                title="Change shell",
                command="sudo usermod -s /bin/zsh alice",
                output="",
                description="Change to zsh.",
            ),
        ],
        options=[
            dict(flag="-aG", description="Append groups"),
            dict(flag="-s", description="Change shell"),
            dict(flag="-L", description="Lock account"),
        ],
        related_commands=[
            dict(name="useradd", relationship="create users"),
            dict(name="userdel", relationship="delete users"),
        ],
        tags=["users", "modify"],
    ),
    _cmd(
        "passwd",
        "users",
        "Change user password",
        "Changes the password for a user account.",
        "passwd [USERNAME]",
        keywords="password, passwd, security",
        official_docs="https://man7.org/linux/man-pages/man1/passwd.1.html",
        examples=[
            dict(
                title="Own password",
                command="passwd",
                output="Current password:",
                description="Change your password.",
            ),
            dict(
                title="Other user",
                command="sudo passwd alice",
                output="New password:",
                description="Root changes alice's password.",
            ),
        ],
        options=[
            dict(flag="-l", description="Lock account"),
            dict(flag="-S", description="Show status"),
        ],
        related_commands=[dict(name="useradd", relationship="create users")],
        tags=["users", "password"],
    ),
    _cmd(
        "sudo",
        "users",
        "Execute command as superuser",
        "Allows authorized users to run commands as root based on /etc/sudoers policy.",
        "sudo [OPTION]... COMMAND",
        risk_level="DANGEROUS",
        keywords="sudo, root, superuser, privilege",
        warnings="sudo rm -rf / destroys the system.",
        official_docs="https://man7.org/linux/man-pages/man8/sudo.8.html",
        examples=[
            dict(
                title="Run as root",
                command="sudo apt update",
                output="[sudo] password:",
                description="Update package lists.",
            ),
            dict(
                title="Root shell",
                command="sudo -i",
                output="root@host:~#",
                description="Interactive root shell.",
            ),
        ],
        options=[
            dict(flag="-u", description="Run as user"),
            dict(flag="-i", description="Login shell"),
            dict(flag="-k", description="Reset credentials"),
        ],
        common_errors=[
            dict(
                error_pattern="not in sudoers",
                explanation="User not authorized.",
                solution="Add user to sudo group via visudo.",
            )
        ],
        related_commands=[
            dict(name="su", relationship="switch user"),
            dict(name="visudo", relationship="edit sudoers"),
        ],
        tags=["users", "privilege", "essential"],
    ),
    # ── Processes ───────────────────────────────────────────────────────
    _cmd(
        "ps",
        "processes",
        "Report process status",
        "Displays information about running processes.",
        "ps [OPTION]...",
        keywords="ps, process, status, PID",
        official_docs="https://man7.org/linux/man-pages/man1/ps.1.html",
        examples=[
            dict(
                title="All processes",
                command="ps aux",
                output="USER PID %CPU %MEM COMMAND",
                description="Show all processes.",
            ),
            dict(
                title="Process tree",
                command="ps -ejH",
                output="  PID  PGID   SID CMD",
                description="Hierarchy view.",
            ),
        ],
        options=[
            dict(flag="aux", description="All processes"),
            dict(flag="-ef", description="Full listing"),
            dict(flag="-eo", description="Custom output"),
        ],
        related_commands=[
            dict(name="top", relationship="real-time monitor"),
            dict(name="kill", relationship="terminate processes"),
        ],
        tags=["processes", "monitoring"],
    ),
    _cmd(
        "top",
        "processes",
        "Display processes in real-time",
        "Shows real-time view of running processes with CPU, memory, and swap usage.",
        "top [OPTION]...",
        keywords="top, process, real-time, CPU, memory",
        notes="Press 'q' to quit, 'h' for help.",
        official_docs="https://man7.org/linux/man-pages/man1/top.1.html",
        examples=[
            dict(
                title="Start top",
                command="top",
                output="top - 10:30:42 up 3 days",
                description="Launch interactive viewer.",
            )
        ],
        options=[
            dict(flag="-u", description="Filter by user"),
            dict(flag="-p", description="Monitor specific PID"),
            dict(flag="-b", description="Batch mode"),
        ],
        related_commands=[
            dict(name="ps", relationship="process snapshot"),
            dict(name="htop", relationship="enhanced top"),
        ],
        tags=["processes", "monitoring"],
    ),
    _cmd(
        "kill",
        "processes",
        "Send signal to a process",
        "Sends a signal to a process. Default signal is SIGTERM (15). SIGKILL (9) forcefully ends it.",
        "kill [OPTION]... PID...",
        difficulty="intermediate",
        risk_level="DANGEROUS",
        keywords="kill, signal, terminate, PID",
        official_docs="https://man7.org/linux/man-pages/man1/kill.1.html",
        examples=[
            dict(
                title="Graceful stop",
                command="kill 1234",
                output="",
                description="Send SIGTERM.",
            ),
            dict(
                title="Force kill",
                command="kill -9 1234",
                output="",
                description="Send SIGKILL.",
            ),
            dict(
                title="List signals",
                command="kill -l",
                output="SIGHUP SIGINT SIGQUIT SIGKILL SIGTERM",
                description="List available signals.",
            ),
        ],
        common_errors=[
            dict(
                error_pattern="No such process",
                explanation="Process not found.",
                solution="Check PID with ps.",
            )
        ],
        related_commands=[
            dict(name="pkill", relationship="kill by name"),
            dict(name="killall", relationship="kill by exact name"),
        ],
        tags=["processes", "kill", "dangerous"],
    ),
    _cmd(
        "crontab",
        "processes",
        "Manage cron jobs",
        "Schedules commands to run at specific times. Each user has their own crontab.",
        "crontab [OPTION]...",
        difficulty="intermediate",
        risk_level="CAUTION",
        keywords="cron, schedule, job, crontab",
        notes="Format: minute hour day month weekday command.",
        official_docs="https://man7.org/linux/man-pages/man1/crontab.1.html",
        examples=[
            dict(
                title="Edit crontab",
                command="crontab -e",
                output="",
                description="Open crontab editor.",
            ),
            dict(
                title="List jobs",
                command="crontab -l",
                output="0 2 * * * /backup.sh",
                description="List cron jobs.",
            ),
            dict(
                title="Every 5 min",
                command="crontab -e",
                output="*/5 * * * * /check.sh",
                description="Run every 5 minutes.",
            ),
        ],
        options=[
            dict(flag="-e", description="Edit"),
            dict(flag="-l", description="List"),
            dict(flag="-r", description="Remove"),
        ],
        related_commands=[
            dict(name="at", relationship="one-time tasks"),
            dict(name="systemctl", relationship="systemd timers"),
        ],
        tags=["processes", "schedule", "cron"],
    ),
    # ── Disk ────────────────────────────────────────────────────────────
    _cmd(
        "df",
        "disk",
        "Display disk space usage",
        "Shows available and used disk space on mounted filesystems.",
        "df [OPTION]... [FILE]...",
        keywords="disk, space, df, filesystem",
        official_docs="https://man7.org/linux/man-pages/man1/df.1.html",
        examples=[
            dict(
                title="Human-readable",
                command="df -h",
                output="Filesystem Size Used Avail Use% Mounted on",
                description="Show disk usage.",
            ),
            dict(
                title="Inode usage",
                command="df -i",
                output="",
                description="Show inode usage.",
            ),
        ],
        options=[
            dict(flag="-h", description="Human-readable"),
            dict(flag="-T", description="Show FS type"),
            dict(flag="-i", description="Inodes"),
        ],
        related_commands=[
            dict(name="du", relationship="directory space"),
            dict(name="lsblk", relationship="block devices"),
        ],
        tags=["disk", "storage"],
    ),
    _cmd(
        "du",
        "disk",
        "Estimate file and directory space usage",
        "Summarizes disk usage. Useful for finding space hogs.",
        "du [OPTION]... [FILE]...",
        keywords="du, disk, usage, size",
        examples=[
            dict(
                title="Directory size",
                command="du -sh /home/user",
                output="1.5G    /home/user",
                description="Total size.",
            ),
            dict(
                title="Largest dirs",
                command="du -sh /* | sort -h",
                output="5.0G    /home",
                description="Find large directories.",
            ),
        ],
        options=[
            dict(flag="-h", description="Human-readable"),
            dict(flag="-s", description="Summary"),
            dict(flag="--max-depth", description="Limit depth"),
        ],
        related_commands=[
            dict(name="df", relationship="disk free space"),
            dict(name="lsblk", relationship="block devices"),
        ],
        tags=["disk", "usage"],
    ),
    _cmd(
        "lsblk",
        "disk",
        "List block devices",
        "Lists information about all block devices in a tree format.",
        "lsblk [OPTION]... [DEVICE]",
        keywords="lsblk, block, device, disk",
        official_docs="https://man7.org/linux/man-pages/man8/lsblk.8.html",
        examples=[
            dict(
                title="All devices",
                command="lsblk",
                output="NAME MAJ:MIN RM SIZE RO TYPE MOUNTPOINT",
                description="List block devices.",
            ),
            dict(
                title="With filesystem",
                command="lsblk -f",
                output="NAME FSTYPE LABEL UUID",
                description="Show filesystem info.",
            ),
        ],
        options=[
            dict(flag="-f", description="Filesystem info"),
            dict(flag="-m", description="Permissions"),
        ],
        related_commands=[
            dict(name="df", relationship="disk space"),
            dict(name="fdisk", relationship="partition editor"),
        ],
        tags=["disk", "devices"],
    ),
    # ── Archives ────────────────────────────────────────────────────────
    _cmd(
        "tar",
        "archives",
        "Archive and extract files",
        "Creates and extracts archive files (tarballs). Supports gzip, bzip2, and xz compression.",
        "tar [OPTION...] [FILE]...",
        difficulty="intermediate",
        risk_level="CAUTION",
        keywords="tar, archive, compress, extract",
        official_docs="https://man7.org/linux/man-pages/man1/tar.1.html",
        examples=[
            dict(
                title="Create archive",
                command="tar -czf archive.tar.gz dir/",
                output="",
                description="Create gzipped tarball.",
            ),
            dict(
                title="Extract",
                command="tar -xzf archive.tar.gz",
                output="",
                description="Extract tarball.",
            ),
            dict(
                title="List contents",
                command="tar -tzf archive.tar.gz",
                output="file1.txt",
                description="List without extracting.",
            ),
            dict(
                title="Extract to dir",
                command="tar -xzf archive.tar.gz -C /target",
                output="",
                description="Extract to specific directory.",
            ),
        ],
        options=[
            dict(flag="-c", description="Create"),
            dict(flag="-x", description="Extract"),
            dict(flag="-z", description="gzip"),
            dict(flag="-j", description="bzip2"),
            dict(flag="-f", description="Filename"),
        ],
        related_commands=[
            dict(name="gzip", relationship="compress files"),
            dict(name="zip", relationship="cross-platform archiver"),
        ],
        tags=["archives", "compression"],
    ),
    _cmd(
        "gzip",
        "archives",
        "Compress or decompress files",
        "Compresses files using LZ77 coding. Produces .gz files.",
        "gzip [OPTION]... [FILE]...",
        keywords="gzip, compress, gunzip, decompress",
        official_docs="https://man7.org/linux/man-pages/man1/gzip.1.html",
        examples=[
            dict(
                title="Compress",
                command="gzip file.txt",
                output="",
                description="Compress to file.txt.gz.",
            ),
            dict(
                title="Decompress",
                command="gunzip file.txt.gz",
                output="",
                description="Restore original file.",
            ),
            dict(
                title="Keep original",
                command="gzip -k file.txt",
                output="",
                description="Compress but keep original.",
            ),
        ],
        options=[
            dict(flag="-d", description="Decompress"),
            dict(flag="-k", description="Keep original"),
            dict(flag="-1..-9", description="Compression level"),
        ],
        related_commands=[
            dict(name="tar", relationship="archiver"),
            dict(name="bzip2", relationship="alternative compression"),
        ],
        tags=["archives", "compress"],
    ),
    # ── Networking ──────────────────────────────────────────────────────
    _cmd(
        "ping",
        "networking",
        "Test network connectivity",
        "Sends ICMP ECHO_REQUEST packets to test reachability and measure latency.",
        "ping [OPTION]... DESTINATION",
        keywords="ping, network, latency, ICMP",
        official_docs="https://man7.org/linux/man-pages/man8/ping.8.html",
        examples=[
            dict(
                title="Test host",
                command="ping -c 4 google.com",
                output="64 bytes from 142.250.80.46: icmp_seq=1 ttl=118 time=14ms",
                description="Send 4 pings.",
            )
        ],
        options=[
            dict(flag="-c", description="Packet count"),
            dict(flag="-i", description="Interval"),
            dict(flag="-4/-6", description="IP version"),
        ],
        common_errors=[
            dict(
                error_pattern="Name or service not known",
                explanation="DNS failed.",
                solution="Check DNS settings.",
            )
        ],
        related_commands=[
            dict(name="traceroute", relationship="trace path"),
            dict(name="curl", relationship="HTTP requests"),
        ],
        tags=["networking", "connectivity"],
    ),
    _cmd(
        "curl",
        "networking",
        "Transfer data from/to a server",
        "Command-line tool for data transfer using HTTP, HTTPS, FTP, and more.",
        "curl [OPTION]... URL",
        difficulty="intermediate",
        keywords="curl, HTTP, API, download",
        official_docs="https://curl.se/docs/manpage.html",
        examples=[
            dict(
                title="Fetch URL",
                command="curl https://api.example.com/data",
                output='{"key": "value"}',
                description="Fetch API data.",
            ),
            dict(
                title="Download file",
                command="curl -O https://example.com/file.zip",
                output="",
                description="Download with original name.",
            ),
            dict(
                title="POST request",
                command="curl -X POST -d '{\"name\":\"test\"}' -H 'Content-Type: application/json' https://api.example.com/create",
                output="",
                description="Send JSON POST.",
            ),
        ],
        options=[
            dict(flag="-o", description="Output to file"),
            dict(flag="-L", description="Follow redirects"),
            dict(flag="-X", description="HTTP method"),
            dict(flag="-H", description="Custom headers"),
        ],
        common_errors=[
            dict(
                error_pattern="Could not resolve",
                explanation="DNS failed.",
                solution="Check URL.",
            )
        ],
        related_commands=[
            dict(name="wget", relationship="download tool"),
            dict(name="ping", relationship="connectivity"),
        ],
        tags=["networking", "HTTP", "API"],
    ),
    _cmd(
        "wget",
        "networking",
        "Retrieve files from the web",
        "Non-interactive downloader supporting HTTP, HTTPS, and FTP.",
        "wget [OPTION]... URL",
        keywords="wget, download, HTTP",
        official_docs="https://man7.org/linux/man-pages/man1/wget.1.html",
        examples=[
            dict(
                title="Download",
                command="wget https://example.com/file.zip",
                output="Saving to: file.zip",
                description="Download file.",
            ),
            dict(
                title="Resume",
                command="wget -c https://example.com/large.iso",
                output="",
                description="Resume interrupted download.",
            ),
        ],
        options=[
            dict(flag="-c", description="Resume"),
            dict(flag="-O", description="Output file"),
            dict(flag="-P", description="Directory prefix"),
            dict(flag="-q", description="Quiet"),
        ],
        related_commands=[dict(name="curl", relationship="HTTP tool")],
        tags=["networking", "download"],
    ),
    _cmd(
        "ssh",
        "networking",
        "Secure Shell (remote login)",
        "Connects to a remote machine using the encrypted SSH protocol.",
        "ssh [OPTION]... [USER@]HOST [COMMAND]",
        difficulty="intermediate",
        keywords="ssh, remote, secure, shell",
        official_docs="https://man7.org/linux/man-pages/man1/ssh.1.html",
        examples=[
            dict(
                title="Connect",
                command="ssh user@192.168.1.100",
                output="user@192.168.1.100's password:",
                description="SSH to remote server.",
            ),
            dict(
                title="Run command",
                command="ssh user@server 'ls -la'",
                output="total 24",
                description="Execute remote command.",
            ),
            dict(
                title="Port forward",
                command="ssh -L 8080:localhost:80 user@server",
                output="",
                description="Forward local port 8080 to remote 80.",
            ),
        ],
        options=[
            dict(flag="-p", description="Port"),
            dict(flag="-i", description="Identity file"),
            dict(flag="-L", description="Local forward"),
            dict(flag="-v", description="Verbose"),
        ],
        common_errors=[
            dict(
                error_pattern="Connection refused",
                explanation="SSH server not running.",
                solution="Check sshd status.",
            ),
            dict(
                error_pattern="Permission denied",
                explanation="Key auth failed.",
                solution="Check authorized_keys.",
            ),
        ],
        related_commands=[
            dict(name="scp", relationship="secure copy"),
            dict(name="ssh-keygen", relationship="generate keys"),
        ],
        tags=["networking", "ssh", "remote"],
    ),
    _cmd(
        "scp",
        "networking",
        "Secure copy over SSH",
        "Copies files between hosts over the SSH protocol.",
        "scp [OPTION]... [[USER@]HOST:]SOURCE [[USER@]HOST:]DEST",
        difficulty="intermediate",
        keywords="scp, copy, SSH, transfer",
        examples=[
            dict(
                title="Copy to remote",
                command="scp file.txt user@server:/path/",
                output="",
                description="Upload file.",
            ),
            dict(
                title="Copy from remote",
                command="scp user@server:/file.txt .",
                output="",
                description="Download file.",
            ),
            dict(
                title="Copy directory",
                command="scp -r dir/ user@server:/path/",
                output="",
                description="Recursive copy.",
            ),
        ],
        options=[
            dict(flag="-r", description="Recursive"),
            dict(flag="-P", description="Port"),
            dict(flag="-C", description="Compression"),
        ],
        related_commands=[
            dict(name="ssh", relationship="remote shell"),
            dict(name="rsync", relationship="advanced sync"),
        ],
        tags=["networking", "copy", "SSH"],
    ),
    _cmd(
        "ip",
        "networking",
        "Show/manipulate network interfaces and routing",
        "Modern tool for managing network interfaces, IP addresses, and routing tables.",
        "ip [OPTION]... OBJECT [COMMAND]...",
        difficulty="intermediate",
        risk_level="CAUTION",
        keywords="ip, network, interface, route",
        examples=[
            dict(
                title="Show addresses",
                command="ip addr show",
                output="1: lo: inet 127.0.0.1/8",
                description="Show IP addresses.",
            ),
            dict(
                title="Routing table",
                command="ip route show",
                output="default via 192.168.1.1 dev eth0",
                description="Show routes.",
            ),
        ],
        options=[
            dict(flag="addr", description="IP addresses"),
            dict(flag="link", description="Interfaces"),
            dict(flag="route", description="Routing"),
        ],
        related_commands=[
            dict(name="ifconfig", relationship="legacy config"),
            dict(name="nmcli", relationship="NetworkManager"),
        ],
        tags=["networking", "interfaces"],
    ),
    # ── Package Managers ────────────────────────────────────────────────
    _cmd(
        "apt",
        "packages",
        "Debian/Ubuntu package manager",
        "High-level package management for Debian-based distributions.",
        "apt [COMMAND] [PACKAGE...]",
        risk_level="CAUTION",
        availability="debian",
        keywords="apt, package, install, debian, ubuntu",
        examples=[
            dict(
                title="Update lists",
                command="sudo apt update",
                output="Hit:1 http://archive.ubuntu.com",
                description="Refresh package index.",
            ),
            dict(
                title="Install",
                command="sudo apt install nginx",
                output="Reading package lists...",
                description="Install nginx.",
            ),
            dict(
                title="Upgrade",
                command="sudo apt upgrade",
                output="0 upgraded, 0 newly installed",
                description="Upgrade all packages.",
            ),
            dict(
                title="Search",
                command="apt search python",
                output="python3 - Python interpreter",
                description="Search packages.",
            ),
        ],
        common_errors=[
            dict(
                error_pattern="Unable to locate",
                explanation="Package not found.",
                solution="Run apt update first.",
            ),
            dict(
                error_pattern="Could not open lock",
                explanation="Another apt running.",
                solution="Wait or kill process.",
            ),
        ],
        related_commands=[dict(name="dpkg", relationship="low-level Debian tool")],
        tags=["packages", "apt", "debian"],
    ),
    _cmd(
        "dnf",
        "packages",
        "Fedora/RHEL package manager",
        "Package manager for Fedora, RHEL, Rocky Linux, and AlmaLinux.",
        "dnf [COMMAND] [PACKAGE...]",
        risk_level="CAUTION",
        availability="rhel",
        keywords="dnf, yum, package, fedora, RHEL",
        examples=[
            dict(
                title="Install",
                command="sudo dnf install nginx",
                output="Installed: nginx",
                description="Install nginx.",
            ),
            dict(
                title="Search",
                command="dnf search python",
                output="python3.x86_64 : Python",
                description="Search packages.",
            ),
        ],
        related_commands=[
            dict(name="rpm", relationship="RPM tool"),
            dict(name="yum", relationship="legacy DNF"),
        ],
        tags=["packages", "dnf", "fedora"],
    ),
    _cmd(
        "pacman",
        "packages",
        "Arch Linux package manager",
        "Package manager for Arch Linux and derivatives.",
        "pacman [OPTION]... [PACKAGE...]",
        difficulty="intermediate",
        risk_level="CAUTION",
        availability="arch",
        keywords="pacman, arch, package",
        examples=[
            dict(
                title="Install",
                command="sudo pacman -S nginx",
                output="resolving dependencies...",
                description="Install nginx.",
            ),
            dict(
                title="System upgrade",
                command="sudo pacman -Syu",
                output="",
                description="Full system upgrade.",
            ),
        ],
        options=[
            dict(flag="-S", description="Synchronize"),
            dict(flag="-R", description="Remove"),
            dict(flag="-Q", description="Query"),
            dict(flag="-U", description="Install local"),
        ],
        related_commands=[dict(name="yay", relationship="AUR helper")],
        tags=["packages", "arch"],
    ),
    _cmd(
        "zypper",
        "packages",
        "openSUSE package manager",
        "Package manager for openSUSE and SUSE Linux Enterprise.",
        "zypper [COMMAND] [PACKAGE...]",
        risk_level="CAUTION",
        availability="suse",
        keywords="zypper, suse, opensuse, package",
        examples=[
            dict(
                title="Install",
                command="sudo zypper install nginx",
                output="Resolving dependencies...",
                description="Install nginx.",
            ),
            dict(
                title="Update",
                command="sudo zypper update",
                output="",
                description="Update all packages.",
            ),
        ],
        related_commands=[dict(name="rpm", relationship="RPM tool")],
        tags=["packages", "suse"],
    ),
    # ── System ──────────────────────────────────────────────────────────
    _cmd(
        "systemctl",
        "system",
        "Control systemd services and system state",
        "Central management tool for systemd, controlling services, timers, sockets, and system state.",
        "systemctl [OPTION]... COMMAND [UNIT...]",
        difficulty="intermediate",
        risk_level="CAUTION",
        keywords="systemctl, systemd, service, unit",
        warnings="Disabling critical services can make the system unbootable.",
        official_docs="https://man7.org/linux/man-pages/man1/systemctl.1.html",
        examples=[
            dict(
                title="Start service",
                command="sudo systemctl start nginx",
                output="",
                description="Start nginx.",
            ),
            dict(
                title="Enable at boot",
                command="sudo systemctl enable nginx",
                output="Created symlink...",
                description="Enable nginx on boot.",
            ),
            dict(
                title="Check status",
                command="systemctl status nginx",
                output="active (running)",
                description="Show service status.",
            ),
            dict(
                title="List services",
                command="systemctl list-units --type=service --state=running",
                output="nginx.service loaded active running",
                description="List running services.",
            ),
        ],
        options=[
            dict(flag="start", description="Start unit"),
            dict(flag="stop", description="Stop unit"),
            dict(flag="restart", description="Restart"),
            dict(flag="enable", description="Enable at boot"),
            dict(flag="status", description="Show status"),
        ],
        common_errors=[
            dict(
                error_pattern="Failed to start",
                explanation="Service failed.",
                solution="Check journalctl -u servicename.",
            )
        ],
        related_commands=[
            dict(name="journalctl", relationship="query logs"),
            dict(name="service", relationship="legacy manager"),
        ],
        tags=["system", "systemd", "services"],
    ),
    _cmd(
        "journalctl",
        "system",
        "Query systemd journal logs",
        "Queries and displays logs from the systemd journal with filtering by time, unit, and priority.",
        "journalctl [OPTION]...",
        difficulty="intermediate",
        keywords="journalctl, logs, journal, systemd",
        official_docs="https://man7.org/linux/man-pages/man1/journalctl.1.html",
        examples=[
            dict(
                title="All logs",
                command="journalctl",
                output="-- Logs begin at ...",
                description="Show all journal logs.",
            ),
            dict(
                title="Follow",
                command="journalctl -f",
                output="",
                description="Follow new entries.",
            ),
            dict(
                title="By service",
                command="journalctl -u nginx",
                output="",
                description="Filter by service.",
            ),
            dict(
                title="By time",
                command="journalctl --since '1 hour ago'",
                output="",
                description="Last hour of logs.",
            ),
        ],
        options=[
            dict(flag="-u", description="By unit"),
            dict(flag="-f", description="Follow"),
            dict(flag="-p", description="By priority"),
            dict(flag="--since", description="Start time"),
        ],
        related_commands=[
            dict(name="systemctl", relationship="service manager"),
            dict(name="dmesg", relationship="kernel messages"),
        ],
        tags=["system", "logs", "journald"],
    ),
    _cmd(
        "uname",
        "system",
        "Print system information",
        "Displays kernel name, hostname, kernel release, architecture, and OS.",
        "uname [OPTION]...",
        keywords="uname, system, kernel, architecture",
        examples=[
            dict(
                title="All info",
                command="uname -a",
                output="Linux hostname 6.5.0-15 x86_64 GNU/Linux",
                description="All system info.",
            ),
            dict(
                title="Kernel",
                command="uname -r",
                output="6.5.0-15-generic",
                description="Kernel version only.",
            ),
        ],
        options=[
            dict(flag="-a", description="All"),
            dict(flag="-r", description="Kernel release"),
            dict(flag="-m", description="Architecture"),
        ],
        related_commands=[
            dict(name="hostnamectl", relationship="systemd hostname"),
            dict(name="lsb_release", relationship="distro info"),
        ],
        tags=["system", "kernel"],
    ),
    _cmd(
        "free",
        "system",
        "Display memory usage",
        "Shows total, used, and available memory including RAM and swap.",
        "free [OPTION]...",
        keywords="free, memory, RAM, swap",
        examples=[
            dict(
                title="Human-readable",
                command="free -h",
                output="total used free shared buff/cache available",
                description="Memory usage.",
            )
        ],
        options=[
            dict(flag="-h", description="Human-readable"),
            dict(flag="-m", description="MB"),
            dict(flag="-s", description="Repeat N seconds"),
        ],
        related_commands=[
            dict(name="top", relationship="process memory"),
            dict(name="vmstat", relationship="system perf"),
        ],
        tags=["system", "memory"],
    ),
    # ── Git ─────────────────────────────────────────────────────────────
    _cmd(
        "git",
        "git",
        "Distributed version control system",
        "A distributed version control system for tracking changes in source code.",
        "git [COMMAND] [ARG...]",
        difficulty="intermediate",
        keywords="git, version, control, vcs",
        notes="The most widely used version control system.",
        official_docs="https://git-scm.com/docs",
        examples=[
            dict(
                title="Initialize repo",
                command="git init",
                output="Initialized empty Git repository",
                description="Create new repository.",
            ),
            dict(
                title="Clone repo",
                command="git clone https://github.com/user/repo.git",
                output="Cloning into 'repo'...",
                description="Clone remote repository.",
            ),
            dict(
                title="Check status",
                command="git status",
                output="On branch main",
                description="Show working tree status.",
            ),
        ],
        related_commands=[
            dict(name="git-clone", relationship="clone repos"),
            dict(name="git-commit", relationship="commit changes"),
            dict(name="git-push", relationship="push changes"),
        ],
        tags=["git", "vcs", "version-control"],
    ),
    _cmd(
        "git-clone",
        "git",
        "Clone a repository into a new directory",
        "Clones a remote Git repository into a local directory.",
        "git clone [OPTION]... URL [DIRECTORY]",
        difficulty="intermediate",
        keywords="git, clone, repository, remote",
        official_docs="https://git-scm.com/docs/git-clone",
        examples=[
            dict(
                title="Clone HTTPS",
                command="git clone https://github.com/user/repo.git",
                output="Cloning into 'repo'...",
                description="Clone via HTTPS.",
            ),
            dict(
                title="Clone SSH",
                command="git clone git@github.com:user/repo.git",
                output="Cloning into 'repo'...",
                description="Clone via SSH.",
            ),
            dict(
                title="Shallow clone",
                command="git clone --depth 1 https://github.com/user/repo.git",
                output="",
                description="Clone only latest commit.",
            ),
        ],
        options=[
            dict(flag="--depth", description="Shallow clone"),
            dict(flag="--branch", description="Clone specific branch"),
            dict(flag="--recursive", description="Clone submodules"),
        ],
        related_commands=[
            dict(name="git-init", relationship="initialize repo"),
            dict(name="git-push", relationship="push to remote"),
        ],
        tags=["git", "clone"],
    ),
    _cmd(
        "git-commit",
        "git",
        "Record changes to the repository",
        "Records staged changes in the repository with a descriptive message.",
        "git commit [OPTION]...",
        difficulty="intermediate",
        keywords="git, commit, changes, save",
        official_docs="https://git-scm.com/docs/git-commit",
        examples=[
            dict(
                title="Commit staged",
                command="git commit -m 'feat: add login'",
                output="[main abc1234] feat: add login",
                description="Commit with message.",
            ),
            dict(
                title="Commit all",
                command="git commit -a -m 'fix: resolve bug'",
                output="",
                description="Stage all and commit.",
            ),
        ],
        options=[
            dict(flag="-m", description="Message"),
            dict(flag="-a", description="Stage all"),
            dict(flag="--amend", description="Amend last commit"),
        ],
        related_commands=[
            dict(name="git-add", relationship="stage changes"),
            dict(name="git-push", relationship="push commits"),
        ],
        tags=["git", "commit"],
    ),
    _cmd(
        "git-branch",
        "git",
        "List, create, or delete branches",
        "Manages Git branches for parallel development.",
        "git branch [OPTION]... [BRANCH_NAME]",
        difficulty="intermediate",
        keywords="git, branch, branches",
        official_docs="https://git-scm.com/docs/git-branch",
        examples=[
            dict(
                title="List branches",
                command="git branch",
                output="* main\\n  feature",
                description="Show local branches.",
            ),
            dict(
                title="Create branch",
                command="git branch feature-login",
                output="",
                description="Create new branch.",
            ),
            dict(
                title="Delete branch",
                command="git branch -d old-feature",
                output="Deleted branch old-feature.",
                description="Delete merged branch.",
            ),
        ],
        options=[
            dict(flag="-d", description="Delete"),
            dict(flag="-D", description="Force delete"),
            dict(flag="-a", description="All branches (including remote)"),
        ],
        related_commands=[
            dict(name="git-checkout", relationship="switch branches"),
            dict(name="git-merge", relationship="merge branches"),
        ],
        tags=["git", "branching"],
    ),
    # ── Docker ──────────────────────────────────────────────────────────
    _cmd(
        "docker",
        "docker",
        "Container management tool",
        "Manages containers, images, volumes, and networks for Docker.",
        "docker [COMMAND] [ARG...]",
        difficulty="intermediate",
        risk_level="CAUTION",
        keywords="docker, container, image",
        official_docs="https://docs.docker.com/engine/reference/commandline/docker/",
        examples=[
            dict(
                title="List containers",
                command="docker ps",
                output="CONTAINER ID IMAGE STATUS PORTS",
                description="Running containers.",
            ),
            dict(
                title="List images",
                command="docker images",
                output="REPOSITORY TAG IMAGE ID CREATED SIZE",
                description="Local images.",
            ),
        ],
        options=[
            dict(flag="ps", description="List containers"),
            dict(flag="images", description="List images"),
            dict(flag="run", description="Run container"),
            dict(flag="stop", description="Stop container"),
        ],
        related_commands=[
            dict(name="docker-ps", relationship="list containers"),
            dict(name="docker-run", relationship="run containers"),
        ],
        tags=["docker", "containers"],
    ),
    _cmd(
        "docker-ps",
        "docker",
        "List Docker containers",
        "Lists running containers. Use -a to show all containers including stopped ones.",
        "docker ps [OPTION]...",
        difficulty="intermediate",
        keywords="docker, ps, containers, list",
        official_docs="https://docs.docker.com/engine/reference/commandline/ps/",
        examples=[
            dict(
                title="Running containers",
                command="docker ps",
                output="CONTAINER ID IMAGE COMMAND STATUS PORTS",
                description="Show running containers.",
            ),
            dict(
                title="All containers",
                command="docker ps -a",
                output="",
                description="Show all containers including stopped.",
            ),
        ],
        options=[
            dict(flag="-a", description="All containers"),
            dict(flag="-q", description="Quiet (IDs only)"),
            dict(flag="--filter", description="Filter output"),
        ],
        related_commands=[
            dict(name="docker", relationship="Docker CLI"),
            dict(name="docker-run", relationship="run containers"),
        ],
        tags=["docker", "containers"],
    ),
    # ── Python ──────────────────────────────────────────────────────────
    _cmd(
        "python3",
        "python",
        "Python interpreter",
        "The Python 3 programming language interpreter. Used to execute Python scripts and run interactive sessions.",
        "python3 [OPTION]... [FILE] [ARG...]",
        keywords="python, python3, interpreter, script",
        official_docs="https://docs.python.org/3/",
        examples=[
            dict(
                title="Run script",
                command="python3 script.py",
                output="",
                description="Execute Python script.",
            ),
            dict(
                title="Interactive",
                command="python3",
                output="Python 3.12.0 ...\\n>>>",
                description="Start interactive session.",
            ),
            dict(
                title="Module as script",
                command="python3 -m http.server 8000",
                output="Serving HTTP on 0.0.0.0 port 8000",
                description="Run module as script.",
            ),
        ],
        options=[
            dict(flag="-m", description="Run module"),
            dict(flag="-c", description="Execute string"),
            dict(flag="-i", description="Interactive after script"),
        ],
        related_commands=[dict(name="pip", relationship="Python package manager")],
        tags=["python", "interpreter"],
    ),
    _cmd(
        "pip",
        "python",
        "Python package installer",
        "Installs, upgrades, and manages Python packages from PyPI.",
        "pip [COMMAND] [PACKAGE...]",
        keywords="pip, python, package, install",
        official_docs="https://pip.pypa.io/",
        examples=[
            dict(
                title="Install package",
                command="pip install requests",
                output="Successfully installed requests",
                description="Install from PyPI.",
            ),
            dict(
                title="List packages",
                command="pip list",
                output="Package    Version\\nrequests   2.31.0",
                description="Installed packages.",
            ),
            dict(
                title="Freeze requirements",
                command="pip freeze > requirements.txt",
                output="",
                description="Export installed packages.",
            ),
        ],
        options=[
            dict(flag="install", description="Install packages"),
            dict(flag="uninstall", description="Remove packages"),
            dict(flag="list", description="List packages"),
            dict(flag="freeze", description="Output in requirements format"),
        ],
        common_errors=[
            dict(
                error_pattern="No matching distribution",
                explanation="Package not found.",
                solution="Check spelling.",
            )
        ],
        related_commands=[
            dict(name="python3", relationship="Python interpreter"),
            dict(name="venv", relationship="virtual environments"),
        ],
        tags=["python", "packages"],
    ),
    # ── Security ────────────────────────────────────────────────────────
    _cmd(
        "ssh-keygen",
        "security",
        "Generate SSH key pairs",
        "Generates, manages, and converts SSH authentication keys.",
        "ssh-keygen [OPTION]...",
        difficulty="intermediate",
        keywords="ssh, key, generate, authentication",
        official_docs="https://man7.org/linux/man-pages/man1/ssh-keygen.1.html",
        examples=[
            dict(
                title="Generate RSA key",
                command="ssh-keygen -t rsa -b 4096",
                output="Generating public/private rsa key pair.",
                description="Generate 4096-bit RSA key.",
            ),
            dict(
                title="Generate Ed25519 key",
                command="ssh-keygen -t ed25519",
                output="",
                description="Generate Ed25519 key (recommended).",
            ),
        ],
        options=[
            dict(flag="-t", description="Key type"),
            dict(flag="-b", description="Bits"),
            dict(flag="-f", description="Output file"),
            dict(flag="-N", description="Passphrase"),
        ],
        related_commands=[
            dict(name="ssh", relationship="remote login"),
            dict(name="ssh-copy-id", relationship="copy key to host"),
        ],
        tags=["security", "ssh", "keys"],
    ),
    _cmd(
        "ufw",
        "security",
        "Uncomplicated firewall",
        "User-friendly interface for managing iptables firewall rules.",
        "ufw [COMMAND] [OPTION]...",
        risk_level="CAUTION",
        keywords="ufw, firewall, security, iptables",
        notes="Enable with ufw enable after configuring rules.",
        official_docs="https://man7.org/linux/man-pages/man8/ufw.8.html",
        examples=[
            dict(
                title="Allow SSH",
                command="sudo ufw allow ssh",
                output="Rule added",
                description="Allow SSH connections.",
            ),
            dict(
                title="Enable firewall",
                command="sudo ufw enable",
                output="Firewall is active",
                description="Enable the firewall.",
            ),
            dict(
                title="Check status",
                command="sudo ufw status",
                output="Status: active",
                description="Show firewall status.",
            ),
        ],
        options=[
            dict(flag="enable", description="Enable firewall"),
            dict(flag="disable", description="Disable"),
            dict(flag="allow", description="Allow port/service"),
            dict(flag="deny", description="Deny port/service"),
        ],
        common_errors=[
            dict(
                error_pattern="ERROR: Need to be root",
                explanation="Must use sudo.",
                solution="Use sudo ufw.",
            )
        ],
        related_commands=[dict(name="iptables", relationship="low-level firewall")],
        tags=["security", "firewall"],
    ),
]


_ALIAS_MAP: dict[str, list[str]] = {
    "ls": ["list"],
    "rm": ["del", "delete"],
    "cp": ["copy"],
    "mv": ["move", "rename"],
    "gunzip": [],
    "ps": ["process"],
    "top": ["htop"],
    "apt": ["apt-get", "apt-cache"],
    "dnf": ["yum"],
    "ip": ["ifconfig"],
    "ssh-keygen": [],
    "ufw": [],
    "systemctl": [],
    "journalctl": [],
    "python3": ["python"],
    "pip": ["pip3"],
    "docker-ps": [],
    "docker": [],
    "git": [],
    "git-clone": [],
    "git-commit": [],
    "git-branch": [],
    "sudo": [],
    "su": [],
    "useradd": ["adduser"],
    "usermod": [],
    "userdel": ["deluser"],
    "passwd": [],
    "df": ["diskfree"],
    "du": ["diskusage"],
    "lsblk": [],
    "fdisk": [],
    "mkfs": ["mkfs.ext4", "mkfs.xfs"],
    "mount": [],
    "umount": [],
    "tar": [],
    "gzip": ["gunzip"],
    "zip": ["unzip"],
    "ping": [],
    "curl": [],
    "wget": [],
    "ssh": [],
    "scp": [],
    "traceroute": ["tracert"],
    "nslookup": ["dig", "host"],
    "ss": ["netstat"],
    "lsof": [],
    "nmap": [],
    "free": [],
    "uptime": [],
    "dmesg": [],
    "uname": [],
    "crontab": [],
    "find": [],
    "tree": [],
    "grep": [],
    "sed": [],
    "awk": ["gawk"],
    "cut": [],
    "sort": [],
    "uniq": [],
    "wc": ["wordcount"],
    "chmod": [],
    "chown": [],
    "chgrp": [],
    "umask": [],
    "touch": [],
    "mkdir": [],
}


def get_commands() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for cmd in _COMMANDS_DATA:
        name = cmd["name"]
        if name not in seen:
            seen.add(name)
            if not cmd.get("aliases"):
                cmd["aliases"] = _ALIAS_MAP.get(name, [])
            result.append(cmd)
    return result


def get_command_names() -> list[str]:
    return sorted(set(cmd["name"] for cmd in _COMMANDS_DATA))


def get_categories() -> list[str]:
    return sorted(set(cmd["category"] for cmd in _COMMANDS_DATA))
