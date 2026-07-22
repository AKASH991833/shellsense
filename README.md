# ShellSense AI

> **Think Less. Command More.**

ShellSense AI is an intelligent Linux terminal assistant that helps users work more efficiently inside the terminal. It provides command suggestions, spelling correction, command explanations, Linux learning, error analysis, AI-powered assistance, automation generation, plugin SDK, and marketplace.

---

## Features

- **Command Suggestions** — Get intelligent command suggestions as you type
- **Search & Discovery** — Search commands, categories, related commands
- **Spelling Correction** — Automatically fix typos in commands
- **Command Explanations** — Understand what a command does before running it
- **Linux Learning** — Learn Linux concepts interactively
- **Error Analysis** — Get explanations and fixes for command errors
- **AI Assistance** — Natural language to command translation
- **Terminal Intelligence** — Context-aware prompts, privacy controls
- **Automation Generation** — Generate bash, systemd, docker, cron, and more
- **Plugin SDK** — Extend ShellSense with custom plugins
- **Plugin Marketplace** — Discover and install community plugins
- **Enterprise Policies** — Compliance, audit logging, approved/blocked lists
- **Backup & Recovery** — Backup and restore config, database, plugins
- **Shell Integration** — Seamless integration with your shell

---

## Installation

### Prerequisites

- **Python 3.12+**
- **Linux** (Ubuntu, Debian, Fedora, Arch, openSUSE, and more)
- **pip**

### Quick Install

```bash
git clone https://github.com/shellsense-ai/shellsense.git
cd shellsense-ai
pip install -e .
```

### Using Docker

```bash
docker build -t shellsense .
docker run --rm shellsense --help
```

### Verify Installation

```bash
ss --version
ss doctor
```

---

## Usage

```bash
# Show help
ss --help

# Show version
ss --version

# Show system information
ss info

# Run diagnostics
ss doctor

# Manage configuration
ss config show
ss config get general.theme
ss config set general.theme dark
ss config reset
ss config path

# Backup and restore
ss backup create                          # Full backup
ss backup create --item config            # Backup config only
ss backup list                            # List backups
ss backup restore <backup_name>           # Restore from backup

# Search commands
ss search find file by name
ss explain tar
ss examples grep

# AI assistance (requires AI provider)
ss ask "how to compress a directory"
ss fix "error: command not found"

# Automation generation
ss generate bash.backup-script --output ./scripts
ss generate systemd.service --name myapp
ss template list

# Plugin management
ss plugin list
ss plugin install /path/to/plugin
ss plugin create my-plugin

# Marketplace
ss marketplace search docker
ss marketplace install docker-helper
ss marketplace verify docker-helper

# Privacy controls
ss privacy show
ss privacy deny share_git_info
```

---

## Configuration

Configuration is stored at `~/.shellsense/config.json`. You can manage it via:

```bash
ss config show      # View all settings
ss config get <key> # Get a specific value
ss config set <key> <value>  # Set a value
ss config reset     # Restore defaults
ss config path      # Show config file location
```

---

## Development

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

### Code Quality

```bash
make lint     # Run ruff and mypy
make format   # Run black
make typecheck  # Run mypy
```

### Testing

```bash
make test     # Run pytest
make coverage # Run with coverage
```

---

## Project Structure

```
shellsense-ai/
├── src/
│   └── shellsense/
│       ├── cli/             # CLI commands and Typer app
│       ├── ai/              # AI abstraction layer and providers
│       ├── automation/      # Automation & infrastructure generation
│       ├── core/            # Core exceptions and base classes
│       ├── database/        # SQLite database management
│       ├── intelligence/    # Terminal intelligence layer
│       ├── knowledge/       # Command knowledge engine
│       ├── marketplace/     # Plugin marketplace & enterprise
│       ├── plugins/         # Plugin SDK & extension framework
│       ├── shell/           # Live shell integration
│       └── utils/           # Configuration, logging, i18n, platform
├── tests/                   # Comprehensive test suite
├── docs/                    # Documentation
├── installer/               # Installation scripts
├── scripts/                 # Development and build scripts
├── resources/               # Static resources
├── examples/                # Usage examples
├── Dockerfile               # Container image
├── SECURITY.md              # Security policy
├── CHANGELOG.md             # Release history
└── pyproject.toml           # Project metadata
```

---

## Roadmap

- **Phase 1** — Project foundation
- **Phase 2** — Command knowledge engine
- **Phase 3** — Intelligent suggestion engine
- **Phase 4** — Live shell integration
- **Phase 5** — AI abstraction layer
- **Phase 6** — Terminal intelligence layer
- **Phase 7** — Automation & infrastructure generator
- **Phase 8** — Plugin SDK & extension framework
- **Phase 9** — Plugin marketplace & enterprise collaboration
- **Phase 10** — Production hardening, packaging, security, v1.0.0 (complete)

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Support

- Documentation: https://shellsense-ai.github.io/shellsense
- Issues: https://github.com/shellsense-ai/shellsense/issues
- Security: https://github.com/shellsense-ai/shellsense/security/policy
