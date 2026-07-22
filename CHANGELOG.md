# Changelog

## 1.0.0 (2026-07-21)

### Production Release

ShellSense AI reaches its first stable release. All previous functionality is fully backward-compatible.

### Added
- **Backup & Recovery**: New `ss backup` commands (`create`, `restore`, `list`) for config, database, plugins, and logs
- **Internationalization**: i18n architecture with language file support, translation key infrastructure, locale detection
- **Enhanced Diagnostics**: Comprehensive `ss doctor` with 10 check categories (platform, installation, config, database, plugins, marketplace, AI providers, permissions, performance, packages)
- **Security Hardening**:
  - Config directory permissions set to 0700 (restrictive)
  - Config file permissions set to 0600
  - Plugin sandbox executor now restricts imports via `__import__` override
  - API key detection in diagnostics
- **Logging**: Rotating file handler (10MB max, 5 backups)
- **Packaging**: Production/Stable classifier, optional-dependencies for AI providers, maintainers field
- **CI/CD**: GitHub Actions workflow for linting, type checking, tests, security scanning, and build
- **Dockerfile**: Container image support
- **Security policy**: SECURITY.md with vulnerability reporting guidelines
- **Pre-commit**: Pre-commit configuration for code quality

### Changed
- Version bumped from 0.1.0 to 1.0.0 (semantic versioning)
- Renamed `GitIntelligence.git_intel` to `git_intelligence` for consistency
- Consolidated duplicate imports in knowledge/engine.py, knowledge/related.py
- Enhanced sandbox executor with restricted import enforcement
- Updated pyproject.toml metadata (classifiers, URLs, optional deps)

### Fixed
- Removed dead code: `get_commands_by_category()` in dataset.py, unused `pass` in ai/core.py, unused `HOOK_TEMPLATES` in shell/hooks.py
- Removed unused imports: `timedelta` in knowledge/history.py, duplicate `get_command_by_name` in knowledge/related.py, unused `optimize_callback` alias in cli/app.py
- Plugin `isolation.py` sandbox executor now properly restricts module imports

### Security
- Config directory now created with 0700 permissions
- Config file permissions checked in diagnostics
- Plugin import sandboxing enforced via restricted builtins
- API key plaintext storage warning in diagnostics
- Path traversal protection in backup/restore commands

### Documentation
- Comprehensive CHANGELOG.md
- SECURITY.md with vulnerability reporting
- Pre-commit configuration
- Dockerfile for containerized deployment
