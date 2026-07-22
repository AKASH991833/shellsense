# ShellSense AI

<p align="center">
  <b>Think Less. Command More.</b><br>
  <i>Intelligent Linux Terminal Assistant — Fish-like autosuggestions for Bash/Zsh/Fish</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python 3.12+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License">
  <img src="https://img.shields.io/badge/shell-bash%20|%20zsh%20|%20fish-orange" alt="Shells">
  <img src="https://img.shields.io/badge/tests-493%20passed-brightgreen" alt="Tests">
</p>

---

## Demo

```
$ ▊                          →   $ git push origin main ▊
  (typing "git pu")              (grey ghost text suggests rest)

Press Ctrl-E or Ctrl-F to accept the suggestion.
```

ShellSense runs as a background daemon, learns your usage patterns, and suggests the right command before you finish typing — just like Fish shell, but for *any* shell.

---

## Features

### ⚡ Live Inline Autosuggestions
Ghost text appears as you type. Press `Ctrl-E` or `Ctrl-F` to accept. Works in Bash, Zsh, and Fish.

### 🔎 Fuzzy Matching
Typo-tolerant matching powered by RapidFuzz:
`gti pus` → `git push`, `chmo` → `chmod`, `systemct` → `systemctl`, `kubectl get po` → `kubectl get pods`

### 🧠 Context-Aware
Detects your current working context and boosts relevant commands:
- **Git repos** → suggests `git commit`, `git push`, `git log`
- **Docker projects** → suggests `docker compose up`, `docker build`
- **Kubernetes** → suggests `kubectl get pods`, `kubectl logs -f`
- **Python venvs** → suggests `pip install`, `python3 -m`
- **Terraform** → suggests `terraform plan`, `terraform apply`

### 📜 History-Aware
Learns your most-used commands and recency-boosts them. Commands you use often appear first.

### 🚀 Background Daemon
Persistent Unix socket server for sub-30ms responses. Auto-starts, multi-client safe, graceful shutdown.

### 🖥️ TUI Browser
`shellsense tui` launches a terminal UI to browse all 2000+ indexed commands by category with search and detail view.

### 🔄 Ctrl+R History Search
Fuzzy-search your command history with RapidFuzz + `fzf` integration. Press `Ctrl+R` to search interactively.

### 🛡️ Error Correction
When a command fails (non-zero exit), ShellSense analyzes the error and suggests a fix.

### 🔌 2000+ Commands Discovered
Automatically indexes every command on your system from man pages, help output, and PATH binaries.

---

## Quick Start

```bash
# Install from GitHub
pip install git+https://github.com/AKASH991833/shellsense.git

# One-command setup (daemon + scan + shell hooks)
shellsense init

# Reload your shell
exec bash
```

You can also use the alias `shs` instead of `shellsense`.

---

## Installation

### Via pip

```bash
pip install git+https://github.com/AKASH991833/shellsense.git
```

### From source

```bash
git clone https://github.com/AKASH991833/shellsense.git
cd shellsense
pip install -e ".[dev]"
```

### Dependencies

- Python 3.12+
- Linux (Bash, Zsh, or Fish)
- Recommended: `rapidfuzz`, `rich`, `fzf` (for Ctrl+R search)

---

## Usage

### Live Suggestions (Inline)

Once installed and your shell is reloaded, suggestions appear automatically as you type:

| Typing | Suggestion |
|--------|------------|
| `git pu` | `git push origin main` |
| `docker-com` | `docker compose up` |
| `sudo sys` | `sudo systemctl status` |
| `kubectl get po` | `kubectl get pods --all-namespaces` |
| `chmo` | `chmod` |
| `python3 -m` | `python3 -m venv .venv` |
| `ssh root@` | `ssh root@server_ip` |

Press `Ctrl-E` or `Ctrl-F` to accept.

### Ctrl+R History Search

Press `Ctrl+R` at any prompt to fuzzy-search your command history interactively with `fzf`.

### Commands

```bash
# Suggest a command
shellsense suggest "git com"

# Search indexed commands
shellsense search "find large files"

# Explain a command
shellsense explain "git rebase -i HEAD~3"

# Check command safety
shellsense check "rm -rf /"

# TUI browser
shellsense tui

# Daemon management
shellsense daemon start
shellsense daemon status
shellsense daemon restart
shellsense daemon stop

# Diagnostics
shellsense doctor

# Repair installation
shellsense repair

# AI assistant (requires API key)
shellsense ai chat "How do I grep for multiple patterns?"
```

### Daemon

The daemon runs as a background Unix socket server:

```bash
shellsense daemon start     # Fork to background
shellsense daemon status    # Show PID, uptime, stats
shellsense daemon stop      # Graceful shutdown
```

Auto-start on login:

```bash
systemctl --user enable shellsense-daemon
```

---

## Configuration

Config file: `~/.shellsense/config.json`

```json
{
  "general": {
    "theme": "auto",
    "language": "en"
  },
  "daemon": {
    "auto_start": true,
    "port": 0
  },
  "features": {
    "autosuggest": true,
    "error_correction": true,
    "context_detection": true
  }
}
```

---

## TUI Browser

```
shellsense tui
```

A Rich-powered terminal browser that lets you:
- Browse commands by category (git, docker, kubectl, system, etc.)
- Search commands with `/`
- View full command details and descriptions
- Navigate with arrow keys

---

## Architecture

```
~/.shellsense/
├── config.json              # User configuration
├── shellsense.db            # SQLite database (commands, history, metadata)
├── cache/                   # Suggestion cache, marketplace, AI cache
├── plugins/                 # Loadable plugins
├── conversations/           # AI chat history
└── logs/                    # Daemon logs

/tmp/shellsense-daemon.sock  # Unix socket
/tmp/shellsense-daemon.pid   # PID file
```

### How It Works

1. **Discover**: On first run, ShellSense scans your system for all available commands (man pages, `--help`, PATH binaries).
2. **Index**: Commands are stored in SQLite with metadata, categories, and descriptions.
3. **Daemon**: A persistent daemon loads the database into memory and responds to suggestion requests via Unix socket.
4. **Suggest**: Each keystroke queries the daemon, which ranks suggestions by fuzzy match, history frequency, recency, and context.
5. **Display**: The shell hook renders the top suggestion as ghost text inline.

---

## Development

```bash
git clone https://github.com/AKASH991833/shellsense.git
cd shellsense
pip install -e ".[dev]"

# Run tests
pytest
pytest -v
pytest tests/ -k "suggest"   # Run specific test module

# Lint & format
black src/shellsense/ tests/
ruff check src/shellsense/
mypy src/shellsense/

# Type check specific modules
mypy src/shellsense/daemon/server.py
mypy src/shellsense/knowledge/suggest.py
```

### Test Suite

- **493 tests** covering: suggestions, fuzzy matching, history ranking, context detection, IPC protocol, daemon lifecycle, shell integration, CLI commands
- All tests pass, Black-clean across 186 files, mypy-clean on all core modules

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Suggestions not appearing | Run `shellsense doctor` or `shellsense repair` |
| Daemon won't start | Check `/tmp/shellsense-daemon.log` for errors |
| Stale socket file | `shellsense daemon stop` removes old socket |
| Shell not sourced | `shellsense install` reinstalls shell hooks |
| `ss` command not found | CLI is `shellsense` (or `shs`), not `ss` |

---

## License

MIT © Akash Vishwakarma
