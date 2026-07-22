# Developer Guide

## Development Environment Setup

### Prerequisites

- Python 3.12+
- Git
- Visual Studio Code (recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/shellsense-ai/shellsense.git
cd shellsense-ai
```

### Step 2: Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements-dev.txt
pip install -e .
```

### Step 4: Verify Setup

```bash
ss --version
ss doctor
```

## Code Quality

### Formatting

```bash
black src/ tests/
```

### Linting

```bash
ruff check src/ tests/
```

### Type Checking

```bash
mypy src/
```

### Testing

```bash
pytest
```

With coverage:

```bash
pytest --cov=shellsense --cov-report=html
```

## Project Architecture

The project follows a modular architecture:

- `src/shellsense/cli/` — CLI interface using Typer
- `src/shellsense/core/` — Core abstractions and exceptions
- `src/shellsense/database/` — SQLite database management
- `src/shellsense/utils/` — Utilities (config, logging, platform)

## Adding a New Command

1. Create the command function in `src/shellsense/cli/commands/`
2. Import and register it in `src/shellsense/cli/app.py`
3. Add tests in `tests/`

## Code Standards

- Follow PEP 8
- Use type hints for all function signatures
- Write docstrings for all public functions
- Keep functions small and focused (single responsibility)
- Use dependency injection where appropriate
- Log significant operations
