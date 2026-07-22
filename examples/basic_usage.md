# Basic Usage Examples

## Getting Help

```bash
# Show top-level help
ss --help

# Show help for a specific command
ss config --help
ss config set --help
```

## Version and Information

```bash
# Show version
ss --version
ss version

# Show system information
ss info
```

## Diagnostics

```bash
# Run system health check
ss doctor
```

## Configuration Management

```bash
# View all configuration
ss config show

# Get a specific value
ss config get general.theme
ss config get ai.enabled

# Set a value
ss config set general.theme dark
ss config set ai.enabled true
ss config set ai.model gpt-4

# Reset to defaults
ss config reset

# Show config file path
ss config path
```

## Common Workflow

```bash
# 1. Check your system
ss doctor

# 2. View system info
ss info

# 3. Customize configuration
ss config set general.theme dark

# 4. Verify settings
ss config show
```
