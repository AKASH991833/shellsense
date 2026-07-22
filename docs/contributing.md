# Contributing to ShellSense AI

We welcome contributions! Here's how you can help.

## Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Install development dependencies
4. Make your changes
5. Run tests and linting
6. Submit a pull request

## Development Workflow

```bash
# Setup
git clone https://github.com/your-username/shellsense.git
cd shellsense-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .

# Before committing
make lint
make typecheck
make test
```

## Pull Request Guidelines

- Keep PRs focused on a single feature or fix
- Write clear commit messages
- Add tests for new functionality
- Update documentation if needed
- Ensure all checks pass

## Code of Conduct

Be respectful and constructive in all communications.

## Reporting Issues

Report bugs and suggest features via [GitHub Issues](https://github.com/shellsense-ai/shellsense/issues).
