# Architecture Overview

## High-Level Architecture

ShellSense AI follows a modular, layered architecture designed for extensibility.

```
┌─────────────────────────────────────────┐
│              CLI Layer                   │
│  (Typer commands: ss, info, config...)  │
├─────────────────────────────────────────┤
│            Core Layer                    │
│  (Exceptions, base classes)             │
├─────────────────────────────────────────┤
│          Utility Layer                   │
│  (Config, Logging, Platform)            │
├─────────────────────────────────────────┤
│         Database Layer                   │
│  (SQLite, models, migrations)           │
├─────────────────────────────────────────┤
│         Future Layers                    │
│  (AI, Shell Integration, Plugins)       │
└─────────────────────────────────────────┘
```

## Layer Responsibilities

### CLI Layer (`src/shellsense/cli/`)

Entry point for all user interactions. Uses Typer for command-line argument parsing and Rich for terminal output formatting.

### Core Layer (`src/shellsense/core/`)

Contains base classes, custom exceptions, and shared abstractions used across the application.

### Utility Layer (`src/shellsense/utils/`)

Provides cross-cutting services:

- **Configuration** — JSON-based config management
- **Logging** — Structured logging with file and console output
- **Platform** — System information and platform detection
- **Paths** — Standardized path resolution

### Database Layer (`src/shellsense/database/`)

SQLite database with schema versioning and thread-safe access patterns.

## Design Principles

- **Separation of Concerns** — Each module has a single, well-defined responsibility
- **Dependency Injection** — Components receive their dependencies explicitly
- **SOLID Principles** — Single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion
- **Fail Gracefully** — All errors are caught and presented user-friendly
- **Extensibility** — New features are added by extending existing modules, not modifying them

## Data Flow

```
User Input → CLI (Typer) → Command Handler → Utility/Database → Output (Rich)
```

## Configuration

Configuration is stored in `~/.shellsense/config.json` with sensible defaults. All settings are accessible via the `ss config` command.

## Database

SQLite database stored at `~/.shellsense/shellsense.db`. Schema is versioned for future migrations.
