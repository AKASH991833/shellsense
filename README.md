# ShellSense AI

**Think Less. Command More. — Intelligent Linux Terminal Assistant**

ShellSense brings Fish-like autosuggestions, context-aware command prediction, and workflow automation to any Linux terminal (Bash, Zsh, Fish). It runs as a background daemon, learns your usage patterns, and suggests the right command before you finish typing.

## Features

- **Live inline suggestions** — ghost text appears as you type (like Fish shell)
- **Fuzzy matching** — `gti pus` → `git push`, `chmo` → `chmod`, `systemct` → `systemctl`
- **History-aware** — learns your frequently used commands and prioritizes them
- **Context-aware** — detects git repos, Dockerfiles, Python venvs, kubectl contexts, terraform projects
- **Workflow automation** — `kubectl get pods` → suggests `kubectl logs -f`, `git add` → suggests `git commit`
- **Command discovery** — automatically indexes all 2000+ commands on your system
- **Background daemon** — persistent Unix socket server for sub-30ms responses
- **Multi-shell support** — Bash, Zsh, Fish with native integration
- **Zero-latency** — in-memory cache, parallel discovery, optimized SQLite

## Quick Start

```bash
# Install
pip install git+https://github.com/AKASH991833/shellsense.git

# One-command setup (daemon + discovery + shell hooks)
shellsense init

# Or manually:
shellsense daemon start
shellsense discover scan
shellsense install

# Reload your shell
exec bash
```

## Usage

### Live suggestions (inline, while typing)

| Typing | Suggestion |
|--------|------------|
| `git pu` | `git push origin main` |
| `sudo sys` | `sudo systemctl` |
| `dock` | `docker` |
| `kubectl get po` | `kubectl get pods` |
| `chmo` | `chmod` |
| `python3 -m` | `python3 -m venv` |

Press `Ctrl-E` or `Ctrl-F` to accept the suggestion.

### Commands

```bash
# Command suggestions
shellsense suggest "git com"

# Search commands
shellsense search "find large files"

# Explain a command
shellsense explain "git rebase -i HEAD~3"

# Check command safety
shellsense check "rm -rf /"

# Daemon management
shellsense daemon status
shellsense daemon restart

# System diagnostics
shellsense doctor

# Repair installation
shellsense repair

# Get AI assistance (if API key configured)
shellsense ai chat "How do I grep for multiple patterns?"
```

You can also use the alias: `shs` instead of `shellsense`.

### Daemon

The daemon runs as a background Unix socket server:

```bash
shellsense daemon start     # Fork to background
shellsense daemon status    # Show PID, uptime, stats
shellsense daemon stop      # Graceful shutdown
shellsense daemon suggest "git com"   # Quick suggestion
```

Auto-start on login with systemd:

```bash
systemctl --user enable shellsense-daemon
```

## Architecture

```
~/.shellsense/
├── config.json          # Configuration
├── shellsense.db        # SQLite database (commands, history, discovered)
├── cache/               # Suggestion cache, marketplace, AI cache
├── plugins/             # Loadable plugins
├── conversations/       # AI chat history
└── logs/                # Daemon logs

/tmp/shellsense-daemon.sock  # Unix socket
/tmp/shellsense-daemon.pid   # PID file
```

## Requirements

- Python 3.12+
- Linux (Bash, Zsh, or Fish)
- Recommended: `rapidfuzz` (for fuzzy matching), `rich` (for CLI output)

## Development

```bash
git clone https://github.com/AKASH991833/shellsense.git
cd shellsense
pip install -e ".[dev]"
pytest
black src/shellsense/ tests/
ruff src/shellsense/
mypy src/shellsense/
```

## License

MIT
